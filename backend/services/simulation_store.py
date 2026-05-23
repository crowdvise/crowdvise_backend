from fastapi import HTTPException, status

from dependencies.auth import get_supabase
from models import SimulationRequest, SimulationResult


class SimulationStoreError(Exception):
    pass


def save_simulation_run(
    user_id: str,
    request: SimulationRequest,
    result: SimulationResult,
) -> None:
    row = {
        "id": result.simulation_id,
        "user_id": user_id,
        "product_description": request.product_description,
        "target_segment": request.target_segment,
        "panel_size": request.panel_size,
        "journey_stages": [s.model_dump() for s in request.journey_stages],
        "result": result.model_dump(),
        "overall_conversion_rate": result.overall_conversion_rate,
        "overall_dropout_rate": result.overall_dropout_rate,
        "overall_delayed_rate": result.overall_delayed_rate,
        "readiness_score": result.readiness_score,
    }

    try:
        response = get_supabase().table("simulation_runs").insert(row).execute()
    except Exception as exc:
        raise SimulationStoreError(str(exc)) from exc

    if getattr(response, "data", None) is None and getattr(response, "error", None):
        raise SimulationStoreError(str(response.error))


def list_simulation_runs(user_id: str, limit: int = 50) -> list[dict]:
    try:
        response = (
            get_supabase()
            .table("simulation_runs")
            .select(
                "id, product_description, target_segment, panel_size, "
                "overall_conversion_rate, overall_dropout_rate, overall_delayed_rate, "
                "readiness_score, created_at"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise SimulationStoreError(str(exc)) from exc

    return response.data or []


def get_simulation_run(user_id: str, simulation_id: str) -> SimulationResult | None:
    try:
        response = (
            get_supabase()
            .table("simulation_runs")
            .select("result, user_id")
            .eq("id", simulation_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise SimulationStoreError(str(exc)) from exc

    rows = response.data or []
    if not rows:
        return None

    return SimulationResult(**rows[0]["result"])


def handle_store_error(exc: SimulationStoreError) -> HTTPException:
    detail = str(exc)
    if "22P02" in detail and "uuid" in detail.lower():
        detail = "Invalid simulation id."
    elif "simulation_runs" in detail and ("does not exist" in detail or "PGRST205" in detail):
        detail = "Database table missing. Run backend/supabase/schema.sql in Supabase SQL Editor."
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
