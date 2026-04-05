export type ValidationSeverity =
  | "BLOCKER"
  | "WARNING"
  | "SCENARIO_PENALTY"
  | "FABRICATION_REQUIRED"
  | "UNKNOWN";

export type VisualizationMode =
  | "exact_mesh_ready"
  | "proxy_from_dimensions"
  | "catalog_only"
  | "unsupported";

export type V1ReadinessNote = {
  code: string;
  message: string;
};

export type V1ProxyGeometry = {
  kind: "box" | "cylinder" | "disc";
  color: string;
  size_mm?: [number, number, number] | null;
  radius_mm?: number | null;
  width_mm?: number | null;
  thickness_mm?: number | null;
  length_mm?: number | null;
};

export type V1SceneDimensions = {
  length_mm: number;
  width_mm: number;
  height_mm: number;
};

export type V1SceneTransform = {
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
};

export type V1SceneAnchor = {
  slot: string;
  zone?: string | null;
};

export type V1SceneHighlight = {
  zone: string;
  severity: "warning" | "error";
  message: string;
};

export type V1VisualizationSummary = {
  exact_mesh_ready: number;
  proxy_from_dimensions: number;
  catalog_only: number;
  unsupported: number;
  renderable_count: number;
  catalog_visible_count: number;
};

export type V1VehicleSearchItem = {
  trim_id: string;
  label: string;
  platform: string;
  transmission: string;
  body_style: string;
  source_mode: "seed" | "licensed" | "verified";
  supported_domains: string[];
};

export type V1VehicleSearchResponse = {
  items: V1VehicleSearchItem[];
  total: number;
  source_mode: "seed" | "licensed" | "verified";
};

export type V1VehicleDetail = {
  vehicle: VehicleTrim;
  source_mode: "seed" | "licensed" | "verified";
  production_ready: boolean;
  supported_domains: string[];
  readiness_notes: V1ReadinessNote[];
};

export type V1PartSummary = {
  part_id: string;
  subsystem: string;
  label: string;
  brand: string;
  notes: string;
  tags: string[];
  cost_usd: number;
  source_mode: "seed" | "licensed" | "verified";
  production_ready: boolean;
  visualization_mode: VisualizationMode;
  has_exact_mesh: boolean;
  has_proxy_geometry: boolean;
  has_dimensional_specs: boolean;
  scene_renderable: boolean;
  catalog_visible: boolean;
  geometry: Record<string, number | string | boolean | null>;
  performance: Record<string, number | string | boolean | null>;
  visualization_notes: V1ReadinessNote[];
};

export type V1PartDetail = V1PartSummary & {
  compatible_platforms: string[];
  compatible_transmissions: string[];
  interface: Record<string, number | string | boolean | null>;
  capabilities: Record<string, number>;
  dependency_rules: Array<Record<string, unknown>>;
  visual: Record<string, unknown>;
};

export type V1PartSearchResponse = {
  items: V1PartSummary[];
  total: number;
  source_mode: "seed" | "licensed" | "verified";
};

export type V1PartPricesResponse = {
  part_id: string;
  snapshots: Array<{
    source: string;
    source_mode: "seed" | "licensed" | "verified";
    price_usd: number;
    currency: string;
    availability: string;
    product_url?: string | null;
    observed_at: string;
  }>;
};

export type V1SubsystemFitmentOutcome = {
  subsystem: string;
  selection_id?: string | null;
  outcome:
    | "direct_fit"
    | "fits_with_adapter"
    | "fits_with_fabrication"
    | "simulation_only"
    | "invalid";
  source_mode: "seed" | "licensed" | "verified";
  visualization_mode: VisualizationMode;
  scene_renderable: boolean;
  catalog_visible: boolean;
  reasons: string[];
  support_notes: V1ReadinessNote[];
};

