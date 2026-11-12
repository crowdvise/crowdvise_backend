from fastapi.testclient import TestClient

from main import app
from models import StageInsight
from services.readiness_score import compute_readiness_score, readiness_level


def test_app_metadata():
    assert app.title == "Crowdvise API"


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_compute_readiness_score_deterministic():
    insights = [
        StageInsight(
            stage_name="signup",
            dropout_rate=0.1,
            delay_rate=0.05,
            top_friction_trigger=None,
            confusion_rate=0.02,
        )
    ]
    score = compute_readiness_score(
        conversion_rate=0.8,
        dropout_rate=0.1,
        delayed_rate=0.05,
        stage_insights=insights,
    )
    assert score == 74
    assert readiness_level(score) == "ready"
