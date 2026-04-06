"""seed mode foundation schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trims",
        sa.Column("trim_id", sa.String(length=64), primary_key=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("make", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("trim", sa.String(length=64), nullable=False),
        sa.Column("stock_wheel_diameter", sa.Integer(), nullable=False),
        sa.Column("safety_index", sa.Float(), nullable=False),
        sa.Column("mod_potential", sa.Float(), nullable=False),
    )
    op.create_table(
        "nhtsa_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("trim_id", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_nhtsa_snapshots_trim_id", "nhtsa_snapshots", ["trim_id"])
    op.create_table(
        "recommendation_cache",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "ingest_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_ingest_audit_dataset", "ingest_audit", ["dataset"])
    op.create_table(
        "catalog_sources",
        sa.Column("source_id", sa.String(length=64), primary_key=True),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("contract_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "catalog_import_runs",
        sa.Column("import_run_id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("adapter_mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("categories_json", sa.JSON(), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("raw_record_count", sa.Integer(), nullable=False),
        sa.Column("normalized_record_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("notes_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_catalog_import_runs_source_id", "catalog_import_runs", ["source_id"])
    op.create_table(
        "catalog_import_attempts",
        sa.Column("attempt_id", sa.String(length=64), primary_key=True),
        sa.Column("import_run_id", sa.String(length=64), nullable=False),
        sa.Column("adapter_mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_catalog_import_attempts_import_run_id", "catalog_import_attempts", ["import_run_id"])
    op.create_table(
        "raw_source_payloads",
        sa.Column("payload_id", sa.String(length=64), primary_key=True),
        sa.Column("import_run_id", sa.String(length=64), nullable=False),
        sa.Column("attempt_id", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_raw_source_payloads_attempt_id", "raw_source_payloads", ["attempt_id"])
    op.create_index("ix_raw_source_payloads_entity_type", "raw_source_payloads", ["entity_type"])
    op.create_index("ix_raw_source_payloads_import_run_id", "raw_source_payloads", ["import_run_id"])
    op.create_index("ix_raw_source_payloads_payload_hash", "raw_source_payloads", ["payload_hash"])
    op.create_index("ix_raw_source_payloads_source_id", "raw_source_payloads", ["source_id"])
    op.create_index("ix_raw_source_payloads_source_record_id", "raw_source_payloads", ["source_record_id"])
    op.create_table(
        "vehicles",
        sa.Column("vehicle_id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("import_run_id", sa.String(length=64), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("supported_slice", sa.Boolean(), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("vehicle_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_vehicles_import_run_id", "vehicles", ["import_run_id"])
    op.create_index("ix_vehicles_source_id", "vehicles", ["source_id"])
    op.create_table(
        "engine_families",
        sa.Column("engine_family_id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("import_run_id", sa.String(length=64), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("engine_family_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_engine_families_import_run_id", "engine_families", ["import_run_id"])
    op.create_index("ix_engine_families_source_id", "engine_families", ["source_id"])
    op.create_table(
        "engine_configs",
        sa.Column("config_id", sa.String(length=64), primary_key=True),
        sa.Column("engine_family_id", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("import_run_id", sa.String(length=64), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("engine_config_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_engine_configs_engine_family_id", "engine_configs", ["engine_family_id"])
    op.create_index("ix_engine_configs_import_run_id", "engine_configs", ["import_run_id"])
    op.create_index("ix_engine_configs_source_id", "engine_configs", ["source_id"])
    op.create_table(
        "drivetrain_configs",
        sa.Column("config_id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("import_run_id", sa.String(length=64), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("drivetrain_config_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_drivetrain_configs_import_run_id", "drivetrain_configs", ["import_run_id"])
    op.create_index("ix_drivetrain_configs_source_id", "drivetrain_configs", ["source_id"])
    op.create_table(
        "parts",
        sa.Column("part_id", sa.String(length=64), primary_key=True),
        sa.Column("subsystem", sa.String(length=64), nullable=False),
        sa.Column("brand", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("import_run_id", sa.String(length=64), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("supported_slice", sa.Boolean(), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("part_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_parts_import_run_id", "parts", ["import_run_id"])
    op.create_index("ix_parts_subsystem", "parts", ["subsystem"])
    op.create_index("ix_parts_source_id", "parts", ["source_id"])
    op.create_table(
        "part_applications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("part_id", sa.String(length=64), nullable=False),
        sa.Column("vehicle_id", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("import_run_id", sa.String(length=64), nullable=True),
        sa.Column("application_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_part_applications_import_run_id", "part_applications", ["import_run_id"])
    op.create_index("ix_part_applications_part_id", "part_applications", ["part_id"])
    op.create_index("ix_part_applications_source_id", "part_applications", ["source_id"])
    op.create_index("ix_part_applications_vehicle_id", "part_applications", ["vehicle_id"])
    op.create_table(
        "digital_assets",
        sa.Column("asset_id", sa.String(length=64), primary_key=True),
        sa.Column("part_id", sa.String(length=64), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("readiness_status", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("import_run_id", sa.String(length=64), nullable=True),
        sa.Column("storage_uri", sa.String(length=512), nullable=True),
        sa.Column("asset_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_digital_assets_import_run_id", "digital_assets", ["import_run_id"])
    op.create_index("ix_digital_assets_part_id", "digital_assets", ["part_id"])
    op.create_index("ix_digital_assets_source_id", "digital_assets", ["source_id"])
    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("part_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("import_run_id", sa.String(length=64), nullable=True),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("price_usd", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("availability", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_price_snapshots_import_run_id", "price_snapshots", ["import_run_id"])
    op.create_index("ix_price_snapshots_part_id", "price_snapshots", ["part_id"])
    op.create_index("ix_price_snapshots_source_id", "price_snapshots", ["source_id"])
    op.create_table(
        "build_states",
        sa.Column("build_id", sa.String(length=64), primary_key=True),
        sa.Column("build_hash", sa.String(length=32), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("build_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_build_states_build_hash", "build_states", ["build_hash"])


def downgrade() -> None:
    op.drop_index("ix_build_states_build_hash", table_name="build_states")
    op.drop_table("build_states")
    op.drop_index("ix_price_snapshots_source_id", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_import_run_id", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_part_id", table_name="price_snapshots")
    op.drop_table("price_snapshots")
    op.drop_index("ix_digital_assets_source_id", table_name="digital_assets")
    op.drop_index("ix_digital_assets_import_run_id", table_name="digital_assets")
    op.drop_index("ix_digital_assets_part_id", table_name="digital_assets")
    op.drop_table("digital_assets")
    op.drop_index("ix_part_applications_source_id", table_name="part_applications")
    op.drop_index("ix_part_applications_import_run_id", table_name="part_applications")
    op.drop_index("ix_part_applications_vehicle_id", table_name="part_applications")
    op.drop_index("ix_part_applications_part_id", table_name="part_applications")
    op.drop_table("part_applications")
    op.drop_index("ix_parts_source_id", table_name="parts")
    op.drop_index("ix_parts_import_run_id", table_name="parts")
    op.drop_index("ix_parts_subsystem", table_name="parts")
    op.drop_table("parts")
    op.drop_index("ix_drivetrain_configs_source_id", table_name="drivetrain_configs")
    op.drop_index("ix_drivetrain_configs_import_run_id", table_name="drivetrain_configs")
    op.drop_table("drivetrain_configs")
    op.drop_index("ix_engine_configs_source_id", table_name="engine_configs")
    op.drop_index("ix_engine_configs_import_run_id", table_name="engine_configs")
    op.drop_index("ix_engine_configs_engine_family_id", table_name="engine_configs")
    op.drop_table("engine_configs")
    op.drop_index("ix_engine_families_source_id", table_name="engine_families")
    op.drop_index("ix_engine_families_import_run_id", table_name="engine_families")
    op.drop_table("engine_families")
    op.drop_index("ix_vehicles_source_id", table_name="vehicles")
    op.drop_index("ix_vehicles_import_run_id", table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index("ix_raw_source_payloads_source_record_id", table_name="raw_source_payloads")
    op.drop_index("ix_raw_source_payloads_source_id", table_name="raw_source_payloads")
    op.drop_index("ix_raw_source_payloads_payload_hash", table_name="raw_source_payloads")
    op.drop_index("ix_raw_source_payloads_import_run_id", table_name="raw_source_payloads")
    op.drop_index("ix_raw_source_payloads_entity_type", table_name="raw_source_payloads")
    op.drop_index("ix_raw_source_payloads_attempt_id", table_name="raw_source_payloads")
    op.drop_table("raw_source_payloads")
    op.drop_index("ix_catalog_import_attempts_import_run_id", table_name="catalog_import_attempts")
    op.drop_table("catalog_import_attempts")
    op.drop_index("ix_catalog_import_runs_source_id", table_name="catalog_import_runs")
    op.drop_table("catalog_import_runs")
    op.drop_table("catalog_sources")
    op.drop_index("ix_ingest_audit_dataset", table_name="ingest_audit")
    op.drop_table("ingest_audit")
    op.drop_table("recommendation_cache")
    op.drop_index("ix_nhtsa_snapshots_trim_id", table_name="nhtsa_snapshots")
    op.drop_table("nhtsa_snapshots")
    op.drop_table("trims")
