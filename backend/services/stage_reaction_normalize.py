"""Normalize LLM stage reaction JSON and apply deterministic friction rules."""

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

_INTERMEDIATE_BEHAVIOURS = _VALID_BEHAVIOURS - {"converted"}


def normalize_stage_reaction(raw: dict) -> dict:
    """Parse and sanitize LLM fields (does not apply friction budget or stage rules)."""
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

    r["internal_monologue"] = str(r.get("internal_monologue") or "")
    r["stage_name"] = str(r.get("stage_name") or "")
    r["stage_order"] = int(r.get("stage_order", 0))

    return r


def apply_stage_rules(
    raw: dict,
    *,
    remaining_before: int,
    is_final_stage: bool,
) -> dict:
    """
    Server-side rules after LLM normalization:
    - remaining_threshold = remaining_before - friction_cost (clamped)
    - "converted" only on the final stage (commitment: buy / subscribe / register)
    - friction exhausted (0) → dropped
    """
    r = normalize_stage_reaction(raw)
    remaining_before = max(0, min(100, int(remaining_before)))
    cost = r["friction_cost"]
    remaining_after = max(0, remaining_before - cost)
    r["remaining_threshold"] = remaining_after

    if not is_final_stage:
        if r["behaviour"] == "converted":
            r["behaviour"] = "continuing"
        elif r["behaviour"] not in _INTERMEDIATE_BEHAVIOURS:
            r["behaviour"] = "continuing"
    elif r["behaviour"] == "converted" and remaining_after <= 0:
        # Cannot commit after friction budget is gone
        r["behaviour"] = "dropped"

    if remaining_after <= 0 and r["behaviour"] != "dropped":
        r["behaviour"] = "dropped"

    return r
