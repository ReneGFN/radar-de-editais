export type DocumentSelection = { pncp_id: string; document_sequence: number }
export type Edital = { pncp_id: string; agency: string; uf: string | null; object: string; official_url: string }
export type Candidate = { pncp_id: string; agency: string; uf: string | null; document_sequence: number; page: number; url: string }
export type Source = Candidate & { index: number; quote: string }
export type Reply = { status: 'answered' | 'refused' | 'insufficient_evidence' | 'needs_clarification' | 'discovery_only' | 'no_candidates';
  answer: string; claims: { text: string; source_indices: number[] }[]; sources: Source[]; candidates: Candidate[]; confidence?: { level: 'unavailable' | 'review_required'; label: string; reasons: string[]; calibrated: false } }
export type Health = { generation_enabled: boolean }
declare const __CHAT_ENABLED__: boolean
export const chatEnabled = () => typeof __CHAT_ENABLED__ === 'undefined' || __CHAT_ENABLED__

export async function chatRequest<T>(path: 'health' | 'editais' | 'ask', body?: { question: string; pncp_id?: string; documents?: DocumentSelection[] }): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 90000)
  try {
    const response = await fetch(`/chat/${path}`, { method: body ? 'POST' : 'GET', credentials: 'omit',
      signal: controller.signal, headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json', 'X-Radar-Chat': '1' } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}) })
    if (!response.ok) {
      if (response.status === 429) throw new Error('Há uma consulta em andamento ou o intervalo de 35 segundos ainda não terminou. Aguarde e envie novamente.')
      if (response.status === 422) throw new Error('Confira a pergunta e o edital selecionado antes de enviar novamente.')
      throw new Error('O serviço de perguntas está indisponível. Confira se ele está iniciado e tente novamente.')
    }
    return await response.json() as T
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw new Error('A consulta demorou mais que o esperado. Ela pode continuar no servidor; aguarde antes de tentar novamente.')
    if (error instanceof TypeError) throw new Error('Não foi possível conectar ao serviço. Confira a conexão local e tente novamente.')
    throw error
  } finally { clearTimeout(timer) }
}
