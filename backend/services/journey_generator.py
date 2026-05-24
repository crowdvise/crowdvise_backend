from models import JourneyStage
from prompts.journey import build_stage_generation_prompt
from services.llm_client import create_message
from services.llm_json import get_response_text, parse_llm_json
from services.prompt_safety import chat_messages


def _extract_stages(raw) -> list:
    if isinstance(raw, dict):
        return raw.get("stages") or raw.get("suggested_stages") or []
    if isinstance(raw, list):
        return raw
    return []


async def generate_stages(
    product_description: str,
    test_scenario: str,
    target_segment: str,
) -> list[JourneyStage]:
    prompt = build_stage_generation_prompt(product_description, test_scenario, target_segment)

    response = await create_message(
        max_tokens=2000,
        messages=chat_messages(prompt, json_response=True),
        json_mode=True,
    )

    raw = parse_llm_json(get_response_text(response))
    items = _extract_stages(raw)
    return [JourneyStage(**s) for s in items]
