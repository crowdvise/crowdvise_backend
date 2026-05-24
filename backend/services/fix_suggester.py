import uuid

from models import FixSuggestion, JourneyStage, SimulationResult
from prompts.fixes import build_fix_suggestions_prompt
from services.fix_apply import find_stage_by_order
from services.llm_client import create_message
from services.llm_json import get_response_text, parse_llm_json
from services.prompt_safety import chat_messages


def _extract_fixes(raw) -> list[dict]:
    if isinstance(raw, dict):
        return raw.get("fixes") or []
    if isinstance(raw, list):
        return raw
    return []


def enrich_fixes(
    raw_fixes: list[dict],
    baseline_stages: list[JourneyStage],
) -> list[FixSuggestion]:
    suggestions: list[FixSuggestion] = []
    for i, item in enumerate(raw_fixes[:3]):
        if not isinstance(item, dict):
            continue
        order = int(item.get("target_stage_order", 0))
        stage = find_stage_by_order(baseline_stages, order)
        if not stage:
            continue
        suggestions.append(
            FixSuggestion(
                id=str(item.get("id") or f"fix_{i + 1}"),
                title=str(item.get("title") or f"Fix {i + 1}"),
                rationale=str(item.get("rationale") or ""),
                target_stage_order=order,
                target_stage_name=str(item.get("target_stage_name") or stage.name),
                original_description=stage.description,
                patched_description=str(item.get("patched_description") or stage.description),
                expected_impact=str(item.get("expected_impact") or ""),
            )
        )
    return suggestions


async def generate_fix_suggestions(
    product_description: str,
    baseline_stages: list[JourneyStage],
    result: SimulationResult,
) -> list[FixSuggestion]:
    overall_stats = {
        "conversion_rate": result.overall_conversion_rate,
        "dropout_rate": result.overall_dropout_rate,
        "delayed_rate": result.overall_delayed_rate,
        "readiness_score": result.readiness_score,
    }
    prompt = build_fix_suggestions_prompt(
        product_description=product_description,
        journey_stages=[s.model_dump() for s in baseline_stages],
        top_insights=result.top_insights,
        stage_insights=[s.model_dump() for s in result.stage_insights],
        overall_stats=overall_stats,
    )
    response = await create_message(
        max_tokens=2500,
        messages=chat_messages(prompt, json_response=True),
        json_mode=True,
    )
    raw = parse_llm_json(get_response_text(response))
    fixes = enrich_fixes(_extract_fixes(raw), baseline_stages)
    if len(fixes) < 3:
        raise ValueError(f"Expected 3 fix suggestions, got {len(fixes)}")
    return fixes[:3]
