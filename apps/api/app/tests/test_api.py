from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parse_and_recommend_endpoints() -> None:
    parsed = client.post(
        "/api/query/parse",
        json={"text": "Best daily brake + wheel upgrade under $2,500", "mode": "build_path"},
    )
    assert parsed.status_code == 200
    payload = parsed.json()
    assert payload["budget_max"] == 2500

    response = client.post(
        "/api/recommend/builds",
        json={
            "trim_id": "gr86_2022_base",
            "query": payload,
            "selected_goals": payload["goals"],
            "budget_max": payload["budget_max"],
            "current_setup": {"wheel_diameter": 17, "keep_current_wheels": False, "notes": []},
        },
    )
    assert response.status_code == 200
    assert response.json()
