import logging
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from dependencies.auth import (
    AuthUser,
    get_current_user,
    require_generate_stages_limit,
    require_history_limit,
    require_run_limit,
)
from models import (
    ExperimentCompareResponse,
    FixSuggestionsResponse,
    PreviewFixRequest,
    PreviewFixResponse,
    SimulationHistoryResponse,
    SimulationRequest,
    SimulationResult,
    SimulationRunResponse,
    SimulationRunSummary,
    StageGenerationRequest,
    StageGenerationResponse,
    TestFixRequest,
)
from services.experiment_store import (
    ExperimentStoreError,
    build_compare_response,
    cache_fix_suggestions,
    count_reruns,
    create_experiment,
    get_baseline_journey_stages,
    get_cached_fix_suggestions,
    get_experiment_row,
    get_fix_by_id,
    get_panel_profiles,
    handle_experiment_store_error,
    reruns_remaining,
    save_baseline_run,
    save_rerun,
)
from services.fix_apply import apply_fix_to_stages
from services.fix_suggester import generate_fix_suggestions
from services.insight_aggregator import build_simulation_result
from services.journey_generator import generate_stages
from services.simulation_runner import run_simulation, run_simulation_with_panel
from services.simulation_store import (
    SimulationStoreError,
    get_simulation_run,
    handle_store_error,
    list_simulation_runs,
)
from services.usage_context import set_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulation", tags=["simulation"])

_EXPERIMENTS_AUTH_DETAIL = (
    "Experiments require authentication. Set AUTH_DISABLED=false and send "
    "Authorization: Bearer <supabase_access_token>. Use experiment_id from "
    "POST /simulation/run (top-level field), not result.simulation_id."
)


def _require_experiments_auth() -> None:
    if settings.auth_disabled:
        raise HTTPException(status_code=400, detail=_EXPERIMENTS_AUTH_DETAIL)


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


@router.post("/run", response_model=SimulationRunResponse)
async def run(
    request: SimulationRequest,
    user: AuthUser = Depends(require_run_limit),
) -> SimulationRunResponse:
    set_user(user.id)
    journeys, profiles = await run_simulation(request)
    result = await build_simulation_result(journeys, request.product_description)

    experiment_id = ""
    remaining = 2

    if not settings.auth_disabled:
        try:
            experiment_id = create_experiment(
                user.id,
                request.product_description,
                request.target_segment,
                request.panel_size,
            )
            save_baseline_run(user.id, experiment_id, request, result, profiles)
            remaining = reruns_remaining(user.id, experiment_id)
        except ExperimentStoreError as exc:
            logger.exception("Failed to save baseline experiment for user %s", user.id)
            raise handle_experiment_store_error(exc) from exc

    return SimulationRunResponse(
        result=result,
        experiment_id=experiment_id,
        run_kind="baseline",
        run_index=0,
        reruns_remaining=remaining,
        journey_stages=request.journey_stages,
    )


@router.get("/run", include_in_schema=False)
async def run_wrong_method() -> None:
    raise HTTPException(
        status_code=405,
        detail=(
            "Use POST /simulation/run to start a simulation. "
            "Use GET /simulation/{simulation_id} with the id from the POST response to fetch a saved run."
        ),
    )


@router.get("/experiments/{experiment_id}", response_model=ExperimentCompareResponse)
async def get_experiment(
    experiment_id: UUID,
    user: AuthUser = Depends(get_current_user),
) -> ExperimentCompareResponse:
    _require_experiments_auth()
    try:
        return build_compare_response(user.id, str(experiment_id))
    except ExperimentStoreError as exc:
        raise handle_experiment_store_error(exc) from exc


