from models import AgentProfile, AgentJourney, StageReaction, JourneyStage
from prompts.stage import build_stage_prompt
from services.llm_client import create_message
from services.llm_json import get_response_text, parse_llm_json
from services.prompt_safety import chat_messages
from services.stage_reaction_normalize import normalize_stage_reaction


def _slim_reaction(raw: dict) -> dict:
    return {
        "stage_name": raw["stage_name"],
        "behaviour": raw["behaviour"],
        "friction_triggered": raw.get("friction_triggered"),
        "remaining_threshold": raw.get("remaining_threshold"),
    }


async def run_agent_journey(
    agent: AgentProfile,
    stages: list[JourneyStage],
    product_description: str
) -> AgentJourney:
    reactions: list[StageReaction] = []
    agent_dict = agent.model_dump()
    previous_reactions: list[dict] = []
    dropped = False
    dropped_at = None

    for stage in sorted(stages, key=lambda s: s.order):
        if dropped:
            break

        prompt = build_stage_prompt(
            agent=agent_dict,
            stage=stage.model_dump(),
            previous_reactions=previous_reactions,
            product_description=product_description
        )

        response = await create_message(
            max_tokens=600,
            messages=chat_messages(prompt, json_response=True),
            json_mode=True,
        )

        raw = normalize_stage_reaction(parse_llm_json(get_response_text(response)))

        agent_dict["friction_threshold"] = raw["remaining_threshold"]

        reaction = StageReaction(**raw)
        reactions.append(reaction)
        previous_reactions.append(_slim_reaction(raw))

        if reaction.behaviour == "dropped":
            dropped = True
            dropped_at = stage.name

    last = reactions[-1] if reactions else None
    final_outcome = (
        "converted" if last and last.behaviour == "converted"
        else "dropped" if dropped
        else "delayed"
    )

    return AgentJourney(
        agent=agent,
        reactions=reactions,
        final_outcome=final_outcome,
        dropped_at_stage=dropped_at
    )
