import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BuildPlanner } from "@/components/planner/build-planner";
import { api } from "@/lib/api";
import { useBuildStore } from "@/state/build-store";

vi.mock("@/components/planner/build-viewport", () => ({ BuildViewport: () => <div>viewport</div> }));
vi.mock("@/components/planner/dyno-chart", () => ({ DynoChart: () => <div>dyno-chart</div> }));

vi.mock("@/lib/api", () => ({
  api: {
    searchVehiclesV1: vi.fn(),
    createBuildV1: vi.fn(),
    getBuildV1: vi.fn(),
    searchPartsV1: vi.fn(),
    validateBuildV1: vi.fn(),
    getSceneV1: vi.fn(),
    simulateBuildV1: vi.fn(),
    patchBuildAssemblyV1: vi.fn()
  }
}));

const build = {
  build_id: "build-1",
  vehicle: {
    trim_id: "gr86_2022_base",
    platform: "zn8",
    year: 2022,
    make: "Toyota",
    model: "GR86",
    trim: "Base",
    drivetrain: "RWD",
    transmission: "manual",
    body_style: "coupe",
    stock_wheel_diameter: 17,
    stock_tire: "215/45R17",
    stock_hp: 228,
    stock_torque_lbft: 184,
    stock_weight_lb: 2811,
    redline_rpm: 7500,
    stock_zero_to_sixty_s: 6.1,
    stock_top_speed_mph: 140,
    stock_braking_distance_ft: 114,
    stock_lateral_grip_g: 0.93,
    stock_thermal_headroom: 0.68,
    stock_comfort_index: 0.78,
    stock_drag_index: 0.61,
    stock_downforce_index: 0.18,
    driveline_limit_lbft: 245,
    gear_ratios: [3.626, 2.188],
    final_drive_ratio: 4.1,
    safety_index: 0.88,
    recall_burden: 0.22,
    complaint_burden: 0.34,
    recall_summary: "Recall summary",
    complaint_summary: "Complaint summary",
    utility_note: "Utility",
    mod_potential: 0.96,
    provenance: { source: "seed", confidence: 1, basis: "seed", last_verified: "2026-04-05", kind: "hand_curated" }
  },
  vehicle_platform: {
    platform_id: "zn8",
    label: "ZN8",
    manufacturer: "Toyota/Subaru",
    drivetrain_layout: "front_engine_rwd",
    stock_mount_family: "fa24",
    stock_bellhousing_family: "fa24",
    stock_ecu_family: "toyobaru",
    stock_cooling_family: "stock",
    stock_driveline_family: "zn8_manual",
    wheel_bolt_pattern: "5x100",
    hub_bore_mm: 56.1,
    lineage: { source_system: "seed", source_record_id: "seed", import_batch_id: "seed", verification_status: "seeded", measurement_basis: "seed" },
    provenance: { source: "seed", confidence: 1, basis: "seed", last_verified: "2026-04-05", kind: "hand_curated" }
  },
  chassis_envelope: {
    platform_id: "zn8",
    engine_bay: { length_mm: 850, width_mm: 1020, height_mm: 650 },
    transmission_tunnel: { length_mm: 1500, width_mm: 420, height_mm: 420 },
    ride_height_travel: { envelope_id: "ride", nominal_drop_mm: 0, safe_compression_margin_mm: 38 },
    front_tire_sweep: { envelope_id: "sweep", nominal_width_mm: 235, rub_risk: 0.05, full_lock_margin_mm: 18 },
    wheel_barrel_profile: { profile_id: "barrel", min_brake_diameter_in: 17, barrel_width_in: 7.5 },
    stock_brake_envelope: { envelope_id: "oem", minimum_wheel_diameter_in: 17, radial_clearance_mm: 8 }
  },
  base_config: {
    config_id: "base",
    trim_id: "gr86_2022_base",
    subsystem_slots: [
      { subsystem: "engine", label: "Engine", description: "", stock_config_id: "engine_cfg_fa24_stock" },
      { subsystem: "tune", label: "Tune", description: "", stock_part_id: "tune_stock" },
      { subsystem: "brakes", label: "Brakes", description: "", stock_part_id: "brakes_stock_17" },
      { subsystem: "wheels", label: "Wheels", description: "", stock_part_id: "wheels_stock_17" }
    ],
    stock_parts: [
      { subsystem: "tune", stock_part_id: "tune_stock" },
      { subsystem: "brakes", stock_part_id: "brakes_stock_17" },
      { subsystem: "wheels", stock_part_id: "wheels_stock_17" }
    ],
    stock_configs: [{ subsystem: "engine", stock_config_id: "engine_cfg_fa24_stock" }]
  },
  active_scenario: "daily",
  target_metrics: { budget_max: 5000, hp_min: null, torque_min: null, weight_max_lb: null, redline_min_rpm: null, top_speed_min_mph: null, zero_to_sixty_max_s: null, braking_distance_max_ft: null },
  tolerances: { allow_fabrication: false, keep_street_legal: true, protect_daily_comfort: true },
  selections: [
    { subsystem: "engine", selected_config_id: "engine_cfg_fa24_stock", source: "stock" },
    { subsystem: "tune", selected_part_id: "tune_stock", source: "stock" },
    { subsystem: "brakes", selected_part_id: "brakes_stock_17", source: "stock" },
    { subsystem: "wheels", selected_part_id: "wheels_stock_17", source: "stock" }
  ],
  engine_build_spec: {
    config_id: "engine_cfg_fa24_stock",
    engine_family_id: "fa24d_native",
    label: "FA24 stock",
    cylinder_count: 4,
    layout: "flat4",
    bore_mm: 94,
    stroke_mm: 86,
    compression_ratio: 12.5,
    valve_train: { label: "Factory", head_flow_stage: "stock", valves_per_cylinder: 4, variable_valve_timing: true },
    cam_profile: { profile_id: "cam_street", label: "Street" },
    induction: { type: "na", boost_psi: 0, intercooler_required: false },
    fuel: { fuel_type: "93_octane", injector_scale: "stock", pump_scale: "stock" },
    exhaust: { exhaust_style: "stock", flow_bias: 0, noise_bias: 0 },
    tune_bias: "comfort",
    rev_limit_rpm: 7500,
    notes: []
  },
  drivetrain_config: {
    config_id: "drivetrain_manual_stock",
    label: "6MT stock gearing",
    transmission_mode: "manual",
    gear_ratios: [3.626, 2.188],
    final_drive_ratio: 4.1,
    driveline_loss_factor: 0.13,
    differential_bias: "street_lsd",
    shift_latency_ms: 180
  },
  computation: { build_hash: "hash-1", revision: 1, updated_at: "2026-04-05T00:00:00Z" },
  active_notes: []
};

