import asyncio
from models import SimulationRequest, AgentJourney
from services.profile_generator import generate_profiles
from services.behaviour_engine import run_agent_journey


async def run_simulation(request: SimulationRequest) -> list[AgentJourney]:
    profiles = await generate_profiles(
        product_description=request.product_description,
        target_segment=request.target_segment,
        count=request.panel_size,
    )
    if len(profiles) != request.panel_size:
        raise RuntimeError(
            f"Expected {request.panel_size} agents, got {len(profiles)} after profile generation"
        )

    journeys = await asyncio.gather(*[
        run_agent_journey(agent, request.journey_stages, request.product_description)
        for agent in profiles
    ])

    return list(journeys)
