"""Deterministic launch readiness from simulation outcomes (not LLM-judged)."""

from models import StageInsight

# Weights on 0–1 rates; perfect panel (all converted, no stage dropout) → 100
WEIGHT_CONVERSION = 1.00
WEIGHT_DROPOUT = 0.35
WEIGHT_DELAYED = 0.25
WEIGHT_WORST_STAGE_DROPOUT = 0.15

# readiness_level cutoffs on 0–100 score
CUTOFF_READY = 70
CUTOFF_ITERATE = 40


def compute_readiness_score(
    conversion_rate: float,
    dropout_rate: float,
    delayed_rate: float,
    stage_insights: list[StageInsight],
) -> int:
    """
    Same inputs → same score.

    Higher conversion raises the score; dropout and delay lower it.
    Worst-stage dropout adds a bounded penalty for concentrated funnel failure.
    """
    worst_stage_dropout = max((s.dropout_rate for s in stage_insights), default=0.0)

    raw = 100 * (
        WEIGHT_CONVERSION * conversion_rate
        - WEIGHT_DROPOUT * dropout_rate
        - WEIGHT_DELAYED * delayed_rate
        - WEIGHT_WORST_STAGE_DROPOUT * worst_stage_dropout
    )
    return int(max(0, min(100, round(raw))))


def readiness_level(score: int) -> str:
    if score >= CUTOFF_READY:
        return "ready"
    if score >= CUTOFF_ITERATE:
        return "iterate"
    return "not_ready"
