import { VARIANTS, type CaseDetail, type CaseSummary, type Comparison, type Corpus, type Quality, type VariantId,
  type Versions } from './types'

declare const __DATA_SOURCE__: 'api' | 'static'

const CASE_ID = /^(pilot|independent)-\d{2}$/
const PNCP_URL = /^https:\/\/pncp\.gov\.br\/[A-Za-z0-9/._~%#=-]+$/

export function source(): 'api' | 'static' {
  return typeof __DATA_SOURCE__ === 'undefined' ? 'static' : __DATA_SOURCE__
}

/** Só caminhos fixos: nenhum texto do usuário entra na URL sem validação. */
export function path(kind: string, a?: string, b?: string): string {
  const api = source() === 'api'
  switch (kind) {
    case 'versions': return api ? '/api/versions' : 'data/versions.json'
    case 'cases': return api ? '/api/cases' : 'data/cases.json'
    case 'quality': return api ? '/api/quality' : 'data/quality.json'
    case 'corpus': return api ? '/api/corpus' : 'data/corpus.json'
    case 'case':
      if (!a || !CASE_ID.test(a)) throw new Error('Caso inválido')
      return api ? `/api/cases/${a}` : `data/case-${a}.json`
    case 'compare':
      if (!isVariant(a) || !isVariant(b) || a === b) throw new Error('Comparação inválida')
      return api ? `/api/versions/${a}/compare/${b}` : `data/compare-${a}-${b}.json`
    default: throw new Error('Recurso desconhecido')
  }
}

export function isVariant(value: unknown): value is VariantId {
  return typeof value === 'string' && (VARIANTS as string[]).includes(value)
}

/** Link externo só é renderizado se for HTTPS do PNCP; caso contrário vira texto. */
export function safePncpUrl(url: string): string | null {
  return PNCP_URL.test(url) ? url : null
}

async function get<T>(url: string): Promise<T> {
  const response = await fetch(url, { credentials: 'omit', headers: { Accept: 'application/json' } })
  if (!response.ok) throw new Error(`Falha ao carregar ${url} (HTTP ${response.status})`)
  return (await response.json()) as T
}

export const load = {
  versions: () => get<Versions>(path('versions')),
  compare: (a: VariantId, b: VariantId) => get<Comparison>(path('compare', a, b)),
  cases: () => get<CaseSummary[]>(path('cases')),
  case: (id: string) => get<CaseDetail>(path('case', id)),
  quality: () => get<Quality>(path('quality')),
  corpus: () => get<Corpus>(path('corpus')),
}
