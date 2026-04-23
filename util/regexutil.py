import re

MAX_REGEX_LENGTH = 200
MAX_REGEX_GROUPS = 5
MAX_REGEX_QUANTIFIERS = 5


def isRegexSafe(pattern: str) -> bool:
	if not isinstance(pattern, str) or not pattern:
		return False

	if len(pattern) > MAX_REGEX_LENGTH:
		return False

	try:
		re.compile(pattern)
	except re.error:
		return False

	# Ignore escaped characters when checking structural complexity.
	stripped = re.sub(r"\\.", "", pattern)

	groups = re.findall(r"\(", stripped)
	if len(groups) > MAX_REGEX_GROUPS:
		return False

	quantifiers = re.findall(r"(?:\*|\+|\{\d+,?\d*\})\??", stripped)
	if len(quantifiers) > MAX_REGEX_QUANTIFIERS:
		return False

	# Block nested quantifier patterns like (a+)+ or (a*){2,}
	if re.search(r"(\([^)]*[*+][^)]*\))[*+{]", stripped):
		return False

	return True
