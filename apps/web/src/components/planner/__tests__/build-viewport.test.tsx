import { cleanup, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BuildViewport } from "@/components/planner/build-viewport";

vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: { children: ReactNode }) => <div data-testid="canvas">{children}</div>
}));

vi.mock("@react-three/drei", () => ({
  OrbitControls: () => <div data-testid="orbit-controls" />,
  useGLTF: () => ({ scene: { clone: () => ({}) } })
}));

afterEach(() => {
  cleanup();
});

describe("BuildViewport", () => {
  it("explains when a build is specs-only", () => {
    render(
      <BuildViewport
        scene={{
          build_id: "build-1",
          build_hash: "hash-1",
          source_mode: "seed",
          items: [],
          omitted_items: [
            {
              part_id: "tune_stock",
              subsystem: "tune",
              asset_mode: "catalog_only",
              hidden_reason: "This part is intentionally omitted from the 3D scene."
            }
          ],
          highlights: [],
          summary: { renderable_count: 0, exact_count: 0, proxy_count: 0, omitted_count: 1 }
        }}
      />
    );

    expect(screen.getByText("3D Is Optional")).toBeInTheDocument();
    expect(screen.getByText("Specs only 1")).toBeInTheDocument();
  });

  it("shows omitted item reasons alongside renderable coverage", () => {
    render(
      <BuildViewport
        scene={{
          build_id: "build-1",
          build_hash: "hash-1",
          source_mode: "seed",
          items: [
            {
              part_id: "brakes_stock_17",
              instance_id: "brakes_stock_17",
              subsystem: "brakes",
              asset_mode: "proxy_from_dimensions",
              proxy_geometry: { kind: "disc", color: "#ff7b31", radius_mm: 160, thickness_mm: 32 },
              dimensions: { length_mm: 320, width_mm: 32, height_mm: 320 },
              transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
              anchor: { slot: "brakes", zone: "brakes" },
              hidden_reason: null
            }
          ],
          omitted_items: [
            {
              part_id: "tune_stage1",
              subsystem: "tune",
              asset_mode: "catalog_only",
              hidden_reason: "Scene omitted while specs remain active."
            }
          ],
          highlights: [],
          summary: { renderable_count: 1, exact_count: 0, proxy_count: 1, omitted_count: 1 }
        }}
      />
    );

    expect(screen.getByText("Scene Coverage")).toBeInTheDocument();
    expect(screen.getByText("Scene omitted while specs remain active.")).toBeInTheDocument();
  });
});
