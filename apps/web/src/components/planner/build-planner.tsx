"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, CarFront, GitCompareArrows, Network, Search } from "lucide-react";
import { useEffect, useState } from "react";

import { BuildGraphCanvas } from "@/components/planner/build-graph-canvas";
import { CompareDrawer } from "@/components/planner/compare-drawer";
import { ExplanationPanel } from "@/components/planner/explanation-panel";
import { QueryWorkbench } from "@/components/planner/query-workbench";
import { RecallSafetyPanel } from "@/components/planner/recall-safety-panel";
import { RecommendationCard } from "@/components/planner/recommendation-card";
import { api } from "@/lib/api";
import { demoScenarios } from "@/lib/demo";
import type { BuildRecommendation, ParsedBuildQuery } from "@/lib/types";
import { useCompareStore } from "@/state/compare-store";

type MobilePane = "build" | "results" | "graph" | "compare";

const mobilePanes: Array<{ id: MobilePane; label: string; icon: typeof Search }> = [
  { id: "build", label: "Build", icon: Search },
  { id: "results", label: "Results", icon: CarFront },
  { id: "graph", label: "Graph", icon: Network },
  { id: "compare", label: "Compare", icon: GitCompareArrows }
];

function unique(values: string[]) {
  return [...new Set(values.filter(Boolean))];
}

