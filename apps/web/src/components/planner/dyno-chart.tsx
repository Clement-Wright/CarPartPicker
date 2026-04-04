"use client";

import { line, scaleLinear } from "d3";

import type { BuildDynoSnapshot } from "@/lib/types";

type Props = {
  dyno?: BuildDynoSnapshot;
};

export function DynoChart({ dyno }: Props) {
  if (!dyno) {
    return <div className="text-sm text-slate-400">Dyno data will appear once the build is loaded.</div>;
  }

  const width = 520;
  const height = 240;
  const points = dyno.dyno.engine_curve;
  const x = scaleLinear()
    .domain([points[0]?.rpm ?? 2000, points[points.length - 1]?.rpm ?? 8000])
    .range([24, width - 24]);
  const yTorque = scaleLinear()
    .domain([0, Math.max(...points.map((point) => point.torque_lbft)) * 1.15])
    .range([height - 22, 14]);
  const yHp = scaleLinear()
    .domain([0, Math.max(...points.map((point) => point.hp)) * 1.15])
    .range([height - 22, 14]);

  const torquePath =
    line<(typeof points)[number]>()
      .x((point) => x(point.rpm))
      .y((point) => yTorque(point.torque_lbft))(points) ?? "";
  const hpPath =
    line<(typeof points)[number]>()
      .x((point) => x(point.rpm))
      .y((point) => yHp(point.hp))(points) ?? "";

  return (
    <div>
      <div className="mb-3 grid grid-cols-3 gap-2 text-sm">
        <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2">
          <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">Peak HP</p>
          <p className="mt-1 font-display text-lg text-white">{dyno.dyno.peak_hp.toFixed(1)}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2">
          <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">Peak Torque</p>
          <p className="mt-1 font-display text-lg text-white">{dyno.dyno.peak_torque_lbft.toFixed(1)}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2">
          <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">Shift RPM</p>
          <p className="mt-1 font-display text-lg text-white">{dyno.dyno.shift_rpm}</p>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="h-[240px] w-full rounded-[22px] border border-white/6 bg-[#090d11]">
        <path d={torquePath} fill="none" stroke="#ff7b31" strokeWidth={3} />
        <path d={hpPath} fill="none" stroke="#7ce7c6" strokeWidth={3} />
        {points.map((point) => (
          <g key={point.rpm}>
            <circle cx={x(point.rpm)} cy={yTorque(point.torque_lbft)} r={2.2} fill="#ff7b31" />
            <circle cx={x(point.rpm)} cy={yHp(point.hp)} r={2.2} fill="#7ce7c6" />
          </g>
        ))}
      </svg>
    </div>
  );
}
