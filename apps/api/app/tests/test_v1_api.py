from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_v1_catalog_endpoints_expose_seed_mode_contracts() -> None:
    vehicles = client.get("/api/v1/vehicles/search", params={"q": "GR86"})
    assert vehicles.status_code == 200
    assert vehicles.json()["items"]

    parts = client.get("/api/v1/parts/search", params={"subsystem": "brakes"})
    assert parts.status_code == 200
    assert parts.json()["items"]

    part_id = parts.json()["items"][0]["part_id"]
    detail = client.get(f"/api/v1/parts/{part_id}")
    assert detail.status_code == 200
    assert detail.json()["asset_readiness"]["status"] == "seed_proxy_only"

    prices = client.get(f"/api/v1/parts/{part_id}/prices")
    assert prices.status_code == 200
    assert prices.json()["snapshots"][0]["source"] == "seed_catalog"

    contracts = client.get("/api/v1/catalog/contracts")
    assert contracts.status_code == 200
    assert any(item["source_id"] == "tecdoc_catalog" for item in contracts.json()["items"])


def test_v1_build_endpoints_cover_assembly_validation_scene_and_simulation() -> None:
    created = client.post("/api/v1/builds", json={"trim_id": "gr86_2022_base", "scenario_name": "daily"})
    assert created.status_code == 200
    build_id = created.json()["build_id"]

    patched = client.patch(
        f"/api/v1/builds/{build_id}/assembly",
        json={
            "parts": {"brakes": "brakes_big_18", "wheels": "wheels_stock_17"},
            "engine_patch": {"cam_profile_id": "cam_balanced"},
        },
    )
    assert patched.status_code == 200
    assert patched.json()["engine_build_spec"]["cam_profile"]["profile_id"] == "cam_balanced"

    validation = client.post(f"/api/v1/builds/{build_id}/validate")
    assert validation.status_code == 200
    payload = validation.json()
    assert payload["assembly_graph"]["nodes"]
    assert any(item["outcome"] == "invalid" for item in payload["subsystem_outcomes"])
    assert payload["production_blockers"]

    scene = client.get(f"/api/v1/builds/{build_id}/scene")
    assert scene.status_code == 200
    assert scene.json()["assets"]

    engine_sim = client.post(f"/api/v1/builds/{build_id}/simulate/engine")
    assert engine_sim.status_code == 200
    assert engine_sim.json()["mode"] == "engine"

    thermal_sim = client.post(f"/api/v1/builds/{build_id}/simulate/thermal")
    assert thermal_sim.status_code == 200
    assert "thermal_headroom" in thermal_sim.json()["payload"]
