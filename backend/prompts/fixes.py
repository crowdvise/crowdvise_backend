import json

from services.prompt_safety import wrap_user_input


def build_fix_suggestions_prompt(
    product_description: str,
    journey_stages: list[dict],
    top_insights: list[str],
    stage_insights: list[dict],
    overall_stats: dict,
) -> str:
    product = wrap_user_input(product_description, "product_description")

    return f"""
You are a senior product strategist. Propose exactly 3 concrete journey fixes to test based on simulation results.

{product}

Current journey stages:
{json.dumps(journey_stages)}

Overall panel outcomes:
{json.dumps(overall_stats)}

Stage metrics:
{json.dumps(stage_insights)}

Top insights from the simulation:
{json.dumps(top_insights)}

Each fix must:
- Target exactly ONE existing stage (use its "order" as target_stage_order)
- Rewrite that stage's customer-facing experience (patched_description) — specific and implementable
- Stay within the same product idea (no new product pivots)
- Be distinct from the other two fixes

Return a JSON object:
{{
  "fixes": [
    {{
      "id": "fix_1",
      "title": "short fix name",
      "rationale": "why this fix addresses the data",
      "target_stage_order": number,
      "target_stage_name": "stage name matching that order",
      "patched_description": "full new stage experience text for the customer",
      "expected_impact": "what metric or behaviour should improve"
    }}
  ]
}}

Return exactly 3 fixes in the array.
"""
