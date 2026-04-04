"use client";

import React from "react";
import { Search, Sparkles, Ticket, Wrench } from "lucide-react";

import { demoScenarios } from "@/lib/demo";
import type { ParsedBuildQuery, VehicleSummary } from "@/lib/types";

type QueryWorkbenchProps = {
  trims: VehicleSummary[];
  selectedTrimId: string;
  onTrimChange: (trimId: string) => void;
  vinInput: string;
  onVinInputChange: (value: string) => void;
  onDecodeVin: () => void;
  queryText: string;
  onQueryTextChange: (value: string) => void;
  budget: number;
  onBudgetChange: (value: number) => void;
  selectedGoals: string[];
  onGoalToggle: (goal: string) => void;
  wheelDiameter: number;
  onWheelDiameterChange: (value: number) => void;
  keepCurrentWheels: boolean;
  onKeepCurrentWheelsChange: (value: boolean) => void;
  onRunQuery: () => void;
  onLoadScenario: (scenarioId: string) => void;
  parsedQuery?: ParsedBuildQuery | null;
  isBusy: boolean;
};

const goalOptions = [
  { id: "daily", label: "Daily" },
  { id: "braking", label: "Braking" },
  { id: "winter", label: "Winter" },
  { id: "budget_grip", label: "Budget Grip" },
  { id: "street_performance", label: "Street Performance" }
];

