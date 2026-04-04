import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RecommendationCard } from "@/components/planner/recommendation-card";

describe("RecommendationCard", () => {
  it("shows score, cost band, and tradeoffs", () => {
    const onSelect = vi.fn();

    render(
      <RecommendationCard
        recommendation={{
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
          required_changes: ["Fresh bleed required"],
          conflicts: ["Less outright fade resistance than a full big brake kit."],
          cost_band: { min: 520, max: 740 },
          effect_tags: ["daily usability", "pedal confidence"],
          compatibility_status: "Compatible with supporting changes",
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
        }}
        selected
        pinned={false}
        onSelect={onSelect}
        onTogglePin={vi.fn()}
      />
    );

    expect(screen.getByText(/Daily Brake Refresh/i)).toBeInTheDocument();
    expect(screen.getByText(/\$520 to \$740/i)).toBeInTheDocument();
    expect(screen.getByText(/fade resistance/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Show Graph Reasoning/i }));
    expect(onSelect).toHaveBeenCalled();
  });
});
