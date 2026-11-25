from fastapi.testclient import TestClient

from app.database.database import get_session
from app.main import app
from tests.conftest import pdf_bytes


def test_health_when_database_fails():
    class Failed:
        def execute(self, *args):
            raise RuntimeError("private connection data")

    app.dependency_overrides[get_session] = lambda: Failed()
    try:
        response = TestClient(app).get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["database"] == "unavailable"
        assert "private" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_invalid_upload_and_empty_job():
    # No DB operation should occur for invalid requests.
    app.dependency_overrides[get_session] = lambda: None
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/analyses",
            files={"resume": ("x.exe", b"bad")},
            data={"job_description": "Python required for a development internship role."},
        )
        assert response.status_code == 422
        response = client.post(
            "/api/v1/analyses", files={"resume": ("x.pdf", pdf_bytes())}, data={"job_description": " "}
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_cors_restricts_unrecognized_origins():
    response = TestClient(app).options(
        "/api/v1/analyses",
        headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers
