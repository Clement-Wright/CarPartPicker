"use client";

import { AlertTriangle, Shield, Wrench } from "lucide-react";

import { formatPercent } from "@/lib/format";
import type { VehicleDetail } from "@/lib/types";

export function RecallSafetyPanel({ vehicle }: { vehicle?: VehicleDetail | null }) {
  if (!vehicle) {
    return (
      <div className="panel rounded-[24px] p-4">
        <p className="text-sm text-slate-400">Pick a trim to load safety and recall context.</p>
      </div>
    );
  }

  return (
    <div className="panel rounded-[24px] p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
            Official Anchor
          </p>
          <h2 className="mt-2 font-display text-2xl text-white">
            {vehicle.trim.year} {vehicle.trim.make} {vehicle.trim.model} {vehicle.trim.trim}
          </h2>
        </div>
        <div className="rounded-2xl border border-safety-mint/30 bg-safety-mint/10 px-3 py-2 text-xs uppercase tracking-[0.22em] text-safety-mint">
          Seed Mode
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="panel-muted rounded-2xl p-3">
          <div className="flex items-center gap-2 text-slate-300">
            <Shield className="h-4 w-4 text-safety-mint" />
            Safety Index
          </div>
          <p className="mt-3 font-display text-2xl text-white">
            {formatPercent(vehicle.safety_context.safety_index)}
          </p>
        </div>
        <div className="panel-muted rounded-2xl p-3">
          <div className="flex items-center gap-2 text-slate-300">
            <AlertTriangle className="h-4 w-4 text-safety-orange" />
            Recall Burden
          </div>
          <p className="mt-3 font-display text-2xl text-white">
            {formatPercent(1 - vehicle.safety_context.recall_burden)}
          </p>
        </div>
        <div className="panel-muted rounded-2xl p-3">
          <div className="flex items-center gap-2 text-slate-300">
            <Wrench className="h-4 w-4 text-slate-300" />
            Stock Wheel
          </div>
          <p className="mt-3 font-display text-2xl text-white">
            {vehicle.trim.stock_wheel_diameter}&quot;
          </p>
        </div>
      </div>
      <p className="mt-4 text-sm text-slate-300">{vehicle.safety_context.recall_summary}</p>
      <p className="mt-2 text-sm text-slate-400">{vehicle.safety_context.seed_notice}</p>
    </div>
  );
}
