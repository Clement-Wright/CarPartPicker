from __future__ import annotations

from app.schemas import (
    BellhousingInterface,
    BoundingEnvelope,
    BrakeEnvelope,
    BuildPreset,
    CamProfileSpec,
    ChassisEnvelope,
    CoolingInterface,
    DependencyRule,
    DrivelineInterface,
    DrivetrainConfig,
    ElectricalInterface,
    EngineArchitecture,
    EngineBuildSpec,
    EngineEnvelope,
    EngineFamily,
    ExhaustSpec,
    FactProvenance,
    FabricationRequirement,
    FuelSpec,
    GeometryProfile,
    ImportBatch,
    InductionSpec,
    IngestLineage,
    MountInterface,
    PartCatalogItem,
    PartInterface,
    PerformanceDelta,
    RideHeightTravelEnvelope,
    ScenarioDefinition,
    StockConfigReference,
    StockPartReference,
    SubsystemSlotDefinition,
    TireSweepEnvelope,
    ValveTrainSpec,
    VehicleBaseConfig,
    VehiclePlatform,
    VehicleTrim,
    VisualAsset,
    WheelBarrelProfile,
)


def prov(source: str, basis: str, kind: str = "hand_curated", confidence: float = 0.82) -> FactProvenance:
    return FactProvenance(
        source=source,
        confidence=confidence,
        basis=basis,
        last_verified="2026-04-04",
        kind=kind,
    )


def lineage(
    source_system: str,
    source_record_id: str,
    import_batch_id: str,
    measurement_basis: str,
    verification_status: str = "seeded",
) -> IngestLineage:
    return IngestLineage(
        source_system=source_system,
        source_record_id=source_record_id,
        import_batch_id=import_batch_id,
        verification_status=verification_status,
        measurement_basis=measurement_basis,
    )


def visual(slot: str, kind: str, color: str = "#b9c6d2", *, scale=(1.0, 1.0, 1.0), position=(0.0, 0.0, 0.0)):
    return VisualAsset(slot=slot, kind=kind, color=color, scale=scale, position=position)


def perf(**kwargs: float | int) -> PerformanceDelta:
    return PerformanceDelta(**kwargs)


def geom(**kwargs: float | str | None) -> GeometryProfile:
    return GeometryProfile(**kwargs)


def rule(
    kind: str,
    message: str,
    *,
    subsystem: str | None = None,
    required_part_ids: list[str] | None = None,
    minimum_value: float | None = None,
    severity: str = "BLOCKER",
    basis: str = "seeded dependency rule",
) -> DependencyRule:
    return DependencyRule(
        kind=kind,
        message=message,
        subsystem=subsystem,
        required_part_ids=required_part_ids or [],
        minimum_value=minimum_value,
        severity=severity,
        provenance=prov("catalog_seed", basis),
    )


def part(
    part_id: str,
    subsystem: str,
    label: str,
    *,
    brand: str,
    notes: str,
    cost_usd: int,
    compatible_platforms: list[str],
    compatible_transmissions: list[str] | None = None,
    tags: list[str] | None = None,
    interface: PartInterface | None = None,
    geometry: GeometryProfile | None = None,
    performance: PerformanceDelta | None = None,
    capabilities: dict[str, float] | None = None,
    dependency_rules: list[DependencyRule] | None = None,
    visual_asset: VisualAsset | None = None,
    basis: str = "manufacturer fitment guide + curated demo assumptions",
) -> PartCatalogItem:
    return PartCatalogItem(
        part_id=part_id,
        subsystem=subsystem,
        label=label,
        brand=brand,
        notes=notes,
        cost_usd=cost_usd,
        compatible_platforms=compatible_platforms,
        compatible_transmissions=compatible_transmissions or ["any"],
        tags=tags or [],
        interface=interface or PartInterface(),
        geometry=geometry or GeometryProfile(),
        performance=performance or PerformanceDelta(),
        capabilities=capabilities or {},
        dependency_rules=dependency_rules or [],
        visual=visual_asset or visual(subsystem, "generic"),
        lineage=lineage("seed_catalog", part_id, "seed_parts_2026q2", "curated ACES-like seed mapping"),
        provenance=prov("catalog_seed", basis),
    )


SUBSYSTEM_ORDER = [
    "body_aero",
    "engine",
    "forced_induction",
    "intake",
    "exhaust",
    "cooling",
    "fuel_system",
    "tune",
    "transmission",
    "clutch",
    "differential",
    "suspension",
    "brakes",
    "wheels",
    "tires",
]


IMPORT_BATCHES = {
    "seed_vehicle_2026q2": ImportBatch(
        import_batch_id="seed_vehicle_2026q2",
        source_system="seed_vehicle_catalog",
        imported_at="2026-04-04T10:00:00Z",
        status="seeded",
        record_count=4,
        notes="Demo vehicle + NHTSA-backed trim snapshot layer.",
    ),
    "seed_engine_2026q2": ImportBatch(
        import_batch_id="seed_engine_2026q2",
        source_system="seed_engine_catalog",
        imported_at="2026-04-04T10:03:00Z",
        status="seeded",
        record_count=3,
        notes="Seeded engine families for the automation-style builder phase.",
    ),
    "seed_parts_2026q2": ImportBatch(
        import_batch_id="seed_parts_2026q2",
        source_system="seed_parts_catalog",
        imported_at="2026-04-04T10:05:00Z",
        status="seeded",
        record_count=30,
        notes="Curated wheels, tires, brakes, suspension, driveline, and support parts.",
    ),
}


PLATFORMS: dict[str, VehiclePlatform] = {
    "zn8": VehiclePlatform(
        platform_id="zn8",
        label="Toyota GR86 ZN8",
        manufacturer="Toyota/Subaru",
        drivetrain_layout="front_engine_rwd",
        stock_mount_family="fa24_zn8_mount",
        stock_bellhousing_family="fa24_gr86_bell",
        stock_ecu_family="toyobaru_fa24",
        stock_cooling_family="zn8_stock_cooling",
        stock_driveline_family="zn8_rwd_manual",
        wheel_bolt_pattern="5x100",
        hub_bore_mm=56.1,
        lineage=lineage("seed_vehicle_catalog", "platform_zn8", "seed_vehicle_2026q2", "VCdb-inspired platform seed"),
        provenance=prov("catalog_seed", "platform interface baseline"),
    ),
    "zd8": VehiclePlatform(
        platform_id="zd8",
        label="Subaru BRZ ZD8",
        manufacturer="Toyota/Subaru",
        drivetrain_layout="front_engine_rwd",
        stock_mount_family="fa24_zn8_mount",
        stock_bellhousing_family="fa24_gr86_bell",
        stock_ecu_family="toyobaru_fa24",
        stock_cooling_family="zd8_stock_cooling",
        stock_driveline_family="zd8_rwd_manual",
        wheel_bolt_pattern="5x100",
        hub_bore_mm=56.1,
        lineage=lineage("seed_vehicle_catalog", "platform_zd8", "seed_vehicle_2026q2", "VCdb-inspired platform seed"),
        provenance=prov("catalog_seed", "platform interface baseline"),
    ),
}


