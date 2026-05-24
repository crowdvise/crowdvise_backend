from fastapi import HTTPException

from models import AgentProfile, OceanProfile
from prompts.profile import build_profile_prompt
from services.context_attributes import normalize_context_attributes
from services.profile_normalize import normalize_profile_dict
from services.llm_client import create_message
from services.llm_json import LLMParseError, get_response_text, parse_llm_json
from services.prompt_safety import chat_messages
from services.simulation_limits import MAX_TOP_UP_ROUNDS, PROFILE_BATCH_SIZE


def _extract_profiles(raw) -> list:
    if isinstance(raw, dict):
        return raw.get("profiles") or []
    if isinstance(raw, list):
        return raw
    return []


def _profiles_from_raw(raw: list) -> list[AgentProfile]:
    profiles: list[AgentProfile] = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        p = normalize_profile_dict(p)
        p["id"] = f"agent_{len(profiles) + 1}"
        p["ocean"] = OceanProfile(**p["ocean"])
        p["context_attributes"] = normalize_context_attributes(p.get("context_attributes"))
        profiles.append(AgentProfile(**p))
    return profiles


async def _fetch_profiles(
    product_description: str,
    target_segment: str,
    count: int,
    *,
    top_up: bool = False,
) -> list[AgentProfile]:
    prompt = build_profile_prompt(
        product_description,
        target_segment,
        count,
        top_up=top_up,
    )
    response = await create_message(
        max_tokens=8000,
        messages=chat_messages(prompt, json_response=True),
        json_mode=True,
    )
    raw = parse_llm_json(get_response_text(response))
    items = _extract_profiles(raw)
    if not isinstance(items, list):
        raise LLMParseError(f"Expected profiles array, got {type(items).__name__}")
    return _profiles_from_raw(items)


async def _fetch_profiles_with_top_up(
    product_description: str,
    target_segment: str,
    count: int,
) -> list[AgentProfile]:
    profiles = await _fetch_profiles(product_description, target_segment, count)

    if len(profiles) > count:
        return profiles[:count]

    for _ in range(MAX_TOP_UP_ROUNDS):
        if len(profiles) >= count:
            break
        missing = count - len(profiles)
        extra = await _fetch_profiles(
            product_description,
            target_segment,
            missing,
            top_up=True,
        )
        profiles.extend(extra)

    return profiles[:count]


async def generate_profiles(
    product_description: str,
    target_segment: str,
    count: int,
) -> list[AgentProfile]:
    profiles: list[AgentProfile] = []
    remaining = count

    while remaining > 0:
        batch_size = min(PROFILE_BATCH_SIZE, remaining)
        batch = await _fetch_profiles_with_top_up(
            product_description,
            target_segment,
            batch_size,
        )
        if len(batch) < batch_size:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Panel generation returned {len(profiles) + len(batch)} profiles "
                    f"but panel_size requires {count}. Retry the simulation."
                ),
            )
        profiles.extend(batch)
        remaining = count - len(profiles)

    for i, profile in enumerate(profiles):
        profiles[i] = profile.model_copy(update={"id": f"agent_{i + 1}"})

    return profiles