export type V1BuildValidationReport = {
  build_id: string;
  build_hash: string;
  source_mode: "seed" | "licensed" | "verified";
  build: BuildState;
  assembly_graph: {
    build_id: string;
    build_hash: string;
    nodes: Array<{
      node_id: string;
      kind: "vehicle" | "scenario" | "engine" | "part";
      subsystem: string;
      label: string;
      selection_id?: string | null;
    }>;
    edges: Array<{
      edge_id: string;
      source: string;
      target: string;
      relation: string;
      status:
        | "direct_fit"
        | "fits_with_adapter"
        | "fits_with_fabrication"
        | "simulation_only"
        | "invalid";
    }>;
  };
  validation: BuildValidationSnapshot;
  subsystem_outcomes: V1SubsystemFitmentOutcome[];
  visualization_summary: V1VisualizationSummary;
  support_notes: string[];
};

export type V1SceneItem = {
  part_id: string;
  instance_id: string;
  subsystem: string;
  asset_mode: "exact_mesh_ready" | "proxy_from_dimensions";
  mesh_url?: string | null;
  proxy_geometry?: V1ProxyGeometry | null;
  dimensions: V1SceneDimensions;
  transform: V1SceneTransform;
  anchor: V1SceneAnchor;
  hidden_reason?: string | null;
};

export type V1OmittedSceneItem = {
  part_id: string;
  subsystem: string;
  asset_mode: "catalog_only" | "unsupported";
  hidden_reason: string;
};

export type V1BuildSceneResponse = {
  build_id: string;
  build_hash: string;
  source_mode: "seed" | "licensed" | "verified";
  items: V1SceneItem[];
  omitted_items: V1OmittedSceneItem[];
  highlights: V1SceneHighlight[];
  summary: {
    renderable_count: number;
    exact_count: number;
    proxy_count: number;
    omitted_count: number;
  };
};

export type V1SimulationResponse = {
  build_id: string;
  build_hash: string;
  mode: "engine" | "vehicle" | "thermal" | "braking" | "handling";
  source_mode: "seed" | "licensed" | "verified";
  calibration_state: "seed_heuristic" | "calibration_required" | "calibrated";
  payload: Record<string, unknown>;
};

export type VehicleSummary = {
  trim_id: string;
  label: string;
  platform: string;
  stock_wheel_diameter: number;
  transmission: string;
};

export type VehicleTrim = {
  trim_id: string;
  platform: string;
  year: number;
  make: string;
  model: string;
  trim: string;
  drivetrain: string;
  transmission: string;
  body_style: string;
  stock_wheel_diameter: number;
  stock_tire: string;
  stock_hp: number;
  stock_torque_lbft: number;
  stock_weight_lb: number;
  redline_rpm: number;
  stock_zero_to_sixty_s: number;
  stock_top_speed_mph: number;
  stock_braking_distance_ft: number;
  stock_lateral_grip_g: number;
  stock_thermal_headroom: number;
  stock_comfort_index: number;
  safety_index: number;
  recall_burden: number;
  complaint_burden: number;
  recall_summary: string;
  complaint_summary: string;
  utility_note: string;
  mod_potential: number;
};

export type VehicleDetail = {
  trim: VehicleTrim;
  safety_context: {
    safety_index: number;
    recall_burden: number;
    complaint_burden: number;
    recall_summary: string;
    complaint_summary: string;
    seed_notice: string;
  };
};

export type EngineFamily = {
  engine_family_id: string;
  label: string;
  architecture: {
    architecture_id: string;
    label: string;
    layout: string;
    cylinder_count: number;
    head_type: string;
    valves_per_cylinder: number;
    valvetrain: string;
  };
  base_displacement_l: number;
  base_weight_lb: number;
  base_peak_hp: number;
  base_peak_torque_lbft: number;
  base_redline_rpm: number;
  tags: string[];
};

export type PartCatalogItem = {
  part_id: string;
  subsystem: string;
  label: string;
  brand: string;
  notes: string;
  cost_usd: number;
  tags: string[];
  geometry: {
    wheel_diameter_in?: number | null;
    wheel_width_in?: number | null;
    tire_width_mm?: number | null;
    brake_min_wheel_in?: number | null;
    hood_clearance_needed_mm: number;
    hood_clearance_gain_mm: number;
    ride_height_drop_mm: number;
    tire_rub_risk: number;
  };
  performance: {
    hp_delta: number;
    torque_delta: number;
    weight_delta_lb: number;
    cooling_delta: number;
    braking_delta: number;
    grip_delta: number;
    drag_delta: number;
    downforce_delta: number;
    comfort_delta: number;
    driveline_stress_delta: number;
    thermal_delta: number;
    redline_delta_rpm: number;
  };
};