CHASSIS_ENVELOPES: dict[str, ChassisEnvelope] = {
    "zn8": ChassisEnvelope(
        platform_id="zn8",
        engine_bay=BoundingEnvelope(length_mm=850, width_mm=1020, height_mm=650),
        transmission_tunnel=BoundingEnvelope(length_mm=1500, width_mm=420, height_mm=420),
        ride_height_travel=RideHeightTravelEnvelope(envelope_id="zn8_ride", nominal_drop_mm=0.0, safe_compression_margin_mm=38.0),
        front_tire_sweep=TireSweepEnvelope(envelope_id="zn8_front_sweep", nominal_width_mm=235.0, rub_risk=0.05, full_lock_margin_mm=18.0),
        wheel_barrel_profile=WheelBarrelProfile(profile_id="zn8_stock_barrel", min_brake_diameter_in=17.0, barrel_width_in=7.5),
        stock_brake_envelope=BrakeEnvelope(envelope_id="zn8_oem_brake", minimum_wheel_diameter_in=17.0, radial_clearance_mm=8.0),
    ),
    "zd8": ChassisEnvelope(
        platform_id="zd8",
        engine_bay=BoundingEnvelope(length_mm=850, width_mm=1020, height_mm=650),
        transmission_tunnel=BoundingEnvelope(length_mm=1500, width_mm=420, height_mm=420),
        ride_height_travel=RideHeightTravelEnvelope(envelope_id="zd8_ride", nominal_drop_mm=0.0, safe_compression_margin_mm=38.0),
        front_tire_sweep=TireSweepEnvelope(envelope_id="zd8_front_sweep", nominal_width_mm=235.0, rub_risk=0.05, full_lock_margin_mm=18.0),
        wheel_barrel_profile=WheelBarrelProfile(profile_id="zd8_stock_barrel", min_brake_diameter_in=17.0, barrel_width_in=7.5),
        stock_brake_envelope=BrakeEnvelope(envelope_id="zd8_oem_brake", minimum_wheel_diameter_in=17.0, radial_clearance_mm=8.0),
    ),
}


CAM_PROFILES = {
    "cam_street": CamProfileSpec(profile_id="cam_street", label="Street", intake_bias=0.08, exhaust_bias=0.05, top_end_bias=0.06, low_end_bias=0.08),
    "cam_balanced": CamProfileSpec(profile_id="cam_balanced", label="Balanced", intake_bias=0.12, exhaust_bias=0.1, top_end_bias=0.1, low_end_bias=0.1),
    "cam_aggressive": CamProfileSpec(profile_id="cam_aggressive", label="Aggressive", intake_bias=0.18, exhaust_bias=0.16, top_end_bias=0.22, low_end_bias=0.04),
}


ENGINE_FAMILIES: dict[str, EngineFamily] = {
    "fa24d_native": EngineFamily(
        engine_family_id="fa24d_native",
        label="FA24D naturally aspirated flat-four",
        architecture=EngineArchitecture(architecture_id="arch_flat4_dohc", label="Flat-four DOHC", layout="flat4", cylinder_count=4, head_type="aluminum DOHC", valves_per_cylinder=4, valvetrain="dohc"),
        base_displacement_l=2.4,
        base_weight_lb=305,
        base_peak_hp=228,
        base_peak_torque_lbft=184,
        base_redline_rpm=7500,
        stock_bore_mm=94.0,
        stock_stroke_mm=86.0,
        compression_ratio=12.5,
        mount_interface=MountInterface(mount_family="fa24_zn8_mount"),
        bellhousing_interface=BellhousingInterface(bellhousing_family="fa24_gr86_bell"),
        cooling_interface=CoolingInterface(cooling_family="zn8_stock_cooling", cooling_load_index=0.48),
        driveline_interface=DrivelineInterface(drivetrain_family="zn8_rwd_manual", axle_family="zn8_axle"),
        electrical_interface=ElectricalInterface(ecu_family="toyobaru_fa24", harness_family="zn8_stock_harness"),
        envelope=EngineEnvelope(length_mm=640, width_mm=780, height_mm=520),
        tags=["stock", "na", "builder"],
        lineage=lineage("seed_engine_catalog", "fa24d_native", "seed_engine_2026q2", "curated engine family baseline"),
        provenance=prov("catalog_seed", "seeded stock engine family baseline"),
    ),
    "g16e_turbo_swap": EngineFamily(
        engine_family_id="g16e_turbo_swap",
        label="G16E-GTS turbo three-cylinder swap",
        architecture=EngineArchitecture(architecture_id="arch_i3_turbo", label="Inline-three turbo", layout="inline4", cylinder_count=3, head_type="aluminum turbo head", valves_per_cylinder=4, valvetrain="dohc"),
        base_displacement_l=1.6,
        base_weight_lb=286,
        base_peak_hp=300,
        base_peak_torque_lbft=273,
        base_redline_rpm=7600,
        stock_bore_mm=87.5,
        stock_stroke_mm=89.7,
        compression_ratio=10.5,
        mount_interface=MountInterface(mount_family="g16_swap_mount"),
        bellhousing_interface=BellhousingInterface(bellhousing_family="g16_adapter_bell"),
        cooling_interface=CoolingInterface(cooling_family="swap_frontmount", cooling_load_index=0.74),
        driveline_interface=DrivelineInterface(drivetrain_family="swap_rwd_adapter", axle_family="zn8_axle"),
        electrical_interface=ElectricalInterface(ecu_family="g16_standalone", harness_family="swap_standalone"),
        envelope=EngineEnvelope(length_mm=610, width_mm=620, height_mm=610),
        fabrication_requirements=[FabricationRequirement(fabrication_id="g16_mounts", label="Swap mounts required", detail="Custom mounts and a standalone ECU base map are required for the G16 swap.", severity="moderate")],
        required_supporting_part_ids=["cooling_track_pack", "fuel_system_upgrade", "clutch_stage2"],
        required_visual_slots=["engine_bay", "intercooler"],
        tags=["swap", "turbo", "lightweight"],
        lineage=lineage("seed_engine_catalog", "g16e_turbo_swap", "seed_engine_2026q2", "curated swap family baseline"),
        provenance=prov("catalog_seed", "seeded turbo swap family baseline"),
    ),
    "2gr_v6_swap": EngineFamily(
        engine_family_id="2gr_v6_swap",
        label="2GR-FKS V6 swap",
        architecture=EngineArchitecture(architecture_id="arch_v6_na", label="V6 DOHC", layout="v6", cylinder_count=6, head_type="aluminum DOHC", valves_per_cylinder=4, valvetrain="dohc"),
        base_displacement_l=3.5,
        base_weight_lb=378,
        base_peak_hp=315,
        base_peak_torque_lbft=280,
        base_redline_rpm=7100,
        stock_bore_mm=94.0,
        stock_stroke_mm=83.0,
        compression_ratio=11.8,
        mount_interface=MountInterface(mount_family="2gr_swap_mount"),
        bellhousing_interface=BellhousingInterface(bellhousing_family="2gr_adapter_bell"),
        cooling_interface=CoolingInterface(cooling_family="swap_large_radiator", cooling_load_index=0.66),
        driveline_interface=DrivelineInterface(drivetrain_family="swap_rwd_adapter", axle_family="zn8_axle"),
        electrical_interface=ElectricalInterface(ecu_family="2gr_standalone", harness_family="swap_standalone"),
        envelope=EngineEnvelope(length_mm=710, width_mm=760, height_mm=640),
        fabrication_requirements=[FabricationRequirement(fabrication_id="2gr_headers", label="Header and crossmember work", detail="The V6 swap needs custom headers and crossmember clearance work.", severity="major")],
        required_supporting_part_ids=["cooling_track_pack", "clutch_stage2", "transmission_6mt_reinforced"],
        tags=["swap", "na", "torque"],
        lineage=lineage("seed_engine_catalog", "2gr_v6_swap", "seed_engine_2026q2", "curated swap family baseline"),
        provenance=prov("catalog_seed", "seeded V6 swap family baseline"),
    ),
}


