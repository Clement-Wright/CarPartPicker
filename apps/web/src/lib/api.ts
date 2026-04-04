import type {
  BuildDetailResponse,
  BuildDiffResponse,
  BuildDynoSnapshot,
  BuildMetricSnapshot,
  BuildScenarioSnapshot,
  BuildValidationSnapshot,
  DecodedVehicle,
  GraphResponse,
  RenderConfig,
  TargetSpecResponse,
  VehicleDetail,
  VehicleMetricSnapshot,
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
  decodeVin: (vin: string) =>
    request<DecodedVehicle>("/vin/decode", {
      method: "POST",
      body: JSON.stringify({ vin })
    }),
  createBuild: (body: {
    trim_id?: string;
    vin?: string;
    scenario_name?: string;
    target_metrics?: Record<string, number | null | undefined>;
    tolerances?: {
      allow_fabrication: boolean;
      keep_street_legal: boolean;
      protect_daily_comfort: boolean;
    };
  }) =>
    request<BuildDetailResponse>("/builds", {
      method: "POST",
      body: JSON.stringify(body)
    }),
  getBuild: (buildId: string) => request<BuildDetailResponse>(`/builds/${buildId}`),
  patchBuild: (
    buildId: string,
    body: {
      parts?: Record<string, string>;
      scenario_name?: string;
      target_metrics?: Record<string, number | null | undefined>;
      tolerances?: {
        allow_fabrication: boolean;
        keep_street_legal: boolean;
        protect_daily_comfort: boolean;
      };
    }
  ) =>
    request<BuildDetailResponse>(`/builds/${buildId}/parts`, {
      method: "PATCH",
      body: JSON.stringify(body)
    }),
  patchEngine: (
    buildId: string,
    body: {
      engine_family_id?: string;
      label?: string;
      cylinder_count?: number;
      layout?: string;
      bore_mm?: number;
      stroke_mm?: number;
      compression_ratio?: number;
      head_flow_stage?: "stock" | "street" | "race";
      valves_per_cylinder?: number;
      variable_valve_timing?: boolean;
      cam_profile_id?: string;
      induction_type?: "na" | "turbo" | "supercharger";
      boost_psi?: number;
      fuel_type?: "91_octane" | "93_octane" | "e85";
      injector_scale?: "stock" | "upgrade" | "high_flow";
      pump_scale?: "stock" | "upgrade" | "high_flow";
      exhaust_style?: "stock" | "catback" | "turbo_back" | "equal_length";
      tune_bias?: "comfort" | "balanced" | "aggressive";
      rev_limit_rpm?: number;
    }
  ) =>
    request<BuildDetailResponse>(`/builds/${buildId}/engine`, {
      method: "PATCH",
      body: JSON.stringify(body)
    }),
  patchDrivetrain: (
    buildId: string,
    body: {
      label?: string;
      transmission_mode?: "manual" | "automatic";
      gear_ratios?: number[];
      final_drive_ratio?: number;
      driveline_loss_factor?: number;
      differential_bias?: "street_lsd" | "track_lsd" | "open" | "torsen";
      shift_latency_ms?: number;
    }
  ) =>
    request<BuildDetailResponse>(`/builds/${buildId}/drivetrain`, {
      method: "PATCH",
      body: JSON.stringify(body)
    }),
  applyPreset: (buildId: string, presetId: string) =>
    request<{ build: BuildDetailResponse["build"] } & Record<string, unknown>>(
      `/builds/${buildId}/presets/${presetId}/apply`,
      {
        method: "POST"
      }
    ),
  getValidation: (buildId: string, phase: "fast" | "heavy") =>
    request<BuildValidationSnapshot>(`/builds/${buildId}/validate?phase=${phase}`),
  getMetrics: (buildId: string) => request<BuildMetricSnapshot>(`/builds/${buildId}/metrics`),
  getVehicleMetrics: (buildId: string) =>
    request<VehicleMetricSnapshot>(`/builds/${buildId}/vehicle-metrics`),
  getDyno: (buildId: string) => request<BuildDynoSnapshot>(`/builds/${buildId}/dyno`),
  getScenario: (buildId: string, name?: string) =>
    request<BuildScenarioSnapshot>(
      `/builds/${buildId}/scenario${name ? `?name=${encodeURIComponent(name)}` : ""}`
    ),
  getRenderConfig: (buildId: string) => request<RenderConfig>(`/builds/${buildId}/render-config`),
  getGraph: (buildId: string) => request<GraphResponse>(`/builds/${buildId}/graph`),
  getDiff: (buildId: string, against: string) =>
    request<BuildDiffResponse>(`/builds/${buildId}/diff?against=${encodeURIComponent(against)}`),
  cloneBuild: (buildId: string) =>
    request<{ build_id: string; source_build_id: string }>(`/builds/${buildId}/clone`, {
      method: "POST"
    }),
  targetSpecSearch: (text: string) =>
    request<TargetSpecResponse>("/search/target-spec", {
      method: "POST",
      body: JSON.stringify({ text })
    }),
  importSeedCatalog: (scope: "seed_engine_families" | "seed_parts" | "seed_all" = "seed_all") =>
    request<{
      import_batch: {
        import_batch_id: string;
      };
      imported_entities: Record<string, number>;
      notes: string[];
    }>("/catalog/import/seed", {
      method: "POST",
      body: JSON.stringify({ source_system: "seed_catalog", import_scope: scope })
    })
};