const parts = [
  {
    part_id: "tune_stock",
    subsystem: "tune",
    label: "Factory calibration",
    brand: "OEM",
    notes: "Stock ECU behavior.",
    tags: ["stock"],
    cost_usd: 0,
    source_mode: "seed",
    production_ready: false,
    visualization_mode: "catalog_only",
    has_exact_mesh: false,
    has_proxy_geometry: false,
    has_dimensional_specs: false,
    scene_renderable: false,
    catalog_visible: true,
    geometry: {},
    performance: { hp_delta: 0 },
    visualization_notes: []
  },
  {
    part_id: "tune_stage1",
    subsystem: "tune",
    label: "Stage 1 street tune",
    brand: "Circuit Logic",
    notes: "NA tune.",
    tags: ["na"],
    cost_usd: 600,
    source_mode: "seed",
    production_ready: false,
    visualization_mode: "catalog_only",
    has_exact_mesh: false,
    has_proxy_geometry: false,
    has_dimensional_specs: false,
    scene_renderable: false,
    catalog_visible: true,
    geometry: {},
    performance: { hp_delta: 10 },
    visualization_notes: []
  },
  {
    part_id: "brakes_stock_17",
    subsystem: "brakes",
    label: "Stock brakes",
    brand: "OEM",
    notes: "Factory brakes.",
    tags: ["stock"],
    cost_usd: 0,
    source_mode: "seed",
    production_ready: false,
    visualization_mode: "proxy_from_dimensions",
    has_exact_mesh: false,
    has_proxy_geometry: true,
    has_dimensional_specs: true,
    scene_renderable: true,
    catalog_visible: true,
    geometry: { brake_min_wheel_in: 17 },
    performance: { braking_delta: 0 },
    visualization_notes: []
  },
  {
    part_id: "brakes_big_18",
    subsystem: "brakes",
    label: "18-inch big brake kit",
    brand: "Brembo-style",
    notes: "Needs 18-inch clearance.",
    tags: ["track"],
    cost_usd: 3280,
    source_mode: "seed",
    production_ready: false,
    visualization_mode: "proxy_from_dimensions",
    has_exact_mesh: false,
    has_proxy_geometry: true,
    has_dimensional_specs: true,
    scene_renderable: true,
    catalog_visible: true,
    geometry: { brake_min_wheel_in: 18 },
    performance: { braking_delta: 0.19 },
    visualization_notes: []
  },
  {
    part_id: "wheels_stock_17",
    subsystem: "wheels",
    label: "Factory 17-inch wheel",
    brand: "OEM",
    notes: "Stock wheel.",
    tags: ["stock"],
    cost_usd: 0,
    source_mode: "seed",
    production_ready: false,
    visualization_mode: "proxy_from_dimensions",
    has_exact_mesh: false,
    has_proxy_geometry: true,
    has_dimensional_specs: true,
    scene_renderable: true,
    catalog_visible: true,
    geometry: { wheel_diameter_in: 17 },
    performance: { grip_delta: 0 },
    visualization_notes: []
  }
];

