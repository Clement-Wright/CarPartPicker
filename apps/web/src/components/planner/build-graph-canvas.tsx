"use client";

import "@xyflow/react/dist/style.css";

import { Background, Controls, MiniMap, ReactFlow } from "@xyflow/react";

import type { GraphResponse } from "@/lib/types";

type Props = {
  graph?: GraphResponse;
  loading?: boolean;
};

function statusColor(status: GraphResponse["nodes"][number]["status"]) {
  switch (status) {
    case "positive":
      return "#7ce7c6";
    case "warning":
      return "#ffb36b";
    case "conflict":
      return "#ff7b31";
    default:
      return "#c6d2dc";
  }
}

export function BuildGraphCanvas({ graph, loading }: Props) {
  const nodes =
    graph?.nodes.map((node) => ({
      id: node.id,
      position: node.position,
      data: { label: node.label },
      style: {
        borderRadius: 18,
        border: `1px solid ${statusColor(node.status)}`,
        background: "rgba(10, 14, 19, 0.94)",
        color: "#eff5fa",
        width: 178,
        fontSize: 12,
        boxShadow: "0 16px 42px rgba(0, 0, 0, 0.28)"
      }
    })) ?? [];

  const edges =
    graph?.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      style: { stroke: statusColor(edge.status), strokeWidth: 1.3 },
      labelStyle: { fill: "#c6d2dc", fontSize: 10 }
    })) ?? [];

  return (
    <section className="panel rounded-[28px] p-4">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
            Graph Reasoning
          </p>
          <h3 className="mt-1 font-display text-2xl text-white">Why this build works</h3>
        </div>
        {graph ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right">
            <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Nodes
            </p>
            <p className="mt-1 font-display text-lg text-white">{graph.nodes.length}</p>
          </div>
        ) : null}
      </div>

      <div className="h-[360px] overflow-hidden rounded-[22px] border border-white/6 bg-[#090d11]">
        {loading ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            Building dependency graph...
          </div>
        ) : graph ? (
          <ReactFlow fitView nodes={nodes} edges={edges} panOnDrag zoomOnScroll>
            <Background color="rgba(255,255,255,0.06)" gap={24} />
            <MiniMap
              pannable
              zoomable
              style={{ background: "rgba(12,18,24,0.9)" }}
              nodeColor={(node) => String(node.style?.borderColor ?? "#c6d2dc")}
            />
            <Controls />
          </ReactFlow>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            Build reasoning will appear once a build is loaded.
          </div>
        )}
      </div>

      {graph?.findings?.length ? (
        <div className="mt-4 space-y-2">
          {graph.findings.slice(0, 3).map((finding) => (
            <div
              key={finding}
              className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2 text-sm text-slate-300"
            >
              {finding}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
