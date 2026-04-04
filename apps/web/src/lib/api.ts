import type {
  BuildRecommendation,
  CompareResponse,
  DecodedVehicle,
  GraphResponse,
  ParsedBuildQuery,
  VehicleDetail,
  VehicleSummary
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  listTrims: () => request<VehicleSummary[]>("/catalog/trims"),
  getVehicle: (trimId: string) => request<VehicleDetail>(`/vehicle/${trimId}`),
  parseQuery: (body: { text: string; mode: "build_path"; vehicle_context?: { trim_id?: string } }) =>
    request<ParsedBuildQuery>("/query/parse", {
      method: "POST",
      body: JSON.stringify(body)
    }),
  recommendBuilds: (body: {
    trim_id: string;
    query: ParsedBuildQuery;
    selected_goals: string[];
    budget_max?: number | null;
    current_setup?: {
      wheel_diameter?: number | null;
      keep_current_wheels: boolean;
      notes: string[];
    };
  }) =>
    request<BuildRecommendation[]>("/recommend/builds", {
      method: "POST",
      body: JSON.stringify(body)
    }),
  compareBuilds: (body: { trim_id: string; package_ids: string[] }) =>
    request<CompareResponse>("/compare", {
      method: "POST",
      body: JSON.stringify(body)
    }),
  getGraph: (graphId: string) => request<GraphResponse>(`/graph/${graphId}`),
  decodeVin: (vin: string) =>
    request<DecodedVehicle>("/vin/decode", {
      method: "POST",
      body: JSON.stringify({ vin })
    })
};
