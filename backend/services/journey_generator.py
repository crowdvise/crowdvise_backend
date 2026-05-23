from models import JourneyStage
from prompts.journey import build_stage_generation_prompt
from services.llm_client import create_message
from services.llm_json import get_response_text, parse_llm_json


async def generate_stages(
    product_description: str,
    test_scenario: str,
    target_segment: str
) -> list[JourneyStage]:
    prompt = build_stage_generation_prompt(product_description, test_scenario, target_segment)

    response = await create_message(
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = parse_llm_json(get_response_text(response))
    stages = [JourneyStage(**s) for s in raw]
    return sorted(stages, key=lambda s: s.order)
