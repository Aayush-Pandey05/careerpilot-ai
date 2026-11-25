import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database.database import get_session
from app.database.models import Analysis, AnalysisResult, Application, ResumeProfileRecord
from app.main import app
from tests.conftest import pdf_bytes


@pytest.mark.database
def test_postgres_api_crud_report_edits_and_cascade(pg_session, job_text):
    app.dependency_overrides[get_session] = lambda: pg_session
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/analyses",
            files={"resume": ("resume.pdf", pdf_bytes())},
            data={"job_description": job_text},
        )
        assert response.status_code == 201, response.text
        row = response.json()
        assert (
            client.get("/api/v1/analyses/" + row["id"]).json()["result"]["resume"]["candidate_name"]
            == "Aarav Mehta"
        )
        assert len(client.get("/api/v1/analyses").json()) == 1
        assert client.get("/api/v1/analyses/" + row["id"] + "/report").content.startswith(b"%PDF")
        assert (
            client.patch(
                "/api/v1/applications/" + row["application_id"], json={"status": "Applied"}
            ).status_code
            == 200
        )
        assert (
            client.patch(
                "/api/v1/applications/" + row["application_id"], json={"status": "Invalid"}
            ).status_code
            == 422
        )
        result = client.patch(
            f"/api/v1/analyses/{row['id']}/sections/email",
            json={"content": "I improved revenue by 99% using AWS."},
        )
        assert result.json()["workflow_status"] == "manual_review"
        result = client.patch(
            f"/api/v1/analyses/{row['id']}/sections/resume_suggestions",
            json={"content": "Clarify project scope.\nAdd only verified outcomes."},
        )
        assert result.json()["result"]["application"]["resume_suggestions"] == [
            "Clarify project scope.",
            "Add only verified outcomes.",
        ]
        assert client.post(f"/api/v1/analyses/{row['id']}/sections/email/regenerate").status_code == 200
        assert client.delete("/api/v1/analyses/" + row["id"]).status_code == 204
        for model in [Analysis, AnalysisResult, ResumeProfileRecord, Application]:
            assert pg_session.scalar(select(func.count()).select_from(model)) == 0
    finally:
        app.dependency_overrides.clear()
