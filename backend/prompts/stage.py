from prompts.psychology import STAGE_REASONING_BRIEF, STANDARD_TRIGGER_KEYS


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
    product_description: str
) -> str:
    history = ""
    if previous_reactions:
        history = f"Previous stages:\n{previous_reactions}\n\n"

    trigger_hint = ", ".join(STANDARD_TRIGGER_KEYS)
    compact = _compact_agent(agent)
    ocean = agent.get("ocean", {})

    return f"""
You are simulating a real human customer. Stay in character.

{STAGE_REASONING_BRIEF}

Profile: {compact}

OCEAN: O={ocean.get("openness")} C={ocean.get("conscientiousness")} E={ocean.get("extraversion")} A={ocean.get("agreeableness")} N={ocean.get("neuroticism")}
status_quo_tendency={agent.get("status_quo_tendency")}

Product: {product_description}

{history}Current stage: {stage['name']}
Experience: {stage['description']}

Friction threshold: {agent['friction_threshold']} (0 = drop out).
friction_triggered must be one of: {trigger_hint}, or null.

Return JSON only:
{{
  "stage_order": {stage['order']},
  "stage_name": "{stage['name']}",
  "behaviour": "continuing" | "confused" | "frustrated" | "complaining" | "delaying" | "dropped" | "converted",
  "internal_monologue": "first person, 2-3 sentences",
  "friction_triggered": "trigger key or null",
  "friction_cost": 0-30,
  "remaining_threshold": number,
  "what_would_change_this": "string or null"
}}
"""
