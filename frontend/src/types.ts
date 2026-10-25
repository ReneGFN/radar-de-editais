// Tipos espelham os esquemas `extra='forbid'` de backend/src/radar/api.py.
export type VariantId = 'alias_items' | 'alias_items_v2' | 'alias_items_v3'
export const VARIANTS: VariantId[] = ['alias_items', 'alias_items_v2', 'alias_items_v3']

export interface Human {
  answerable_reviewed: number
  answerable_cases: number
  answerable_all_criteria_true: number
  refusals_reviewed: number
  refusals_cases: number
  refusals_all_criteria_true: number
  rate_available: boolean
  error_tag_counts: Record<string, number>
}

export interface Findings {
  fixed: string[]
  blocked_safely_still_wrong: string[]
  still_failing: string[]
  regressions_vs_default: string[]
}

export interface Version {
  id: VariantId
  label: string
  role: string
  status: string
  is_default: boolean
  promoted: boolean
  factual_answered_of_40: number
  input_tokens_total: number
  input_tokens_counted_cases: number
  generation_ms_median: number
  total_ms_median: number
  human: Human | null
  findings: Findings | null
}

export interface Versions {
  default_variant: VariantId
  decision_record: { date: string; basis: string[]; reason: string }
  metric_caveats: string[]
  versions: Version[]
}

export interface Metrics {
  input_tokens: number | null
  output_tokens: number | null
  generation_ms: number | null
  total_ms: number | null
}

export interface CompareCase {
  case_id: string
  kind: string
  category: string | null
  state_a: string
  state_b: string
  technical_change: string
  human_a: string
  human_b: string
  human_pass_a: boolean | null
  human_pass_b: boolean | null
  human_change: string
  metrics_a: Metrics | null
  metrics_b: Metrics | null
}

export interface Comparison {
  a: VariantId
  b: VariantId
  retrieval_changed: boolean
  holdout_used: boolean
  factual_answered: Record<string, number>
  aggregate: Record<string, Record<string, { n: number; median: number | null; total: number | null }>>
  regressions: string[]
  improvements: string[]
  cases: CompareCase[]
  note: string
}

export interface CaseSummary {
  id: string
  set: string
  kind: string
  category: string | null
  pncp_id: string
  states: Record<string, string>
  human: Record<string, string>
  human_pass: Record<string, boolean | null>
}

export interface Source { document_sha256: string; document_sequence: number | null; page: number; url: string }

export interface VariantState {
  technical_state: string
  human_status: string
  human_pass: boolean | null
  criteria: Record<string, boolean | null> | null
  error_tags: string[]
}

export interface CaseDetail {
  id: string
  set: string
  kind: string
  category: string | null
  pncp_id: string
  question: string
  expected_answer: string | null
  sources: Source[]
  variants: Record<string, VariantState>
}

export interface Quality {
  decision: string
  target: number
  target_status: string
  default_variant: VariantId
  criteria_met: string[]
  blockers: string[]
  previous_gate_reasons: string[]
  holdout: { cases: number; cases_pending_user_approval: number; status: string; executed: boolean }
  holdout_requirements: string[]
  development_set_note: string
  guarantee: string
}

export interface UfRow {
  role: string
  region: string
  uf: string | null
  editais: number
  documents: number
  pages: number | null
  pages_known: boolean
}

export interface Corpus {
  development: { snapshot_id: string | null; editais: number; documents: number; pages: number; chunks?: number | null }
  holdout: { snapshot_id: string | null; editais: number; documents: number; pages: number; status?: string | null }
  by_uf: UfRow[]
  editais: { pncp_id: string; uf: string | null; region: string; role: string; documents: number; pages: number | null;
    official_url: string | null; document_urls: string[] }[]
  note: string
}
