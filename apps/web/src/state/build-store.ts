"use client";

import { create } from "zustand";

type FreshnessState = {
  fast: boolean;
  heavy: boolean;
};

type AssetReadiness = "idle" | "loading" | "ready";

type BuildStore = {
  dirtySlots: string[];
  pendingRecomputations: string[];
  validationFreshness: FreshnessState;
  assetReadiness: AssetReadiness;
  activeComparisonBaseline: string;
  setDirtySlots: (slots: string[]) => void;
  setPendingRecomputations: (pending: string[]) => void;
  setValidationFreshness: (freshness: FreshnessState) => void;
  setAssetReadiness: (status: AssetReadiness) => void;
  setActiveComparisonBaseline: (baseline: string) => void;
};

export const useBuildStore = create<BuildStore>((set) => ({
  dirtySlots: [],
  pendingRecomputations: [],
  validationFreshness: { fast: false, heavy: false },
  assetReadiness: "idle",
  activeComparisonBaseline: "stock",
  setDirtySlots: (dirtySlots) => set({ dirtySlots }),
  setPendingRecomputations: (pendingRecomputations) => set({ pendingRecomputations }),
  setValidationFreshness: (validationFreshness) => set({ validationFreshness }),
  setAssetReadiness: (assetReadiness) => set({ assetReadiness }),
  setActiveComparisonBaseline: (activeComparisonBaseline) => set({ activeComparisonBaseline })
}));
