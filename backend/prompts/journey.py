def build_stage_generation_prompt(
    product_description: str,
    test_scenario: str,
    target_segment: str
) -> str:
    return f"""
You are a UX researcher and customer journey expert.

Product: {product_description}
What we want to test: {test_scenario}
Target customer: {target_segment}

Generate a realistic customer journey for this product broken into 3-6 stages. Each stage should represent a distinct moment where the customer encounters new information, makes a micro-decision, or experiences friction.

Stages should reflect how a real customer would actually encounter this product — not an idealised funnel. Think about the actual touchpoints: discovery, consideration, price encounter, comparison, commitment.

Return a JSON array:
[
  {{ "order": 1, "name": "short stage name", "description": "what the customer sees and experiences at this specific moment" }}
]

Return ONLY the JSON array. No explanation, no markdown.
"""
