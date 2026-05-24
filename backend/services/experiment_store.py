from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException

from dependencies.auth import get_supabase
from models import (
    AgentProfile,
    ExperimentCompareResponse,
    ExperimentRunSummary,
    FixSuggestion,
    JourneyStage,
    SimulationRequest,
    SimulationResult,
)
from services.simulation_store import SimulationStoreError

MAX_RERUNS = 2
MAX_RUNS = MAX_RERUNS + 1


class ExperimentStoreError(Exception):
    pass


def _table_missing(exc: Exception) -> bool:
    detail = str(exc)
    return "simulation_experiments" in detail and (
        "does not exist" in detail or "PGRST205" in detail
    )


def create_experiment(
    user_id: str,
    product_description: str,
    target_segment: str,
    panel_size: int,
) -> str:
    experiment_id = str(uuid.uuid4())
    row = {
        "id": experiment_id,
        "user_id": user_id,
        "product_description": product_description,
        "target_segment": target_segment,
        "panel_size": panel_size,
        "panel_profiles": [],
    }
    try:
        get_supabase().table("simulation_experiments").insert(row).execute()
    except Exception as exc:
        raise ExperimentStoreError(str(exc)) from exc
    return experiment_id


def save_baseline_run(
    user_id: str,
    experiment_id: str,
    request: SimulationRequest,
    result: SimulationResult,
    profiles: list[AgentProfile],
) -> None:
    run_row = _build_run_row(
        user_id=user_id,
        experiment_id=experiment_id,
        request=request,
        result=result,
        run_kind="baseline",
        run_index=0,
        applied_fix=None,
        parent_run_id=None,
    )
    try:
        get_supabase().table("simulation_runs").insert(run_row).execute()
        get_supabase().table("simulation_experiments").update(
            {
                "baseline_run_id": result.simulation_id,
                "panel_profiles": [p.model_dump() for p in profiles],
            }
        ).eq("id", experiment_id).eq("user_id", user_id).execute()
    except Exception as exc:
        raise ExperimentStoreError(str(exc)) from exc


def save_rerun(
    user_id: str,
    experiment_id: str,
    request: SimulationRequest,
    result: SimulationResult,
    *,
    run_index: int,
    applied_fix: FixSuggestion,
    parent_run_id: str,
) -> None:
    run_row = _build_run_row(
        user_id=user_id,
        experiment_id=experiment_id,
        request=request,
        result=result,
        run_kind="rerun",
        run_index=run_index,
        applied_fix=applied_fix,
        parent_run_id=parent_run_id,
    )
    try:
        get_supabase().table("simulation_runs").insert(run_row).execute()
    except Exception as exc:
        raise ExperimentStoreError(str(exc)) from exc


def _build_run_row(
    *,
    user_id: str,
    experiment_id: str,
    request: SimulationRequest,
    result: SimulationResult,
    run_kind: str,
    run_index: int,
    applied_fix: FixSuggestion | None,
    parent_run_id: str | None,
) -> dict[str, Any]:
    return {
        "id": result.simulation_id,
        "user_id": user_id,
        "experiment_id": experiment_id,
        "product_description": request.product_description,
        "target_segment": request.target_segment,
        "panel_size": request.panel_size,
        "journey_stages": [s.model_dump() for s in request.journey_stages],
        "result": result.model_dump(),
        "overall_conversion_rate": result.overall_conversion_rate,
        "overall_dropout_rate": result.overall_dropout_rate,
        "overall_delayed_rate": result.overall_delayed_rate,
        "readiness_score": result.readiness_score,
        "run_kind": run_kind,
        "run_index": run_index,
        "applied_fix": applied_fix.model_dump() if applied_fix else None,
        "parent_run_id": parent_run_id,
    }


