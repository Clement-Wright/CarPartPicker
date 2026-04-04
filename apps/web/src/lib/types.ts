export type VehicleSummary = {
  trim_id: string;
  label: string;
  stock_wheel_diameter: number;
  platform: string;
};

export type CurrentSetup = {
  wheel_diameter?: number | null;
  keep_current_wheels: boolean;
  notes: string[];
};

export type ParsedBuildQuery = {
  goals: string[];
  budget_max?: number | null;
  hard_constraints: string[];
  current_setup?: CurrentSetup | null;
  confidence: number;
  extracted_terms: string[];
};

export type VehicleDetail = {
  trim: {
    trim_id: string;
    platform: string;
    year: number;
    make: string;
    model: string;
    trim: string;
    stock_wheel_diameter: number;
    stock_tire: string;
    safety_index: number;
    recall_burden: number;
    complaint_burden: number;
    recall_summary: string;
    complaint_summary: string;
    utility_note: string;
    mod_potential: number;
    drivetrain: string;
    transmission: string;
    body_style: string;
  };
  safety_context: {
    safety_index: number;
    recall_burden: number;
    complaint_burden: number;
    recall_summary: string;
    complaint_summary: string;
    seed_notice: string;
  };
};

export type ScoreBreakdown = {
  goal_alignment: number;
  fitment_confidence: number;
  cost_efficiency: number;
  safety_preservation: number;
  dependency_simplicity: number;
  conflict_penalty: number;
};

export type BuildRecommendation = {
  package_id: string;
  title: string;
  subtitle: string;
  description: string;
  score: number;
  score_breakdown: ScoreBreakdown;
  matched_goals: string[];
  required_changes: string[];
  conflicts: string[];
  cost_band: {
    min: number;
    max: number;
  };
  effect_tags: string[];
  compatibility_status: string;
  fitment_confidence: number;
  safety_context: VehicleDetail["safety_context"];
  why_it_matched: string[];
  explanation: string;
  what_would_change: string[];
  graph_id: string;
};

export type GraphNode = {
  id: string;
  label: string;
  kind: string;
  status: "info" | "positive" | "warning" | "conflict";
  description: string;
  position: { x: number; y: number };
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  status: "info" | "positive" | "warning" | "conflict";
};

export type GraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlights: string[];
  eliminated_options: {
    package_id: string;
    title: string;
    reason: string;
  }[];
};

export type CompareResponse = {
  axes: string[];
  package_summaries: {
    package_id: string;
    title: string;
    subtitle: string;
    axes: Record<string, number>;
    cost_band: {
      min: number;
      max: number;
    };
    fitment_confidence: number;
    effect_tags: string[];
    tradeoffs: string[];
  }[];
  deltas: Record<string, Record<string, number>>;
  explanation_facts: {
    summary: string;
    baseline: string;
    challenger: string;
  };
};

export type DecodedVehicle = {
  vin: string;
  trim_id?: string | null;
  year?: number | null;
  make?: string | null;
  model?: string | null;
  trim?: string | null;
  source: string;
  cache_hit: boolean;
};

