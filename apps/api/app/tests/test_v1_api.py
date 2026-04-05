from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_v1_catalog_endpoints_expose_visualization_tiers() -> None:
    vehicles = client.get("/api/v1/vehicles/search", params={"q": "GR86"})
    assert vehicles.status_code == 200
    assert vehicles.json()["items"]

    proxy_parts = client.get("/api/v1/parts/search", params={"subsystem": "brakes", "vehicle_id": "gr86_2022_base"})
    assert proxy_parts.status_code == 200
    assert proxy_parts.json()["items"]
    assert proxy_parts.json()["items"][0]["visualization_mode"] == "proxy_from_dimensions"
    assert proxy_parts.json()["items"][0]["scene_renderable"] is True

    catalog_only_parts = client.get("/api/v1/parts/search", params={"subsystem": "tune", "vehicle_id": "gr86_2022_base"})
    assert catalog_only_parts.status_code == 200
    assert catalog_only_parts.json()["items"]
    assert all(item["visualization_mode"] == "catalog_only" for item in catalog_only_parts.json()["items"])
    assert all(item["catalog_visible"] is True for item in catalog_only_parts.json()["items"])

    part_id = catalog_only_parts.json()["items"][1]["part_id"]
    detail = client.get(f"/api/v1/parts/{part_id}")
    assert detail.status_code == 200
    assert detail.json()["visualization_mode"] == "catalog_only"
    assert detail.json()["scene_renderable"] is False

    prices = client.get(f"/api/v1/parts/{part_id}/prices")
    assert prices.status_code == 200
    assert prices.json()["snapshots"][0]["source"] == "seed_catalog"

    contracts = client.get("/api/v1/catalog/contracts")
    assert contracts.status_code == 200
    assert any(item["source_id"] == "tecdoc_catalog" for item in contracts.json()["items"])


def test_v1_build_endpoints_keep_validation_independent_from_scene_rendering() -> None:
    created = client.post("/api/v1/builds", json={"trim_id": "gr86_2022_base", "scenario_name": "daily"})
    assert created.status_code == 200
    build_id = created.json()["build_id"]

    patched = client.patch(
        f"/api/v1/builds/{build_id}/assembly",
        json={
            "parts": {"tune": "tune_stage1", "brakes": "brakes_big_18", "wheels": "wheels_stock_17"},
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
    assert payload["visualization_summary"]["catalog_only"] >= 1
    assert payload["support_notes"]
    tune_outcome = next(item for item in payload["subsystem_outcomes"] if item["subsystem"] == "tune")
    assert tune_outcome["visualization_mode"] == "catalog_only"
    assert tune_outcome["scene_renderable"] is False

    scene = client.get(f"/api/v1/builds/{build_id}/scene")
    assert scene.status_code == 200
    scene_payload = scene.json()
    assert scene_payload["items"]
    assert any(item["asset_mode"] == "proxy_from_dimensions" for item in scene_payload["items"])
    assert any(item["subsystem"] == "tune" for item in scene_payload["omitted_items"])
    assert scene_payload["summary"]["renderable_count"] >= 1

    renderable_only = client.get(
        "/api/v1/parts/search",
        params={"vehicle_id": "gr86_2022_base", "renderable_only": True},
    )
    assert renderable_only.status_code == 200
    assert renderable_only.json()["items"]
    assert all(item["scene_renderable"] is True for item in renderable_only.json()["items"])

    engine_sim = client.post(f"/api/v1/builds/{build_id}/simulate/engine")
    assert engine_sim.status_code == 200
    assert engine_sim.json()["mode"] == "engine"

    thermal_sim = client.post(f"/api/v1/builds/{build_id}/simulate/thermal")
    assert thermal_sim.status_code == 200
    assert "thermal_headroom" in thermal_sim.json()["payload"]
