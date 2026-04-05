import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BuildPlanner } from "@/components/planner/build-planner";
import { api } from "@/lib/api";
import { useBuildStore } from "@/state/build-store";

vi.mock("@/components/planner/build-viewport", () => ({ BuildViewport: () => <div>viewport</div> }));
vi.mock("@/components/planner/build-graph-canvas", () => ({ BuildGraphCanvas: () => <div>graph</div> }));
vi.mock("@/components/planner/dyno-chart", () => ({ DynoChart: () => <div>dyno-chart</div> }));
vi.mock("@/components/planner/compare-radar", () => ({ CompareRadar: () => <div>compare-radar</div> }));

vi.mock("@/lib/api", () => ({
  api: {
    listTrims: vi.fn(),
    createBuild: vi.fn(),
    getBuild: vi.fn(),
    getValidation: vi.fn(),
    getVehicleMetrics: vi.fn(),
    getDyno: vi.fn(),
    getScenario: vi.fn(),
    getRenderConfig: vi.fn(),
    getGraph: vi.fn(),
    getDiff: vi.fn(),
    cloneBuild: vi.fn(),
    decodeVin: vi.fn(),
    applyPreset: vi.fn(),
    targetSpecSearch: vi.fn(),
    patchBuild: vi.fn(),
    patchEngine: vi.fn(),
    patchDrivetrain: vi.fn()
  }
}));

const detail = {
  build: {
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
      safety_index: 0.88,
      recall_burden: 0.22,
      complaint_burden: 0.34,
      recall_summary: "Recall summary",
      complaint_summary: "Complaint summary",
      utility_note: "Utility",
      mod_potential: 0.96
    },
    base_config: {
      config_id: "base",
      trim_id: "gr86_2022_base",
      subsystem_slots: [
        { subsystem: "engine", label: "Engine Family", description: "", stock_config_id: "engine_cfg_fa24_stock" },
        { subsystem: "suspension", label: "Suspension", description: "", stock_part_id: "suspension_stock" },
        { subsystem: "brakes", label: "Brakes", description: "", stock_part_id: "brakes_stock_17" }
      ],
      stock_parts: [
        { subsystem: "suspension", stock_part_id: "suspension_stock" },
        { subsystem: "brakes", stock_part_id: "brakes_stock_17" }
      ],
      stock_configs: [{ subsystem: "engine", stock_config_id: "engine_cfg_fa24_stock" }]
    },
    active_scenario: "daily",
    target_metrics: { budget_max: 5000, hp_min: null, weight_max_lb: null },
    tolerances: { allow_fabrication: false, keep_street_legal: true, protect_daily_comfort: true },
    selections: [
      { subsystem: "engine", selected_config_id: "engine_cfg_fa24_stock", source: "stock" },
      { subsystem: "suspension", selected_part_id: "suspension_daily", source: "manual" },
      { subsystem: "brakes", selected_part_id: "brakes_stock_17", source: "stock" }
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
      exhaust: { exhaust_style: "stock" },
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
    computation: { build_hash: "hash-1", revision: 1, updated_at: "2026-04-04T00:00:00Z" },
    active_notes: ["Build updated via subsystem patch."]
  },
  available_parts: {
    suspension: [
      { part_id: "suspension_stock", subsystem: "suspension", label: "Factory suspension", brand: "OEM", notes: "", cost_usd: 0, tags: [], geometry: { hood_clearance_needed_mm: 0, hood_clearance_gain_mm: 0, ride_height_drop_mm: 0, tire_rub_risk: 0 }, performance: { hp_delta: 0, torque_delta: 0, weight_delta_lb: 0, cooling_delta: 0, braking_delta: 0, grip_delta: 0, drag_delta: 0, downforce_delta: 0, comfort_delta: 0, driveline_stress_delta: 0, thermal_delta: 0, redline_delta_rpm: 0 } },
      { part_id: "suspension_daily", subsystem: "suspension", label: "Daily coilovers", brand: "OEM", notes: "", cost_usd: 1850, tags: [], geometry: { hood_clearance_needed_mm: 0, hood_clearance_gain_mm: 0, ride_height_drop_mm: 18, tire_rub_risk: 0.05 }, performance: { hp_delta: 0, torque_delta: 0, weight_delta_lb: 0, cooling_delta: 0, braking_delta: 0, grip_delta: 0.05, drag_delta: 0, downforce_delta: 0, comfort_delta: -0.03, driveline_stress_delta: 0, thermal_delta: 0, redline_delta_rpm: 0 } }
    ],
    brakes: [{ part_id: "brakes_stock_17", subsystem: "brakes", label: "Stock brakes", brand: "OEM", notes: "", cost_usd: 0, tags: [], geometry: { hood_clearance_needed_mm: 0, hood_clearance_gain_mm: 0, ride_height_drop_mm: 0, tire_rub_risk: 0 }, performance: { hp_delta: 0, torque_delta: 0, weight_delta_lb: 0, cooling_delta: 0, braking_delta: 0, grip_delta: 0, drag_delta: 0, downforce_delta: 0, comfort_delta: 0, driveline_stress_delta: 0, thermal_delta: 0, redline_delta_rpm: 0 } }]
  },
  available_presets: [{ preset_id: "preset_daily_brake", title: "Daily Brake Refresh", description: "desc", scenario_name: "daily", tags: [], patch: {} }],
  scenario_definitions: [{ scenario_name: "daily", label: "Daily", description: "desc", weights: {}, gates: [], penalties: [], assumptions: [] }],
  engine_families: [
    { engine_family_id: "fa24d_native", label: "FA24D naturally aspirated flat-four", architecture: { architecture_id: "arch_flat4", label: "Flat four", layout: "flat4", cylinder_count: 4, head_type: "dohc", valves_per_cylinder: 4, valvetrain: "dohc" }, base_displacement_l: 2.4, base_weight_lb: 305, base_peak_hp: 228, base_peak_torque_lbft: 184, base_redline_rpm: 7500, tags: ["stock"] }
  ],
  import_batches: [{ import_batch_id: "seed_parts_2026q2", source_system: "seed_parts_catalog", imported_at: "2026-04-04", status: "seeded", record_count: 30, notes: "seed" }]
};

