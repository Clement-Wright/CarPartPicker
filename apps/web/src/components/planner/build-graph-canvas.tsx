"use client";

import "@xyflow/react/dist/style.css";

import {
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  ReactFlow,
  useEdgesState,
  useNodesState,
  MarkerType
} from "@xyflow/react";
import { useEffect, useState } from "react";

import type { GraphResponse } from "@/lib/types";

const statusStyle = {
  info: {
    border: "1px solid rgba(148, 163, 184, 0.28)",
    background: "rgba(148, 163, 184, 0.12)"
  },
  positive: {
    border: "1px solid rgba(124, 231, 198, 0.34)",
    background: "rgba(124, 231, 198, 0.12)"
  },
  warning: {
    border: "1px solid rgba(255, 181, 77, 0.34)",
    background: "rgba(255, 181, 77, 0.12)"
  },
  conflict: {
    border: "1px solid rgba(248, 113, 113, 0.34)",
    background: "rgba(248, 113, 113, 0.12)"
  }
} as const;

type BuildGraphCanvasProps = {
  graph?: GraphResponse | null;
  loading: boolean;
};

export function BuildGraphCanvas({ graph, loading }: BuildGraphCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [activeNode, setActiveNode] = useState<string | null>(null);

  useEffect(() => {
    if (!graph) {
      setNodes([]);
      setEdges([]);
      return;
    }

    setNodes(
      graph.nodes.map((node) => ({
        id: node.id,
        position: node.position,
        data: {
          label: (
            <div>
              <p className="font-display text-[11px] uppercase tracking-[0.18em] text-slate-400">
                {node.kind}
              </p>
              <p className="mt-1 text-sm font-medium text-white">{node.label}</p>
              <p className="mt-2 text-xs text-slate-300">{node.description}</p>
            </div>
          )
        },
        style: {
          width: 220,
          borderRadius: 20,
          color: "white",
          ...statusStyle[node.status]
        }
      }))
    );

    setEdges(
      graph.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        markerEnd: { type: MarkerType.ArrowClosed },
        labelStyle: { fill: "#cbd5e1", fontSize: 11, letterSpacing: "0.08em" },
        style: {
          stroke:
            edge.status === "positive"
              ? "#7ce7c6"
              : edge.status === "warning"
                ? "#ffb54d"
                : edge.status === "conflict"
                  ? "#f87171"
                  : "#94a3b8",
          strokeWidth: 1.6
        }
      }))
    );
  }, [graph, setEdges, setNodes]);

  if (loading) {
    return (
      <div className="panel flex h-[420px] items-center justify-center rounded-[24px] p-4 text-sm text-slate-400">
        Building graph reasoning...
      </div>
    );
  }

  if (!graph) {
    return (
      <div className="panel flex h-[420px] items-center justify-center rounded-[24px] p-4 text-sm text-slate-400">
        Select a recommendation to visualize its dependency chain.
      </div>
    );
  }

  const inspector = graph.nodes.find((node) => node.id === activeNode) ?? graph.nodes[0];

  return (
    <div className="panel rounded-[24px] p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
            Graph Reasoning
          </p>
          <h2 className="mt-2 font-display text-2xl text-white">
            Fitment + tradeoff graph
          </h2>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right">
          <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">
            Nodes
          </p>
          <p className="mt-1 font-display text-lg text-white">{graph.nodes.length}</p>
        </div>
      </div>

      <div className="mt-4 h-[420px] overflow-hidden rounded-[24px] border border-white/8 bg-graphite-900/70">
        <ReactFlow
          fitView
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => setActiveNode(node.id)}
        >
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) => {
              if (graph.highlights.includes(node.id)) {
                return "#ff7b31";
              }
              return "#7c8b99";
            }}
          />
          <Controls />
          <Background gap={24} color="rgba(255,255,255,0.05)" />
        </ReactFlow>
      </div>

      <div className="mt-4 panel-muted rounded-[24px] p-4">
        <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
          Node Inspector
        </p>
        <p className="mt-2 font-display text-xl text-white">{inspector.label}</p>
        <p className="mt-2 text-sm text-slate-300">{inspector.description}</p>
      </div>
    </div>
  );
}