export type BuildPreset = {
  preset_id: string;
  title: string;
  description: string;
  scenario_name: string;
  tags: string[];
  patch: Record<string, string>;
};

export type BuildSelection = {
  subsystem: string;
  selected_part_id?: string | null;
  selected_config_id?: string | null;
  source: "stock" | "preset" | "manual";
};

export type ScenarioDefinition = {
  scenario_name: string;
  label: string;
  description: string;
  weights: Record<string, number>;
  gates: string[];
  penalties: string[];
  assumptions: string[];
};

export type EngineBuildSpec = {
  config_id: string;
  engine_family_id: string;
  label: string;
  cylinder_count: number;
  layout: string;
  bore_mm: number;
  stroke_mm: number;
  compression_ratio: number;
  valve_train: {
    label: string;
    head_flow_stage: "stock" | "street" | "race";
    valves_per_cylinder: number;
    variable_valve_timing: boolean;
  };
  cam_profile: {
    profile_id: string;
    label: string;
  };
  induction: {
    type: "na" | "turbo" | "supercharger";
    boost_psi: number;
    intercooler_required: boolean;
  };
  fuel: {
    fuel_type: "91_octane" | "93_octane" | "e85";
    injector_scale: "stock" | "upgrade" | "high_flow";
    pump_scale: "stock" | "upgrade" | "high_flow";
  };
  exhaust: {
    exhaust_style: "stock" | "catback" | "turbo_back" | "equal_length";
  };
  tune_bias: "comfort" | "balanced" | "aggressive";
  rev_limit_rpm: number;
  notes: string[];
};

export type DrivetrainConfig = {
  config_id: string;
  label: string;
  transmission_mode: "manual" | "automatic";
  gear_ratios: number[];
  final_drive_ratio: number;
  driveline_loss_factor: number;
  differential_bias: "street_lsd" | "track_lsd" | "open" | "torsen";
  shift_latency_ms: number;
};

export type BuildState = {
  build_id: string;
  vehicle: VehicleTrim;
  base_config: {
    config_id: string;
    trim_id: string;
    subsystem_slots: Array<{
      subsystem: string;
      label: string;
      description: string;
      stock_part_id?: string | null;
      stock_config_id?: string | null;
    }>;
    stock_parts: Array<{
      subsystem: string;
      stock_part_id: string;
    }>;
    stock_configs: Array<{
      subsystem: string;
      stock_config_id: string;
    }>;
  };
  active_scenario: string;
  target_metrics: {
    budget_max?: number | null;
    hp_min?: number | null;
    torque_min?: number | null;
    weight_max_lb?: number | null;
    redline_min_rpm?: number | null;
  };
  tolerances: {
    allow_fabrication: boolean;
    keep_street_legal: boolean;
    protect_daily_comfort: boolean;
  };
  selections: BuildSelection[];
  engine_build_spec: EngineBuildSpec;
  drivetrain_config: DrivetrainConfig;
  computation: {
    build_hash: string;
    revision: number;
    updated_at: string;
  };
  active_notes: string[];
};

export type BuildDetailResponse = {
  build: BuildState;
  available_parts: Record<string, PartCatalogItem[]>;
  available_presets: BuildPreset[];
  scenario_definitions: ScenarioDefinition[];
  engine_families: EngineFamily[];
  import_batches: Array<{
    import_batch_id: string;
    source_system: string;
    imported_at: string;
    status: string;
    record_count: number;
    notes: string;
  }>;
};

export type BuildValidationSnapshot = {
  build_id: string;
  build_hash: string;
  phase: "fast" | "heavy";
  summary: {
    blockers: number;
    warnings: number;
    scenario_penalties: number;
    fabrication_required: number;
    unknown: number;
  };
  findings: Array<{
    finding_id: string;
    phase: "fast" | "heavy";
    category: "interface" | "geometry" | "dependency" | "scenario";
    severity: ValidationSeverity;
    subsystem: string;
    title: string;
    detail: string;
    blocking: boolean;
    related_parts: string[];
    related_configs: string[];
  }>;
  computed_at: string;
};