ENGINE_CONFIGS: dict[str, EngineBuildSpec] = {
    "engine_cfg_fa24_stock": EngineBuildSpec(
        config_id="engine_cfg_fa24_stock",
        engine_family_id="fa24d_native",
        label="FA24 stock",
        cylinder_count=4,
        layout="flat4",
        bore_mm=94.0,
        stroke_mm=86.0,
        compression_ratio=12.5,
        valve_train=ValveTrainSpec(label="Factory DOHC", head_flow_stage="stock", valves_per_cylinder=4, variable_valve_timing=True),
        cam_profile=CAM_PROFILES["cam_street"],
        induction=InductionSpec(type="na", boost_psi=0.0, intercooler_required=False),
        fuel=FuelSpec(fuel_type="93_octane", injector_scale="stock", pump_scale="stock"),
        exhaust=ExhaustSpec(exhaust_style="stock", flow_bias=0.0, noise_bias=0.0),
        tune_bias="comfort",
        rev_limit_rpm=7500,
        notes=["Baseline stock engine spec for ZN8/ZD8."],
    ),
    "engine_cfg_g16_swap": EngineBuildSpec(
        config_id="engine_cfg_g16_swap",
        engine_family_id="g16e_turbo_swap",
        label="G16 turbo swap",
        cylinder_count=3,
        layout="inline3",
        bore_mm=87.5,
        stroke_mm=89.7,
        compression_ratio=10.5,
        valve_train=ValveTrainSpec(label="Turbo DOHC", head_flow_stage="street", valves_per_cylinder=4, variable_valve_timing=True),
        cam_profile=CAM_PROFILES["cam_balanced"],
        induction=InductionSpec(type="turbo", boost_psi=18.0, intercooler_required=True),
        fuel=FuelSpec(fuel_type="93_octane", injector_scale="upgrade", pump_scale="upgrade"),
        exhaust=ExhaustSpec(exhaust_style="turbo_back", flow_bias=0.2, noise_bias=0.14),
        tune_bias="balanced",
        rev_limit_rpm=7600,
        notes=["Seed swap spec with standalone ECU and front-mount intercooler."],
    ),
    "engine_cfg_2gr_swap": EngineBuildSpec(
        config_id="engine_cfg_2gr_swap",
        engine_family_id="2gr_v6_swap",
        label="2GR V6 swap",
        cylinder_count=6,
        layout="v6",
        bore_mm=94.0,
        stroke_mm=83.0,
        compression_ratio=11.8,
        valve_train=ValveTrainSpec(label="V6 DOHC", head_flow_stage="street", valves_per_cylinder=4, variable_valve_timing=True),
        cam_profile=CAM_PROFILES["cam_balanced"],
        induction=InductionSpec(type="na", boost_psi=0.0, intercooler_required=False),
        fuel=FuelSpec(fuel_type="93_octane", injector_scale="upgrade", pump_scale="upgrade"),
        exhaust=ExhaustSpec(exhaust_style="equal_length", flow_bias=0.16, noise_bias=0.1),
        tune_bias="balanced",
        rev_limit_rpm=7100,
        notes=["High-torque swap spec with custom headers and adapter driveline."],
    ),
}


DRIVETRAIN_CONFIGS: dict[str, DrivetrainConfig] = {
    "drivetrain_manual_stock": DrivetrainConfig(config_id="drivetrain_manual_stock", label="6MT stock gearing", transmission_mode="manual", gear_ratios=[3.626, 2.188, 1.541, 1.213, 1.0, 0.767], final_drive_ratio=4.1, driveline_loss_factor=0.13, differential_bias="street_lsd", shift_latency_ms=180),
    "drivetrain_manual_close": DrivetrainConfig(config_id="drivetrain_manual_close", label="Close-ratio manual", transmission_mode="manual", gear_ratios=[3.4, 2.25, 1.68, 1.3, 1.08, 0.86], final_drive_ratio=4.3, driveline_loss_factor=0.125, differential_bias="track_lsd", shift_latency_ms=165),
    "drivetrain_auto_stock": DrivetrainConfig(config_id="drivetrain_auto_stock", label="6AT stock gearing", transmission_mode="automatic", gear_ratios=[3.538, 2.06, 1.404, 1.0, 0.713, 0.582], final_drive_ratio=4.1, driveline_loss_factor=0.17, differential_bias="street_lsd", shift_latency_ms=240),
}


