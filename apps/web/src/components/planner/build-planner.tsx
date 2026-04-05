"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { BuildViewport } from "@/components/planner/build-viewport";
import { DynoChart } from "@/components/planner/dyno-chart";
import { api } from "@/lib/api";
import type {
  BuildDynoSnapshot,
  BuildScenarioSnapshot,
  MetricSet,
  V1PartSummary,
  VisualizationMode
} from "@/lib/types";
import { useBuildStore } from "@/state/build-store";

type Tab = "validate" | "dyno" | "vehicle" | "handling";

const TABS: Tab[] = ["validate", "dyno", "vehicle", "handling"];
const SCENARIOS = [
  ["daily", "Daily"],
  ["winter", "Winter"],
  ["canyon", "Canyon"]
] as const;

function badgeLabel(mode: VisualizationMode) {
  if (mode === "exact_mesh_ready") return "3D";
  if (mode === "proxy_from_dimensions") return "Proxy";
  if (mode === "catalog_only") return "Specs only";
  return "Hidden";
}

function badgeTone(mode: VisualizationMode) {
  if (mode === "exact_mesh_ready") return "border-emerald-300/25 bg-emerald-300/10 text-emerald-100";
  if (mode === "proxy_from_dimensions") return "border-sky-300/20 bg-sky-300/10 text-sky-100";
  if (mode === "catalog_only") return "border-white/10 bg-white/5 text-slate-200";
  return "border-red-300/20 bg-red-300/10 text-red-100";
}

function summarizePerformance(part: V1PartSummary) {
  const perf = part.performance as Record<string, number | null>;
  const items: string[] = [];
  for (const [key, label] of [
    ["hp_delta", "hp"],
    ["torque_delta", "lb-ft"],
    ["braking_delta", "brake"],
    ["grip_delta", "grip"],
    ["comfort_delta", "comfort"]
  ] as const) {
    const value = Number(perf[key] ?? 0);
    if (value) items.push(`${value > 0 ? "+" : ""}${value}${label === "lb-ft" ? " " : ""}${label}`);
  }
  return items.slice(0, 3);
}

function vehicleMetrics(payload?: Record<string, unknown>) {
  return (payload as { metrics?: MetricSet } | undefined)?.metrics;
}

function dynoSnapshot(payload?: Record<string, unknown>) {
  return payload && "dyno" in payload ? (payload as BuildDynoSnapshot) : undefined;
}

function handlingSnapshot(payload?: Record<string, unknown>) {
  return payload && "result" in payload ? (payload as BuildScenarioSnapshot) : undefined;
}

