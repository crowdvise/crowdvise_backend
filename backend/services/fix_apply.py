from models import FixSuggestion, JourneyStage


def apply_fix_to_stages(
    baseline_stages: list[JourneyStage],
    fix: FixSuggestion,
) -> list[JourneyStage]:
    merged: list[JourneyStage] = []
    for stage in baseline_stages:
        if stage.order == fix.target_stage_order:
            merged.append(
                stage.model_copy(
                    update={
                        "name": fix.target_stage_name,
                        "description": fix.patched_description,
                    }
                )
            )
        else:
            merged.append(stage.model_copy())
    return merged


def find_stage_by_order(stages: list[JourneyStage], order: int) -> JourneyStage | None:
    for stage in stages:
        if stage.order == order:
            return stage
    return None
