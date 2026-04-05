"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Copy, GitBranchPlus, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { BuildGraphCanvas } from "@/components/planner/build-graph-canvas";
import { BuildViewport } from "@/components/planner/build-viewport";
import { CompareRadar } from "@/components/planner/compare-radar";
import { DynoChart } from "@/components/planner/dyno-chart";
import { api } from "@/lib/api";
import type { BuildDetailResponse, MetricSet, ValidationSeverity } from "@/lib/types";
import { useBuildStore } from "@/state/build-store";

type Tab = "validate" | "dyno" | "vehicle" | "scenario" | "graph" | "compare";
const TABS: Tab[] = ["validate", "dyno", "vehicle", "scenario", "graph", "compare"];

function stockMetrics(build: BuildDetailResponse["build"]): MetricSet {
  return {
    peak_hp: build.vehicle.stock_hp,
    peak_torque_lbft: build.vehicle.stock_torque_lbft,
    curb_weight_lb: build.vehicle.stock_weight_lb,
    upgrade_cost_usd: 0,
    redline_rpm: build.vehicle.redline_rpm,
    power_to_weight_hp_per_ton: build.vehicle.stock_hp / (build.vehicle.stock_weight_lb / 2000),
    top_speed_mph: build.vehicle.stock_top_speed_mph,
    zero_to_sixty_s: build.vehicle.stock_zero_to_sixty_s,
    quarter_mile_s: 14.4,
    braking_distance_ft: build.vehicle.stock_braking_distance_ft,
    lateral_grip_g: build.vehicle.stock_lateral_grip_g,
    thermal_headroom: build.vehicle.stock_thermal_headroom,
    driveline_stress: 0,
    comfort_index: build.vehicle.stock_comfort_index,
    fabrication_index: 0,
    budget_remaining_usd: build.target_metrics.budget_max ?? null
  };
}

const radar = (metrics: MetricSet) => [
  Math.min(1, metrics.power_to_weight_hp_per_ton / 340),
  Math.min(1, metrics.lateral_grip_g / 1.2),
  Math.min(1, 130 / Math.max(metrics.braking_distance_ft, 1)),
  Math.min(1, metrics.thermal_headroom),
  Math.min(1, metrics.comfort_index)
];

const tone = (severity: ValidationSeverity) =>
  severity === "BLOCKER"
    ? "border-red-300/25 bg-red-300/10 text-red-100"
    : severity === "WARNING"
      ? "border-amber-300/20 bg-amber-300/10 text-amber-100"
      : severity === "FABRICATION_REQUIRED"
        ? "border-orange-300/20 bg-orange-300/10 text-orange-100"
        : "border-white/8 bg-white/[0.03] text-slate-300";

