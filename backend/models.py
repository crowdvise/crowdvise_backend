from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class JourneyStage(BaseModel):
    order: int
    name: str
    description: str


class StageGenerationRequest(BaseModel):
    product_description: str
    test_scenario: str
    target_segment: str


class StageGenerationResponse(BaseModel):
    suggested_stages: list[JourneyStage]


class SimulationRequest(BaseModel):
    product_description: str
    target_segment: str
    panel_size: Literal[10, 25, 50]
    journey_stages: list[JourneyStage]


class OceanProfile(BaseModel):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float


class AgentProfile(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    location: str
    income_bracket: Literal["low", "middle", "high"]
    decision_style: Literal["impulsive", "deliberate", "analytical"]
    friction_threshold: int
    backstory: str
    ocean: OceanProfile
    status_quo_tendency: float
    context_attributes: dict[str, str] = Field(default_factory=dict)
    trigger_sensitivities: dict[str, float] = Field(default_factory=dict)
    lifestyle_notes: str


class StageReaction(BaseModel):
    stage_order: int
    stage_name: str
    behaviour: str
    internal_monologue: str
    friction_triggered: str | None
    friction_cost: int
    remaining_threshold: int
    what_would_change_this: str | None


class AgentJourney(BaseModel):
    agent: AgentProfile
    reactions: list[StageReaction]
    final_outcome: Literal["converted", "dropped", "delayed"]
    dropped_at_stage: str | None


class StageInsight(BaseModel):
    stage_name: str
    dropout_rate: float
    delay_rate: float
    top_friction_trigger: str | None
    confusion_rate: float


class SimulationResult(BaseModel):
    simulation_id: str
    overall_conversion_rate: float
    overall_dropout_rate: float
    overall_delayed_rate: float
    agent_journeys: list[AgentJourney]
    stage_insights: list[StageInsight]
    top_insights: list[str]
    readiness_score: int
    readiness_level: Literal["not_ready", "iterate", "ready"] | None = None

    @model_validator(mode="after")
    def _default_readiness_level(self) -> Self:
        if self.readiness_level is None:
            from services.readiness_score import readiness_level as level_for_score

            self.readiness_level = level_for_score(self.readiness_score)
        return self


class SimulationRunSummary(BaseModel):
    id: str
    product_description: str
    target_segment: str
    panel_size: int
    overall_conversion_rate: float
    overall_dropout_rate: float
    overall_delayed_rate: float
    readiness_score: int
    created_at: str


class SimulationHistoryResponse(BaseModel):
    runs: list[SimulationRunSummary]