export function BuildPlanner() {
  const queryClient = useQueryClient();
  const [buildId, setBuildId] = useState<string | null>(null);
  const [trimId, setTrimId] = useState("gr86_2022_base");
  const [tab, setTab] = useState<Tab>("validate");
  const [budget, setBudget] = useState("5000");
  const [targetHp, setTargetHp] = useState("");
  const [maxWeight, setMaxWeight] = useState("");
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
  const [showRenderableOnly, setShowRenderableOnly] = useState(false);

  const dirtySlots = useBuildStore((state) => state.dirtySlots);
  const setDirtySlots = useBuildStore((state) => state.setDirtySlots);
  const setPending = useBuildStore((state) => state.setPendingRecomputations);
  const setFreshness = useBuildStore((state) => state.setValidationFreshness);
  const sceneCoverage = useBuildStore((state) => state.sceneCoverage);
  const setSceneCoverage = useBuildStore((state) => state.setSceneCoverage);

  const startRecompute = () => {
    setPending(["validation", "scene", "vehicle", "dyno", "handling"]);
    setSceneCoverage("loading");
  };

  const vehiclesQuery = useQuery({ queryKey: ["v1", "vehicles"], queryFn: () => api.searchVehiclesV1() });
  const createBuild = useMutation({
    mutationFn: api.createBuildV1,
    onSuccess: (build) => {
      setBuildId(build.build_id);
      setTrimId(build.vehicle.trim_id);
      queryClient.setQueryData(["v1", "build", build.build_id], build);
    }
  });
  const buildQuery = useQuery({
    queryKey: ["v1", "build", buildId],
    queryFn: () => api.getBuildV1(buildId!),
    enabled: Boolean(buildId)
  });
  const build = buildQuery.data;
  const hash = build?.computation.build_hash;
  const partsQuery = useQuery({
    queryKey: ["v1", "parts", build?.vehicle.trim_id],
    queryFn: () => api.searchPartsV1({ vehicleId: build!.vehicle.trim_id }),
    enabled: Boolean(build?.vehicle.trim_id)
  });
  const validationQuery = useQuery({
    queryKey: ["v1", "build", buildId, hash, "validate"],
    queryFn: () => api.validateBuildV1(buildId!),
    enabled: Boolean(buildId && hash)
  });
  const sceneQuery = useQuery({
    queryKey: ["v1", "build", buildId, hash, "scene"],
    queryFn: () => api.getSceneV1(buildId!),
    enabled: Boolean(buildId && hash)
  });
  const engineQuery = useQuery({
    queryKey: ["v1", "build", buildId, hash, "engine"],
    queryFn: () => api.simulateBuildV1(buildId!, "engine"),
    enabled: Boolean(buildId && hash)
  });
  const vehicleQuery = useQuery({
    queryKey: ["v1", "build", buildId, hash, "vehicle"],
    queryFn: () => api.simulateBuildV1(buildId!, "vehicle"),
    enabled: Boolean(buildId && hash)
  });
  const handlingQuery = useQuery({
    queryKey: ["v1", "build", buildId, hash, "handling"],
    queryFn: () => api.simulateBuildV1(buildId!, "handling"),
    enabled: Boolean(buildId && hash)
  });
  const patchAssembly = useMutation({
    mutationFn: (body: Parameters<typeof api.patchBuildAssemblyV1>[1]) => api.patchBuildAssemblyV1(buildId!, body),
    onMutate: startRecompute,
    onSuccess: async (nextBuild) => {
      queryClient.setQueryData(["v1", "build", nextBuild.build_id], nextBuild);
      await queryClient.invalidateQueries({ queryKey: ["v1", "build", nextBuild.build_id] });
    }
  });

  useEffect(() => {
    if (!buildId && vehiclesQuery.data?.items[0] && !createBuild.isPending) {
      void createBuild.mutateAsync({ trim_id: vehiclesQuery.data.items[0].trim_id, scenario_name: "daily" });
    }
  }, [buildId, createBuild, vehiclesQuery.data]);

  useEffect(() => {
    if (!build) return;
    setBudget(build.target_metrics.budget_max ? String(build.target_metrics.budget_max) : "");
    setTargetHp(build.target_metrics.hp_min ? String(build.target_metrics.hp_min) : "");
    setMaxWeight(build.target_metrics.weight_max_lb ? String(build.target_metrics.weight_max_lb) : "");
    setBore(String(build.engine_build_spec.bore_mm));
    setStroke(String(build.engine_build_spec.stroke_mm));
    setCompression(String(build.engine_build_spec.compression_ratio));
    setBoost(String(build.engine_build_spec.induction.boost_psi));
    setRevLimit(String(build.engine_build_spec.rev_limit_rpm));
    setCam(build.engine_build_spec.cam_profile.profile_id);
    setHeadFlow(build.engine_build_spec.valve_train.head_flow_stage);
    setTuneBias(build.engine_build_spec.tune_bias);
    setInduction(build.engine_build_spec.induction.type);
    setFuel(build.engine_build_spec.fuel.fuel_type);
    setFinalDrive(String(build.drivetrain_config.final_drive_ratio));
    setLoss(String(build.drivetrain_config.driveline_loss_factor));
    setDiffBias(build.drivetrain_config.differential_bias);

    const stockParts = Object.fromEntries(build.base_config.stock_parts.map((item) => [item.subsystem, item.stock_part_id]));
    const stockConfigs = Object.fromEntries(build.base_config.stock_configs.map((item) => [item.subsystem, item.stock_config_id]));
    setDirtySlots(
      build.selections
        .filter((selection) => selection.selected_part_id !== stockParts[selection.subsystem] || selection.selected_config_id !== stockConfigs[selection.subsystem])
        .map((selection) => selection.subsystem)
    );
  }, [build, setDirtySlots]);

  useEffect(() => {
    setFreshness({ fast: validationQuery.data?.build_hash === hash, heavy: validationQuery.data?.build_hash === hash });
  }, [hash, setFreshness, validationQuery.data?.build_hash]);

  useEffect(() => {
    setPending([
      validationQuery.isFetching ? "validation" : "",
      sceneQuery.isFetching ? "scene" : "",
      vehicleQuery.isFetching ? "vehicle" : "",
      engineQuery.isFetching ? "dyno" : "",
      handlingQuery.isFetching ? "handling" : ""
    ].filter(Boolean));
    setSceneCoverage(sceneQuery.isLoading || sceneQuery.isFetching ? "loading" : sceneQuery.data ? "ready" : "idle");
  }, [engineQuery.isFetching, handlingQuery.isFetching, sceneQuery.data, sceneQuery.isFetching, sceneQuery.isLoading, setPending, setSceneCoverage, validationQuery.isFetching, vehicleQuery.isFetching]);

  const currentMetrics = vehicleMetrics(vehicleQuery.data?.payload);
  const dyno = dynoSnapshot(engineQuery.data?.payload);
  const handling = handlingSnapshot(handlingQuery.data?.payload);
  const partById = useMemo(() => Object.fromEntries((partsQuery.data?.items ?? []).map((item) => [item.part_id, item])), [partsQuery.data?.items]);
  const optionsBySubsystem = useMemo(() => {
    const grouped: Record<string, V1PartSummary[]> = {};
    const selected = new Set((build?.selections ?? []).map((item) => item.selected_part_id).filter((item): item is string => Boolean(item)));
    for (const item of partsQuery.data?.items ?? []) {
      if (showRenderableOnly && !item.scene_renderable && !selected.has(item.part_id)) continue;
      grouped[item.subsystem] = [...(grouped[item.subsystem] ?? []), item];
    }
    return grouped;
  }, [build?.selections, partsQuery.data?.items, showRenderableOnly]);

  return (
    <main className="min-h-screen px-4 py-4 lg:px-6 lg:py-6">
      <div className="mx-auto max-w-[1860px]">
        <div className="mb-4 rounded-[28px] border border-white/10 bg-black/20 px-5 py-4">
          <p className="font-display text-xs uppercase tracking-[0.28em] text-slate-400">CarPartPicker v1 Builder</p>
          <h1 className="mt-2 font-display text-4xl font-semibold text-white">Fitment-First Car Builder</h1>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-300">
            Parts stay supported when they only have specs, pricing, fitment rules, or simulation data. The scene renders only the exact or proxy-capable subset.
          </p>
        </div>

        <div className="grid gap-4 xl:grid-cols-[430px_minmax(0,1.02fr)_minmax(0,0.98fr)]">
          <aside className="panel rounded-[28px] p-5 lg:p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">Build Layer</p>
                <h2 className="mt-1 font-display text-3xl text-white">Configure</h2>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right">
                <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">Dirty</p>
                <p className="mt-1 font-display text-lg text-white">{dirtySlots.length}</p>
              </div>
            </div>

            <div className="mt-5 space-y-4">
              <div className="grid gap-3">
                <select value={trimId} onChange={(event) => { setTrimId(event.target.value); void createBuild.mutateAsync({ trim_id: event.target.value, scenario_name: build?.active_scenario ?? "daily" }); }} className="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-3 text-white outline-none">
                  {(vehiclesQuery.data?.items ?? []).map((vehicle) => <option key={vehicle.trim_id} value={vehicle.trim_id} className="bg-slate-900">{vehicle.label}</option>)}
                </select>
                <div className="grid gap-3 sm:grid-cols-2">
                  <select value={build?.active_scenario ?? "daily"} onChange={(event) => void patchAssembly.mutateAsync({ scenario_name: event.target.value })} className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none">
                    {SCENARIOS.map(([value, label]) => <option key={value} value={value} className="bg-slate-900">{label}</option>)}
                  </select>
                  <input value={budget} onChange={(event) => setBudget(event.target.value)} placeholder="Budget" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <input value={targetHp} onChange={(event) => setTargetHp(event.target.value)} placeholder="Target HP" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={maxWeight} onChange={(event) => setMaxWeight(event.target.value)} placeholder="Max weight" className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                </div>
                <button type="button" onClick={() => void patchAssembly.mutateAsync({ target_metrics: { budget_max: budget ? Number(budget) : null, hp_min: targetHp ? Number(targetHp) : null, weight_max_lb: maxWeight ? Number(maxWeight) : null } })} className="chip chip-active w-full rounded-2xl px-4 py-3 text-sm">Apply Targets</button>
              </div>

              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                <p className="mb-3 font-display text-xs uppercase tracking-[0.2em] text-slate-400">Engine Tuning</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <input value={bore} onChange={(event) => setBore(event.target.value)} placeholder="Bore" className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={stroke} onChange={(event) => setStroke(event.target.value)} placeholder="Stroke" className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={compression} onChange={(event) => setCompression(event.target.value)} placeholder="Compression" className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={boost} onChange={(event) => setBoost(event.target.value)} placeholder="Boost PSI" className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={revLimit} onChange={(event) => setRevLimit(event.target.value)} placeholder="Rev limit" className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <select value={cam} onChange={(event) => setCam(event.target.value)} className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="cam_street" className="bg-slate-900">Cam Street</option><option value="cam_balanced" className="bg-slate-900">Cam Balanced</option><option value="cam_aggressive" className="bg-slate-900">Cam Aggressive</option></select>
                  <select value={headFlow} onChange={(event) => setHeadFlow(event.target.value as typeof headFlow)} className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="stock" className="bg-slate-900">Head Stock</option><option value="street" className="bg-slate-900">Head Street</option><option value="race" className="bg-slate-900">Head Race</option></select>
                  <select value={induction} onChange={(event) => setInduction(event.target.value as typeof induction)} className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="na" className="bg-slate-900">NA</option><option value="turbo" className="bg-slate-900">Turbo</option><option value="supercharger" className="bg-slate-900">Supercharger</option></select>
                  <select value={fuel} onChange={(event) => setFuel(event.target.value as typeof fuel)} className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="91_octane" className="bg-slate-900">91</option><option value="93_octane" className="bg-slate-900">93</option><option value="e85" className="bg-slate-900">E85</option></select>
                  <select value={tuneBias} onChange={(event) => setTuneBias(event.target.value as typeof tuneBias)} className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="comfort" className="bg-slate-900">Comfort</option><option value="balanced" className="bg-slate-900">Balanced</option><option value="aggressive" className="bg-slate-900">Aggressive</option></select>
                  <button type="button" onClick={() => void patchAssembly.mutateAsync({ engine_patch: { bore_mm: Number(bore), stroke_mm: Number(stroke), compression_ratio: Number(compression), boost_psi: Number(boost), rev_limit_rpm: Number(revLimit), cam_profile_id: cam, head_flow_stage: headFlow, induction_type: induction, fuel_type: fuel, tune_bias: tuneBias } })} className="sm:col-span-2 chip chip-active rounded-2xl px-4 py-3 text-sm">Apply Engine Spec</button>
                </div>
              </div>

              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                <p className="mb-3 font-display text-xs uppercase tracking-[0.2em] text-slate-400">Drivetrain</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <input value={finalDrive} onChange={(event) => setFinalDrive(event.target.value)} placeholder="Final drive" className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <input value={loss} onChange={(event) => setLoss(event.target.value)} placeholder="Loss factor" className="rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none" />
                  <select value={diffBias} onChange={(event) => setDiffBias(event.target.value as typeof diffBias)} className="sm:col-span-2 rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-white outline-none"><option value="street_lsd" className="bg-slate-900">Street LSD</option><option value="track_lsd" className="bg-slate-900">Track LSD</option><option value="open" className="bg-slate-900">Open</option><option value="torsen" className="bg-slate-900">Torsen</option></select>
                  <button type="button" onClick={() => void patchAssembly.mutateAsync({ drivetrain_patch: { final_drive_ratio: Number(finalDrive), driveline_loss_factor: Number(loss), differential_bias: diffBias } })} className="sm:col-span-2 chip chip-active rounded-2xl px-4 py-3 text-sm">Apply Drivetrain</button>
                </div>
              </div>

              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">Part Picker</p>
                  <label className="flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-200">
                    <input type="checkbox" checked={showRenderableOnly} onChange={(event) => setShowRenderableOnly(event.target.checked)} />
                    Show renderable only
                  </label>
                </div>
                <div className="mt-4 space-y-4">
                  {build?.base_config.subsystem_slots.filter((slot) => slot.subsystem !== "engine").map((slot) => (
                    <div key={slot.subsystem} className="rounded-[22px] border border-white/8 bg-black/10 p-3">
                      <div className="mb-3 flex items-center justify-between">
                        <p className="font-display text-xs uppercase tracking-[0.18em] text-slate-400">{slot.label}</p>
                        {dirtySlots.includes(slot.subsystem) ? <span className="rounded-full border border-amber-300/25 bg-amber-300/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.18em] text-amber-100">Modified</span> : null}
                      </div>
                      <div className="space-y-2">
                        {(optionsBySubsystem[slot.subsystem] ?? []).map((part) => {
                          const selected = (build?.selections ?? []).find((item) => item.subsystem === slot.subsystem)?.selected_part_id === part.part_id;
                          return (
                            <button key={part.part_id} type="button" onClick={() => void patchAssembly.mutateAsync({ parts: { [slot.subsystem]: part.part_id } })} className={`w-full rounded-2xl border px-3 py-3 text-left ${selected ? "border-[#ff7b31]/50 bg-[#ff7b31]/10" : "border-white/8 bg-white/[0.02]"}`}>
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <p className="font-display text-sm uppercase tracking-[0.16em] text-white">{part.label}</p>
                                  <p className="mt-1 text-xs text-slate-400">${part.cost_usd.toLocaleString()}</p>
                                </div>
                                <span className={`rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] ${badgeTone(part.visualization_mode)}`}>{badgeLabel(part.visualization_mode)}</span>
                              </div>
                              <div className="mt-2 flex flex-wrap gap-2">{summarizePerformance(part).map((item) => <span key={`${part.part_id}-${item}`} className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[10px] uppercase tracking-[0.16em] text-slate-300">{item}</span>)}</div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                <p className="mb-3 font-display text-xs uppercase tracking-[0.2em] text-slate-400">Selected Parts</p>
                <div className="space-y-2">
                  {(build?.selections ?? []).filter((selection) => selection.selected_part_id).map((selection) => {
                    const part = partById[String(selection.selected_part_id)];
                    if (!part) return null;
                    return <div key={selection.subsystem} className="rounded-2xl border border-white/8 bg-black/10 px-3 py-2 text-sm text-slate-300"><div className="flex items-center justify-between gap-3"><span className="font-display text-[11px] uppercase tracking-[0.18em] text-slate-400">{selection.subsystem.replace(/_/g, " ")}</span><span className={`rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] ${badgeTone(part.visualization_mode)}`}>{badgeLabel(part.visualization_mode)}</span></div><p className="mt-1 text-white">{part.label}</p></div>;
                  })}
                </div>
              </div>
            </div>
          </aside>

          <section className="space-y-4">
            <BuildViewport scene={sceneQuery.data} loading={sceneQuery.isLoading} />
            <div className="grid gap-4 md:grid-cols-4">
              {[["Peak HP", currentMetrics?.peak_hp ? currentMetrics.peak_hp.toFixed(0) : "--"], ["0-60", currentMetrics?.zero_to_sixty_s ? `${currentMetrics.zero_to_sixty_s.toFixed(1)} s` : "--"], ["Renderable", sceneQuery.data?.summary.renderable_count ?? 0], ["Scene", sceneCoverage.toUpperCase()]].map(([label, value]) => <div key={String(label)} className="panel rounded-[24px] p-4"><p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">{label}</p><p className="mt-2 font-display text-3xl text-white">{value}</p></div>)}
            </div>
          </section>

          <section className="panel rounded-[28px] p-5 lg:p-6">
            <div className="mb-4 flex flex-wrap gap-2">
              {TABS.map((item) => <button key={item} type="button" onClick={() => setTab(item)} className={`rounded-full px-4 py-2 font-display text-xs uppercase tracking-[0.22em] ${tab === item ? "chip chip-active" : "chip text-slate-300"}`}>{item}</button>)}
            </div>

            {tab === "validate" ? (
              <div className="space-y-4">
                <div className="grid gap-3 md:grid-cols-3">
                  <div className={`rounded-[24px] border p-4 ${validationQuery.data?.validation.summary.blockers ? "border-red-300/25 bg-red-300/10 text-red-100" : "border-emerald-300/25 bg-emerald-300/10 text-emerald-100"}`}>
                    <p className="font-display text-xs uppercase tracking-[0.2em]">Blockers</p>
                    <p className="mt-2 font-display text-3xl">{validationQuery.data?.validation.summary.blockers ?? 0}</p>
                  </div>
                  <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                    <p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">Warnings</p>
                    <p className="mt-2 font-display text-3xl text-white">{validationQuery.data?.validation.summary.warnings ?? 0}</p>
                  </div>
                  <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                    <p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">Specs Only</p>
                    <p className="mt-2 font-display text-3xl text-white">{validationQuery.data?.visualization_summary.catalog_only ?? 0}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  {(validationQuery.data?.support_notes ?? []).map((note) => <div key={note} className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2 text-sm text-slate-300">{note}</div>)}
                </div>
                <div className="space-y-3">
                  {(validationQuery.data?.validation.findings ?? []).map((finding) => <div key={`${finding.finding_id}-${finding.subsystem}`} className={`rounded-2xl border px-3 py-3 text-sm ${finding.severity === "BLOCKER" ? "border-red-300/25 bg-red-300/10 text-red-100" : "border-amber-300/20 bg-amber-300/10 text-amber-100"}`}><p className="font-display text-xs uppercase tracking-[0.18em]">{finding.title}</p><p className="mt-1 leading-6">{finding.detail}</p></div>)}
                </div>
              </div>
            ) : null}

            {tab === "dyno" ? <DynoChart dyno={dyno} /> : null}

            {tab === "vehicle" && currentMetrics ? (
              <div className="grid gap-3 md:grid-cols-2">
                {[["Weight", `${currentMetrics.curb_weight_lb} lb`], ["Power / Weight", `${currentMetrics.power_to_weight_hp_per_ton} hp/ton`], ["Top Speed", `${currentMetrics.top_speed_mph} mph`], ["Quarter Mile", `${currentMetrics.quarter_mile_s} s`], ["Braking", `${currentMetrics.braking_distance_ft} ft`], ["Grip", `${currentMetrics.lateral_grip_g} g`]].map(([label, value]) => <div key={String(label)} className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"><p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">{label}</p><p className="mt-2 font-display text-3xl text-white">{value}</p></div>)}
              </div>
            ) : null}

            {tab === "handling" ? (
              handling ? (
                <div className="space-y-3">
                  <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                    <p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">Scenario Score</p>
                    <p className="mt-2 font-display text-4xl text-white">{handling.result.score}</p>
                  </div>
                  {handling.result.strengths.map((item) => <div key={item} className="rounded-2xl border border-emerald-300/20 bg-emerald-300/10 px-3 py-2 text-sm text-emerald-100">{item}</div>)}
                  {handling.result.penalties.map((item) => <div key={item} className="rounded-2xl border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-sm text-amber-100">{item}</div>)}
                </div>
              ) : <div className="rounded-[24px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-400">Handling simulation will appear once the build is ready.</div>
            ) : null}
          </section>
        </div>

        {buildQuery.error ? (
          <div className="mt-4 rounded-[24px] border border-red-300/25 bg-red-300/10 px-4 py-3 text-sm text-red-100">
            <AlertTriangle className="mr-2 inline h-4 w-4" />
            {buildQuery.error instanceof Error ? buildQuery.error.message : "Build load failed."}
          </div>
        ) : null}
      </div>
    </main>
  );
}
