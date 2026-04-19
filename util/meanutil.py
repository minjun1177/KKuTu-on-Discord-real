import json
from pathlib import Path
import re

# Theme labels derived from the mapping documented in app.py comments.
THEME_NAME_MAP = {
	"e03": "★",
	"e05": "동물",
	"e08": "인체",
	"e12": "감정",
	"e13": "음식",
	"e15": "지명",
	"e18": "사람",
	"e20": "식물",
	"e43": "날씨",
	"10": "가톨릭",
	"20": "건설",
	"30": "경제",
	"40": "고적",
	"50": "고유",
	"60": "공업",
	"70": "광업",
	"80": "교육",
	"90": "교통",
	"100": "군사",
	"110": "기계",
	"120": "기독교",
	"130": "논리",
	"140": "농업",
	"150": "문학",
	"160": "물리",
	"170": "미술",
	"180": "민속",
	"190": "동물",
	"200": "법률",
	"210": "불교",
	"220": "사회",
	"230": "생물",
	"240": "수학",
	"250": "수산",
	"260": "수공",
	"270": "식물",
	"280": "심리",
	"290": "약학",
	"300": "언론",
	"310": "언어",
	"320": "역사",
	"330": "연영",
	"340": "예술",
	"350": "운동",
	"360": "음악",
	"370": "의학",
	"380": "인명",
	"390": "전기",
	"400": "정치",
	"410": "종교",
	"420": "지리",
	"430": "지명",
	"440": "책명",
	"450": "천문",
	"460": "철학",
	"470": "출판",
	"480": "통신",
	"490": "컴퓨터",
	"500": "한의학",
	"510": "항공",
	"520": "해양",
	"530": "화학",
	"1001": "나라 이름과 수도",
}


def _load_injeong_theme_map() -> dict[str, str]:
	file_path = Path(__file__).with_name("injeong_list.json")
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			raw = json.load(f)
	except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
		return {}

	result: dict[str, str] = {}
	for key, value in raw.items():
		if not isinstance(value, str):
			continue
		normalized_key = str(key)
		if normalized_key.startswith("theme_"):
			normalized_key = normalized_key.replace("theme_", "", 1)
		result[normalized_key] = value

	return result


INJEONG_THEME_MAP = _load_injeong_theme_map()


MAJOR_PATTERN = re.compile(r"＂(\d+)＂")
SUB_PATTERN = re.compile(r"［(\d+)］")
ITEM_PATTERN = re.compile(r"（(\d+)）")


def _flatten_mean_text(value) -> str:
	if value is None:
		return ""
	if isinstance(value, str):
		return value
	if isinstance(value, list):
		return "".join(_flatten_mean_text(item) for item in value)
	return str(value)


def _normalize_theme_code(theme_value) -> str:
	theme_str = str(theme_value)
	if theme_str.startswith("theme_"):
		theme_str = theme_str.replace("theme_", "", 1)
	return theme_str


def _theme_label(theme_value) -> str:
	code = _normalize_theme_code(theme_value)
	if code in INJEONG_THEME_MAP:
		return INJEONG_THEME_MAP[code]
	return THEME_NAME_MAP.get(code, code)


def format_theme_text(theme_raw, fallback_text: str) -> str:
	themes = _theme_list(theme_raw)
	if not themes:
		return fallback_text

	seen = set()
	labels = []
	for theme in themes:
		label = f"<{_theme_label(theme)}>"
		if label not in seen:
			seen.add(label)
			labels.append(label)

	return ", ".join(labels) if labels else fallback_text


def format_type_text(type_raw, type_name_map: dict[str, str], fallback_text: str) -> str:
	if type_raw is None:
		return fallback_text

	type_text = str(type_raw).strip()
	if type_text.startswith("class_"):
		type_text = type_text.replace("class_", "", 1)

	return type_name_map.get(type_text, str(type_raw))


