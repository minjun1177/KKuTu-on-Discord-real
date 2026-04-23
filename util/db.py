import json
import re
import importlib
import logging
import sys
import os
from typing import Any

logging.basicConfig(
	level=logging.INFO,
	format='[%(asctime)s] %(message)s',
	datefmt='%H:%M:%S',
	stream=sys.stdout,
)
logger = logging.getLogger(__name__)

def CheckDB(USE_PGSQL, pginfo, jsonpath) -> None:
	if isinstance(pginfo, dict) and isinstance(pginfo.get("PGSQL_CONFIG"), dict):
		PGSQL_CONFIG = pginfo.get("PGSQL_CONFIG", {})
	else:
		PGSQL_CONFIG = pginfo if isinstance(pginfo, dict) else {}

	if USE_PGSQL:
		try:
			psycopg2 = importlib.import_module("psycopg2")
		except ImportError as exc:
			raise RuntimeError(
				"psycopg2 is not installed."
			) from exc

		try:
			with psycopg2.connect(
				host=PGSQL_CONFIG.get("host", "localhost"),
				port=PGSQL_CONFIG.get("port", 5432),
				user=PGSQL_CONFIG.get("user", "postgres"),
				password=PGSQL_CONFIG.get("password", ""),
				dbname=PGSQL_CONFIG.get("database", "main"),
			) as conn:
				with conn.cursor() as cur:
					cur.execute('SELECT 1 FROM "kkutu_ko" LIMIT 1')
					cur.fetchone()
		except Exception as exc:
			raise RuntimeError(
				"DB connection check failed: Please check connection information or kkutu_ko table."
			) from exc

		logger.info("DB Check passed (backend=pgsql)")
		return

	if not os.path.exists(jsonpath):
		raise RuntimeError(f"DB json not found: {jsonpath}")

	try:
		with open(jsonpath, "r", encoding="utf-8") as f:
			db_json = json.load(f)
	except json.JSONDecodeError as exc:
		raise RuntimeError(f"DB json parsing failed: {jsonpath}") from exc

	table_data = db_json.get("kkutu_ko")
	if not isinstance(table_data, list):
		raise RuntimeError("DB json check failed: kkutu_ko key is missing or not a list.")

	logger.info("DB Check passed (backend=json)")

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

def _load_table_json(db_path: str, table: str) -> list[dict[str, Any]]:
	try:
		with open(db_path, "r", encoding="utf-8") as f:
			db = json.load(f)
		rows = db.get(table, [])
		return rows if isinstance(rows, list) else []
	except (FileNotFoundError, json.JSONDecodeError, TypeError):
		return []


def _to_theme_values(theme_raw: Any) -> list[str]:
	if theme_raw is None:
		return []
	if isinstance(theme_raw, list):
		return [str(v) for v in theme_raw]
	theme_str = str(theme_raw)
	if "," in theme_str:
		return [v.strip() for v in theme_str.split(",") if v.strip()]
	return [theme_str]


def SearchByChar(
	table: str,
	char: str,
	position: str = "start",
	dblimit: int = 20,
	db_path: str = "db.json",
	use_pgsql: bool = False,
	pgsql_config: dict[str, Any] | None = None,
):
	limit = max(1, int(dblimit))
	like_prefix = str(char)

	if use_pgsql:
		if not _is_safe_table_name(table):
			return []
		try:
			psycopg2 = importlib.import_module("psycopg2")
		except ImportError:
			return []

		config = pgsql_config or {}
		like_pattern = f"{like_prefix}%" if position == "start" else f"%{like_prefix}"
		sql = (
			f'SELECT "_id", "type", "mean", "flag", "theme" FROM "{table}" '
			f'WHERE "_id" LIKE %s AND "_id" NOT LIKE %s '
			f'ORDER BY CHAR_LENGTH("_id") DESC LIMIT %s'
		)

		try:
			with psycopg2.connect(
				host=config.get("host", "localhost"),
				port=config.get("port", 5432),
				user=config.get("user", "postgres"),
				password=config.get("password", ""),
				dbname=config.get("database", "main"),
			) as conn:
				with conn.cursor() as cur:
					cur.execute(sql, (like_pattern, "% %", limit))
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

	rows = _load_table_json(db_path, table)
	if position == "start":
		filtered = [w for w in rows if str(w.get("_id", "")).startswith(like_prefix)]
	else:
		filtered = [w for w in rows if str(w.get("_id", "")).endswith(like_prefix)]

	filtered = [w for w in filtered if " " not in str(w.get("_id", ""))]
	filtered.sort(key=lambda w: len(str(w.get("_id", ""))), reverse=True)
	return filtered[:limit]


