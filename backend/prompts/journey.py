from services.prompt_safety import wrap_user_input


def build_stage_generation_prompt(
    product_description: str,
    test_scenario: str,
    target_segment: str,
) -> str:
    product = wrap_user_input(product_description, "product_description")
    scenario = wrap_user_input(test_scenario, "test_scenario")
    segment = wrap_user_input(target_segment, "target_segment")

    return f"""
You are a UX researcher and customer journey expert.

{product}
{scenario}
{segment}

Generate a realistic customer journey for this product broken into 3-6 stages. Each stage should represent a distinct moment where the customer encounters new information, makes a micro-decision, or experiences friction.

Stages should reflect how a real customer would actually encounter this product — not an idealised funnel. Think about the actual touchpoints: discovery, consideration, price encounter, comparison, commitment.

Return a JSON object with a "stages" array:
{{
  "stages": [
    {{ "order": 1, "name": "short stage name", "description": "what the customer sees and experiences at this specific moment" }}
  ]
}}
"""
