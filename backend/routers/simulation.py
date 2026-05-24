import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
from config import settings
from dependencies.auth import (
    AuthUser,
    get_current_user,
    require_generate_stages_limit,
    require_history_limit,
    require_run_limit,
)
from services.usage_context import set_user
from models import (
    SimulationHistoryResponse,
    SimulationRequest,
    SimulationResult,
    SimulationRunSummary,
    StageGenerationRequest,
    StageGenerationResponse,
)
from services.journey_generator import generate_stages
from services.simulation_runner import run_simulation
from services.insight_aggregator import build_simulation_result
from services.simulation_store import (
    SimulationStoreError,
    get_simulation_run,
    handle_store_error,
    list_simulation_runs,
    save_simulation_run,
)

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/generate-stages", response_model=StageGenerationResponse)
async def generate_journey_stages(
    request: StageGenerationRequest,
    user: AuthUser = Depends(require_generate_stages_limit),
) -> StageGenerationResponse:
    set_user(user.id)
    stages = await generate_stages(
        product_description=request.product_description,
        test_scenario=request.test_scenario,
        target_segment=request.target_segment,
    )
    if not stages:
        raise HTTPException(status_code=500, detail="No journey stages were generated")

    return StageGenerationResponse(suggested_stages=stages)


@router.post("/run", response_model=SimulationResult)
async def run(
    request: SimulationRequest,
    user: AuthUser = Depends(require_run_limit),
) -> SimulationResult:
    set_user(user.id)
    journeys = await run_simulation(request)
    result = await build_simulation_result(journeys, request.product_description)

    if not settings.auth_disabled:
        try:
            save_simulation_run(user.id, request, result)
        except SimulationStoreError as exc:
            logger.exception("Failed to save simulation run for user %s", user.id)
            raise handle_store_error(exc) from exc

    return result


@router.get("/run", include_in_schema=False)
async def run_wrong_method() -> None:
    """Catch GET /simulation/run — otherwise it is treated as GET /simulation/{simulation_id}."""
    raise HTTPException(
        status_code=405,
        detail=(
            "Use POST /simulation/run to start a simulation. "
            "Use GET /simulation/{simulation_id} with the id from the POST response to fetch a saved run."
        ),
    )


@router.get("/history", response_model=SimulationHistoryResponse)
async def history(user: AuthUser = Depends(require_history_limit)) -> SimulationHistoryResponse:
    try:
        rows = list_simulation_runs(user.id)
    except SimulationStoreError as exc:
        logger.exception("Failed to list simulation history")
        raise handle_store_error(exc) from exc

    runs = [
        SimulationRunSummary(
            id=row["id"],
            product_description=row["product_description"],
            target_segment=row["target_segment"],
            panel_size=row["panel_size"],
            overall_conversion_rate=row["overall_conversion_rate"],
            overall_dropout_rate=row["overall_dropout_rate"],
            overall_delayed_rate=row["overall_delayed_rate"],
            readiness_score=row["readiness_score"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return SimulationHistoryResponse(runs=runs)


@router.get("/{simulation_id}", response_model=SimulationResult)
async def get_run(
    simulation_id: UUID,
    user: AuthUser = Depends(get_current_user),
) -> SimulationResult:
    try:
        result = get_simulation_run(user.id, str(simulation_id))
    except SimulationStoreError as exc:
        logger.exception("Failed to fetch simulation %s", simulation_id)
        raise handle_store_error(exc) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return result