export type MetricSet = {
  peak_hp: number;
  peak_torque_lbft: number;
  curb_weight_lb: number;
  upgrade_cost_usd: number;
  redline_rpm: number;
  power_to_weight_hp_per_ton: number;
  top_speed_mph: number;
  zero_to_sixty_s: number;
  quarter_mile_s: number;
  braking_distance_ft: number;
  lateral_grip_g: number;
  thermal_headroom: number;
  driveline_stress: number;
  comfort_index: number;
  fabrication_index: number;
  budget_remaining_usd?: number | null;
};

export type BuildMetricSnapshot = {
  build_id: string;
  build_hash: string;
  metrics: MetricSet;
  computed_at: string;
};

export type VehicleMetricSnapshot = BuildMetricSnapshot;

export type BuildDynoSnapshot = {
  build_id: string;
  build_hash: string;
  engine_family_id: string;
  spec_hash: string;
  dyno: {
    peak_hp: number;
    peak_torque_lbft: number;
    shift_rpm: number;
    engine_curve: Array<{
      rpm: number;
      torque_lbft: number;
      hp: number;
    }>;
    gear_curves: Array<{
      gear: string;
      points: Array<{
        rpm: number;
        speed_mph: number;
        wheel_torque_lbft: number;
      }>;
    }>;
  };
  computed_at: string;
};

export type BuildScenarioSnapshot = {
  build_id: string;
  build_hash: string;
  result: {
    scenario_name: string;
    score: number;
    passing: boolean;
    strengths: string[];
    penalties: string[];
    notes: string[];
  };
  computed_at: string;
};

export type RenderConfig = {
  build_id: string;
  build_hash: string;
  ride_height_drop_mm: number;
  paint_color: string;
  scene_objects: Array<{
    object_id: string;
    slot: string;
    kind: string;
    color: string;
    position: [number, number, number];
    scale: [number, number, number];
    rotation: [number, number, number];
    visible: boolean;
    highlight: "none" | "warning" | "error";
  }>;
  highlights: Array<{
    zone: string;
    severity: "warning" | "error";
    message: string;
  }>;
  computed_at: string;
};

export type GraphResponse = {
  build_id: string;
  build_hash: string;
  nodes: Array<{
    id: string;
    label: string;
    kind: string;
    status: "info" | "positive" | "warning" | "conflict";
    description: string;
    position: { x: number; y: number };
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label: string;
    status: "info" | "positive" | "warning" | "conflict";
  }>;
  highlights: string[];
  findings: string[];
};

export type BuildDiffResponse = {
  build_id: string;
  against: string;
  slots: Array<{
    subsystem: string;
    stock_part_id?: string | null;
    stock_config_id?: string | null;
    baseline_part_id?: string | null;
    baseline_config_id?: string | null;
    current_part_id?: string | null;
    current_config_id?: string | null;
    changed: boolean;
  }>;
};

export type DecodedVehicle = {
  vin: string;
  trim_id?: string | null;
  year?: number | null;
  make?: string | null;
  model?: string | null;
  trim?: string | null;
  source: string;
  cache_hit: boolean;
};

export type TargetSpecResponse = {
  parsed: {
    text: string;
    budget_max?: number | null;
    target_metrics: {
      hp_min?: number | null;
      weight_max_lb?: number | null;
      redline_min_rpm?: number | null;
      budget_max?: number | null;
    };
    hard_constraints: Record<string, string[]>;
    soft_similarity: {
      reference_vehicle?: string | null;
      attributes: string[];
    };
    use_cases: string[];
    avoid: string[];
    confidence: number;
  };
  candidates: Array<{
    title: string;
    trim_id: string;
    preset_id?: string | null;
    score: number;
    why: string[];
    estimated_metrics: MetricSet;
    scenario_name: string;
  }>;
};
