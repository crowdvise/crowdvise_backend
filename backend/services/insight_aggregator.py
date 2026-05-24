import uuid
from models import AgentJourney, StageInsight, SimulationResult
from prompts.insight import build_insight_prompt
from services.llm_client import create_message
from services.llm_json import get_response_text, parse_llm_json
from services.prompt_safety import chat_messages
from services.readiness_score import compute_readiness_score, readiness_level


def aggregate_stage_insights(journeys: list[AgentJourney]) -> list[StageInsight]:
    stage_data: dict[str, dict] = {}

    for journey in journeys:
        reactions = journey.reactions
        for idx, reaction in enumerate(reactions):
            s = reaction.stage_name
            if s not in stage_data:
                stage_data[s] = {"total": 0, "dropped": 0, "delayed": 0, "confused": 0, "triggers": []}

            stage_data[s]["total"] += 1

            if reaction.behaviour == "dropped":
                stage_data[s]["dropped"] += 1
            is_last_reaction = idx == len(reactions) - 1
            if reaction.behaviour == "delaying":
                stage_data[s]["delayed"] += 1
            elif (
                is_last_reaction
                and journey.final_outcome == "delayed"
                and reaction.behaviour == "continuing"
            ):
                stage_data[s]["delayed"] += 1
            if reaction.behaviour == "confused":
                stage_data[s]["confused"] += 1
            if reaction.friction_triggered:
                stage_data[s]["triggers"].append(reaction.friction_triggered)

    insights = []
    for stage_name, data in stage_data.items():
        total = data["total"]
        top_trigger = max(set(data["triggers"]), key=data["triggers"].count) if data["triggers"] else None
        insights.append(StageInsight(
            stage_name=stage_name,
            dropout_rate=round(data["dropped"] / total, 2) if total else 0,
            delay_rate=round(data["delayed"] / total, 2) if total else 0,
            top_friction_trigger=top_trigger,
            confusion_rate=round(data["confused"] / total, 2) if total else 0
        ))

    return insights


def _dominant_pattern(converted: int, dropped: int, delayed: int) -> str:
    counts = {"conversion": converted, "dropout": dropped, "delay_epidemic": delayed}
    top = max(counts, key=counts.get)
    if counts[top] == 0:
        return "mixed"
    if delayed >= dropped and delayed >= converted and delayed > 0:
        return "delay_epidemic"
    if dropped >= delayed and dropped >= converted and dropped > 0:
        return "dropout_epidemic"
    if converted >= delayed and converted >= dropped and converted > 0:
        return "conversion_led"
    return "mixed"


def _summarize_delayed_segment(journeys: list[AgentJourney]) -> list[dict]:
    summary = []
    for journey in journeys:
        if journey.final_outcome != "delayed":
            continue
        last = journey.reactions[-1] if journey.reactions else None
        summary.append({
            "agent_id": journey.agent.id,
            "name": journey.agent.name,
            "location": journey.agent.location,
            "decision_style": journey.agent.decision_style,
            "stalled_at_stage": last.stage_name if last else None,
            "last_behaviour": last.behaviour if last else None,
            "friction_triggered": last.friction_triggered if last else None,
            "what_would_change_this": last.what_would_change_this if last else None,
        })
    return summary


async def build_simulation_result(
    journeys: list[AgentJourney],
    product_description: str
) -> SimulationResult:
    total = len(journeys)
    converted = sum(1 for j in journeys if j.final_outcome == "converted")
    dropped = sum(1 for j in journeys if j.final_outcome == "dropped")
    delayed = sum(1 for j in journeys if j.final_outcome == "delayed")

    stage_insights = aggregate_stage_insights(journeys)
    delayed_segment = _summarize_delayed_segment(journeys)

    overall_stats = {
        "total_agents": total,
        "converted": converted,
        "dropped": dropped,
        "delayed": delayed,
        "conversion_rate": round(converted / total, 2) if total else 0,
        "dropout_rate": round(dropped / total, 2) if total else 0,
        "delayed_rate": round(delayed / total, 2) if total else 0,
        "dominant_pattern": _dominant_pattern(converted, dropped, delayed),
    }

    prompt = build_insight_prompt(
        product_description=product_description,
        stage_insights=[s.model_dump() for s in stage_insights],
        overall_stats=overall_stats,
        delayed_segment=delayed_segment,
    )

    response = await create_message(
        max_tokens=1000,
        messages=chat_messages(prompt, json_response=True),
        json_mode=True,
    )

    raw = parse_llm_json(get_response_text(response))

    score = compute_readiness_score(
        conversion_rate=overall_stats["conversion_rate"],
        dropout_rate=overall_stats["dropout_rate"],
        delayed_rate=overall_stats["delayed_rate"],
        stage_insights=stage_insights,
    )

    return SimulationResult(
        simulation_id=str(uuid.uuid4()),
        overall_conversion_rate=overall_stats["conversion_rate"],
        overall_dropout_rate=overall_stats["dropout_rate"],
        overall_delayed_rate=overall_stats["delayed_rate"],
        agent_journeys=journeys,
        stage_insights=stage_insights,
        top_insights=raw["top_insights"],
        readiness_score=score,
        readiness_level=readiness_level(score),
    )
