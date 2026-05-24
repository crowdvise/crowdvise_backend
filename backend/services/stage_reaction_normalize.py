"""Normalize LLM stage reaction JSON before Pydantic validation."""

from prompts.psychology import STANDARD_TRIGGER_KEYS

_VALID_BEHAVIOURS = frozenset({
    "continuing",
    "confused",
    "frustrated",
    "complaining",
    "delaying",
    "dropped",
    "converted",
})


def normalize_stage_reaction(raw: dict) -> dict:
    r = dict(raw)

    if "what_would_change_this" not in r or r["what_would_change_this"] in ("", "null", "none"):
        r["what_would_change_this"] = None

    trigger = r.get("friction_triggered")
    if trigger in ("", "null", "none", None):
        r["friction_triggered"] = None
    elif isinstance(trigger, str) and trigger not in STANDARD_TRIGGER_KEYS:
        r["friction_triggered"] = None

    behaviour = str(r.get("behaviour", "continuing")).lower().strip()
    r["behaviour"] = behaviour if behaviour in _VALID_BEHAVIOURS else "continuing"

    r["friction_cost"] = max(0, min(30, int(r.get("friction_cost", 0))))
    r["remaining_threshold"] = max(0, min(100, int(r.get("remaining_threshold", 50))))

    r["internal_monologue"] = str(r.get("internal_monologue") or "")
    r["stage_name"] = str(r.get("stage_name") or "")
    r["stage_order"] = int(r.get("stage_order", 0))

    return r
