from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analysis_requires_repository_input() -> None:
    response = client.post(
        "/analysis",
        json={},
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Provide either repository_path "
            "or repository_url."
        )
    }