def SearchMissionWords(
	table: str,
	mission_char: str,
	topic: str | None = None,
	target_char: str | None = None,
	position: str = "start",
	dblimit: int = 20,
	db_path: str = "db.json",
	use_pgsql: bool = False,
	pgsql_config: dict[str, Any] | None = None,
):
	limit = max(1, int(dblimit))

	if use_pgsql:
		if not _is_safe_table_name(table):
			return []
		try:
			psycopg2 = importlib.import_module("psycopg2")
		except ImportError:
			return []

		config = pgsql_config or {}
		where_clauses = ['"_id" NOT LIKE %s']
		params: list[Any] = ["% %"]

		if target_char:
			like_pattern = f"{target_char}%" if position == "start" else f"%{target_char}"
			where_clauses.append('"_id" LIKE %s')
			params.append(like_pattern)

		if topic:
			where_clauses.append('CAST("theme" AS TEXT) ILIKE %s')
			params.append(f"%{topic}%")

		where_sql = " AND ".join(where_clauses)
		sql = (
			f'SELECT "_id", "type", "mean", "flag", "theme" FROM "{table}" '
			f'WHERE {where_sql} '
			f"ORDER BY (CHAR_LENGTH(\"_id\") - CHAR_LENGTH(REPLACE(\"_id\", %s, ''))) DESC, "
			f'CHAR_LENGTH("_id") DESC LIMIT %s'
		)
		params.append(mission_char)
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

	rows = _load_table_json(db_path, table)
	filtered = [w for w in rows if " " not in str(w.get("_id", ""))]

	if target_char:
		if position == "start":
			filtered = [w for w in filtered if str(w.get("_id", "")).startswith(target_char)]
		else:
			filtered = [w for w in filtered if str(w.get("_id", "")).endswith(target_char)]

	if topic:
		filtered = [
			w for w in filtered
			if any(str(topic) == str(v) for v in _to_theme_values(w.get("theme")))
		]

	filtered.sort(
		key=lambda w: (
			str(w.get("_id", "")).count(mission_char),
			len(str(w.get("_id", ""))),
		),
		reverse=True,
	)
	return filtered[:limit]


def SearchRandomWords(
	table: str,
	count: int,
	db_path: str = "db.json",
	use_pgsql: bool = False,
	pgsql_config: dict[str, Any] | None = None,
):
	limit = max(1, int(count))

	if use_pgsql:
		if not _is_safe_table_name(table):
			return []
		try:
			psycopg2 = importlib.import_module("psycopg2")
		except ImportError:
			return []

		config = pgsql_config or {}
		sql = (
			f'SELECT "_id", "type", "mean", "flag", "theme" FROM "{table}" '
			f'WHERE "_id" NOT LIKE %s ORDER BY RANDOM() LIMIT %s'
		)

		try:
			with psycopg2.connect(
				host=config.get("host", "localhost"),
				port=config.get("port", 5432),
				user=config.get("user", "postgres"),
				password=config.get("password", ""),
				dbname=config.get("database", "main"),
			) as conn:
				with conn.cursor() as cur:
					cur.execute(sql, ("% %", limit))
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

	rows = [w for w in _load_table_json(db_path, table) if " " not in str(w.get("_id", ""))]
	if not rows:
		return []

	import random

	if limit >= len(rows):
		random.shuffle(rows)
		return rows

	return random.sample(rows, limit)