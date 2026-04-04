import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { QueryWorkbench } from "@/components/planner/query-workbench";

describe("QueryWorkbench", () => {
  it("renders parsed chips and runs the planner", () => {
    const onRunQuery = vi.fn();

    render(
      <QueryWorkbench
        trims={[
          {
            trim_id: "gr86_2022_base",
            label: "2022 Toyota GR86 Base",
            stock_wheel_diameter: 17,
            platform: "zn8"
          }
        ]}
        selectedTrimId="gr86_2022_base"
        onTrimChange={vi.fn()}
        vinInput="JF1ZNAA10N9700001"
        onVinInputChange={vi.fn()}
        onDecodeVin={vi.fn()}
        queryText="Best daily brake + wheel upgrade under $2,500"
        onQueryTextChange={vi.fn()}
        budget={2500}
        onBudgetChange={vi.fn()}
        selectedGoals={["daily", "braking"]}
        onGoalToggle={vi.fn()}
        wheelDiameter={17}
        onWheelDiameterChange={vi.fn()}
        keepCurrentWheels={false}
        onKeepCurrentWheelsChange={vi.fn()}
        onRunQuery={onRunQuery}
        onLoadScenario={vi.fn()}
        parsedQuery={{
          goals: ["daily", "braking"],
          budget_max: 2500,
          hard_constraints: [],
          current_setup: { wheel_diameter: 17, keep_current_wheels: false, notes: [] },
          confidence: 0.92,
          extracted_terms: ["daily", "brake", "17-inch"]
        }}
        isBusy={false}
      />
    );

    expect(screen.getByText(/Parsed Constraint Chips/i)).toBeInTheDocument();
    expect(screen.getAllByText(/under \$2,500/i).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: /Run Build Graph/i }));
    expect(onRunQuery).toHaveBeenCalled();
  });
});