function renderPlanner() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BuildPlanner />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  useBuildStore.setState({
    dirtySlots: [],
    pendingRecomputations: [],
    validationFreshness: { fast: false, heavy: false },
    assetReadiness: "idle",
    activeComparisonBaseline: "stock"
  });
  vi.mocked(api.listTrims).mockResolvedValue([{ trim_id: "gr86_2022_base", label: "2022 Toyota GR86 Base", platform: "zn8", stock_wheel_diameter: 17, transmission: "manual" }] as never);
  vi.mocked(api.createBuild).mockResolvedValue(detail as never);
  vi.mocked(api.getBuild).mockResolvedValue(detail as never);
  vi.mocked(api.getValidation).mockImplementation(async (_buildId, phase) => ({
    build_id: "build-1",
    build_hash: "hash-1",
    phase,
    summary: { blockers: 1, warnings: 1, scenario_penalties: 0, fabrication_required: 0, unknown: 0 },
    findings: [{ finding_id: phase === "fast" ? "1" : "2", phase, category: "geometry", severity: "BLOCKER", subsystem: "brakes", title: "Wheel clearance failure", detail: "18-inch wheel clearance required.", blocking: true, related_parts: ["brakes_big_18"], related_configs: [] }],
    computed_at: "2026-04-04T00:00:00Z"
  } as never));
  vi.mocked(api.getVehicleMetrics).mockResolvedValue({ build_id: "build-1", build_hash: "hash-1", metrics: { peak_hp: 250, peak_torque_lbft: 195, curb_weight_lb: 2810, upgrade_cost_usd: 1850, redline_rpm: 7500, power_to_weight_hp_per_ton: 177.9, top_speed_mph: 142, zero_to_sixty_s: 5.7, quarter_mile_s: 13.9, braking_distance_ft: 110, lateral_grip_g: 0.99, thermal_headroom: 0.7, driveline_stress: 0.1, comfort_index: 0.74, fabrication_index: 0, budget_remaining_usd: 3150 }, computed_at: "2026-04-04T00:00:00Z" } as never);
  vi.mocked(api.getDyno).mockResolvedValue({ build_id: "build-1", build_hash: "hash-1", engine_family_id: "fa24d_native", spec_hash: "spec-1", dyno: { peak_hp: 250, peak_torque_lbft: 195, shift_rpm: 7300, engine_curve: [], gear_curves: [] }, computed_at: "2026-04-04T00:00:00Z" } as never);
  vi.mocked(api.getScenario).mockResolvedValue({ build_id: "build-1", build_hash: "hash-1", result: { scenario_name: "daily", score: 78, passing: true, strengths: ["Ride remains daily-usable."], penalties: ["None"], notes: [] }, computed_at: "2026-04-04T00:00:00Z" } as never);
  vi.mocked(api.getRenderConfig).mockResolvedValue({ build_id: "build-1", build_hash: "hash-1", ride_height_drop_mm: 18, paint_color: "#fff", scene_objects: [], highlights: [], computed_at: "2026-04-04T00:00:00Z" } as never);
  vi.mocked(api.getGraph).mockResolvedValue({ build_id: "build-1", build_hash: "hash-1", nodes: [], edges: [], highlights: [], findings: [] } as never);
  vi.mocked(api.getDiff).mockResolvedValue({ build_id: "build-1", against: "stock", slots: [{ subsystem: "engine", stock_config_id: "engine_cfg_fa24_stock", baseline_config_id: "engine_cfg_fa24_stock", current_config_id: "engine_cfg_fa24_stock", changed: false }, { subsystem: "suspension", stock_part_id: "suspension_stock", baseline_part_id: "suspension_stock", current_part_id: "suspension_daily", changed: true }] } as never);
  vi.mocked(api.cloneBuild).mockResolvedValue({ build_id: "build-2", source_build_id: "build-1" } as never);
  vi.mocked(api.decodeVin).mockResolvedValue({ vin: "JF1ZNAA10N9700001", trim_id: "gr86_2022_base", source: "seed", cache_hit: true } as never);
  vi.mocked(api.applyPreset).mockResolvedValue({ build: detail.build } as never);
  vi.mocked(api.targetSpecSearch).mockResolvedValue({ parsed: { text: "query", target_metrics: {}, hard_constraints: {}, soft_similarity: { attributes: [] }, use_cases: [], avoid: [], confidence: 0.8 }, candidates: [] } as never);
  vi.mocked(api.patchBuild).mockResolvedValue(detail as never);
  vi.mocked(api.patchEngine).mockResolvedValue(detail as never);
  vi.mocked(api.patchDrivetrain).mockResolvedValue(detail as never);
});

describe("BuildPlanner", () => {
  it("renders automation-style controls and modified slots", async () => {
    renderPlanner();
    await screen.findByText("Free-Roam Car Builder");
    await screen.findByText("Engine Builder");
    expect(await screen.findByText("Modified")).toBeInTheDocument();
  });

  it("shows validation findings from the build snapshots", async () => {
    renderPlanner();
    expect((await screen.findAllByText("Wheel clearance failure")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("18-inch wheel clearance required.")).length).toBeGreaterThan(0);
  });

  it("switches to dyno and compare tabs", async () => {
    renderPlanner();
    fireEvent.click(screen.getAllByRole("button", { name: "dyno" })[0]);
    expect(await screen.findByText("dyno-chart")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "compare" })[0]);
    expect(await screen.findByText("compare-radar")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Capture Baseline/i }));
    await waitFor(() => expect(api.cloneBuild).toHaveBeenCalled());
  });
});
