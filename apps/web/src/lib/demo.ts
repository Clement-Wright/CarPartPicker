export const demoScenarios = [
  {
    id: "daily-brake",
    label: "Daily Brake + Wheel",
    trimId: "gr86_2022_base",
    query: "Best daily brake + wheel upgrade under $2,500",
    goals: ["daily", "braking"],
    budget: 2500,
    wheel: 17
  },
  {
    id: "winter-vs-grip",
    label: "Winter vs Grip",
    trimId: "brz_2023_premium",
    query: "Show me a winter build with room to compare against a budget grip setup under $2,200",
    goals: ["winter"],
    budget: 2200,
    wheel: 17
  },
  {
    id: "bbk-conflict",
    label: "BBK Conflict",
    trimId: "gr86_2022_base",
    query: "Give me the best street brake package while staying on my current 17-inch wheels",
    goals: ["braking", "daily"],
    budget: 2600,
    wheel: 17
  }
] as const;