@router.post(
    "/experiments/{experiment_id}/suggest-fixes",
    response_model=FixSuggestionsResponse,
)
async def suggest_fixes(
    experiment_id: UUID,
    user: AuthUser = Depends(get_current_user),
) -> FixSuggestionsResponse:
    _require_experiments_auth()
    set_user(user.id)
    eid = str(experiment_id)
    try:
        experiment = get_experiment_row(user.id, eid)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")

        cached = get_cached_fix_suggestions(experiment)
        if cached:
            fixes = cached
        else:
            baseline_run_id = experiment.get("baseline_run_id")
            if not baseline_run_id:
                raise HTTPException(status_code=400, detail="Baseline run not found")
            result = get_simulation_run(user.id, baseline_run_id)
            if not result:
                raise HTTPException(status_code=404, detail="Baseline result not found")
            baseline_stages = get_baseline_journey_stages(user.id, eid)
            fixes = await generate_fix_suggestions(
                experiment["product_description"],
                baseline_stages,
                result,
            )
            cache_fix_suggestions(user.id, eid, fixes)

        return FixSuggestionsResponse(
            experiment_id=eid,
            fixes=fixes,
            reruns_remaining=reruns_remaining(user.id, eid),
        )
    except ExperimentStoreError as exc:
        raise handle_experiment_store_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/experiments/{experiment_id}/preview-fix",
    response_model=PreviewFixResponse,
)
async def preview_fix(
    experiment_id: UUID,
    body: PreviewFixRequest,
    user: AuthUser = Depends(get_current_user),
) -> PreviewFixResponse:
    _require_experiments_auth()
    eid = str(experiment_id)
    try:
        experiment = get_experiment_row(user.id, eid)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")

        fixes = get_cached_fix_suggestions(experiment)
        if not fixes:
            raise HTTPException(
                status_code=400,
                detail="Generate fix suggestions first via POST .../suggest-fixes",
            )

        fix = get_fix_by_id(fixes, body.fix_id)
        if not fix:
            raise HTTPException(status_code=404, detail="Fix not found")

        baseline_stages = get_baseline_journey_stages(user.id, eid)
        journey_after = (
            body.journey_stages
            if body.journey_stages
            else apply_fix_to_stages(baseline_stages, fix)
        )

        return PreviewFixResponse(
            experiment_id=eid,
            fix=fix,
            journey_before=baseline_stages,
            journey_after=journey_after,
        )
    except ExperimentStoreError as exc:
        raise handle_experiment_store_error(exc) from exc


@router.post(
    "/experiments/{experiment_id}/test-fix",
    response_model=SimulationRunResponse,
)
async def test_fix(
    experiment_id: UUID,
    body: TestFixRequest,
    user: AuthUser = Depends(require_run_limit),
) -> SimulationRunResponse:
    set_user(user.id)
    eid = str(experiment_id)

    _require_experiments_auth()

    try:
        experiment = get_experiment_row(user.id, eid)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")

        remaining = reruns_remaining(user.id, eid)
        if remaining <= 0:
            raise HTTPException(
                status_code=400,
                detail="Maximum reruns reached (2). Start a new experiment to test more fixes.",
            )

        fixes = get_cached_fix_suggestions(experiment)
        if not fixes:
            raise HTTPException(
                status_code=400,
                detail="Generate fix suggestions first via POST .../suggest-fixes",
            )

        fix = get_fix_by_id(fixes, body.fix_id)
        if not fix:
            raise HTTPException(status_code=404, detail="Fix not found")

        baseline_stages = get_baseline_journey_stages(user.id, eid)
        journey_stages = (
            body.journey_stages
            if body.journey_stages
            else apply_fix_to_stages(baseline_stages, fix)
        )

        rerun_request = SimulationRequest(
            product_description=experiment["product_description"],
            target_segment=experiment["target_segment"],
            panel_size=experiment["panel_size"],
            journey_stages=journey_stages,
        )

        profiles = get_panel_profiles(experiment)
        journeys = await run_simulation_with_panel(rerun_request, profiles)
        result = await build_simulation_result(
            journeys,
            rerun_request.product_description,
        )
        result.simulation_id = str(uuid.uuid4())

        run_index = count_reruns(user.id, eid) + 1
        baseline_run_id = experiment.get("baseline_run_id")
        save_rerun(
            user.id,
            eid,
            rerun_request,
            result,
            run_index=run_index,
            applied_fix=fix,
            parent_run_id=baseline_run_id,
        )

        return SimulationRunResponse(
            result=result,
            experiment_id=eid,
            run_kind="rerun",
            run_index=run_index,
            reruns_remaining=reruns_remaining(user.id, eid),
            journey_stages=journey_stages,
        )
    except ExperimentStoreError as exc:
        logger.exception("Failed test-fix for experiment %s", eid)
        raise handle_experiment_store_error(exc) from exc


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
