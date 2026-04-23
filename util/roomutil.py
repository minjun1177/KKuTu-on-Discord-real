from typing import Any

ROOM_OPTION_ORDER = [
	"injeong", "manner", "mission", "loanword", "proverb", "strict", "sami", "no2", "unknown", "easymission",
	"longword", "hard", "morse", "phonetic", "onlylong", "onlyshort", "nonoinjeong", "unlimited", "short",
]
ROOM_OPTION_VALUES = set(ROOM_OPTION_ORDER)


def get_option_display(option_value: str, language_dict: dict[str, Any]) -> tuple[str, str]:
	name = language_dict.get(f"RoomOptionName_{option_value}", option_value)
	description = language_dict.get(
		f"RoomOptionDesc_{option_value}",
		language_dict.get("RoomOptionNoDescription", "설명 없음"),
	)

	return name, description


def build_option_summary_lines(option_values: list[str], language_dict: dict[str, Any]) -> list[str]:
	lines = []
	for option_value in option_values:
		name, desc = get_option_display(option_value, language_dict)
		lines.append(f"- **{name}**: {desc}")
	return lines


def get_room_option_catalog(language_dict: dict[str, Any]) -> list[tuple[str, str]]:
	return [(value, get_option_display(value, language_dict)[0]) for value in ROOM_OPTION_ORDER]
