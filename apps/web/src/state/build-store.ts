"use client";

import { create } from "zustand";

type FreshnessState = {
  fast: boolean;
  heavy: boolean;
};

type SceneCoverage = "idle" | "loading" | "ready";

type BuildStore = {
  dirtySlots: string[];
  pendingRecomputations: string[];
  validationFreshness: FreshnessState;
  sceneCoverage: SceneCoverage;
  activeComparisonBaseline: string;
  setDirtySlots: (slots: string[]) => void;
  setPendingRecomputations: (pending: string[]) => void;
  setValidationFreshness: (freshness: FreshnessState) => void;
  setSceneCoverage: (status: SceneCoverage) => void;
  setActiveComparisonBaseline: (baseline: string) => void;
};

export const useBuildStore = create<BuildStore>((set) => ({
  dirtySlots: [],
  pendingRecomputations: [],
  validationFreshness: { fast: false, heavy: false },
  sceneCoverage: "idle",
  activeComparisonBaseline: "stock",
  setDirtySlots: (dirtySlots) => set({ dirtySlots }),
  setPendingRecomputations: (pendingRecomputations) => set({ pendingRecomputations }),
  setValidationFreshness: (validationFreshness) => set({ validationFreshness }),
  setSceneCoverage: (sceneCoverage) => set({ sceneCoverage }),
  setActiveComparisonBaseline: (activeComparisonBaseline) => set({ activeComparisonBaseline })
}));
