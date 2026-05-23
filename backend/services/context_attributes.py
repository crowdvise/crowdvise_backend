from prompts.psychology import CONTEXT_ATTRIBUTE_LEVELS, STANDARD_CONTEXT_KEYS

_DEFAULT_LEVEL = "moderate"


def normalize_context_attributes(raw: dict | None) -> dict[str, str]:
    """Force a stable key set and value enum for API clients and mobile mocks."""
    raw = raw or {}
    normalized: dict[str, str] = {}

    for key in STANDARD_CONTEXT_KEYS:
        value = raw.get(key, _DEFAULT_LEVEL)
        if not isinstance(value, str):
            value = _DEFAULT_LEVEL
        value = value.lower().strip()
        if value not in CONTEXT_ATTRIBUTE_LEVELS:
            value = _DEFAULT_LEVEL
        normalized[key] = value

    return normalized
