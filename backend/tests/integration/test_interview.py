import pytest
from fastapi.testclient import TestClient

from app.database.database import get_session
from app.database.models import Analysis, AnalysisResult
from app.interview import coach, routes
from app.interview.schemas import InterviewReport, NextTurn, QuestionPlan
from app.main import app

QUESTION_COUNT = 12


@pytest.mark.database
def test_interview_persists_variable_length_plan_followups_and_report(pg_session, monkeypatch):
    class ScriptedModel:
        def __init__(self, settings):
            pass

        async def structured(self, schema, instructions, data):
            if schema is QuestionPlan:
                assert data["projects"] == ["Built a FastAPI service"]
                return QuestionPlan(
                    questions=[
                        {
                            "question": f"Explain FastAPI decision {index}.",
                            "topic": f"Decision {index}",
                            "kind": "project",
                            "expected_concepts": ["A specific trade-off"],
                        }
                        for index in range(1, QUESTION_COUNT + 1)
                    ]
                )
            if schema is NextTurn:
                first = data["latest_turn"]["number"] == 1
                return NextTurn(
                    follow_up="What trade-off did you consider?" if first else "",
                    next_question="How would you test your route?" if first else "",
                )
            assert schema is InterviewReport
            assert len(data["transcript"]) == QUESTION_COUNT + 1
            return InterviewReport(
                summary="Keep explaining trade-offs.",
                feedback=[
                    {
                        "number": index,
                        "rating": 3,
                        "evidence": "FastAPI" if index == 1 else "invented quote",
                        "strength": "Named the tool.",
                        "improvement": "Give an example.",
                    }
                    for index in range(1, QUESTION_COUNT + 1)
                ],
                practice_tasks=["Explain a design decision."],
            )

    monkeypatch.setattr(coach, "LLMService", ScriptedModel)
    monkeypatch.setattr(routes, "require_live_model", lambda: None)
    monkeypatch.setattr(routes, "transcribe", lambda audio: "I used FastAPI.")
    analysis = Analysis(
        job_title="Backend intern", job_description="Build APIs with Python", workflow_status="approved"
    )
    analysis.result = AnalysisResult(
        source_text="Built a FastAPI service",
        payload={"resume": {"projects": ["Built a FastAPI service"]}, "job": {"required_skills": ["Python"]}},
    )
    pg_session.add(analysis)
    pg_session.commit()

    app.dependency_overrides[get_session] = lambda: pg_session
    try:
        client = TestClient(app)
        start_path = f"/api/v1/interviews/analysis/{analysis.id}"
        response = client.post(start_path)
        assert response.status_code == 201, response.text
        view = response.json()
        path = f"/api/v1/interviews/{view['id']}"
        assert "expected_concepts" not in response.text
        assert client.post(f"{path}/report").status_code == 409
        transcript = client.post(f"{path}/transcription", files={"audio": ("answer.wav", b"audio")})
        assert transcript.json() == {"text": "I used FastAPI."}

        original = {"version": view["version"], "text": transcript.json()["text"]}
        view = client.post(f"{path}/answers", json=original).json()
        assert view["answered"] == 1 and view["question"]["follow_up"]
        assert client.post(f"{path}/answers", json=original).status_code == 409
        assert client.get(path).json() == view

        view = client.post(
            f"{path}/answers", json={"version": view["version"], "text": "I compared two options."}
        ).json()
        assert view["question"] == {"number": 2, "text": "How would you test your route?", "follow_up": False}
        for number in range(2, QUESTION_COUNT + 1):
            assert view["question"]["number"] == number
            response = client.post(
                f"{path}/answers", json={"version": view["version"], "text": "My example."}
            )
            assert response.status_code == 200, response.text
            view = response.json()

        assert view["answered"] == QUESTION_COUNT and view["question"] is None
        report = client.post(f"{path}/report").json()
        assert report["report"]["feedback"][0]["evidence"] == "FastAPI"
        assert report["report"]["feedback"][1]["evidence"] == ""
        assert client.post(f"{path}/report").json() == report
        assert client.get(start_path).json()[0]["completed"] is True
    finally:
        app.dependency_overrides.clear()
