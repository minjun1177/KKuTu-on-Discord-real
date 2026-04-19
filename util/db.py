import json
import re
import importlib
from typing import Any


def _is_safe_table_name(table: str) -> bool:
	return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table) is not None


def _parse_db_value(value: Any) -> Any:
	if isinstance(value, str):
		stripped = value.strip()
		if stripped and stripped[0] in "[{\"" and stripped[-1] in "]}\"":
			try:
				return json.loads(stripped)
			except json.JSONDecodeError:
				return value
	return value


def _search_db_pgsql(
	table: str,
	query: str,
	is_regex: bool,
	dblimit: int,
	theme: list[str | int] | str | int | None,
	pgsql_config: dict[str, Any] | None,
):
	if not _is_safe_table_name(table):
		return []

	try:
		psycopg2 = importlib.import_module("psycopg2")
	except ImportError:
		return []

	config = pgsql_config or {}
	limit = max(1, int(dblimit))

	where_clauses: list[str] = []
	params: list[Any] = []

	if is_regex:
		where_clauses.append('"_id" ~ %s')
		params.append(query)
	else:
		where_clauses.append('"_id" LIKE %s')
		params.append(f"%{query}%")

	if theme:
		themes = [theme] if isinstance(theme, (str, int)) else theme
		for theme_value in themes:
			where_clauses.append('CAST("theme" AS TEXT) ILIKE %s')
			params.append(f"%{theme_value}%")

	where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
	sql = (
		f'SELECT "_id", "type", "mean", "flag", "theme" '
		f'FROM "{table}" WHERE {where_sql} ORDER BY "_id" ASC LIMIT %s'
	)
	params.append(limit)

	try:
		with psycopg2.connect(
			host=config.get("host", "localhost"),
			port=config.get("port", 5432),
			user=config.get("user", "postgres"),
			password=config.get("password", ""),
			dbname=config.get("database", "main"),
		) as conn:
			with conn.cursor() as cur:
				cur.execute(sql, params)
				rows = cur.fetchall()

		results = []
		for row in rows:
			results.append(
				{
					"_id": row[0],
					"type": _parse_db_value(row[1]),
					"mean": _parse_db_value(row[2]),
					"flag": _parse_db_value(row[3]),
					"theme": _parse_db_value(row[4]),
				}
			)
		return results
	except Exception:
		return []


def _get_mean_pgsql(table: str, word: str, pgsql_config: dict[str, Any] | None):
	if not _is_safe_table_name(table):
		return None

	try:
		psycopg2 = importlib.import_module("psycopg2")
	except ImportError:
		return None

	config = pgsql_config or {}
	sql = f'SELECT "type", "mean", "flag", "theme" FROM "{table}" WHERE "_id" = %s LIMIT 1'

	try:
		with psycopg2.connect(
			host=config.get("host", "localhost"),
			port=config.get("port", 5432),
			user=config.get("user", "postgres"),
			password=config.get("password", ""),
			dbname=config.get("database", "main"),
		) as conn:
			with conn.cursor() as cur:
				cur.execute(sql, (word,))
				row = cur.fetchone()

		if not row:
			return None

		return {
			"type": _parse_db_value(row[0]),
			"mean": _parse_db_value(row[1]),
			"flag": _parse_db_value(row[2]),
			"theme": _parse_db_value(row[3]),
		}
	except Exception:
		return None


def SearchDB(
	table: str,
	query: str,
	is_regex: bool = False,
	db_path: str = "db.json",
	dblimit: int = 20,
	theme: list[str | int] | str | int | None = None,
	use_pgsql: bool = False,
	pgsql_config: dict[str, Any] | None = None,
):
	if use_pgsql:
		return _search_db_pgsql(
			table=table,
			query=query,
			is_regex=is_regex,
			dblimit=dblimit,
			theme=theme,
			pgsql_config=pgsql_config,
		)

	try:
		with open(db_path, "r", encoding="utf-8") as f:
			db = json.load(f)

		words = db.get(table, [])

		if is_regex:
			try:
				pattern = re.compile(query)
			except re.error:
				return []
			results = [word for word in words if pattern.search(word.get("_id", ""))]
		else:
			results = [word for word in words if query in word.get("_id", "")]

		if theme:
			# Support both scalar and list inputs, and match against numeric/string db themes.
			themes = [theme] if isinstance(theme, (str, int)) else theme
			theme_set = {str(t) for t in themes}
			results = [
				word for word in results
				if any(str(db_theme) in theme_set for db_theme in word.get("theme", []))
			]

		if not results:
			return []

		return results[:dblimit]
	except (FileNotFoundError, json.JSONDecodeError, TypeError):
		return []

def Getmean(
	table: str,
	word: str,
	db_path: str = "db.json",
	use_pgsql: bool = False,
	pgsql_config: dict[str, Any] | None = None,
) -> dict[str, str, str, list[str]] | None:
	if use_pgsql:
		return _get_mean_pgsql(table=table, word=word, pgsql_config=pgsql_config)

	try:
		with open(db_path, "r", encoding="utf-8") as f:
			db = json.load(f)
		words = db.get(table, [])
		for entry in words:
			if entry.get("_id") == word:
				return { "type": entry.get("type"), "mean": entry.get("mean"), "flag": entry.get("flag"), "theme": entry.get("theme") }
		return None
	except (FileNotFoundError, json.JSONDecodeError):
		return None