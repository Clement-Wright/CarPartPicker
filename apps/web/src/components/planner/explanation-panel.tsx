"use client";

import type { BuildRecommendation, GraphResponse } from "@/lib/types";

type ExplanationPanelProps = {
  recommendation?: BuildRecommendation | null;
  graph?: GraphResponse | null;
};

export function ExplanationPanel({ recommendation, graph }: ExplanationPanelProps) {
  if (!recommendation) {
    return (
      <div className="panel rounded-[24px] p-4">
        <p className="text-sm text-slate-400">Pick a package to inspect the reasoning narrative.</p>
      </div>
    );
  }

  return (
    <div className="panel rounded-[24px] p-4">
      <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
        Why This Package
      </p>
      <p className="mt-3 text-sm leading-7 text-slate-100">{recommendation.explanation}</p>

      <div className="mt-5">
        <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
          What Would Change It
        </p>
        <div className="mt-2 space-y-2">
          {recommendation.what_would_change.map((item) => (
            <div key={item} className="panel-muted rounded-2xl px-3 py-2 text-sm text-slate-200">
              {item}
            </div>
          ))}
        </div>
      </div>

      {graph?.eliminated_options.length ? (
        <div className="mt-5">
          <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
            Eliminated Alternatives
          </p>
          <div className="mt-2 space-y-2">
            {graph.eliminated_options.map((option) => (
              <div key={option.package_id} className="rounded-2xl border border-red-300/20 bg-red-300/10 px-3 py-2">
                <p className="font-display text-sm text-white">{option.title}</p>
                <p className="mt-1 text-sm text-slate-300">{option.reason}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