export function BuildPlanner() {
  const [selectedTrimId, setSelectedTrimId] = useState("gr86_2022_base");
  const [vinInput, setVinInput] = useState("JF1ZNAA10N9700001");
  const [queryText, setQueryText] = useState("Best daily brake + wheel upgrade under $2,500");
  const [budget, setBudget] = useState(2500);
  const [selectedGoals, setSelectedGoals] = useState<string[]>(["daily", "braking"]);
  const [wheelDiameter, setWheelDiameter] = useState(17);
  const [keepCurrentWheels, setKeepCurrentWheels] = useState(false);
  const [parsedQuery, setParsedQuery] = useState<ParsedBuildQuery | null>(null);
  const [recommendations, setRecommendations] = useState<BuildRecommendation[]>([]);
  const [selectedPackageId, setSelectedPackageId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [mobilePane, setMobilePane] = useState<MobilePane>("build");

  const pinnedIds = useCompareStore((state) => state.pinnedIds);
  const togglePin = useCompareStore((state) => state.togglePin);
  const clearPins = useCompareStore((state) => state.clearPins);

  const trimsQuery = useQuery({
    queryKey: ["catalog", "trims"],
    queryFn: api.listTrims
  });

  useEffect(() => {
    if (!selectedTrimId && trimsQuery.data?.length) {
      setSelectedTrimId(trimsQuery.data[0].trim_id);
    }
  }, [selectedTrimId, trimsQuery.data]);

  useEffect(() => {
    const activeTrim = trimsQuery.data?.find((trim) => trim.trim_id === selectedTrimId);
    if (activeTrim) {
      setWheelDiameter(activeTrim.stock_wheel_diameter);
    }
  }, [selectedTrimId, trimsQuery.data]);

  const vehicleQuery = useQuery({
    queryKey: ["vehicle", selectedTrimId],
    queryFn: () => api.getVehicle(selectedTrimId),
    enabled: Boolean(selectedTrimId)
  });

  const parseMutation = useMutation({
    mutationFn: api.parseQuery
  });

  const recommendMutation = useMutation({
    mutationFn: api.recommendBuilds
  });

  const vinMutation = useMutation({
    mutationFn: api.decodeVin,
    onSuccess: (decoded) => {
      if (decoded.trim_id) {
        setSelectedTrimId(decoded.trim_id);
      }
      setErrorMessage(null);
    },
    onError: (error) => {
      setErrorMessage(error instanceof Error ? error.message : "VIN decode failed.");
    }
  });

  const selectedRecommendation =
    recommendations.find((item) => item.package_id === selectedPackageId) ?? recommendations[0] ?? null;

  useEffect(() => {
    if (recommendations.length && !selectedPackageId) {
      setSelectedPackageId(recommendations[0].package_id);
    }
  }, [recommendations, selectedPackageId]);

  const graphQuery = useQuery({
    queryKey: ["graph", selectedRecommendation?.graph_id],
    queryFn: () => api.getGraph(selectedRecommendation!.graph_id),
    enabled: Boolean(selectedRecommendation?.graph_id)
  });

  const compareQuery = useQuery({
    queryKey: ["compare", selectedTrimId, pinnedIds],
    queryFn: () => api.compareBuilds({ trim_id: selectedTrimId, package_ids: pinnedIds }),
    enabled: pinnedIds.length >= 2 && Boolean(selectedTrimId)
  });

  const pinnedRecommendations = recommendations.filter((item) => pinnedIds.includes(item.package_id));

  async function executePlanner(overrides?: {
    trimId?: string;
    query?: string;
    goals?: string[];
    budget?: number;
    wheel?: number;
    keepCurrentWheels?: boolean;
  }) {
    const trimId = overrides?.trimId ?? selectedTrimId;
    const text = overrides?.query ?? queryText;
    const manualGoals = overrides?.goals ?? selectedGoals;
    const budgetValue = overrides?.budget ?? budget;
    const wheelValue = overrides?.wheel ?? wheelDiameter;
    const keepWheels = overrides?.keepCurrentWheels ?? keepCurrentWheels;

    setErrorMessage(null);

    try {
      const parsed = await parseMutation.mutateAsync({
        text,
        mode: "build_path",
        vehicle_context: { trim_id: trimId }
      });

      const mergedGoals = unique([...parsed.goals, ...manualGoals]);
      const effectiveQuery: ParsedBuildQuery = {
        ...parsed,
        goals: mergedGoals,
        budget_max: budgetValue,
        hard_constraints: unique([
          ...parsed.hard_constraints,
          ...(keepWheels ? ["keep_current_wheels"] : [])
        ]),
        current_setup: {
          wheel_diameter: wheelValue,
          keep_current_wheels: keepWheels,
          notes: keepWheels ? ["User prefers preserving the current wheel setup."] : []
        }
      };

      setParsedQuery(effectiveQuery);

      const nextRecommendations = await recommendMutation.mutateAsync({
        trim_id: trimId,
        query: effectiveQuery,
        selected_goals: effectiveQuery.goals,
        budget_max: effectiveQuery.budget_max,
        current_setup: effectiveQuery.current_setup ?? undefined
      });

      setRecommendations(nextRecommendations);
      setSelectedPackageId(nextRecommendations[0]?.package_id ?? null);
      setMobilePane("results");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Planner request failed.");
    }
  }

  function handleGoalToggle(goal: string) {
    setSelectedGoals((current) =>
      current.includes(goal) ? current.filter((item) => item !== goal) : [...current, goal]
    );
  }

  function handleLoadScenario(scenarioId: string) {
    const scenario = demoScenarios.find((item) => item.id === scenarioId);
    if (!scenario) {
      return;
    }

    setSelectedTrimId(scenario.trimId);
    setQueryText(scenario.query);
    setSelectedGoals([...scenario.goals]);
    setBudget(scenario.budget);
    setWheelDiameter(scenario.wheel);
    setKeepCurrentWheels(scenario.id === "bbk-conflict");
    void executePlanner({
      trimId: scenario.trimId,
      query: scenario.query,
      goals: [...scenario.goals],
      budget: scenario.budget,
      wheel: scenario.wheel,
      keepCurrentWheels: scenario.id === "bbk-conflict"
    });
  }

  function visibleOnMobile(pane: MobilePane) {
    return mobilePane === pane ? "block" : "hidden";
  }

  return (
    <main className="min-h-screen px-4 py-4 lg:px-6 lg:py-6">
      <div className="mx-auto max-w-[1760px]">
        <div className="mb-4 rounded-[28px] border border-white/10 bg-black/20 px-5 py-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="font-display text-xs uppercase tracking-[0.28em] text-slate-400">
                Catapult 2026
              </p>
              <h1 className="mt-2 font-display text-4xl font-semibold text-white">
                Build-planning cockpit, not a marketplace
              </h1>
            </div>
            <p className="max-w-3xl text-sm leading-6 text-slate-300">
              Vehicle facts stay official, compatibility stays deterministic, and every package can
              explain what it needs, what it blocks, and what tradeoff you are accepting.
            </p>
          </div>
        </div>

        {errorMessage ? (
          <div className="mb-4 flex items-start gap-3 rounded-[24px] border border-red-300/25 bg-red-300/10 px-4 py-3 text-sm text-red-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-none" />
            <span>{errorMessage}</span>
          </div>
        ) : null}

        <div className="mb-4 flex items-center gap-2 overflow-x-auto lg:hidden">
          {mobilePanes.map((pane) => {
            const Icon = pane.icon;
            const active = mobilePane === pane.id;
            return (
              <button
                key={pane.id}
                type="button"
                onClick={() => setMobilePane(pane.id)}
                className={`rounded-full px-4 py-2 font-display text-xs uppercase tracking-[0.22em] transition ${
                  active ? "chip chip-active" : "chip text-slate-300"
                }`}
              >
                <span className="inline-flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  {pane.label}
                </span>
              </button>
            );
          })}
        </div>

        <div className="grid gap-4 lg:grid-cols-[340px_minmax(0,1.05fr)_minmax(0,0.95fr)]">
          <div className={`lg:block ${visibleOnMobile("build")}`}>
            <QueryWorkbench
              trims={trimsQuery.data ?? []}
              selectedTrimId={selectedTrimId}
              onTrimChange={setSelectedTrimId}
              vinInput={vinInput}
              onVinInputChange={setVinInput}
              onDecodeVin={() => void vinMutation.mutateAsync(vinInput)}
              queryText={queryText}
              onQueryTextChange={setQueryText}
              budget={budget}
              onBudgetChange={setBudget}
              selectedGoals={selectedGoals}
              onGoalToggle={handleGoalToggle}
              wheelDiameter={wheelDiameter}
              onWheelDiameterChange={setWheelDiameter}
              keepCurrentWheels={keepCurrentWheels}
              onKeepCurrentWheelsChange={setKeepCurrentWheels}
              onRunQuery={() => void executePlanner()}
              onLoadScenario={handleLoadScenario}
              parsedQuery={parsedQuery}
              isBusy={parseMutation.isPending || recommendMutation.isPending}
            />
          </div>

          <div className={`space-y-4 lg:block ${visibleOnMobile("results")}`}>
            <RecallSafetyPanel vehicle={vehicleQuery.data} />
            <section className="panel rounded-[28px] p-5 lg:p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
                    Recommendations
                  </p>
                  <h2 className="mt-2 font-display text-3xl text-white">Build packages</h2>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right">
                  <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">
                    Results
                  </p>
                  <p className="mt-1 font-display text-lg text-white">{recommendations.length}</p>
                </div>
              </div>

              {!recommendations.length ? (
                <div className="mt-6 rounded-[24px] border border-dashed border-white/10 px-4 py-12 text-center text-sm text-slate-400">
                  Run a query to generate deterministic build paths for the selected trim.
                </div>
              ) : (
                <div className="mt-6 space-y-4">
                  {recommendations.map((recommendation) => (
                    <RecommendationCard
                      key={recommendation.package_id}
                      recommendation={recommendation}
                      selected={selectedRecommendation?.package_id === recommendation.package_id}
                      pinned={pinnedIds.includes(recommendation.package_id)}
                      onSelect={() => {
                        setSelectedPackageId(recommendation.package_id);
                        setMobilePane("graph");
                      }}
                      onTogglePin={() => togglePin(recommendation.package_id)}
                    />
                  ))}
                </div>
              )}
            </section>
          </div>

          <div className={`space-y-4 lg:block ${visibleOnMobile("graph")}`}>
            <BuildGraphCanvas graph={graphQuery.data} loading={graphQuery.isLoading} />
            <ExplanationPanel recommendation={selectedRecommendation} graph={graphQuery.data} />
          </div>
        </div>

        <div className={`mt-4 lg:block ${visibleOnMobile("compare")}`}>
          <CompareDrawer
            pinnedRecommendations={pinnedRecommendations}
            compare={compareQuery.data}
            loading={compareQuery.isLoading}
            onClearPins={clearPins}
          />
        </div>
      </div>
    </main>
  );
}
