from app.catalog_import_schemas import CatalogImportTriggerRequest
from app.services.catalog_ingest_service import FixtureApiPullAdapter, FixtureExportLoadAdapter, trigger_catalog_import


def test_fixture_adapters_emit_same_normalized_raw_record_envelope_shape() -> None:
    api_records = FixtureApiPullAdapter().fetch()
    export_records = FixtureExportLoadAdapter().fetch()

    assert [item.entity_type for item in api_records] == [item.entity_type for item in export_records]
    assert [item.source_record_id for item in api_records] == [item.source_record_id for item in export_records]
    assert [sorted(item.payload.keys()) for item in api_records] == [sorted(item.payload.keys()) for item in export_records]


def test_trigger_catalog_import_records_raw_payloads_and_normalized_counts() -> None:
    response = trigger_catalog_import(
        CatalogImportTriggerRequest(
            source_id="licensed_fixture_catalog",
            adapter_mode="export_load",
            force_reimport=True,
        )
    )
    assert response.run.status == "succeeded"
    assert response.raw_payloads >= response.run.normalized_record_count
    assert response.normalized_entities["vehicle"] >= 1
    assert response.normalized_entities["part"] >= 1