export function BuildPlanner() {
  const queryClient = useQueryClient();
  const [buildId, setBuildId] = useState<string | null>(null);
  const [trimId, setTrimId] = useState("gr86_2022_base");
  const [vin, setVin] = useState("JF1ZNAA10N9700001");
  const [searchText, setSearchText] = useState("Like a GT3 RS but more practical, 430 hp, manual, RWD, under $80,000");
  const [tab, setTab] = useState<Tab>("validate");
  const [budget, setBudget] = useState("5000");
  const [targetHp, setTargetHp] = useState("");
  const [maxWeight, setMaxWeight] = useState("");
  const [engineFamilyId, setEngineFamilyId] = useState("fa24d_native");
  const [bore, setBore] = useState("94");
  const [stroke, setStroke] = useState("86");
  const [compression, setCompression] = useState("12.5");
  const [boost, setBoost] = useState("0");
  const [revLimit, setRevLimit] = useState("7500");
  const [cam, setCam] = useState("cam_street");
  const [headFlow, setHeadFlow] = useState<"stock" | "street" | "race">("stock");
  const [tuneBias, setTuneBias] = useState<"comfort" | "balanced" | "aggressive">("comfort");
  const [induction, setInduction] = useState<"na" | "turbo" | "supercharger">("na");
  const [fuel, setFuel] = useState<"91_octane" | "93_octane" | "e85">("93_octane");
  const [finalDrive, setFinalDrive] = useState("4.1");
  const [loss, setLoss] = useState("0.13");
  const [diffBias, setDiffBias] = useState<"street_lsd" | "track_lsd" | "open" | "torsen">("street_lsd");

  const dirtySlots = useBuildStore((state) => state.dirtySlots);
  const setDirtySlots = useBuildStore((state) => state.setDirtySlots);
  const setPending = useBuildStore((state) => state.setPendingRecomputations);
  const setFreshness = useBuildStore((state) => state.setValidationFreshness);
  const assetReadiness = useBuildStore((state) => state.assetReadiness);
  const setAssetReadiness = useBuildStore((state) => state.setAssetReadiness);
  const activeComparisonBaseline = useBuildStore((state) => state.activeComparisonBaseline);
  const setActiveComparisonBaseline = useBuildStore((state) => state.setActiveComparisonBaseline);

  const startRecompute = () => { setPending(["validation", "render", "vehicle", "dyno", "scenario", "graph", "compare"]); setAssetReadiness("loading"); };
  const trimsQuery = useQuery({ queryKey: ["catalog", "trims"], queryFn: api.listTrims });
  const createBuild = useMutation({ mutationFn: api.createBuild, onSuccess: (detail) => { setBuildId(detail.build.build_id); setTrimId(detail.build.vehicle.trim_id); queryClient.setQueryData(["build", detail.build.build_id], detail); } });
  const buildQuery = useQuery({ queryKey: ["build", buildId], queryFn: () => api.getBuild(buildId!), enabled: Boolean(buildId) });
  const build = buildQuery.data?.build;
  const hash = build?.computation.build_hash;
  const validationFast = useQuery({ queryKey: ["build", buildId, hash, "validate", "fast"], queryFn: () => api.getValidation(buildId!, "fast"), enabled: Boolean(buildId && hash) });
  const validationHeavy = useQuery({ queryKey: ["build", buildId, hash, "validate", "heavy"], queryFn: () => api.getValidation(buildId!, "heavy"), enabled: Boolean(buildId && hash) });
  const vehicleMetrics = useQuery({ queryKey: ["build", buildId, hash, "vehicle"], queryFn: () => api.getVehicleMetrics(buildId!), enabled: Boolean(buildId && hash) });
  const dyno = useQuery({ queryKey: ["build", buildId, hash, "dyno"], queryFn: () => api.getDyno(buildId!), enabled: Boolean(buildId && hash) });
  const scenario = useQuery({ queryKey: ["build", buildId, hash, "scenario", build?.active_scenario], queryFn: () => api.getScenario(buildId!, build?.active_scenario), enabled: Boolean(buildId && hash && build?.active_scenario) });
  const render = useQuery({ queryKey: ["build", buildId, hash, "render"], queryFn: () => api.getRenderConfig(buildId!), enabled: Boolean(buildId && hash) });
  const graph = useQuery({ queryKey: ["build", buildId, hash, "graph"], queryFn: () => api.getGraph(buildId!), enabled: Boolean(buildId && hash) });
  const diff = useQuery({ queryKey: ["build", buildId, hash, "diff", activeComparisonBaseline], queryFn: () => api.getDiff(buildId!, activeComparisonBaseline), enabled: Boolean(buildId && hash) });
  const baselineMetrics = useQuery({ queryKey: ["build", activeComparisonBaseline, "vehicle"], queryFn: () => api.getVehicleMetrics(activeComparisonBaseline), enabled: activeComparisonBaseline !== "stock" });
  const patchParts = useMutation({ mutationFn: (body: Parameters<typeof api.patchBuild>[1]) => api.patchBuild(buildId!, body), onMutate: startRecompute, onSuccess: (detail) => queryClient.setQueryData(["build", detail.build.build_id], detail) });
  const patchEngine = useMutation({ mutationFn: (body: Parameters<typeof api.patchEngine>[1]) => api.patchEngine(buildId!, body), onMutate: startRecompute, onSuccess: (detail) => queryClient.setQueryData(["build", detail.build.build_id], detail) });
  const patchDrivetrain = useMutation({ mutationFn: (body: Parameters<typeof api.patchDrivetrain>[1]) => api.patchDrivetrain(buildId!, body), onMutate: startRecompute, onSuccess: (detail) => queryClient.setQueryData(["build", detail.build.build_id], detail) });
  const applyPreset = useMutation({ mutationFn: (presetId: string) => api.applyPreset(buildId!, presetId), onMutate: startRecompute, onSuccess: async () => { if (buildId) await queryClient.invalidateQueries({ queryKey: ["build", buildId] }); } });
  const decodeVin = useMutation({ mutationFn: api.decodeVin, onSuccess: async (decoded) => { if (decoded.trim_id) await createBuild.mutateAsync({ trim_id: decoded.trim_id, scenario_name: build?.active_scenario ?? "daily" }); } });
  const cloneBuild = useMutation({ mutationFn: () => api.cloneBuild(buildId!), onSuccess: (payload) => setActiveComparisonBaseline(payload.build_id) });
  const targetSearch = useMutation({ mutationFn: api.targetSpecSearch });

  useEffect(() => { if (!buildId && trimsQuery.data?.[0] && !createBuild.isPending) void createBuild.mutateAsync({ trim_id: trimsQuery.data[0].trim_id, scenario_name: "daily" }); }, [buildId, createBuild, trimsQuery.data]);
  useEffect(() => { if (!build) return; setBudget(build.target_metrics.budget_max ? String(build.target_metrics.budget_max) : ""); setTargetHp(build.target_metrics.hp_min ? String(build.target_metrics.hp_min) : ""); setMaxWeight(build.target_metrics.weight_max_lb ? String(build.target_metrics.weight_max_lb) : ""); setEngineFamilyId(build.engine_build_spec.engine_family_id); setBore(String(build.engine_build_spec.bore_mm)); setStroke(String(build.engine_build_spec.stroke_mm)); setCompression(String(build.engine_build_spec.compression_ratio)); setBoost(String(build.engine_build_spec.induction.boost_psi)); setRevLimit(String(build.engine_build_spec.rev_limit_rpm)); setCam(build.engine_build_spec.cam_profile.profile_id); setHeadFlow(build.engine_build_spec.valve_train.head_flow_stage); setTuneBias(build.engine_build_spec.tune_bias); setInduction(build.engine_build_spec.induction.type); setFuel(build.engine_build_spec.fuel.fuel_type); setFinalDrive(String(build.drivetrain_config.final_drive_ratio)); setLoss(String(build.drivetrain_config.driveline_loss_factor)); setDiffBias(build.drivetrain_config.differential_bias); const stockMap = Object.fromEntries(build.base_config.stock_parts.map((i) => [i.subsystem, i.stock_part_id])); const stockConfigMap = Object.fromEntries(build.base_config.stock_configs.map((i) => [i.subsystem, i.stock_config_id])); setDirtySlots(build.selections.filter((s) => s.selected_part_id !== stockMap[s.subsystem] || s.selected_config_id !== stockConfigMap[s.subsystem]).map((s) => s.subsystem)); }, [build, setDirtySlots]);
  useEffect(() => { setFreshness({ fast: validationFast.data?.build_hash === hash, heavy: validationHeavy.data?.build_hash === hash }); }, [hash, setFreshness, validationFast.data?.build_hash, validationHeavy.data?.build_hash]);
  useEffect(() => { setPending([validationFast.isFetching ? "validation" : "", render.isFetching ? "render" : "", vehicleMetrics.isFetching ? "vehicle" : "", dyno.isFetching ? "dyno" : "", scenario.isFetching ? "scenario" : "", graph.isFetching ? "graph" : "", diff.isFetching ? "compare" : ""].filter(Boolean)); setAssetReadiness(render.isLoading ? "loading" : render.data ? "ready" : "idle"); }, [diff.isFetching, dyno.isFetching, graph.isFetching, render.data, render.isFetching, render.isLoading, scenario.isFetching, setAssetReadiness, setPending, validationFast.isFetching, vehicleMetrics.isFetching]);

  const currentMetrics = vehicleMetrics.data?.metrics;
  const baseline = useMemo(() => (!build ? null : activeComparisonBaseline === "stock" ? stockMetrics(build) : baselineMetrics.data?.metrics ?? null), [activeComparisonBaseline, baselineMetrics.data?.metrics, build]);
  const compareSeries = currentMetrics && baseline ? [{ label: "Current build", color: "#ff7b31", values: radar(currentMetrics) }, { label: activeComparisonBaseline === "stock" ? "Stock baseline" : "Captured baseline", color: "#7ce7c6", values: radar(baseline) }] : [];
  const availableParts = buildQuery.data?.available_parts ?? {};
  const stockBySubsystem = build ? Object.fromEntries(build.base_config.stock_parts.map((item) => [item.subsystem, item.stock_part_id])) : {};

  return (
    <main className="min-h-screen px-4 py-4 lg:px-6 lg:py-6">
      <div className="mx-auto max-w-[1860px]">
        <div className="mb-4 rounded-[28px] border border-white/10 bg-black/20 px-5 py-4"><p className="font-display text-xs uppercase tracking-[0.28em] text-slate-400">CarPartPicker Seed Mode</p><h1 className="mt-2 font-display text-4xl font-semibold text-white">Free-Roam Car Builder</h1><p className="mt-2 max-w-4xl text-sm leading-6 text-slate-300">Engine family, editable engine spec, drivetrain tuning, deterministic validation, proxy 3D, live dyno, and vehicle metrics all come from the active BuildState while production data and exact assets are brought online.</p></div>
        <div className="grid gap-4 xl:grid-cols-[390px_minmax(0,1.02fr)_minmax(0,0.98fr)]">
          <aside className="panel rounded-[28px] p-5 lg:p-6">
            <div className="flex items-start justify-between"><div><p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">Build Tree</p><h2 className="mt-1 font-display text-3xl text-white">Configure</h2></div><div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right"><p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">Dirty</p><p className="mt-1 font-display text-lg text-white">{dirtySlots.length}</p></div></div>
            <div className="mt-5 space-y-4">
              <div className="grid gap-3">
                <select className="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-3 text-white outline-none" value={trimId} onChange={(event) => { setTrimId(event.target.value); void createBuild.mutateAsync({ trim_id: event.target.value, scenario_name: build?.active_scenario ?? "daily" }); }}>{(trimsQuery.data ?? []).map((trim) => <option key={trim.trim_id} value={trim.trim_id} className="bg-slate-900">{trim.label}</option>)}</select>
                <div className="flex gap-2"><input value={vin} onChange={(event) => setVin(event.target.value)} className="min-w-0 flex-1 rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-sm text-white outline-none" /><button type="button" onClick={() => void decodeVin.mutateAsync(vin)} className="chip chip-active rounded-2xl px-4 py-3 text-sm">Decode</button></div>
                <div className="grid gap-3 sm:grid-cols-2"><select value={build?.active_scenario ?? "daily"} onChange={(event) => void patchParts.mutateAsync({ scenario_name: event.target.value })} className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none">{buildQuery.data?.scenario_definitions.map((scenarioDef) => <option key={scenarioDef.scenario_name} value={scenarioDef.scenario_name} className="bg-slate-900">{scenarioDef.label}</option>)}</select><input value={budget} onChange={(event) => setBudget(event.target.value)} placeholder="Budget" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" /></div>
                <div className="grid gap-3 sm:grid-cols-2"><input value={targetHp} onChange={(event) => setTargetHp(event.target.value)} placeholder="Target HP" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" /><input value={maxWeight} onChange={(event) => setMaxWeight(event.target.value)} placeholder="Max weight" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" /></div>
                <button type="button" onClick={() => void patchParts.mutateAsync({ target_metrics: { budget_max: budget ? Number(budget) : null, hp_min: targetHp ? Number(targetHp) : null, weight_max_lb: maxWeight ? Number(maxWeight) : null } })} className="chip chip-active w-full rounded-2xl px-4 py-3 text-sm">Apply Targets</button>
              </div>

              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                <p className="mb-3 font-display text-xs uppercase tracking-[0.2em] text-slate-400">Engine Builder</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <select value={engineFamilyId} onChange={(event) => setEngineFamilyId(event.target.value)} className="sm:col-span-2 w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none">{buildQuery.data?.engine_families.map((family) => <option key={family.engine_family_id} value={family.engine_family_id} className="bg-slate-900">{family.label}</option>)}</select>
                  <input value={bore} onChange={(event) => setBore(event.target.value)} placeholder="Bore" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={stroke} onChange={(event) => setStroke(event.target.value)} placeholder="Stroke" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={compression} onChange={(event) => setCompression(event.target.value)} placeholder="Compression" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={boost} onChange={(event) => setBoost(event.target.value)} placeholder="Boost PSI" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={revLimit} onChange={(event) => setRevLimit(event.target.value)} placeholder="Rev limit" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <select value={cam} onChange={(event) => setCam(event.target.value)} className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="cam_street" className="bg-slate-900">Cam Street</option><option value="cam_balanced" className="bg-slate-900">Cam Balanced</option><option value="cam_aggressive" className="bg-slate-900">Cam Aggressive</option></select>
                  <select value={headFlow} onChange={(event) => setHeadFlow(event.target.value as typeof headFlow)} className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="stock" className="bg-slate-900">Head Stock</option><option value="street" className="bg-slate-900">Head Street</option><option value="race" className="bg-slate-900">Head Race</option></select>
                  <select value={induction} onChange={(event) => setInduction(event.target.value as typeof induction)} className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="na" className="bg-slate-900">NA</option><option value="turbo" className="bg-slate-900">Turbo</option><option value="supercharger" className="bg-slate-900">Supercharger</option></select>
                  <select value={fuel} onChange={(event) => setFuel(event.target.value as typeof fuel)} className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="91_octane" className="bg-slate-900">91</option><option value="93_octane" className="bg-slate-900">93</option><option value="e85" className="bg-slate-900">E85</option></select>
                  <select value={tuneBias} onChange={(event) => setTuneBias(event.target.value as typeof tuneBias)} className="sm:col-span-2 w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="comfort" className="bg-slate-900">Tune Comfort</option><option value="balanced" className="bg-slate-900">Tune Balanced</option><option value="aggressive" className="bg-slate-900">Tune Aggressive</option></select>
                  <button type="button" onClick={() => void patchEngine.mutateAsync({ engine_family_id: engineFamilyId, bore_mm: Number(bore), stroke_mm: Number(stroke), compression_ratio: Number(compression), boost_psi: Number(boost), rev_limit_rpm: Number(revLimit), cam_profile_id: cam, head_flow_stage: headFlow, induction_type: induction, fuel_type: fuel, tune_bias: tuneBias })} className="sm:col-span-2 chip chip-active w-full rounded-2xl px-4 py-3 text-sm">Apply Engine Spec</button>
                </div>
              </div>

              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                <p className="mb-3 font-display text-xs uppercase tracking-[0.2em] text-slate-400">Drivetrain</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <input value={finalDrive} onChange={(event) => setFinalDrive(event.target.value)} placeholder="Final drive" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={loss} onChange={(event) => setLoss(event.target.value)} placeholder="Loss factor" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <select value={diffBias} onChange={(event) => setDiffBias(event.target.value as typeof diffBias)} className="sm:col-span-2 w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="street_lsd" className="bg-slate-900">Street LSD</option><option value="track_lsd" className="bg-slate-900">Track LSD</option><option value="open" className="bg-slate-900">Open</option><option value="torsen" className="bg-slate-900">Torsen</option></select>
                  <button type="button" onClick={() => void patchDrivetrain.mutateAsync({ final_drive_ratio: Number(finalDrive), driveline_loss_factor: Number(loss), differential_bias: diffBias })} className="sm:col-span-2 chip chip-active w-full rounded-2xl px-4 py-3 text-sm">Apply Drivetrain</button>
                </div>
              </div>

              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><p className="mb-3 font-display text-xs uppercase tracking-[0.2em] text-slate-400">Preset Overlays</p><div className="grid gap-2">{buildQuery.data?.available_presets.map((preset) => <button key={preset.preset_id} type="button" onClick={() => void applyPreset.mutateAsync(preset.preset_id)} className="rounded-2xl border border-white/8 bg-black/10 px-3 py-3 text-left"><p className="font-display text-sm uppercase tracking-[0.16em] text-white">{preset.title}</p><p className="mt-1 text-xs text-slate-300">{preset.description}</p></button>)}</div></div>
              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><p className="mb-3 font-display text-xs uppercase tracking-[0.2em] text-slate-400">Subsystem Slots</p><div className="space-y-3">{build?.base_config.subsystem_slots.filter((slot) => slot.subsystem !== "engine").map((slot) => { const selection = build.selections.find((item) => item.subsystem === slot.subsystem); return <label key={slot.subsystem} className="block text-sm text-slate-300"><span className="mb-2 flex items-center justify-between"><span className="font-display text-xs uppercase tracking-[0.18em] text-slate-400">{slot.label}</span>{dirtySlots.includes(slot.subsystem) ? <span className="rounded-full border border-amber-300/25 bg-amber-300/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.18em] text-amber-100">Modified</span> : null}</span><select value={selection?.selected_part_id ?? ""} onChange={(event) => void patchParts.mutateAsync({ parts: { [slot.subsystem]: event.target.value } })} className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none">{(availableParts[slot.subsystem] ?? []).map((part) => <option key={part.part_id} value={part.part_id} className="bg-slate-900">{part.label}</option>)}</select></label>; })}</div></div>
              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><p className="mb-3 font-display text-xs uppercase tracking-[0.2em] text-slate-400">Inverse Search</p><textarea value={searchText} onChange={(event) => setSearchText(event.target.value)} className="h-24 w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-sm text-white outline-none" /><button type="button" onClick={() => void targetSearch.mutateAsync(searchText)} className="chip chip-active mt-3 w-full rounded-2xl px-4 py-3 text-sm"><Search className="mr-2 inline h-4 w-4" />Run Target Search</button>{(targetSearch.data?.candidates ?? []).slice(0, 2).map((candidate) => <button key={`${candidate.trim_id}-${candidate.preset_id ?? "stock"}`} type="button" onClick={async () => { const detail = await createBuild.mutateAsync({ trim_id: candidate.trim_id, scenario_name: candidate.scenario_name }); if (candidate.preset_id) await applyPreset.mutateAsync(candidate.preset_id); else queryClient.setQueryData(["build", detail.build.build_id], detail); }} className="mt-2 w-full rounded-2xl border border-white/8 bg-black/10 px-3 py-3 text-left"><p className="font-display text-sm uppercase tracking-[0.16em] text-white">{candidate.title}</p><p className="mt-1 text-xs text-slate-300">{candidate.why[0]}</p></button>)}</div>
            </div>
          </aside>

          <section className="space-y-4">
            <BuildViewport renderConfig={render.data} loading={render.isLoading} />
            <div className="grid gap-4 md:grid-cols-4">{[["Peak HP", currentMetrics?.peak_hp], ["0-60", currentMetrics?.zero_to_sixty_s], ["Thermal", currentMetrics?.thermal_headroom], ["Assets", assetReadiness.toUpperCase()]].map(([label, value]) => <div key={String(label)} className="panel rounded-[24px] p-4"><p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">{label}</p><p className="mt-2 font-display text-3xl text-white">{value ?? "--"}</p></div>)}</div>
          </section>

          <section className="panel rounded-[28px] p-5 lg:p-6">
            <div className="mb-4 flex flex-wrap gap-2">{TABS.map((item) => <button key={item} type="button" onClick={() => setTab(item)} className={`rounded-full px-4 py-2 font-display text-xs uppercase tracking-[0.22em] ${tab === item ? "chip chip-active" : "chip text-slate-300"}`}>{item}</button>)}</div>
            {tab === "validate" ? <div className="space-y-4"><div className="grid gap-3 md:grid-cols-2"><div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">Fast Blockers</p><p className="mt-2 font-display text-3xl text-white">{validationFast.data?.summary.blockers ?? 0}</p></div><div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">Heavy Warnings</p><p className="mt-2 font-display text-3xl text-white">{validationHeavy.data?.summary.warnings ?? 0}</p></div></div>{[...(validationFast.data?.findings ?? []), ...(validationHeavy.data?.findings ?? []).slice(0, 4)].map((finding) => <div key={`${finding.finding_id}-${finding.phase}`} className={`rounded-2xl border px-3 py-3 text-sm ${tone(finding.severity)}`}><p className="font-display text-xs uppercase tracking-[0.18em]">{finding.title}</p><p className="mt-1 leading-6">{finding.detail}</p></div>)}</div> : null}
            {tab === "dyno" ? <DynoChart dyno={dyno.data} /> : null}
            {tab === "vehicle" && currentMetrics ? <div className="grid gap-3 md:grid-cols-2">{[["Weight", `${currentMetrics.curb_weight_lb} lb`], ["Power / Weight", `${currentMetrics.power_to_weight_hp_per_ton} hp/ton`], ["Top Speed", `${currentMetrics.top_speed_mph} mph`], ["Quarter Mile", `${currentMetrics.quarter_mile_s} s`], ["Braking", `${currentMetrics.braking_distance_ft} ft`], ["Grip", `${currentMetrics.lateral_grip_g} g`], ["Thermal", currentMetrics.thermal_headroom], ["Stress", currentMetrics.driveline_stress]].map(([label, value]) => <div key={String(label)} className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">{label}</p><p className="mt-2 font-display text-3xl text-white">{value}</p></div>)}</div> : null}
            {tab === "scenario" && scenario.data ? <div className="space-y-3"><div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">Scenario Score</p><p className="mt-2 font-display text-4xl text-white">{scenario.data.result.score}</p></div>{scenario.data.result.strengths.map((item) => <div key={item} className="rounded-2xl border border-emerald-300/20 bg-emerald-300/10 px-3 py-2 text-sm text-emerald-100">{item}</div>)}{scenario.data.result.penalties.map((item) => <div key={item} className="rounded-2xl border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-sm text-amber-100">{item}</div>)}</div> : null}
            {tab === "graph" ? <BuildGraphCanvas graph={graph.data} loading={graph.isLoading} /> : null}
            {tab === "compare" ? <div className="space-y-4"><div className="flex flex-wrap gap-2"><button type="button" onClick={() => setActiveComparisonBaseline("stock")} className={`rounded-full px-4 py-2 font-display text-xs uppercase tracking-[0.22em] ${activeComparisonBaseline === "stock" ? "chip chip-active" : "chip text-slate-300"}`}><Copy className="mr-2 inline h-4 w-4" />Stock</button><button type="button" onClick={() => void cloneBuild.mutateAsync()} className="chip rounded-full px-4 py-2 font-display text-xs uppercase tracking-[0.22em] text-slate-300"><GitBranchPlus className="mr-2 inline h-4 w-4" />Capture Baseline</button></div><CompareRadar axes={["Power", "Grip", "Brake", "Thermal", "Comfort"]} series={compareSeries} />{diff.data?.slots.filter((slot) => slot.changed).map((slot) => <div key={slot.subsystem} className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-3 text-sm text-slate-300"><p className="font-display text-xs uppercase tracking-[0.18em] text-slate-400">{slot.subsystem.replace("_", " ")}</p><p className="mt-1 text-white">{slot.current_part_id ? availableParts[slot.subsystem]?.find((item) => item.part_id === slot.current_part_id)?.label ?? slot.current_part_id : slot.current_config_id ?? "config"}</p><p className="mt-1 text-xs text-slate-400">Baseline: {slot.baseline_part_id ? availableParts[slot.subsystem]?.find((item) => item.part_id === (slot.baseline_part_id ?? stockBySubsystem[slot.subsystem]))?.label ?? slot.baseline_part_id ?? stockBySubsystem[slot.subsystem] : slot.baseline_config_id ?? "stock"}</p></div>)}</div> : null}
          </section>
        </div>
        {buildQuery.error ? <div className="mt-4 rounded-[24px] border border-red-300/25 bg-red-300/10 px-4 py-3 text-sm text-red-100"><AlertTriangle className="mr-2 inline h-4 w-4" />{buildQuery.error instanceof Error ? buildQuery.error.message : "Build load failed."}</div> : null}
      </div>
    </main>
  );
}