def get_experiment_row(user_id: str, experiment_id: str) -> dict | None:
    try:
        response = (
            get_supabase()
            .table("simulation_experiments")
            .select("*")
            .eq("id", experiment_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise ExperimentStoreError(str(exc)) from exc
    rows = response.data or []
    return rows[0] if rows else None


def list_experiment_runs(user_id: str, experiment_id: str) -> list[dict]:
    try:
        response = (
            get_supabase()
            .table("simulation_runs")
            .select(
                "id, run_kind, run_index, applied_fix, journey_stages, "
                "overall_conversion_rate, overall_dropout_rate, overall_delayed_rate, "
                "readiness_score, result, created_at"
            )
            .eq("experiment_id", experiment_id)
            .eq("user_id", user_id)
            .order("run_index")
            .execute()
        )
    except Exception as exc:
        raise ExperimentStoreError(str(exc)) from exc
    return response.data or []


def count_reruns(user_id: str, experiment_id: str) -> int:
    runs = list_experiment_runs(user_id, experiment_id)
    return sum(1 for r in runs if r.get("run_kind") == "rerun")


def reruns_remaining(user_id: str, experiment_id: str) -> int:
    return max(0, MAX_RERUNS - count_reruns(user_id, experiment_id))


def get_panel_profiles(experiment: dict) -> list[AgentProfile]:
    raw = experiment.get("panel_profiles") or []
    return [AgentProfile(**p) for p in raw]


def get_baseline_journey_stages(user_id: str, experiment_id: str) -> list[JourneyStage]:
    runs = list_experiment_runs(user_id, experiment_id)
    baseline = next((r for r in runs if r.get("run_index") == 0), None)
    if not baseline:
        raise ExperimentStoreError("Baseline run not found for experiment")
    return [JourneyStage(**s) for s in baseline.get("journey_stages") or []]


def get_cached_fix_suggestions(experiment: dict) -> list[FixSuggestion] | None:
    raw = experiment.get("fix_suggestions")
    if not raw:
        return None
    return [FixSuggestion(**f) for f in raw]


def cache_fix_suggestions(
    user_id: str,
    experiment_id: str,
    fixes: list[FixSuggestion],
) -> None:
    try:
        get_supabase().table("simulation_experiments").update(
            {"fix_suggestions": [f.model_dump() for f in fixes]}
        ).eq("id", experiment_id).eq("user_id", user_id).execute()
    except Exception as exc:
        raise ExperimentStoreError(str(exc)) from exc


def get_fix_by_id(fixes: list[FixSuggestion], fix_id: str) -> FixSuggestion | None:
    for fix in fixes:
        if fix.id == fix_id:
            return fix
    return None


def build_compare_response(user_id: str, experiment_id: str) -> ExperimentCompareResponse:
    experiment = get_experiment_row(user_id, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    runs = list_experiment_runs(user_id, experiment_id)
    baseline_stages = get_baseline_journey_stages(user_id, experiment_id)
    summaries: list[ExperimentRunSummary] = []

    for row in runs:
        result = SimulationResult(**row["result"])
        applied = row.get("applied_fix")
        summaries.append(
            ExperimentRunSummary(
                run_id=row["id"],
                run_kind=row["run_kind"],
                run_index=row["run_index"],
                applied_fix=FixSuggestion(**applied) if applied else None,
                overall_conversion_rate=row["overall_conversion_rate"],
                overall_dropout_rate=row["overall_dropout_rate"],
                overall_delayed_rate=row["overall_delayed_rate"],
                readiness_score=row["readiness_score"],
                readiness_level=result.readiness_level,
                created_at=row["created_at"],
            )
        )

    return ExperimentCompareResponse(
        experiment_id=experiment_id,
        product_description=experiment["product_description"],
        target_segment=experiment["target_segment"],
        panel_size=experiment["panel_size"],
        baseline_journey_stages=baseline_stages,
        runs=summaries,
        reruns_remaining=reruns_remaining(user_id, experiment_id),
        fix_suggestions=get_cached_fix_suggestions(experiment),
    )


def handle_experiment_store_error(exc: ExperimentStoreError) -> HTTPException:
    detail = str(exc)
    if _table_missing(exc):
        detail = (
            "Experiments tables missing. Run backend/supabase/migrations/"
            "002_experiments_and_reruns.sql in Supabase SQL Editor."
        )
    return HTTPException(status_code=503, detail=detail)


def handle_as_store_error(exc: ExperimentStoreError) -> HTTPException:
    return handle_experiment_store_error(exc)