SCENARIO_DEFINITIONS: dict[str, ScenarioDefinition] = {
    "daily": ScenarioDefinition(
        scenario_name="daily",
        label="Daily",
        description="Bias toward comfort, low drama, and dependable street usability.",
        weights={"comfort": 0.28, "braking": 0.18, "grip": 0.16, "thermal": 0.12, "stress": -0.14, "cost": -0.12},
        gates=["No unresolved blocker findings", "Street-legal bias stays enabled by default"],
        penalties=["Harsh ride", "High thermal load", "Fabrication-required packages"],
        assumptions=["Dry street surface", "Single-driver load", "Commute-speed braking cycles"],
    ),
    "winter": ScenarioDefinition(
        scenario_name="winter",
        label="Winter",
        description="Bias toward cold-weather traction, compliance, and clearance margin.",
        weights={"grip": 0.3, "comfort": 0.2, "ride_height": 0.14, "braking": 0.12, "stress": -0.08, "thermal": 0.06},
        gates=["Winter-oriented tires strongly preferred", "Large ride-height drops are penalized"],
        penalties=["Track tire compounds", "Aggressive ride-height drop", "Low compliance"],
        assumptions=["Cold surface", "Occasional snow", "Cargo for weekend gear"],
    ),
    "canyon": ScenarioDefinition(
        scenario_name="canyon",
        label="Canyon",
        description="Bias toward response, brake repeatability, and composure on rough roads.",
        weights={"grip": 0.26, "braking": 0.22, "comfort": 0.12, "power": 0.16, "stress": -0.08, "thermal": 0.12},
        gates=["No blocker findings", "Brake and tire package should remain balanced"],
        penalties=["Overheated setup", "Mismatched brake and tire capability"],
        assumptions=["Mountain road pace", "Repeated mid-speed braking", "Street alignment"],
    ),
    "track": ScenarioDefinition(
        scenario_name="track",
        label="Track",
        description="Bias toward power delivery, brake endurance, cooling margin, and sustained grip.",
        weights={"power": 0.24, "grip": 0.22, "braking": 0.2, "thermal": 0.18, "stress": -0.08, "comfort": -0.04},
        gates=["No blocker findings", "Thermal headroom should stay positive"],
        penalties=["Weak cooling", "Street-comfort constraints", "Unresolved driveline overload"],
        assumptions=["Hot lap cycle", "High brake energy", "Performance alignment"],
    ),
}


TRIMS: dict[str, VehicleTrim] = {
    "gr86_2022_base": VehicleTrim(
        trim_id="gr86_2022_base",
        platform="zn8",
        year=2022,
        make="Toyota",
        model="GR86",
        trim="Base",
        drivetrain="RWD",
        transmission="manual",
        body_style="coupe",
        stock_wheel_diameter=17,
        stock_tire="215/45R17",
        stock_hp=228,
        stock_torque_lbft=184,
        stock_weight_lb=2811,
        redline_rpm=7500,
        stock_zero_to_sixty_s=6.1,
        stock_top_speed_mph=140,
        stock_braking_distance_ft=114,
        stock_lateral_grip_g=0.93,
        stock_thermal_headroom=0.68,
        stock_comfort_index=0.78,
        stock_drag_index=0.62,
        stock_downforce_index=0.18,
        driveline_limit_lbft=255,
        gear_ratios=[3.626, 2.188, 1.541, 1.213, 1.0, 0.767],
        final_drive_ratio=4.1,
        safety_index=0.88,
        recall_burden=0.22,
        complaint_burden=0.34,
        recall_summary="Demo NHTSA snapshot: low recall burden in the local seed.",
        complaint_summary="Demo complaint profile: moderate complaint volume concentrated around daily-use annoyances.",
        utility_note="Low cargo, strong daily livability for a compact coupe.",
        mod_potential=0.96,
        provenance=prov("NHTSA seed + curated vehicle baseline", "seeded trim profile", "nhtsa", 0.9),
    ),
    "gr86_2023_premium": VehicleTrim(
        trim_id="gr86_2023_premium",
        platform="zn8",
        year=2023,
        make="Toyota",
        model="GR86",
        trim="Premium",
        drivetrain="RWD",
        transmission="automatic",
        body_style="coupe",
        stock_wheel_diameter=18,
        stock_tire="215/40R18",
        stock_hp=228,
        stock_torque_lbft=184,
        stock_weight_lb=2862,
        redline_rpm=7400,
        stock_zero_to_sixty_s=6.6,
        stock_top_speed_mph=138,
        stock_braking_distance_ft=113,
        stock_lateral_grip_g=0.94,
        stock_thermal_headroom=0.66,
        stock_comfort_index=0.8,
        stock_drag_index=0.62,
        stock_downforce_index=0.18,
        driveline_limit_lbft=245,
        gear_ratios=[3.538, 2.06, 1.404, 1.0, 0.713, 0.582],
        final_drive_ratio=4.1,
        safety_index=0.88,
        recall_burden=0.24,
        complaint_burden=0.33,
        recall_summary="Demo NHTSA snapshot: low recall burden in the local seed.",
        complaint_summary="Demo complaint profile: moderate complaint volume concentrated around brake feel and infotainment.",
        utility_note="18-inch stock setup makes aggressive brake packages easier to support.",
        mod_potential=0.97,
        provenance=prov("NHTSA seed + curated vehicle baseline", "seeded trim profile", "nhtsa", 0.9),
    ),
    "brz_2023_premium": VehicleTrim(
        trim_id="brz_2023_premium",
        platform="zd8",
        year=2023,
        make="Subaru",
        model="BRZ",
        trim="Premium",
        drivetrain="RWD",
        transmission="manual",
        body_style="coupe",
        stock_wheel_diameter=17,
        stock_tire="215/45R17",
        stock_hp=228,
        stock_torque_lbft=184,
        stock_weight_lb=2815,
        redline_rpm=7500,
        stock_zero_to_sixty_s=6.0,
        stock_top_speed_mph=140,
        stock_braking_distance_ft=113,
        stock_lateral_grip_g=0.94,
        stock_thermal_headroom=0.69,
        stock_comfort_index=0.79,
        stock_drag_index=0.61,
        stock_downforce_index=0.18,
        driveline_limit_lbft=255,
        gear_ratios=[3.626, 2.188, 1.541, 1.213, 1.0, 0.767],
        final_drive_ratio=4.1,
        safety_index=0.89,
        recall_burden=0.2,
        complaint_burden=0.29,
        recall_summary="Demo NHTSA snapshot: low recall burden in the local seed.",
        complaint_summary="Demo complaint profile: slightly lighter complaint volume in the local seed.",
        utility_note="Strong base for winter and daily packages on a compliant 17-inch setup.",
        mod_potential=0.94,
        provenance=prov("NHTSA seed + curated vehicle baseline", "seeded trim profile", "nhtsa", 0.9),
    ),
    "brz_2024_limited": VehicleTrim(
        trim_id="brz_2024_limited",
        platform="zd8",
        year=2024,
        make="Subaru",
        model="BRZ",
        trim="Limited",
        drivetrain="RWD",
        transmission="automatic",
        body_style="coupe",
        stock_wheel_diameter=18,
        stock_tire="215/40R18",
        stock_hp=228,
        stock_torque_lbft=184,
        stock_weight_lb=2867,
        redline_rpm=7400,
        stock_zero_to_sixty_s=6.5,
        stock_top_speed_mph=138,
        stock_braking_distance_ft=112,
        stock_lateral_grip_g=0.95,
        stock_thermal_headroom=0.66,
        stock_comfort_index=0.8,
        stock_drag_index=0.61,
        stock_downforce_index=0.18,
        driveline_limit_lbft=245,
        gear_ratios=[3.538, 2.06, 1.404, 1.0, 0.713, 0.582],
        final_drive_ratio=4.1,
        safety_index=0.89,
        recall_burden=0.2,
        complaint_burden=0.29,
        recall_summary="Demo NHTSA snapshot: low recall burden in the local seed.",
        complaint_summary="Demo complaint profile: stable owner complaint volume in the local seed.",
        utility_note="18-inch stock setup supports wider street-performance packages.",
        mod_potential=0.95,
        provenance=prov("NHTSA seed + curated vehicle baseline", "seeded trim profile", "nhtsa", 0.9),
    ),
}


