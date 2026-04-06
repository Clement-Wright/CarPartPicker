from fastapi.testclient import TestClient

from app.main import app


def test_import_runs_and_catalog_endpoints_use_imported_slice() -> None:
    with TestClient(app) as client:
        vehicles = client.get("/api/v1/vehicles/search", params={"q": "GR86"})
        assert vehicles.status_code == 200
        assert vehicles.json()["source_mode"] == "licensed"
        assert vehicles.json()["items"]
        assert vehicles.json()["items"][0]["record_provenance"]["source_id"] == "licensed_fixture_catalog"

        runs = client.get("/api/catalog/import/runs")
        assert runs.status_code == 200
        assert runs.json()
        assert runs.json()[0]["run"]["source_id"] == "licensed_fixture_catalog"
        assert runs.json()[0]["raw_payloads"] >= 1

        api_pull = client.post(
            "/api/catalog/import/runs",
            json={"source_id": "licensed_fixture_catalog", "adapter_mode": "api_pull", "force_reimport": True},
        )
        assert api_pull.status_code == 200
        assert api_pull.json()["run"]["status"] == "succeeded"

        brakes = client.get("/api/v1/parts/search", params={"subsystem": "brakes", "vehicle_id": "gr86_2022_base"})
        assert brakes.status_code == 200
        assert brakes.json()["source_mode"] == "licensed"
        assert brakes.json()["items"]
        assert all(item["source_mode"] == "licensed" for item in brakes.json()["items"])
        assert all(item["visualization_mode"] == "proxy_from_dimensions" for item in brakes.json()["items"])

        prices = client.get("/api/v1/parts/brakes_big_18/prices")
        assert prices.status_code == 200
        assert prices.json()["snapshots"][0]["provider"] == "Licensed Fixture Source"
        assert prices.json()["snapshots"][0]["import_run_id"]


def test_v1_build_validation_returns_structured_compatibility_diagnostics() -> None:
    with TestClient(app) as client:
        created = client.post("/api/v1/builds", json={"trim_id": "gr86_2022_base", "scenario_name": "daily"})
        assert created.status_code == 200
        build_id = created.json()["build_id"]

        editor = client.get(f"/api/v1/builds/{build_id}/engine-editor")
        assert editor.status_code == 200
        assert editor.json()["groups"]
        assert any(group["group_id"] == "fuel_and_ignition" for group in editor.json()["groups"])

        patched = client.patch(
            f"/api/v1/builds/{build_id}/assembly",
            json={
                "parts": {
                    "brakes": "brakes_big_18",
                    "wheels": "wheels_stock_17",
                    "tires": "tires_too_wide_18",
                    "tune": "tune_stage1",
                },
                "engine_patch": {
                    "engine_family_id": "g16e_turbo_swap",
                    "boost_psi": 19.0,
                    "ambient_temp_c": 32.0,
                    "intercooler_effectiveness": 0.7,
                },
            },
        )
        assert patched.status_code == 200
        assert patched.json()["engine_build_spec"]["engine_family_id"] == "g16e_turbo_swap"

        validation = client.post(f"/api/v1/builds/{build_id}/validate")
        assert validation.status_code == 200
        payload = validation.json()
        assert payload["source_mode"] == "licensed"
        assert payload["compatibility_stages"]
        codes = {item["error_code"] for item in payload["compatibility_diagnostics"]}
        assert "BRAKE_WHEEL_CLEARANCE_FAILURE" in codes
        assert "TIRE_TOO_WIDE_FOR_WHEEL" in codes
        assert "ENGINE_MOUNT_FAMILY_MISMATCH" in codes
        assert "BELLHOUSING_PATTERN_MISMATCH" in codes
        assert any(item["stage"] == "dependency_rules" for item in payload["compatibility_diagnostics"])

        scene = client.get(f"/api/v1/builds/{build_id}/scene")
        assert scene.status_code == 200
        scene_payload = scene.json()
        assert scene_payload["source_mode"] == "licensed"
        assert scene_payload["summary"]["proxy_count"] >= 1
        assert any(item["subsystem"] == "tune" for item in scene_payload["omitted_items"])
        assert any(item["anchor"]["slot"] == "front_left_hub" for item in scene_payload["items"])

        renderable_only = client.get(
            "/api/v1/parts/search",
            params={"vehicle_id": "gr86_2022_base", "renderable_only": True},
        )
        assert renderable_only.status_code == 200
        assert renderable_only.json()["items"]
        assert all(item["scene_renderable"] is True for item in renderable_only.json()["items"])

        engine_sim = client.post(f"/api/v1/builds/{build_id}/simulate/engine")
        assert engine_sim.status_code == 200
        assert engine_sim.json()["source_mode"] == "licensed"
        assert engine_sim.json()["mode"] == "engine"
        assert engine_sim.json()["calibration_state"] == "calibrated"
        assert engine_sim.json()["payload"]["model_version"] == "mean_value_v1"
        assert engine_sim.json()["payload"]["derived_values"]["charge_temp_c_peak"] >= 32.0
        assert engine_sim.json()["payload"]["warnings"]

        vehicle_sim = client.post(f"/api/v1/builds/{build_id}/simulate/vehicle")
        thermal_sim = client.post(f"/api/v1/builds/{build_id}/simulate/thermal")
        assert vehicle_sim.status_code == 200
        assert thermal_sim.status_code == 200
        assert vehicle_sim.json()["calibration_state"] == "calibrated"
        assert thermal_sim.json()["calibration_state"] == "calibrated"
        assert vehicle_sim.json()["payload"]["engine_spec_hash"] == engine_sim.json()["payload"]["spec_hash"]
        assert thermal_sim.json()["payload"]["engine_spec_hash"] == engine_sim.json()["payload"]["spec_hash"]
        assert thermal_sim.json()["payload"]["warnings"]


def test_imported_uncalibrated_combo_returns_calibration_required() -> None:
    with TestClient(app) as client:
        created = client.post("/api/v1/builds", json={"trim_id": "gr86_2023_premium", "scenario_name": "daily"})
        assert created.status_code == 200
        build_id = created.json()["build_id"]

        patched = client.patch(
            f"/api/v1/builds/{build_id}/assembly",
            json={"engine_patch": {"engine_family_id": "g16e_turbo_swap"}},
        )
        assert patched.status_code == 200

        engine_sim = client.post(f"/api/v1/builds/{build_id}/simulate/engine")
        vehicle_sim = client.post(f"/api/v1/builds/{build_id}/simulate/vehicle")
        thermal_sim = client.post(f"/api/v1/builds/{build_id}/simulate/thermal")
        braking_sim = client.post(f"/api/v1/builds/{build_id}/simulate/braking")
        handling_sim = client.post(f"/api/v1/builds/{build_id}/simulate/handling")

        assert engine_sim.json()["calibration_state"] == "calibration_required"
        assert vehicle_sim.json()["calibration_state"] == "calibration_required"
        assert thermal_sim.json()["calibration_state"] == "calibration_required"
        assert braking_sim.json()["calibration_state"] == "calibration_required"
        assert handling_sim.json()["calibration_state"] == "calibration_required"
        assert engine_sim.json()["calibration_state"] != "seed_heuristic"
