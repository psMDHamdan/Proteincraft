/**
 * Type-safe API client for the ProteinCraft backend.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────

export interface RankedSequence {
  sequence: string;
  mutations_from_input: string[];
  esm_score: number;
  stability_proxy: number;
  diversity_score: number;
  heuristic_score: number;
  rank: number;
}

export interface PropertyResult {
  instability_index: number;
  isoelectric_point: number;
  aromaticity: number;
  molecular_weight: number;
  gravy: number;
  secondary_structure_fraction: { helix: number; turn: number; sheet: number };
}

export interface DesignResponse {
  job_id: string;
  status: string;
  input_sequence: string | null;
  designed_sequences: RankedSequence[];
  properties: PropertyResult | null;
  gemini_explanation: string | null;
  created_at: string;
}

export interface PredictResponse {
  sequence: string;
  length: number;
  properties: PropertyResult;
  esm2_score: number;
  stability_assessment: "stable" | "borderline" | "unstable";
}

export interface StructureResponse {
  job_id: string | null;
  sequence: string;
  pdb_string: string;
  mean_plddt: number;
  min_plddt: number;
  max_plddt: number;
  confidence_note: string;
}

export interface DesignRequest {
  sequence?: string;
  fasta_content?: string;
  mutation_list?: string[];
  target_antigen?: string;
  desired_function?: string;
  top_k?: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// ── Public API ────────────────────────────────────────────────────────────

export const api = {
  designSequence: (req: DesignRequest) =>
    post<DesignResponse>("/design-sequence", req),

  predictProperties: (sequence: string) =>
    post<PredictResponse>("/predict-properties", { sequence }),

  predictStructure: (sequence: string, job_id?: string) =>
    post<StructureResponse>("/structure", { sequence, job_id }),

  getProtein: (id: string) => get<Record<string, unknown>>(`/protein/${id}`),

  health: () => get<{ status: string; version: string }>("/health"),
};
