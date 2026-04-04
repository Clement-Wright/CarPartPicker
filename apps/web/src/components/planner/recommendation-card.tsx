"use client";

import React from "react";
import { ArrowRight, GitCompareArrows, Network, Pin } from "lucide-react";

import { formatCurrency, formatPercent, titleize } from "@/lib/format";
import type { BuildRecommendation } from "@/lib/types";

type RecommendationCardProps = {
  recommendation: BuildRecommendation;
  selected: boolean;
  pinned: boolean;
  onSelect: () => void;
  onTogglePin: () => void;
};

const metricOrder: Array<keyof BuildRecommendation["score_breakdown"]> = [
  "goal_alignment",
  "fitment_confidence",
  "cost_efficiency",
  "safety_preservation",
  "dependency_simplicity"
];

export function RecommendationCard({
  recommendation,
  selected,
  pinned,
  onSelect,
  onTogglePin
}: RecommendationCardProps) {
  return (
    <article
      className={`rounded-[24px] border p-5 transition ${
        selected
          ? "border-safety-orange/60 bg-safety-orange/10"
          : "border-white/10 bg-white/5 hover:border-white/20"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.22em] text-slate-400">
            {recommendation.compatibility_status}
          </p>
          <h3 className="mt-2 font-display text-2xl text-white">{recommendation.title}</h3>
          <p className="mt-2 text-sm text-slate-300">{recommendation.subtitle}</p>
        </div>
        <div className="text-right">
          <p className="font-display text-xs uppercase tracking-[0.22em] text-slate-400">
            Score
          </p>
          <p className="mt-2 font-display text-3xl text-white">{recommendation.score}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {recommendation.effect_tags.map((tag) => (
          <span key={tag} className="chip rounded-full px-3 py-2 text-xs uppercase tracking-[0.18em] text-slate-200">
            {tag}
          </span>
        ))}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="panel-muted rounded-2xl p-3">
          <p className="font-display text-xs uppercase tracking-[0.22em] text-slate-400">
            Cost Band
          </p>
          <p className="mt-2 text-sm text-white">
            {formatCurrency(recommendation.cost_band.min)} to {formatCurrency(recommendation.cost_band.max)}
          </p>
        </div>
        <div className="panel-muted rounded-2xl p-3">
          <p className="font-display text-xs uppercase tracking-[0.22em] text-slate-400">
            Fitment Confidence
          </p>
          <p className="mt-2 text-sm text-white">{formatPercent(recommendation.fitment_confidence)}</p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.22em] text-slate-400">
            Why It Matched
          </p>
          <ul className="mt-2 space-y-2 text-sm text-slate-200">
            {recommendation.why_it_matched.map((reason) => (
              <li key={reason} className="flex gap-2">
                <ArrowRight className="mt-0.5 h-4 w-4 flex-none text-safety-mint" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-display text-xs uppercase tracking-[0.22em] text-slate-400">
            Score Breakdown
          </p>
          <div className="mt-2 space-y-2">
            {metricOrder.map((metric) => (
              <div key={metric}>
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.14em] text-slate-400">
                  <span>{titleize(metric)}</span>
                  <span>{formatPercent(recommendation.score_breakdown[metric])}</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-white/5">
                  <div
                    className="metric-bar h-2 rounded-full"
                    style={{ width: `${recommendation.score_breakdown[metric] * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.22em] text-slate-400">
            Required Supporting Parts
          </p>
          <div className="mt-2 space-y-2 text-sm text-slate-200">
            {recommendation.required_changes.length ? (
              recommendation.required_changes.map((item) => (
                <div key={item} className="panel-muted rounded-2xl px-3 py-2">
                  {item}
                </div>
              ))
            ) : (
              <div className="panel-muted rounded-2xl px-3 py-2 text-slate-400">None</div>
            )}
          </div>
        </div>
        <div>
          <p className="font-display text-xs uppercase tracking-[0.22em] text-slate-400">
            Tradeoffs
          </p>
          <div className="mt-2 space-y-2 text-sm text-slate-200">
            {recommendation.conflicts.length ? (
              recommendation.conflicts.map((item) => (
                <div key={item} className="rounded-2xl border border-amber-300/20 bg-amber-300/10 px-3 py-2">
                  {item}
                </div>
              ))
            ) : (
              <div className="panel-muted rounded-2xl px-3 py-2 text-slate-400">No major tradeoffs.</div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={onSelect}
          className="rounded-2xl border border-safety-orange/40 bg-safety-orange/12 px-4 py-3 font-display text-xs uppercase tracking-[0.22em] text-safety-orange transition hover:bg-safety-orange/18"
        >
          <span className="inline-flex items-center gap-2">
            <Network className="h-4 w-4" />
            Show Graph Reasoning
          </span>
        </button>
        <button
          type="button"
          onClick={onTogglePin}
          className={`rounded-2xl px-4 py-3 font-display text-xs uppercase tracking-[0.22em] transition ${
            pinned
              ? "border border-safety-mint/40 bg-safety-mint/12 text-safety-mint"
              : "border border-white/10 bg-white/5 text-slate-200 hover:border-white/20"
          }`}
        >
          <span className="inline-flex items-center gap-2">
            {pinned ? <GitCompareArrows className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
            {pinned ? "Pinned To Compare" : "Pin To Compare"}
          </span>
        </button>
      </div>
    </article>
  );
}
