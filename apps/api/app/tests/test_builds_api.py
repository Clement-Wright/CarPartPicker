from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_base_build() -> str:
    response = client.post("/api/builds", json={"trim_id": "gr86_2022_base", "scenario_name": "daily"})
    assert response.status_code == 200
    return response.json()["build"]["build_id"]


def test_build_lifecycle_endpoints() -> None:
    build_id = create_base_build()

    patch = client.patch(
        f"/api/builds/{build_id}/parts",
        json={"parts": {"brakes": "brakes_big_18", "wheels": "wheels_stock_17"}},
    )
    assert patch.status_code == 200

    validation = client.get(f"/api/builds/{build_id}/validate")
    assert validation.status_code == 200
    assert validation.json()["summary"]["blockers"] >= 1

    metrics = client.get(f"/api/builds/{build_id}/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["metrics"]["peak_hp"] >= 228

    dyno = client.get(f"/api/builds/{build_id}/dyno")
    assert dyno.status_code == 200
    assert dyno.json()["dyno"]["engine_curve"]

    render_config = client.get(f"/api/builds/{build_id}/render-config")
    assert render_config.status_code == 200
    assert render_config.json()["scene_objects"]

    graph = client.get(f"/api/builds/{build_id}/graph")
    assert graph.status_code == 200
    assert graph.json()["nodes"]


def test_clone_and_diff() -> None:
    build_id = create_base_build()
    client.patch(
        f"/api/builds/{build_id}/parts",
        json={"parts": {"wheels": "wheels_track_18", "tires": "tires_canyon_18"}},
    )

    diff = client.get(f"/api/builds/{build_id}/diff", params={"against": "stock"})
    assert diff.status_code == 200
    assert any(slot["changed"] for slot in diff.json()["slots"])

    cloned = client.post(f"/api/builds/{build_id}/clone")
    assert cloned.status_code == 200
    assert cloned.json()["build_id"] != build_id
