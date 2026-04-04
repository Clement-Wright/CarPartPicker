"use client";

import { create } from "zustand";

type CompareState = {
  pinnedIds: string[];
  togglePin: (packageId: string) => void;
  clearPins: () => void;
};

export const useCompareStore = create<CompareState>((set, get) => ({
  pinnedIds: [],
  togglePin: (packageId) => {
    const existing = get().pinnedIds;
    if (existing.includes(packageId)) {
      set({ pinnedIds: existing.filter((id) => id !== packageId) });
      return;
    }

    if (existing.length >= 3) {
      set({ pinnedIds: [...existing.slice(1), packageId] });
      return;
    }

    set({ pinnedIds: [...existing, packageId] });
  },
  clearPins: () => set({ pinnedIds: [] })
}));

