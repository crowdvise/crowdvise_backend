"""Map common LLM profile field variants to model literals."""

from typing import Any

INCOME_BRACKETS = frozenset({"low", "middle", "high"})
DECISION_STYLES = frozenset({"impulsive", "deliberate", "analytical"})

_INCOME_ALIASES = {
    "low": "low",
    "lower": "low",
    "low-income": "low",
    "medium": "middle",
    "mid": "middle",
    "middle": "middle",
    "middle-income": "middle",
    "average": "middle",
    "high": "high",
    "upper": "high",
    "high-income": "high",
}

_DECISION_ALIASES = {
    "impulsive": "impulsive",
    "impulse": "impulsive",
    "deliberate": "deliberate",
    "thoughtful": "deliberate",
    "analytical": "analytical",
    "analytic": "analytical",
    "rational": "analytical",
}


def normalize_income_bracket(value: Any) -> str:
    if not isinstance(value, str):
        return "middle"
    key = value.lower().strip()
    return _INCOME_ALIASES.get(key, "middle" if key not in INCOME_BRACKETS else key)


def normalize_decision_style(value: Any) -> str:
    if not isinstance(value, str):
        return "deliberate"
    key = value.lower().strip()
    return _DECISION_ALIASES.get(key, "deliberate" if key not in DECISION_STYLES else key)


def normalize_friction_threshold(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 55
    return max(0, min(100, n))


def normalize_profile_dict(raw: dict) -> dict:
    p = dict(raw)
    p["income_bracket"] = normalize_income_bracket(p.get("income_bracket"))
    p["decision_style"] = normalize_decision_style(p.get("decision_style"))
    p["friction_threshold"] = normalize_friction_threshold(p.get("friction_threshold"))
    if not isinstance(p.get("gender"), str):
        p["gender"] = "unspecified"
    return p
