import json, re


def SearchDB(
	table: str,
	query: str,
	is_regex: bool = False,
	db_path: str = "db.json",
	dblimit: int = 20,
	theme: list[str | int] | str | int | None = None,
):
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
