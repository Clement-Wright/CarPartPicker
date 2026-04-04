import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CompareDrawer } from "@/components/planner/compare-drawer";

describe("CompareDrawer", () => {
  it("renders an empty state when fewer than two packages are pinned", () => {
    render(
      <CompareDrawer
        pinnedRecommendations={[
          {
            package_id: "daily_brake_refresh",
            title: "Daily Brake Refresh",
            subtitle: "Keep the stock wheel, sharpen the pedal, stay comfortable",
            description: "A low-drama daily package.",
            score: 86.1,
            score_breakdown: {
              goal_alignment: 0.92,
              fitment_confidence: 0.98,
              cost_efficiency: 0.9,
              safety_preservation: 0.88,
              dependency_simplicity: 0.82,
              conflict_penalty: 0
            },
            matched_goals: ["daily", "braking"],
            required_changes: [],
            conflicts: [],
            cost_band: { min: 520, max: 740 },
            effect_tags: ["daily usability"],
            compatibility_status: "Compatible",
            fitment_confidence: 0.98,
            safety_context: {
              safety_index: 0.88,
              recall_burden: 0.22,
              complaint_burden: 0.34,
              recall_summary: "Demo summary",
              complaint_summary: "Demo complaint summary",
              seed_notice: "Seed mode"
            },
            why_it_matched: ["Goal alignment favors daily, braking."],
            explanation: "Daily Brake Refresh lands well.",
            what_would_change: ["A bigger budget would unlock more aggressive wheel or brake packages."],
            graph_id: "graph"
          }
        ]}
        compare={null}
        loading={false}
        onClearPins={vi.fn()}
      />
    );

    expect(screen.getByText(/Pin at least two packages/i)).toBeInTheDocument();
  });
});
