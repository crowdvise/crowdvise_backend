from models import AgentProfile, OceanProfile
from prompts.profile import build_profile_prompt
from services.context_attributes import normalize_context_attributes
from services.llm_client import create_message
from services.llm_json import get_response_text, parse_llm_json


async def generate_profiles(product_description: str, target_segment: str, count: int) -> list[AgentProfile]:
    prompt = build_profile_prompt(product_description, target_segment, count)

    response = await create_message(
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = parse_llm_json(get_response_text(response))

    profiles = []
    for i, p in enumerate(raw):
        p["id"] = f"agent_{i + 1}"
        p["ocean"] = OceanProfile(**p["ocean"])
        p["context_attributes"] = normalize_context_attributes(p.get("context_attributes"))
        profiles.append(AgentProfile(**p))

    return profiles
