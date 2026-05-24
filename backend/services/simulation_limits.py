"""Shared limits for validation, LLM budgets, and profile batching."""

import math

PROFILE_BATCH_SIZE = 10
MAX_TOP_UP_ROUNDS = 2

# Field length caps (characters)
MAX_PRODUCT_DESCRIPTION = 4_000
MAX_TEST_SCENARIO = 2_000
MAX_TARGET_SEGMENT = 1_000
MAX_STAGE_NAME = 120
MAX_STAGE_DESCRIPTION = 1_500
MAX_JOURNEY_STAGES = 8

# Per POST /simulation/run
MAX_PANEL_STAGE_CALLS = 250  # panel_size × stages (e.g. 50×5)
MAX_LLM_CALLS_PER_SIMULATION = 320  # includes profile batches + insights


def estimate_run_llm_calls(panel_size: int, num_stages: int) -> int:
    batches = math.ceil(panel_size / PROFILE_BATCH_SIZE)
    profile_calls = batches * (1 + MAX_TOP_UP_ROUNDS)
    return profile_calls + (panel_size * num_stages) + 1


def validate_run_budget(panel_size: int, num_stages: int) -> None:
    from fastapi import HTTPException

    if num_stages < 1:
        raise HTTPException(status_code=400, detail="At least one journey stage is required")
    if num_stages > MAX_JOURNEY_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"At most {MAX_JOURNEY_STAGES} journey stages allowed.",
        )
    if panel_size * num_stages > MAX_PANEL_STAGE_CALLS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"panel_size × stages ({panel_size}×{num_stages}="
                f"{panel_size * num_stages}) exceeds limit {MAX_PANEL_STAGE_CALLS}. "
                "Use a smaller panel or fewer stages."
            ),
        )
    estimated = estimate_run_llm_calls(panel_size, num_stages)
    if estimated > MAX_LLM_CALLS_PER_SIMULATION:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Estimated {estimated} LLM calls for this run exceeds limit "
                f"{MAX_LLM_CALLS_PER_SIMULATION}. Reduce panel_size or stages."
            ),
        )