def format_flag_text(flag_raw, flag_name_map: dict[str, str], fallback_text: str) -> str:
	if flag_raw is None:
		return fallback_text

	try:
		flag_value = int(str(flag_raw))
	except (ValueError, TypeError):
		return str(flag_raw)

	if flag_value == 0:
		return fallback_text

	normalized_flag_map: dict[int, str] = {}
	for key, label in flag_name_map.items():
		try:
			normalized_flag_map[int(str(key))] = str(label)
		except (ValueError, TypeError):
			continue

	labels = [
		label
		for bit, label in sorted(normalized_flag_map.items())
		if flag_value & bit
	]

	return ", ".join(labels) if labels else str(flag_raw)


def _theme_list(theme_raw) -> list:
	if theme_raw is None:
		return []
	if isinstance(theme_raw, list):
		return theme_raw
	return [theme_raw]


def _split_numbered_sections(text: str, pattern: re.Pattern) -> list[tuple[str, str]]:
	matches = list(pattern.finditer(text))
	if not matches:
		return []

	sections: list[tuple[str, str]] = []
	for i, match in enumerate(matches):
		number = match.group(1)
		start = match.end()
		end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
		content = text[start:end].strip()
		sections.append((number, content))

	return sections


def _split_subsections(text: str) -> list[tuple[str | None, str]]:
	matches = list(SUB_PATTERN.finditer(text))
	if not matches:
		return [(None, text.strip())] if text.strip() else []

	sections: list[tuple[str | None, str]] = []
	prefix = text[:matches[0].start()].strip()
	if prefix:
		sections.append((None, prefix))

	for i, match in enumerate(matches):
		number = match.group(1)
		start = match.end()
		end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
		content = text[start:end].strip()
		sections.append((number, content))

	return sections


def _split_items(text: str) -> list[tuple[str | None, str]]:
	matches = list(ITEM_PATTERN.finditer(text))
	if not matches:
		return [(None, text.strip())] if text.strip() else []

	items: list[tuple[str | None, str]] = []
	prefix = text[:matches[0].start()].strip()
	if prefix:
		items.append((None, prefix))

	for i, match in enumerate(matches):
		number = match.group(1)
		start = match.end()
		end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
		content = text[start:end].strip()
		items.append((number, content))

	return items


def format_mean_text(mean_raw, theme_raw, mean_notfound_text: str) -> str:
	text = _flatten_mean_text(mean_raw).strip()
	if not text:
		return mean_notfound_text

	major_sections = _split_numbered_sections(text, MAJOR_PATTERN)
	if not major_sections:
		return text

	themes = _theme_list(theme_raw)
	theme_index = 0
	parts: list[str] = []

	for major_number, major_content in major_sections:
		parts.append(f"**{major_number}**")

		if not major_content:
			parts.append(mean_notfound_text)
			continue

		subsections = _split_subsections(major_content)
		if not subsections:
			parts.append(mean_notfound_text)
			continue

		numbered_subsections = [
			(number, content) for number, content in subsections if number is not None
		]
		show_sub_number = not (
			len(numbered_subsections) == 1 and numbered_subsections[0][0] == "1"
		)

		for subsection_number, subsection_content in subsections:
			if subsection_number is not None and show_sub_number:
				parts.append(f"_{subsection_number}_")

			items = _split_items(subsection_content)
			if not items:
				parts.append(mean_notfound_text)
				continue

			numbered_items = [
				(item_number, content)
				for item_number, content in items
				if item_number is not None
			]
			show_item_number = not (
				len(numbered_items) == 1 and numbered_items[0][0] == "1"
			)

			for item_number, item_content in items:
				entry_parts: list[str] = []

				if item_number is not None and show_item_number:
					entry_parts.append(f"({item_number})")

				if themes:
					theme_value = themes[theme_index] if theme_index < len(themes) else themes[-1]
					entry_parts.append(f"<{_theme_label(theme_value)}>")
					theme_index += 1

				entry_parts.append(item_content if item_content else mean_notfound_text)
				parts.append(" ".join(entry_parts))

	if not parts:
		return mean_notfound_text

	return " ".join(parts)