export function QueryWorkbench({
  trims,
  selectedTrimId,
  onTrimChange,
  vinInput,
  onVinInputChange,
  onDecodeVin,
  queryText,
  onQueryTextChange,
  budget,
  onBudgetChange,
  selectedGoals,
  onGoalToggle,
  wheelDiameter,
  onWheelDiameterChange,
  keepCurrentWheels,
  onKeepCurrentWheelsChange,
  onRunQuery,
  onLoadScenario,
  parsedQuery,
  isBusy
}: QueryWorkbenchProps) {
  const trimLabel = trims.find((trim) => trim.trim_id === selectedTrimId)?.label;

  return (
    <section className="panel rounded-[28px] p-5 lg:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.32em] text-slate-400">
            Build Cockpit
          </p>
          <h1 className="mt-2 font-display text-3xl font-semibold text-white">
            GR86 / BRZ Planner
          </h1>
          <p className="mt-2 text-sm text-slate-300">
            Turn a vague mod idea into a constrained, explainable build path.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right">
          <p className="font-display text-[11px] uppercase tracking-[0.24em] text-slate-400">
            Active Car
          </p>
          <p className="mt-1 max-w-[12rem] text-sm text-white">{trimLabel ?? "Pick a trim"}</p>
        </div>
      </div>

      <div className="mt-6 space-y-4">
        <label className="block">
          <span className="mb-2 block font-display text-sm uppercase tracking-[0.24em] text-slate-400">
            Vehicle
          </span>
          <select
            value={selectedTrimId}
            onChange={(event) => onTrimChange(event.target.value)}
            className="w-full rounded-2xl border border-white/10 bg-graphite-900/80 px-4 py-3 text-sm text-white outline-none transition focus:border-safety-orange/60"
          >
            {trims.map((trim) => (
              <option key={trim.trim_id} value={trim.trim_id}>
                {trim.label}
              </option>
            ))}
          </select>
        </label>

        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="flex items-center gap-2 font-display text-sm uppercase tracking-[0.2em] text-slate-400">
            <Ticket className="h-4 w-4 text-safety-orange" />
            VIN Decode
          </div>
          <div className="mt-3 flex gap-2">
            <input
              value={vinInput}
              onChange={(event) => onVinInputChange(event.target.value.toUpperCase())}
              placeholder="JF1ZNAA10N9700001"
              className="min-w-0 flex-1 rounded-2xl border border-white/10 bg-graphite-900/80 px-4 py-3 text-sm text-white outline-none transition focus:border-safety-orange/60"
            />
            <button
              type="button"
              onClick={onDecodeVin}
              className="rounded-2xl border border-safety-orange/40 bg-safety-orange/12 px-4 py-3 font-display text-xs uppercase tracking-[0.24em] text-safety-orange transition hover:bg-safety-orange/18"
            >
              Decode
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Seed cache demo VINs: `JF1ZNAA10N9700001`, `JF1ZDAD19P9700002`
          </p>
        </div>

        <label className="block">
          <span className="mb-2 block font-display text-sm uppercase tracking-[0.24em] text-slate-400">
            Build Query
          </span>
          <textarea
            value={queryText}
            onChange={(event) => onQueryTextChange(event.target.value)}
            rows={5}
            className="w-full rounded-[24px] border border-white/10 bg-graphite-900/80 px-4 py-4 text-sm text-white outline-none transition focus:border-safety-orange/60"
            placeholder="Best daily brake + wheel upgrade under $2,500"
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
            <div className="flex items-center justify-between">
              <p className="font-display text-sm uppercase tracking-[0.24em] text-slate-400">
                Budget
              </p>
              <p className="font-display text-lg text-white">${budget.toLocaleString()}</p>
            </div>
            <input
              type="range"
              min={500}
              max={5000}
              step={100}
              value={budget}
              onChange={(event) => onBudgetChange(Number(event.target.value))}
              className="mt-4 w-full accent-[#ff7b31]"
            />
          </div>

          <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
            <div className="flex items-center justify-between">
              <p className="font-display text-sm uppercase tracking-[0.24em] text-slate-400">
                Current Wheel
              </p>
              <p className="font-display text-lg text-white">{wheelDiameter}&quot;</p>
            </div>
            <div className="mt-4 flex gap-2">
              {[17, 18].map((wheel) => (
                <button
                  key={wheel}
                  type="button"
                  onClick={() => onWheelDiameterChange(wheel)}
                  className={`flex-1 rounded-2xl px-3 py-2 font-display text-sm uppercase tracking-[0.2em] transition ${
                    wheelDiameter === wheel
                      ? "chip chip-active"
                      : "chip text-slate-300 hover:border-white/20"
                  }`}
                >
                  {wheel}&quot;
                </button>
              ))}
            </div>
            <label className="mt-4 flex items-center gap-2 text-sm text-slate-300">
              <input
                checked={keepCurrentWheels}
                onChange={(event) => onKeepCurrentWheelsChange(event.target.checked)}
                type="checkbox"
                className="h-4 w-4 rounded border-white/10 bg-graphite-900 text-safety-orange"
              />
              Keep current wheels if possible
            </label>
          </div>
        </div>

        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="flex items-center gap-2 font-display text-sm uppercase tracking-[0.2em] text-slate-400">
            <Wrench className="h-4 w-4 text-safety-mint" />
            Goals
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {goalOptions.map((goal) => {
              const active = selectedGoals.includes(goal.id);
              return (
                <button
                  key={goal.id}
                  type="button"
                  onClick={() => onGoalToggle(goal.id)}
                  className={`rounded-full px-3 py-2 font-display text-xs uppercase tracking-[0.22em] transition ${
                    active ? "chip chip-active" : "chip text-slate-300 hover:border-white/20"
                  }`}
                >
                  {goal.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="flex items-center gap-2 font-display text-sm uppercase tracking-[0.2em] text-slate-400">
            <Sparkles className="h-4 w-4 text-safety-orange" />
            Parsed Constraint Chips
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {(parsedQuery?.goals ?? selectedGoals).map((goal) => (
              <span key={goal} className="chip rounded-full px-3 py-2 text-xs uppercase tracking-[0.18em] text-slate-200">
                {goal.replace("_", " ")}
              </span>
            ))}
            {parsedQuery?.budget_max ? (
              <span className="chip rounded-full px-3 py-2 text-xs uppercase tracking-[0.18em] text-slate-200">
                under ${parsedQuery.budget_max.toLocaleString()}
              </span>
            ) : null}
            <span className="chip rounded-full px-3 py-2 text-xs uppercase tracking-[0.18em] text-slate-200">
              {wheelDiameter}&quot; current wheel
            </span>
            {keepCurrentWheels ? (
              <span className="chip rounded-full px-3 py-2 text-xs uppercase tracking-[0.18em] text-slate-200">
                keep current wheels
              </span>
            ) : null}
          </div>
          <p className="mt-3 text-xs text-slate-400">
            Confidence {Math.round((parsedQuery?.confidence ?? 0.78) * 100)}%
          </p>
        </div>

        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="flex items-center gap-2 font-display text-sm uppercase tracking-[0.2em] text-slate-400">
            <Search className="h-4 w-4 text-safety-mint" />
            Demo Scripts
          </div>
          <div className="mt-3 grid gap-2">
            {demoScenarios.map((scenario) => (
              <button
                key={scenario.id}
                type="button"
                onClick={() => onLoadScenario(scenario.id)}
                className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-slate-200 transition hover:border-safety-orange/40 hover:bg-safety-orange/10"
              >
                {scenario.label}
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          disabled={isBusy}
          onClick={onRunQuery}
          className="w-full rounded-[24px] bg-gradient-to-r from-[#ff7b31] to-[#ff9d52] px-5 py-4 font-display text-sm font-semibold uppercase tracking-[0.28em] text-graphite-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isBusy ? "Running Build Graph..." : "Run Build Graph"}
        </button>
      </div>
    </section>
  );
}
