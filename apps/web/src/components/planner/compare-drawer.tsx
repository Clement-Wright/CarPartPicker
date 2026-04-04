"use client";

import React from "react";
import { GitCompareArrows, Trash2 } from "lucide-react";

import { formatCurrency, formatPercent, titleize } from "@/lib/format";
import type { BuildRecommendation, CompareResponse } from "@/lib/types";
import { TradeoffRadar } from "@/components/planner/tradeoff-radar";

type CompareDrawerProps = {
  pinnedRecommendations: BuildRecommendation[];
  compare?: CompareResponse | null;
  loading: boolean;
  onClearPins: () => void;
};

const palette = ["#ff7b31", "#7ce7c6", "#93c5fd"];

export function CompareDrawer({
  pinnedRecommendations,
  compare,
  loading,
  onClearPins
}: CompareDrawerProps) {
  return (
    <section className="panel rounded-[28px] p-5 lg:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
            Compare Build Paths
          </p>
          <h2 className="mt-2 font-display text-3xl text-white">Pinned packages</h2>
          <p className="mt-2 text-sm text-slate-300">
            Pin two or three packages from the results column to see axis deltas and tradeoffs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 font-display text-xs uppercase tracking-[0.22em] text-slate-300">
            {pinnedRecommendations.length} pinned
          </div>
          <button
            type="button"
            onClick={onClearPins}
            className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-slate-300 transition hover:border-white/20"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {pinnedRecommendations.length < 2 ? (
        <div className="mt-6 flex h-[240px] items-center justify-center rounded-[24px] border border-dashed border-white/10 text-sm text-slate-400">
          Pin at least two packages to open compare mode.
        </div>
      ) : loading || !compare ? (
        <div className="mt-6 flex h-[240px] items-center justify-center rounded-[24px] border border-dashed border-white/10 text-sm text-slate-400">
          Calculating compare view...
        </div>
      ) : (
        <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
          <div className="rounded-[24px] border border-white/8 bg-black/20 p-4">
            <TradeoffRadar
              axes={compare.axes}
              series={compare.package_summaries.map((summary, index) => ({
                id: summary.package_id,
                label: summary.title,
                values: summary.axes,
                color: palette[index % palette.length]
              }))}
            />
          </div>
          <div className="space-y-4">
            <div className="rounded-[24px] border border-white/8 bg-black/20 p-4">
              <div className="flex items-center gap-2 font-display text-sm uppercase tracking-[0.22em] text-slate-400">
                <GitCompareArrows className="h-4 w-4 text-safety-orange" />
                Compare Summary
              </div>
              <p className="mt-3 text-sm leading-7 text-slate-100">
                {compare.explanation_facts.summary}
              </p>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              {compare.package_summaries.map((summary, index) => (
                <div
                  key={summary.package_id}
                  className="rounded-[24px] border p-4"
                  style={{
                    borderColor: `${palette[index % palette.length]}4d`,
                    backgroundColor: `${palette[index % palette.length]}14`
                  }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-display text-2xl text-white">{summary.title}</h3>
                      <p className="mt-2 text-sm text-slate-200">{summary.subtitle}</p>
                    </div>
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: palette[index % palette.length] }}
                    />
                  </div>
                  <p className="mt-4 text-sm text-slate-200">
                    {formatCurrency(summary.cost_band.min)} to {formatCurrency(summary.cost_band.max)}
                  </p>
                  <p className="mt-1 text-sm text-slate-300">
                    Fitment confidence: {formatPercent(summary.fitment_confidence)}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {summary.effect_tags.map((tag) => (
                      <span
                        key={tag}
                        className="chip rounded-full px-3 py-2 text-[11px] uppercase tracking-[0.16em] text-slate-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="mt-4 space-y-2">
                    {Object.entries(summary.axes).map(([axis, value]) => (
                      <div key={axis}>
                        <div className="flex items-center justify-between text-xs uppercase tracking-[0.14em] text-slate-400">
                          <span>{titleize(axis)}</span>
                          <span>{formatPercent(value)}</span>
                        </div>
                        <div className="mt-1 h-2 rounded-full bg-white/5">
                          <div
                            className="h-2 rounded-full"
                            style={{
                              width: `${value * 100}%`,
                              backgroundColor: palette[index % palette.length]
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
