// Rótulos em português para estados técnicos e humanos. Valor desconhecido aparece como está.
const STATES: Record<string, string> = {
  answered: 'respondeu', refused: 'recusou', insufficient_evidence: 'evidência insuficiente',
  rejected: 'barrada pelo validador', not_run: 'não executado',
}
const HUMAN: Record<string, string> = {
  human_reviewed: 'revisado', partial: 'revisão parcial', pending: 'não avaliado', not_evaluated: 'não avaliado',
}
const CHANGES: Record<string, string> = {
  regression: 'regressão', improvement: 'melhora', changed: 'mudou', unchanged: 'igual', not_comparable: 'sem revisão',
}
const KINDS: Record<string, string> = { answerable: 'factual', out_of_scope: 'recusa' }

export const stateLabel = (s: string) => STATES[s] ?? s
export const humanLabel = (s: string) => HUMAN[s] ?? s
export const changeLabel = (s: string) => CHANGES[s] ?? s
export const kindLabel = (s: string) => KINDS[s] ?? s

export function passLabel(value: boolean | null | undefined): string {
  if (value === true) return 'aprovado'
  if (value === false) return 'reprovado'
  return 'não avaliado'
}

export const fmt = (n: number | null | undefined, digits = 0) =>
  n === null || n === undefined ? '—' : n.toLocaleString('pt-BR', { maximumFractionDigits: digits })
