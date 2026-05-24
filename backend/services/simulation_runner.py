import asyncio

from models import AgentJourney, AgentProfile, SimulationRequest
from services.behaviour_engine import run_agent_journey
from services.profile_generator import generate_profiles


async def _run_journeys(
    profiles: list[AgentProfile],
    request: SimulationRequest,
) -> list[AgentJourney]:
    journeys = await asyncio.gather(*[
        run_agent_journey(agent, request.journey_stages, request.product_description)
        for agent in profiles
    ])
    return list(journeys)


async def run_simulation(request: SimulationRequest) -> tuple[list[AgentJourney], list[AgentProfile]]:
    profiles = await generate_profiles(
        product_description=request.product_description,
        target_segment=request.target_segment,
        count=request.panel_size,
    )
    if len(profiles) != request.panel_size:
        raise RuntimeError(
            f"Expected {request.panel_size} agents, got {len(profiles)} after profile generation"
        )
    journeys = await _run_journeys(profiles, request)
    return journeys, profiles


async def run_simulation_with_panel(
    request: SimulationRequest,
    profiles: list[AgentProfile],
) -> list[AgentJourney]:
    if len(profiles) != request.panel_size:
        raise ValueError(
            f"Panel size mismatch: expected {request.panel_size}, got {len(profiles)} profiles"
        )
    return await _run_journeys(profiles, request)
