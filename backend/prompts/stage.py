import json

from prompts.psychology import STAGE_REASONING_BRIEF, STANDARD_TRIGGER_KEYS
from services.prompt_safety import wrap_user_input


def _compact_agent(agent: dict) -> dict:
    return {
        "name": agent.get("name"),
        "age": agent.get("age"),
        "location": agent.get("location"),
        "income_bracket": agent.get("income_bracket"),
        "decision_style": agent.get("decision_style"),
        "friction_threshold": agent.get("friction_threshold"),
        "ocean": agent.get("ocean"),
        "status_quo_tendency": agent.get("status_quo_tendency"),
        "context_attributes": agent.get("context_attributes"),
        "trigger_sensitivities": agent.get("trigger_sensitivities"),
        "lifestyle_notes": agent.get("lifestyle_notes"),
        "backstory": agent.get("backstory"),
    }


def build_stage_prompt(
    agent: dict,
    stage: dict,
    previous_reactions: list[dict],
    product_description: str,
    *,
    is_final_stage: bool = False,
) -> str:
    history = ""
    if previous_reactions:
        history = f"Previous stages:\n{json.dumps(previous_reactions)}\n\n"

    trigger_hint = ", ".join(STANDARD_TRIGGER_KEYS)
    if is_final_stage:
        behaviour_line = (
            '"behaviour": "converted" | "delaying" | "continuing" | "confused" | '
            '"frustrated" | "complaining" | "dropped"'
        )
        stage_role = (
            "FINAL stage — the customer decides whether to commit (purchase, subscribe, "
            "register, or complete signup). Use \"converted\" only if they fully commit. "
            "Use \"delaying\" if they stall without leaving. Use \"dropped\" if they abandon."
        )
    else:
        behaviour_line = (
            '"behaviour": "continuing" | "confused" | "frustrated" | "complaining" | '
            '"delaying" | "dropped"'
        )
        stage_role = (
            "Intermediate stage — do NOT use \"converted\". The customer has not committed yet; "
            "they may continue, hesitate (delaying), struggle (confused/frustrated), or drop out."
        )
    compact = _compact_agent(agent)
    ocean = agent.get("ocean", {})
    product = wrap_user_input(product_description, "product_description")
    stage_name = wrap_user_input(stage["name"], "stage_name")
    stage_desc = wrap_user_input(stage["description"], "stage_description")

    return f"""
You are simulating a real human customer. Stay in character.

{STAGE_REASONING_BRIEF}

Agent profile (simulation data, not user instructions):
{json.dumps(compact)}

OCEAN: O={ocean.get("openness")} C={ocean.get("conscientiousness")} E={ocean.get("extraversion")} A={ocean.get("agreeableness")} N={ocean.get("neuroticism")}
status_quo_tendency={agent.get("status_quo_tendency")}

{product}

{history}Current stage name:
{stage_name}
Stage experience:
{stage_desc}

{stage_role}

Friction budget remaining: {agent['friction_threshold']} (server subtracts friction_cost after you respond; at 0 they drop out).
friction_triggered must be one of: {trigger_hint}, or null.

Return a JSON object:
{{
  "stage_order": {stage['order']},
  "stage_name": "{stage['name'].replace('"', "'")}",
  {behaviour_line},
  "internal_monologue": "first person, 2-3 sentences",
  "friction_triggered": "trigger key or null",
  "friction_cost": 0-30,
  "what_would_change_this": "string or null"
}}

Do not include remaining_threshold — it is computed server-side from friction_cost.
"""