function renderPlanner() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BuildPlanner />
    </QueryClientProvider>
  );
}

afterEach(() => {
  cleanup();
});

beforeEach(() => {
  vi.clearAllMocks();
  useBuildStore.setState({
    dirtySlots: [],
    pendingRecomputations: [],
    validationFreshness: { fast: false, heavy: false },
    sceneCoverage: "idle",
    activeComparisonBaseline: "stock"
  });

  vi.mocked(api.searchVehiclesV1).mockResolvedValue({
    items: [{ trim_id: "gr86_2022_base", label: "2022 Toyota GR86 Base", platform: "zn8", transmission: "manual", body_style: "coupe", source_mode: "seed", supported_domains: ["ice_road_vehicle"] }],
    total: 1,
    source_mode: "seed"
  } as never);
  vi.mocked(api.createBuildV1).mockResolvedValue(build as never);
  vi.mocked(api.getBuildV1).mockResolvedValue(build as never);
  vi.mocked(api.searchPartsV1).mockResolvedValue({ items: parts, total: parts.length, source_mode: "seed" } as never);
  vi.mocked(api.validateBuildV1).mockResolvedValue({
    build_id: "build-1",
    build_hash: "hash-1",
    source_mode: "seed",
    build,
    assembly_graph: { build_id: "build-1", build_hash: "hash-1", nodes: [], edges: [] },
    validation: {
      build_id: "build-1",
      build_hash: "hash-1",
      phase: "fast",
      summary: { blockers: 1, warnings: 1, scenario_penalties: 0, fabrication_required: 0, unknown: 0 },
      findings: [{ finding_id: "finding-1", phase: "fast", category: "geometry", severity: "BLOCKER", subsystem: "brakes", title: "Wheel clearance failure", detail: "18-inch wheel clearance required.", blocking: true, related_parts: ["brakes_big_18"], related_configs: [] }],
      computed_at: "2026-04-05T00:00:00Z"
    },
    subsystem_outcomes: [],
    visualization_summary: { exact_mesh_ready: 0, proxy_from_dimensions: 2, catalog_only: 1, unsupported: 0, renderable_count: 2, catalog_visible_count: 3 },
    support_notes: ["Visualization coverage does not change whether a part is mechanically valid."]
  } as never);
  vi.mocked(api.getSceneV1).mockResolvedValue({
    build_id: "build-1",
    build_hash: "hash-1",
    source_mode: "seed",
    items: [],
    omitted_items: [{ part_id: "tune_stock", subsystem: "tune", asset_mode: "catalog_only", hidden_reason: "Specs only." }],
    highlights: [],
    summary: { renderable_count: 0, exact_count: 0, proxy_count: 0, omitted_count: 1 }
  } as never);
  vi.mocked(api.simulateBuildV1).mockImplementation(async (_buildId, mode) => {
    if (mode === "engine") {
      return {
        build_id: "build-1",
        build_hash: "hash-1",
        mode,
        source_mode: "seed",
        calibration_state: "seed_heuristic",
        payload: { build_id: "build-1", build_hash: "hash-1", engine_family_id: "fa24d_native", spec_hash: "spec-1", dyno: { peak_hp: 250, peak_torque_lbft: 195, shift_rpm: 7300, engine_curve: [], gear_curves: [] }, computed_at: "2026-04-05T00:00:00Z" }
      } as never;
    }
    if (mode === "vehicle") {
      return {
        build_id: "build-1",
        build_hash: "hash-1",
        mode,
        source_mode: "seed",
        calibration_state: "seed_heuristic",
        payload: { metrics: { peak_hp: 250, peak_torque_lbft: 195, curb_weight_lb: 2810, upgrade_cost_usd: 600, redline_rpm: 7500, power_to_weight_hp_per_ton: 177.9, top_speed_mph: 142, zero_to_sixty_s: 5.7, quarter_mile_s: 13.9, braking_distance_ft: 110, lateral_grip_g: 0.99, thermal_headroom: 0.7, driveline_stress: 0.1, comfort_index: 0.74, fabrication_index: 0, budget_remaining_usd: 4400 } }
      } as never;
    }
    return {
      build_id: "build-1",
      build_hash: "hash-1",
      mode,
      source_mode: "seed",
      calibration_state: "seed_heuristic",
      payload: { result: { scenario_name: "daily", score: 78, passing: true, strengths: ["Ride remains daily-usable."], penalties: ["None"], notes: [] } }
    } as never;
  });
  vi.mocked(api.patchBuildAssemblyV1).mockResolvedValue(build as never);
});

describe("BuildPlanner", () => {
  it("renders the v1 builder and visualization badges", async () => {
    renderPlanner();
    expect(await screen.findByText("Fitment-First Car Builder")).toBeInTheDocument();
    expect(await screen.findAllByText("Specs only")).not.toHaveLength(0);
    expect(await screen.findAllByText("Proxy")).not.toHaveLength(0);
  });

  it("filters non-renderable options without breaking the selected specs-only part", async () => {
    renderPlanner();
    expect(await screen.findByText("Stage 1 street tune")).toBeInTheDocument();
    fireEvent.click(screen.getAllByLabelText(/Show renderable only/i)[0]);
    await waitFor(() => expect(screen.queryByText("Stage 1 street tune")).not.toBeInTheDocument());
    expect(screen.getAllByText("Factory calibration").length).toBeGreaterThan(0);
  });

  it("shows validation findings and simulation tabs through v1 endpoints", async () => {
    renderPlanner();
    expect(await screen.findByText("Wheel clearance failure")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "dyno" })[0]);
    expect(await screen.findByText("dyno-chart")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "handling" })[0]);
    expect(await screen.findByText("Scenario Score")).toBeInTheDocument();
  });
});
