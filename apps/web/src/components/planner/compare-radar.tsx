"use client";

import { curveLinearClosed, lineRadial, scaleLinear } from "d3";

type RadarSeries = {
  label: string;
  color: string;
  values: number[];
};

type Props = {
  axes: string[];
  series: RadarSeries[];
};

export function CompareRadar({ axes, series }: Props) {
  if (!series.length) {
    return <div className="text-sm text-slate-400">Capture a baseline to compare the current build.</div>;
  }

  const size = 280;
  const center = size / 2;
  const radius = 92;
  const levels = [0.25, 0.5, 0.75, 1];
  const scale = scaleLinear().domain([0, 1]).range([0, radius]);
  const angleStep = (Math.PI * 2) / axes.length;

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
      <svg viewBox={`0 0 ${size} ${size}`} className="h-[280px] w-[280px]">
        {levels.map((level) => (
          <polygon
            key={level}
            points={axes
              .map((_, index) => {
                const angle = index * angleStep - Math.PI / 2;
                return `${center + Math.cos(angle) * scale(level)},${center + Math.sin(angle) * scale(level)}`;
              })
              .join(" ")}
            fill="none"
            stroke="rgba(255,255,255,0.12)"
          />
        ))}
        {axes.map((axis, index) => {
          const angle = index * angleStep - Math.PI / 2;
          const x = center + Math.cos(angle) * (radius + 18);
          const y = center + Math.sin(angle) * (radius + 18);
          return (
            <g key={axis}>
              <line
                x1={center}
                y1={center}
                x2={center + Math.cos(angle) * radius}
                y2={center + Math.sin(angle) * radius}
                stroke="rgba(255,255,255,0.12)"
              />
              <text x={x} y={y} fill="#c6d2dc" fontSize="11" textAnchor="middle">
                {axis}
              </text>
            </g>
          );
        })}
        {series.map((entry) => {
          const path =
            lineRadial<number>()
              .curve(curveLinearClosed)
              .angle((_, index) => index * angleStep - Math.PI / 2)
              .radius((value) => scale(value))(entry.values) ?? "";
          return (
            <path
              key={entry.label}
              d={path}
              fill={`${entry.color}22`}
              stroke={entry.color}
              strokeWidth={2.5}
              transform={`translate(${center}, ${center})`}
            />
          );
        })}
      </svg>

      <div className="space-y-2">
        {series.map((entry) => (
          <div
            key={entry.label}
            className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2 text-sm text-slate-300"
          >
            <span className="inline-flex items-center gap-2 font-display uppercase tracking-[0.18em]">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
              {entry.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
