from prompts.psychology import (
    BEHAVIOURAL_FRAMEWORKS,
    OCEAN_TO_SENSITIVITY_RULES,
    STANDARD_TRIGGER_KEYS,
)


def build_profile_prompt(product_description: str, target_segment: str, count: int) -> str:
    trigger_keys = ", ".join(STANDARD_TRIGGER_KEYS)

    return f"""
You are a behavioural scientist generating synthetic customer profiles for a simulation.
Every agent is grounded in the Big Five (OCEAN) — the most empirically validated personality framework in psychology.

{BEHAVIOURAL_FRAMEWORKS}

Product being tested: {product_description}
Target customer segment: {target_segment}
Number of profiles to generate: {count}

Generate {count} psychologically distinct profiles. Vary OCEAN scores meaningfully across the panel — avoid clustering everyone in the middle. Location must be specific and behaviourally meaningful (e.g. "Downtown Toronto", "Suburban Mississauga").

For each profile:
1. Assign OCEAN scores (0.0–1.0 each dimension)
2. Assign status_quo_tendency (0.0–1.0) — how strongly they resist changing from current habits/defaults
3. Add 2–4 context_attributes: product-specific dimensions only (snake_case keys; values like "low" | "moderate" | "high"). Same keys across all profiles.
4. Derive trigger_sensitivities from OCEAN + status_quo_tendency using these rules:

{OCEAN_TO_SENSITIVITY_RULES}

Required trigger_sensitivities keys (exactly these six): {trigger_keys}

Return a JSON array:
[
  {{
    "name": "string",
    "age": number,
    "gender": "string",
    "location": "string",
    "income_bracket": "low" | "middle" | "high",
    "decision_style": "impulsive" | "deliberate" | "analytical",
    "friction_threshold": number 40-90 (lower base threshold when neuroticism is high),
    "backstory": "one sentence",
    "ocean": {{
      "openness": float 0.0-1.0,
      "conscientiousness": float 0.0-1.0,
      "extraversion": float 0.0-1.0,
      "agreeableness": float 0.0-1.0,
      "neuroticism": float 0.0-1.0
    }},
    "status_quo_tendency": float 0.0-1.0,
    "context_attributes": {{ "product_specific_key": "value", ... }},
    "trigger_sensitivities": {{ "{STANDARD_TRIGGER_KEYS[0]}": float, ... }},
    "lifestyle_notes": "1-2 sentences of human texture"
  }}
]

Return ONLY the JSON array. No explanation, no markdown.
"""
