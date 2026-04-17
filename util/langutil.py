import json

def check_language_keys(language_path: str, keys: str) -> list[str]:
	with open(keys, "r", encoding="utf-8") as f:
		lang_keys = json.load(f)
	with open(language_path, "r", encoding="utf-8") as f:
		language_dict = json.load(f)
	missing_keys = [key for key in lang_keys if key not in language_dict]
	return missing_keys

def getlang(language_dict: dict, key: str) -> str:
	return language_dict.get(key, f"Missing language key: {key}")