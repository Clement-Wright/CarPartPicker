"use client";

import * as d3 from "d3";
import { useEffect, useRef } from "react";

type RadarSeries = {
  id: string;
  label: string;
  values: Record<string, number>;
  color: string;
};

export function TradeoffRadar({
  axes,
  series
}: {
  axes: string[];
  series: RadarSeries[];
}) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!ref.current) {
      return;
    }

    const width = 340;
    const height = 300;
    const radius = 104;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const root = svg.append("g").attr("transform", `translate(${width / 2}, ${height / 2})`);
    const scale = d3.scaleLinear().domain([0, 1]).range([0, radius]);
    const angle = d3.scaleLinear().domain([0, axes.length]).range([0, Math.PI * 2]);

    [0.25, 0.5, 0.75, 1].forEach((tick) => {
      const points = axes.map((_, index) => {
        const radians = angle(index) - Math.PI / 2;
        return [Math.cos(radians) * scale(tick), Math.sin(radians) * scale(tick)];
      });
      root
        .append("path")
        .attr("d", d3.line().curve(d3.curveLinearClosed)(points as [number, number][]))
        .attr("fill", "none")
        .attr("stroke", "rgba(255,255,255,0.08)");
    });

    axes.forEach((axis, index) => {
      const radians = angle(index) - Math.PI / 2;
      const x = Math.cos(radians) * radius;
      const y = Math.sin(radians) * radius;
      root
        .append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", x)
        .attr("y2", y)
        .attr("stroke", "rgba(255,255,255,0.09)");
      root
        .append("text")
        .attr("x", Math.cos(radians) * (radius + 24))
        .attr("y", Math.sin(radians) * (radius + 24))
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("fill", "#cbd5e1")
        .text(axis.replace("_", " ").toUpperCase());
    });

    series.forEach((entry) => {
      const points = axes.map((axisKey, index) => {
        const radians = angle(index) - Math.PI / 2;
        const distance = scale(entry.values[axisKey] ?? 0);
        return [Math.cos(radians) * distance, Math.sin(radians) * distance];
      });
      root
        .append("path")
        .attr("d", d3.line().curve(d3.curveLinearClosed)(points as [number, number][]))
        .attr("fill", entry.color)
        .attr("fill-opacity", 0.12)
        .attr("stroke", entry.color)
        .attr("stroke-width", 2.4);
    });
  }, [axes, series]);

  return <svg ref={ref} className="h-[300px] w-full" aria-label="tradeoff radar chart" />;
}