PARTS: dict[str, PartCatalogItem] = {
    item.part_id: item
    for item in [
        part("body_stock", "body_aero", "Stock body and aero", brand="Toyota/Subaru", notes="Factory shell, bumper, and hood state.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["street", "stock"], visual_asset=visual("body", "shell", "#d7dde3", scale=(1.5, 0.35, 3.3))),
        part("body_vented_track", "body_aero", "Vented hood and track aero", brand="Catapult Works", notes="Adds splitter, vented hood clearance, and rear wing.", cost_usd=2850, compatible_platforms=["zn8", "zd8"], tags=["track", "aero"], geometry=geom(hood_clearance_gain_mm=16.0), performance=perf(weight_delta_lb=12, drag_delta=0.08, downforce_delta=0.22, comfort_delta=-0.06), visual_asset=visual("body", "track_aero", "#ff7b31", scale=(1.58, 0.42, 3.38))),
        part("engine_fa24_stock", "engine", "FA24 stock long block", brand="Toyota/Subaru", notes="Stock FA24 naturally aspirated flat-four.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock", "na"], capabilities={"aspiration_na": 1.0}, visual_asset=visual("engine", "flat4", "#72808b", scale=(0.65, 0.42, 0.95), position=(0.0, 0.18, 0.1))),
        part("engine_balanced_fa24", "engine", "Balanced FA24 long block", brand="Built By Design", notes="Blueprinted stock long block with modest rev and smoothness gains.", cost_usd=4200, compatible_platforms=["zn8", "zd8"], tags=["na", "responsive"], performance=perf(hp_delta=12, torque_delta=6, redline_delta_rpm=300, weight_delta_lb=8, comfort_delta=-0.01), visual_asset=visual("engine", "built_flat4", "#8a9ba8", scale=(0.68, 0.44, 0.98), position=(0.0, 0.18, 0.1))),
        part("fi_na_stock", "forced_induction", "Naturally aspirated", brand="Toyota/Subaru", notes="No forced induction installed.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["na", "stock"], capabilities={"aspiration_na": 1.0}, visual_asset=visual("forced_induction", "none")),
        part("fi_turbo_street", "forced_induction", "Street turbo system", brand="Boost Circuit", notes="Single turbo kit targeting a broad street powerband.", cost_usd=5600, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["manual"], tags=["turbo", "street_power"], geometry=geom(hood_clearance_needed_mm=8.0, thermal_load=0.18), performance=perf(hp_delta=118, torque_delta=112, weight_delta_lb=42, driveline_stress_delta=0.24, thermal_delta=-0.12), dependency_rules=[rule("requires_part", "Turbo power needs upgraded fuel delivery.", subsystem="fuel_system", required_part_ids=["fuel_system_upgrade"], basis="turbo install dependency"), rule("requires_part", "Turbo power needs a dedicated calibration.", subsystem="tune", required_part_ids=["tune_turbo_pro"], basis="turbo calibration dependency"), rule("requires_part", "Turbo heat load needs upgraded cooling.", subsystem="cooling", required_part_ids=["cooling_track_pack"], basis="turbo cooling dependency"), rule("requires_part", "Turbo torque exceeds the stock clutch margin.", subsystem="clutch", required_part_ids=["clutch_stage2"], basis="turbo clutch dependency"), rule("geometry_gate", "Turbo compressor cover needs extra hood clearance.", subsystem="body_aero", minimum_value=8.0, severity="WARNING", basis="curated hood clearance envelope")], visual_asset=visual("forced_induction", "turbo", "#ff7b31", scale=(0.36, 0.34, 0.36), position=(0.26, 0.22, 0.08))),
        part("intake_stock", "intake", "Factory intake", brand="Toyota/Subaru", notes="Factory intake tract.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], visual_asset=visual("intake", "stock_intake", "#8b95a1", scale=(0.28, 0.18, 0.46), position=(-0.28, 0.2, 0.02))),
        part("intake_cold_air", "intake", "Cold-air intake", brand="AeroFlow", notes="Improves induction sound and top-end breathing.", cost_usd=460, compatible_platforms=["zn8", "zd8"], tags=["na", "street"], performance=perf(hp_delta=6, torque_delta=4, comfort_delta=-0.01), visual_asset=visual("intake", "cold_air", "#7ce7c6", scale=(0.3, 0.18, 0.48), position=(-0.28, 0.21, 0.02))),
        part("exhaust_stock", "exhaust", "Factory exhaust", brand="Toyota/Subaru", notes="Factory exhaust routing and mufflers.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], visual_asset=visual("exhaust", "stock_exhaust", "#8b95a1", scale=(0.28, 0.16, 0.8), position=(0.0, -0.12, -0.68))),
        part("exhaust_catback", "exhaust", "Performance cat-back", brand="Titan Arc", notes="Improves flow and adds modest weight savings.", cost_usd=1250, compatible_platforms=["zn8", "zd8"], tags=["street", "sound"], performance=perf(hp_delta=8, torque_delta=5, weight_delta_lb=-14, comfort_delta=-0.03), visual_asset=visual("exhaust", "catback", "#d2d9df", scale=(0.3, 0.16, 0.84), position=(0.0, -0.12, -0.68))),
        part("cooling_stock", "cooling", "Factory cooling package", brand="Toyota/Subaru", notes="Stock radiator and oil temperature management.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], visual_asset=visual("cooling", "stock_cooling", "#6d7a85", scale=(0.58, 0.18, 0.1), position=(0.0, 0.1, 0.76))),
        part("cooling_track_pack", "cooling", "Track cooling pack", brand="Thermal Reserve", notes="Radiator, oil cooler, and ducting upgrade.", cost_usd=1380, compatible_platforms=["zn8", "zd8"], tags=["track", "turbo_support"], performance=perf(weight_delta_lb=11, cooling_delta=0.32, thermal_delta=0.22), visual_asset=visual("cooling", "track_cooling", "#7ce7c6", scale=(0.62, 0.22, 0.12), position=(0.0, 0.1, 0.76))),
        part("fuel_stock", "fuel_system", "Factory fuel system", brand="Toyota/Subaru", notes="Stock injectors and pump.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], visual_asset=visual("fuel_system", "stock_fuel", "#78848f", scale=(0.22, 0.18, 0.22), position=(-0.06, 0.22, 0.02))),
        part("fuel_system_upgrade", "fuel_system", "Fueling upgrade", brand="Injector Labs", notes="Injectors and pump sized for turbo torque targets.", cost_usd=980, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["manual"], tags=["turbo_support"], performance=perf(weight_delta_lb=4, driveline_stress_delta=0.02), visual_asset=visual("fuel_system", "upgraded_fuel", "#ffb36b", scale=(0.24, 0.19, 0.24), position=(-0.06, 0.22, 0.02))),
        part("tune_stock", "tune", "Factory calibration", brand="Toyota/Subaru", notes="Stock ECU behavior.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], visual_asset=visual("tune", "ecu_stock", "#6d7a85", scale=(0.14, 0.08, 0.18), position=(0.16, 0.19, -0.04))),
        part("tune_stage1", "tune", "Stage 1 street tune", brand="Circuit Logic", notes="NA tune with sharper throttle and modest gains.", cost_usd=600, compatible_platforms=["zn8", "zd8"], tags=["na", "street"], performance=perf(hp_delta=10, torque_delta=7, redline_delta_rpm=100, comfort_delta=-0.02), visual_asset=visual("tune", "ecu_tuned", "#ff7b31", scale=(0.14, 0.08, 0.18), position=(0.16, 0.19, -0.04))),
        part("tune_turbo_pro", "tune", "Turbo pro calibration", brand="Circuit Logic", notes="Turbo-specific calibration with boost and fuel control.", cost_usd=950, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["manual"], tags=["turbo", "track"], performance=perf(hp_delta=86, torque_delta=68, redline_delta_rpm=200, thermal_delta=-0.04), dependency_rules=[rule("requires_part", "Turbo calibration only applies with the turbo hardware installed.", subsystem="forced_induction", required_part_ids=["fi_turbo_street"], severity="UNKNOWN", basis="calibration dependency")], visual_asset=visual("tune", "ecu_turbo", "#ff7b31", scale=(0.15, 0.08, 0.18), position=(0.16, 0.19, -0.04))),
        part("transmission_6mt_stock", "transmission", "Factory 6-speed manual", brand="Toyota/Subaru", notes="Stock 6MT gearbox.", cost_usd=0, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["manual"], tags=["stock"], capabilities={"torque_capacity": 255}, visual_asset=visual("transmission", "manual_box", "#9aa7b1", scale=(0.48, 0.24, 0.64), position=(0.0, -0.02, -0.14))),
        part("transmission_6mt_reinforced", "transmission", "Reinforced 6-speed manual", brand="Driveline Lab", notes="Upgraded synchros and torque capacity for boosted builds.", cost_usd=4200, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["manual"], tags=["track", "turbo_support"], capabilities={"torque_capacity": 420}, performance=perf(weight_delta_lb=18, driveline_stress_delta=-0.12), visual_asset=visual("transmission", "reinforced_box", "#ffb36b", scale=(0.5, 0.25, 0.67), position=(0.0, -0.02, -0.14))),
        part("transmission_6at_stock", "transmission", "Factory 6-speed automatic", brand="Toyota/Subaru", notes="Stock 6AT with factory converter calibration.", cost_usd=0, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["automatic"], tags=["stock"], capabilities={"torque_capacity": 245}, visual_asset=visual("transmission", "auto_box", "#93a0aa", scale=(0.52, 0.25, 0.66), position=(0.0, -0.02, -0.14))),
        part("clutch_stock", "clutch", "Factory clutch", brand="Toyota/Subaru", notes="Stock clutch capacity for NA torque levels.", cost_usd=0, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["manual"], tags=["stock"], capabilities={"torque_capacity": 255}, visual_asset=visual("clutch", "oem_clutch", "#c9d1d8", scale=(0.18, 0.18, 0.08), position=(0.0, 0.03, -0.03))),
        part("clutch_stage2", "clutch", "Stage 2 clutch", brand="Driveline Lab", notes="Higher clamp load for boosted torque.", cost_usd=1120, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["manual"], tags=["turbo_support"], capabilities={"torque_capacity": 420}, performance=perf(comfort_delta=-0.06, driveline_stress_delta=-0.05), visual_asset=visual("clutch", "stage2_clutch", "#ffb36b", scale=(0.18, 0.18, 0.08), position=(0.0, 0.03, -0.03))),
        part("clutch_not_applicable", "clutch", "Automatic driveline", brand="Toyota/Subaru", notes="Placeholder slot for automatic cars.", cost_usd=0, compatible_platforms=["zn8", "zd8"], compatible_transmissions=["automatic"], tags=["automatic"], visual_asset=visual("clutch", "automatic_placeholder", "#5d6871")),
        part("diff_stock", "differential", "Factory limited-slip differential", brand="Toyota/Subaru", notes="Stock final drive and LSD behavior.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], capabilities={"torque_capacity": 275}, visual_asset=visual("differential", "stock_diff", "#7d8a95", scale=(0.34, 0.2, 0.28), position=(0.0, -0.14, -1.0))),
        part("diff_track_lsd", "differential", "Track-biased differential", brand="Driveline Lab", notes="More aggressive lockup for corner exit traction.", cost_usd=1480, compatible_platforms=["zn8", "zd8"], tags=["track", "canyon"], capabilities={"torque_capacity": 400}, performance=perf(grip_delta=0.07, comfort_delta=-0.03, driveline_stress_delta=-0.04), visual_asset=visual("differential", "track_diff", "#ffb36b", scale=(0.35, 0.2, 0.29), position=(0.0, -0.14, -1.0))),
        part("suspension_stock", "suspension", "Factory suspension", brand="Toyota/Subaru", notes="Factory springs and dampers.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], visual_asset=visual("suspension", "stock_suspension", "#8f9ca7", scale=(1.0, 1.0, 1.0))),
        part("suspension_daily", "suspension", "Daily coilovers", brand="KW-inspired", notes="Moderate drop with street damping focus.", cost_usd=1850, compatible_platforms=["zn8", "zd8"], tags=["daily", "canyon"], geometry=geom(ride_height_drop_mm=18.0, tire_rub_risk=0.05), performance=perf(grip_delta=0.05, comfort_delta=-0.03), visual_asset=visual("suspension", "daily_coilovers", "#7ce7c6")),
        part("suspension_track", "suspension", "Track coilovers", brand="KW-inspired", notes="Higher spring rate and aggressive ride-height reduction.", cost_usd=2550, compatible_platforms=["zn8", "zd8"], tags=["track"], geometry=geom(ride_height_drop_mm=36.0, tire_rub_risk=0.22), performance=perf(grip_delta=0.11, comfort_delta=-0.13, braking_delta=0.03), visual_asset=visual("suspension", "track_coilovers", "#ff7b31")),
        part("brakes_stock_17", "brakes", "Stock 17-inch brake package", brand="Toyota/Subaru", notes="Factory base brake package.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], geometry=geom(brake_min_wheel_in=17.0, brake_envelope="oem_17"), performance=perf(braking_delta=0.0), visual_asset=visual("brakes", "stock_brakes", "#d96e34", scale=(0.7, 0.7, 0.7))),
        part("brakes_stock_18", "brakes", "Stock 18-inch brake package", brand="Toyota/Subaru", notes="Factory premium brake package.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], geometry=geom(brake_min_wheel_in=18.0, brake_envelope="oem_18"), performance=perf(braking_delta=0.03), visual_asset=visual("brakes", "premium_brakes", "#d96e34", scale=(0.78, 0.78, 0.78))),
        part("brakes_daily_bb", "brakes", "Daily brake refresh", brand="Wilwood-style", notes="Pad, line, and rotor-focused refresh without large clearance demands.", cost_usd=1180, compatible_platforms=["zn8", "zd8"], tags=["daily", "braking"], geometry=geom(brake_min_wheel_in=17.0, brake_envelope="refresh_17"), performance=perf(braking_delta=0.09), visual_asset=visual("brakes", "daily_brakes", "#ff7b31", scale=(0.76, 0.76, 0.76))),
        part("brakes_big_18", "brakes", "18-inch big brake kit", brand="Brembo-style", notes="Large multi-piston package that needs 18-inch wheel clearance.", cost_usd=3280, compatible_platforms=["zn8", "zd8"], tags=["track", "braking"], geometry=geom(brake_min_wheel_in=18.0, brake_envelope="bbk_18"), performance=perf(braking_delta=0.19, weight_delta_lb=9), dependency_rules=[rule("geometry_gate", "This big brake package needs at least 18-inch wheel clearance.", subsystem="wheels", minimum_value=18.0, basis="wheel barrel clearance rule")], visual_asset=visual("brakes", "bbk", "#ff7b31", scale=(0.9, 0.9, 0.9))),
        part("wheels_stock_17", "wheels", "Factory 17-inch wheel", brand="Toyota/Subaru", notes="Factory 17-inch wheel with stock barrel profile.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], interface=PartInterface(wheel_bolt_pattern="5x100", hub_bore_mm=56.1), geometry=geom(wheel_diameter_in=17.0, wheel_width_in=7.5, barrel_profile="stock_17"), visual_asset=visual("wheels", "wheel17", "#d0d6dc", scale=(0.88, 0.88, 0.88))),
        part("wheels_stock_18", "wheels", "Factory 18-inch wheel", brand="Toyota/Subaru", notes="Factory 18-inch wheel with premium trim barrel profile.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock"], interface=PartInterface(wheel_bolt_pattern="5x100", hub_bore_mm=56.1), geometry=geom(wheel_diameter_in=18.0, wheel_width_in=7.5, barrel_profile="stock_18"), visual_asset=visual("wheels", "wheel18", "#d0d6dc", scale=(0.94, 0.94, 0.94))),
        part("wheels_winter_17", "wheels", "17-inch winter wheel", brand="Enkei-style", notes="Simple 17-inch wheel for winter tire package.", cost_usd=980, compatible_platforms=["zn8", "zd8"], tags=["winter"], interface=PartInterface(wheel_bolt_pattern="5x100", hub_bore_mm=56.1), geometry=geom(wheel_diameter_in=17.0, wheel_width_in=7.5, barrel_profile="winter_17"), performance=perf(weight_delta_lb=3), visual_asset=visual("wheels", "winter17", "#bcc8d4", scale=(0.88, 0.88, 0.88))),
        part("wheels_track_18", "wheels", "18x9 track wheel", brand="Rays-style", notes="18-inch wheel with wide barrel for BBK clearance and tire support.", cost_usd=1880, compatible_platforms=["zn8", "zd8"], tags=["track", "wide"], interface=PartInterface(wheel_bolt_pattern="5x100", hub_bore_mm=56.1), geometry=geom(wheel_diameter_in=18.0, wheel_width_in=9.0, barrel_profile="track_18"), performance=perf(grip_delta=0.03, comfort_delta=-0.02), visual_asset=visual("wheels", "track18", "#c7d1d9", scale=(0.97, 0.97, 0.97))),
        part("tires_stock_17", "tires", "Factory Michelin Primacy 17", brand="Michelin", notes="Stock 17-inch all-season-biased tire.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock", "street"], geometry=geom(tire_width_mm=215.0), performance=perf(grip_delta=0.0, comfort_delta=0.0), visual_asset=visual("tires", "stock_tire17", "#202327", scale=(0.94, 0.94, 0.94))),
        part("tires_stock_18", "tires", "Factory Michelin 18", brand="Michelin", notes="Stock 18-inch summer-biased tire.", cost_usd=0, compatible_platforms=["zn8", "zd8"], tags=["stock", "street"], geometry=geom(tire_width_mm=215.0), performance=perf(grip_delta=0.02, comfort_delta=-0.01), visual_asset=visual("tires", "stock_tire18", "#202327", scale=(0.98, 0.98, 0.98))),
        part("tires_winter_17", "tires", "17-inch winter tire", brand="Bridgestone", notes="Cold-weather tire with improved compliance and snow traction.", cost_usd=860, compatible_platforms=["zn8", "zd8"], tags=["winter", "street"], geometry=geom(tire_width_mm=215.0), performance=perf(grip_delta=0.05, braking_delta=0.04, comfort_delta=0.04), visual_asset=visual("tires", "winter_tire17", "#1d2126", scale=(0.94, 0.94, 0.94))),
        part("tires_canyon_18", "tires", "18-inch max-performance tire", brand="Michelin", notes="Streetable tire with strong canyon and track bias.", cost_usd=1220, compatible_platforms=["zn8", "zd8"], tags=["canyon", "track"], geometry=geom(tire_width_mm=245.0, tire_rub_risk=0.12), performance=perf(grip_delta=0.12, braking_delta=0.05, comfort_delta=-0.03), visual_asset=visual("tires", "canyon_tire18", "#181b1f", scale=(0.99, 0.99, 0.99))),
        part("tires_track_18", "tires", "18-inch track tire", brand="Yokohama", notes="High-grip track-biased compound.", cost_usd=1460, compatible_platforms=["zn8", "zd8"], tags=["track"], geometry=geom(tire_width_mm=255.0, tire_rub_risk=0.2), performance=perf(grip_delta=0.17, braking_delta=0.08, comfort_delta=-0.08), dependency_rules=[rule("blocks_scenario", "Track tire compound is a poor winter fit.", subsystem="tires", severity="SCENARIO_PENALTY", basis="compound temperature window")], visual_asset=visual("tires", "track_tire18", "#15181c", scale=(1.02, 1.02, 1.02))),
    ]
}


BASE_CONFIGS: dict[str, VehicleBaseConfig] = {}
DEFAULT_ENGINE_BY_TRIM: dict[str, str] = {}
DEFAULT_DRIVETRAIN_BY_TRIM: dict[str, str] = {}
for trim_id, trim in TRIMS.items():
    stock_trans = "transmission_6mt_stock" if trim.transmission == "manual" else "transmission_6at_stock"
    stock_clutch = "clutch_stock" if trim.transmission == "manual" else "clutch_not_applicable"
    stock_brakes = "brakes_stock_17" if trim.stock_wheel_diameter == 17 else "brakes_stock_18"
    stock_wheels = "wheels_stock_17" if trim.stock_wheel_diameter == 17 else "wheels_stock_18"
    stock_tires = "tires_stock_17" if trim.stock_wheel_diameter == 17 else "tires_stock_18"
    default_engine = "engine_cfg_fa24_stock"
    default_drivetrain = "drivetrain_manual_stock" if trim.transmission == "manual" else "drivetrain_auto_stock"
    DEFAULT_ENGINE_BY_TRIM[trim_id] = default_engine
    DEFAULT_DRIVETRAIN_BY_TRIM[trim_id] = default_drivetrain
    slot_map = {
        "body_aero": "body_stock",
        "forced_induction": "fi_na_stock",
        "intake": "intake_stock",
        "exhaust": "exhaust_stock",
        "cooling": "cooling_stock",
        "fuel_system": "fuel_stock",
        "tune": "tune_stock",
        "transmission": stock_trans,
        "clutch": stock_clutch,
        "differential": "diff_stock",
        "suspension": "suspension_stock",
        "brakes": stock_brakes,
        "wheels": stock_wheels,
        "tires": stock_tires,
    }
    subsystem_slots = [
        SubsystemSlotDefinition(
            subsystem="engine",
            label="Engine Family",
            description="Editable engine build specification for the current chassis.",
            stock_config_id=default_engine,
        )
    ]
    subsystem_slots.extend(
        SubsystemSlotDefinition(
            subsystem=subsystem,
            label=subsystem.replace("_", " ").title(),
            description=f"Selected component for the {subsystem.replace('_', ' ')} slot.",
            stock_part_id=part_id,
        )
        for subsystem, part_id in slot_map.items()
    )
    BASE_CONFIGS[trim_id] = VehicleBaseConfig(
        config_id=f"{trim_id}_stock",
        trim_id=trim_id,
        subsystem_slots=subsystem_slots,
        stock_parts=[StockPartReference(subsystem=subsystem, stock_part_id=part_id) for subsystem, part_id in slot_map.items()],
        stock_configs=[StockConfigReference(subsystem="engine", stock_config_id=default_engine)],
    )


PRESETS: dict[str, BuildPreset] = {
    preset.preset_id: preset
    for preset in [
        BuildPreset(preset_id="preset_daily_brake", title="Daily Brake Refresh", description="Street-biased brake and wheel/tire refresh that keeps the car livable.", scenario_name="daily", tags=["daily", "braking"], patch={"brakes": "brakes_daily_bb", "intake": "intake_cold_air", "exhaust": "exhaust_catback"}, provenance=prov("catalog_seed", "curated preset overlay")),
        BuildPreset(preset_id="preset_winter", title="Winter Grip Pack", description="17-inch winter wheel and tire setup that protects compliance and braking confidence.", scenario_name="winter", tags=["winter"], patch={"wheels": "wheels_winter_17", "tires": "tires_winter_17", "suspension": "suspension_stock"}, provenance=prov("catalog_seed", "curated preset overlay")),
        BuildPreset(preset_id="preset_canyon_na", title="Canyon NA Response", description="Sharper NA build with suspension, tire, and diff changes.", scenario_name="canyon", tags=["canyon", "na"], patch={"intake": "intake_cold_air", "exhaust": "exhaust_catback", "tune": "tune_stage1", "differential": "diff_track_lsd", "suspension": "suspension_daily", "wheels": "wheels_track_18", "tires": "tires_canyon_18", "brakes": "brakes_big_18"}, provenance=prov("catalog_seed", "curated preset overlay")),
        BuildPreset(preset_id="preset_turbo_track", title="Turbo Track Build", description="Boosted track-oriented overlay with cooling, driveline, and brake support.", scenario_name="track", tags=["track", "turbo"], patch={"body_aero": "body_vented_track", "forced_induction": "fi_turbo_street", "fuel_system": "fuel_system_upgrade", "cooling": "cooling_track_pack", "tune": "tune_turbo_pro", "transmission": "transmission_6mt_reinforced", "clutch": "clutch_stage2", "differential": "diff_track_lsd", "suspension": "suspension_track", "brakes": "brakes_big_18", "wheels": "wheels_track_18", "tires": "tires_track_18"}, provenance=prov("catalog_seed", "curated preset overlay")),
    ]
}


VIN_CACHE: dict[str, dict[str, str | int]] = {
    "JF1ZNAA10N9700001": {"trim_id": "gr86_2022_base", "year": 2022, "make": "Toyota", "model": "GR86", "trim": "Base"},
    "JF1ZDAD19P9700002": {"trim_id": "brz_2023_premium", "year": 2023, "make": "Subaru", "model": "BRZ", "trim": "Premium"},
    "JF1ZNBF18R9700003": {"trim_id": "gr86_2023_premium", "year": 2023, "make": "Toyota", "model": "GR86", "trim": "Premium"},
}
