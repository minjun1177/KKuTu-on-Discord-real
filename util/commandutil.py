import re

VALID_WORD_CHARS = re.compile(r"^[0-9a-zA-Zㄱ-ㅣ가-힣]+$")


def detect_language(query: str) -> str:
	if re.search(r"[가-힣]", query or ""):
		return "ko"
	if re.fullmatch(r"[a-zA-Z]+", query or ""):
		return "en"
	return "ko"


def parse_meaning(mean) -> str | None:
	if not mean:
		return None

	text = str(mean)
	parts = [p.strip() for p in re.split(r"＂[0-9]+＂", text) if p and p.strip()]
	if not parts:
		return None

	return "\n".join(f"**{i}.** {part}" for i, part in enumerate(parts, start=1))


def format_word(word: str, flag, _type=None) -> str:
	text = str(word)
	try:
		flag_value = int(flag or 0)
	except (TypeError, ValueError):
		flag_value = 0

	is_injeong = bool(flag_value & 2)
	if is_injeong:
		return f"**{text}**"
	return f"__**{text}**__"


def count_char_occurrences(text: str, char: str) -> int:
	if not text or not char:
		return 0
	return str(text).count(str(char))
