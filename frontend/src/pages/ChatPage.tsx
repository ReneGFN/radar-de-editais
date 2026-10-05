import { useEffect, useRef, useState, type FormEvent } from 'react'
import { chatEnabled, chatRequest, type Edital, type Health, type Reply, type DocumentSelection } from '../chat'
import { safePncpUrl } from '../data'

type Turn = { id: number; question: string; scope: string; pncp?: string; result?: Reply; error?: string }
const LABELS: Record<Reply['status'], string> = {
  answered: 'Resposta com fontes', refused: 'Pedido não atendido', insufficient_evidence: 'Evidência insuficiente',
  needs_clarification: 'Precisamos de mais detalhes', discovery_only: 'Editais candidatos', no_candidates: 'Nenhum candidato encontrado',
}

export function ChatPage({ onReply }: { onReply?: (reply: Reply) => void }) {
  const [editais, setEditais] = useState<Edital[]>([])
  const [health, setHealth] = useState<Health | null>(null)
  const [connectionError, setConnectionError] = useState('')
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [documents, setDocuments] = useState<DocumentSelection[]>([])
  const [selected, setSelected] = useState('')
  const [question, setQuestion] = useState('')
  const [validation, setValidation] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [busy, setBusy] = useState(false)
  const busyRef = useRef(false)
  const counter = useRef(0)
  const input = useRef<HTMLTextAreaElement>(null)
  const scopePanel = useRef<HTMLDetailsElement>(null)
  const picker = useRef<HTMLDivElement>(null)
  const drag = useRef<{ x: number; y: number; left: number; top: number } | null>(null)

  function movePicker(left: number, top: number) {
    if (!picker.current) return
    const bounds = picker.current.getBoundingClientRect()
    picker.current.style.position = 'fixed'
    picker.current.style.left = `${Math.max(12, Math.min(left, window.innerWidth - bounds.width - 12))}px`
    picker.current.style.top = `${Math.max(12, Math.min(top, window.innerHeight - bounds.height - 12))}px`
    picker.current.style.bottom = 'auto'
    picker.current.style.transform = 'none'
  }

  useEffect(() => {
    const fit = () => {
      if (scopePanel.current?.open && picker.current?.style.position === 'fixed') {
        const bounds = picker.current.getBoundingClientRect()
        movePicker(bounds.left, bounds.top)
      }
    }
    window.addEventListener('resize', fit)
    return () => window.removeEventListener('resize', fit)
  }, [])

  useEffect(() => {
    if (input.current) {
      input.current.style.height = '80px'
      input.current.style.height = `${Math.min(200, Math.max(80, input.current.scrollHeight))}px`
    }
  }, [question])

  async function connect() {
    if (!chatEnabled()) { setLoading(false); return }
    setLoading(true); setConnectionError('')
    try {
      const [catalog, status] = await Promise.all([chatRequest<Edital[]>('editais'), chatRequest<Health>('health')])
      setEditais(catalog); setHealth(status)
    } catch { setConnectionError('O serviço de perguntas não está conectado. Inicie o serviço local e tente conectar novamente.'); setHealth(null) }
    finally { setLoading(false) }
  }
  useEffect(() => { void connect() }, [])

  useEffect(() => {
    const select = (event: Event) => { const id = (event as CustomEvent<string>).detail; if (editais.some(e => e.pncp_id === id)) { setSelected(id); setDocuments([]); input.current?.focus() } }
    const selectDocuments = (event: Event) => { const docs = (event as CustomEvent<DocumentSelection[]>).detail; if (Array.isArray(docs) && docs.length > 0 && docs.length <= 5 && docs.every(d => editais.some(e => e.pncp_id === d.pncp_id))) { setDocuments(docs); setSelected(''); input.current?.focus() } }
    window.addEventListener('radar-select-documents',selectDocuments)
    window.addEventListener('radar-select-edital', select)
    return () => { window.removeEventListener('radar-select-edital', select); window.removeEventListener('radar-select-documents',selectDocuments) }
  }, [editais])

  const normalize = (text: string) => text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('pt-BR')
  const options = editais.filter(e => normalize(`${e.agency} ${e.uf} ${e.object}`).includes(normalize(filter)) || e.pncp_id === selected)
  const selectedEdital = editais.find(e => e.pncp_id === selected)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (busyRef.current) return
    if (!question.trim()) { setValidation('Escreva sua pergunta antes de enviar.'); input.current?.focus(); return }
    if (question.length > 2000) { setValidation('Use até 2.000 caracteres.'); input.current?.focus(); return }
    if (!health) { setValidation('Conecte o serviço de perguntas antes de enviar.'); return }
    setValidation(''); busyRef.current = true; setBusy(true)
    const turn: Turn = { id: ++counter.current, question: question.trim(), pncp: selected || undefined, scope: documents.length ? `Mesa · ${documents.length} PDFs selecionados` : selectedEdital ? `${selectedEdital.agency} · ${selectedEdital.uf ?? ''}` : 'Busca em toda a base' }
    setTurns(previous => [...previous.slice(-19), turn]); setQuestion('')
    try {
      const result = await chatRequest<Reply>('ask', { question: turn.question, ...(documents.length ? {documents} : selected ? { pncp_id: selected } : {}) })
      setTurns(previous => previous.map(t => t.id === turn.id ? { ...t, result } : t))
      onReply?.(result)
    } catch (error) {
      setTurns(previous => previous.map(t => t.id === turn.id ? { ...t, error: error instanceof Error ? error.message : 'Não foi possível concluir a consulta.' } : t))
    } finally { busyRef.current = false; setBusy(false) }
  }

  function choose(pncp: string, prompt: string) {
    if (!editais.some(e => e.pncp_id === pncp)) return
    setDocuments([]); setSelected(pncp); setQuestion(prompt); setValidation('')
    if (scopePanel.current) scopePanel.current.open = true
    input.current?.focus(); input.current?.scrollIntoView({ block: 'center', behavior: 'auto' })
  }
  function reveal(id: number, index: number) {
    const element = document.getElementById(`chat-source-${id}-${index}`) as HTMLDetailsElement | null
    if (element) { element.open = true; element.scrollIntoView({ block: 'center', behavior: 'auto' }); element.querySelector('summary')?.focus() }
  }

  return <section className={`chat-page ${turns.length ? 'has-conversation' : ''}`} aria-labelledby="chat-title">
    <div className="chat-intro"><p className="eyebrow">DOCUMENTOS PÚBLICOS · FONTES VERIFICÁVEIS</p><h2 id="chat-title">Perguntar sobre editais</h2>
      <p className="muted">Encontre a informação. Confira no documento.</p></div>
    {!chatEnabled() ? <div className="callout">O chatbot funciona no ambiente local com o serviço de perguntas. Nesta publicação, você pode consultar o painel de avaliação.</div> : <>
      <div className="chat-layout">
        <div className="chat-workspace">
          <form onSubmit={submit} className="chat-composer">
            <label htmlFor="chat-question" className="sr-only">Sua pergunta</label>
            <textarea ref={input} id="chat-question" name="question" autoComplete="off" rows={2} maxLength={2000}
              value={question} disabled={busy} onChange={e => { setQuestion(e.target.value); setValidation('') }}
              aria-invalid={!!validation} aria-describedby="question-help question-error"
              placeholder="O que você quer saber sobre os editais?…" />
            <div className="composer-bottom"><span id="question-help" className="muted">{question.length.toLocaleString('pt-BR')}/2.000 caracteres</span>
              <button className="primary-button" type="submit" disabled={busy}><span aria-hidden="true">↑</span><span>{busy ? 'Buscando resposta…' : 'Enviar pergunta'}</span></button></div>
            <p id="question-error" className="error" role="alert">{validation}</p>
            <p className="muted chat-hint">Não sabe o edital? Inclua o órgão, município ou detalhes da compra. Cada pergunta é independente.</p>
          </form>
          {turns.length === 0 && <div className="chat-empty"><h3 className="sr-only">Sugestões de perguntas</h3>
            {[['Encontrar monitores', 'Quais editais incluem monitores?'], ['Consultar garantia', 'Qual a garantia do computador em Uniflor?'], ['Conferir entrega', 'Qual prazo de entrega?']].map(([label, example]) =>
              <button className="example-button" key={label} onClick={() => { setQuestion(example); input.current?.focus() }}>{label}</button>)}
          </div>}
          <div className="conversation" role="log" aria-label="Conversa" aria-live="polite" aria-busy={busy}>
            {turns.map(turn => <article className="chat-turn" key={turn.id}>
              <div className="user-question"><span className="eyebrow">VOCÊ · {turn.scope}</span><p>{turn.question}</p></div>
              {turn.error ? <div className="callout bad" role="alert"><p>{turn.error}</p><button disabled={busy} onClick={() => { setSelected(turn.pncp ?? ''); setQuestion(turn.question); input.current?.focus() }}>Editar e tentar novamente</button></div> :
                !turn.result ? <p className="muted" role="status">Consultando os documentos…</p> : <div className="assistant-reply">
                  <h3>{LABELS[turn.result.status]}</h3>
                  {turn.result.confidence && <details className="evidence-confidence"><summary>{turn.result.confidence.label}</summary><ul>{turn.result.confidence.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul><p className="muted">Sem probabilidade de acerto calibrada.</p></details>}
                  {turn.result.claims.length > 0 ? <><ul className="answer-claims">{turn.result.claims.map((claim, i) => <li key={i}>{claim.text}{' '}
                    {claim.source_indices.map(index => <button className="source-reference" key={index} onClick={() => reveal(turn.id, index)} aria-label={`Ver fonte ${index}`}>[{index}]</button>)}</li>)}</ul>
                    <p className="muted">Confira os trechos abaixo: a fonte existe, mas a interpretação pode conter erros.</p></> : <p>{turn.result.answer}</p>}
                  {turn.result.sources.length > 0 && <section aria-label="Fontes da resposta" className="chat-sources"><h4>Confira no documento</h4><p className="muted">A página indicada é a posição no PDF; pode diferir da numeração impressa.</p>
                    {turn.result.sources.map(source => { const link = safePncpUrl(source.url); return <details key={source.index} id={`chat-source-${turn.id}-${source.index}`}>
                      <summary><strong>[{source.index}] {source.agency} · {source.uf}</strong><span>Arquivo {source.document_sequence} · página {source.page}</span></summary>
                      <p className="muted source-id" translate="no">PNCP {source.pncp_id}</p><blockquote tabIndex={0} aria-label={`Trecho literal da fonte ${source.index}`}>{source.quote}</blockquote>
                      {link ? <a href={`${link}#page=${source.page}`} target="_blank" rel="noopener noreferrer">Abrir PDF oficial · página {source.page}</a> : <p>Link de fonte inválido.</p>}
                    </details> })}</section>}
                  {['needs_clarification', 'discovery_only'].includes(turn.result.status) && turn.result.candidates.length > 0 && <section className="candidate-list" aria-label="Editais candidatos">
                    <h4>Contratações encontradas</h4><p className="muted">Candidatos de busca; esta lista pode não incluir todas as opções.</p>
                    {turn.result.candidates.map(candidate => <div key={candidate.pncp_id} className="candidate-row"><div><strong>{candidate.agency}</strong><span className="muted">{candidate.uf} · Arquivo {candidate.document_sequence} · página {candidate.page}</span><span className="source-id" translate="no">{candidate.pncp_id}</span></div>
                      <button disabled={busy} onClick={() => choose(candidate.pncp_id, turn.question)}>Consultar este edital</button></div>)}
                  </section>}
                </div>}
            </article>)}
          </div>
        </div>
        {documents.length > 0 && <div className="chat-document-scope"><strong>Consulta limitada aos PDFs da mesa</strong>{documents.map(d => <span key={`${d.pncp_id}:${d.document_sequence}`}>{editais.find(e => e.pncp_id === d.pncp_id)?.agency} · PDF {d.document_sequence}<button type="button" disabled={busy} aria-label={`Remover PDF ${d.document_sequence} de ${d.pncp_id}`} onClick={() => setDocuments(previous => previous.filter(p => p !== d))}>×</button></span>)}<button type="button" disabled={busy} onClick={() => setDocuments([])}>Buscar em toda a base</button></div>}
        <details ref={scopePanel} className="chat-scope" aria-label="Escopo da consulta" onToggle={event => {
          if (event.currentTarget.open && picker.current?.style.position === 'fixed') { const bounds = picker.current.getBoundingClientRect(); movePicker(bounds.left, bounds.top) }
          if (!event.currentTarget.open) drag.current = null
        }} onKeyDown={event => { if (event.key === 'Escape' && scopePanel.current) { scopePanel.current.open = false; scopePanel.current.querySelector('summary')?.focus() } }}>
          <summary><span className="scope-symbol" aria-hidden="true">◎</span><span>{documents.length ? `Mesa · ${documents.length} PDFs selecionados` : selectedEdital ? `${selectedEdital.agency} · ${selectedEdital.uf ?? ''}` : 'Buscar em toda a base'}</span><span className="scope-action" aria-hidden="true">⌄</span></summary>
          <div ref={picker} className="scope-picker">
            <div className="scope-picker-header">
              <button type="button" className="scope-drag-handle" aria-label="Mover painel de escopo; use as setas do teclado" onPointerDown={event => {
                if (event.button !== 0 || !picker.current) return
                const bounds = picker.current.getBoundingClientRect()
                drag.current = { x: event.clientX, y: event.clientY, left: bounds.left, top: bounds.top }
                event.currentTarget.setPointerCapture(event.pointerId)
              }} onPointerMove={event => {
                if (drag.current) movePicker(drag.current.left + event.clientX - drag.current.x, drag.current.top + event.clientY - drag.current.y)
              }} onPointerUp={() => { drag.current = null }} onPointerCancel={() => { drag.current = null }} onKeyDown={event => {
                const offset: Record<string, [number, number]> = { ArrowLeft: [-20, 0], ArrowRight: [20, 0], ArrowUp: [0, -20], ArrowDown: [0, 20] }
                if (offset[event.key] && picker.current) { event.preventDefault(); const bounds = picker.current.getBoundingClientRect(); movePicker(bounds.left + offset[event.key][0], bounds.top + offset[event.key][1]) }
              }}><span aria-hidden="true">⠿</span><span>Onde vamos buscar?<small>Arraste para mover</small></span></button>
              <button type="button" className="scope-close" aria-label="Restaurar posição do painel" onClick={() => picker.current?.removeAttribute('style')}>↺</button>
              <button type="button" className="scope-close" aria-label="Fechar seleção de escopo" onClick={() => { if (scopePanel.current) { scopePanel.current.open = false; scopePanel.current.querySelector('summary')?.focus() } }}>×</button>
            </div><p className="muted">Explore a base ou escolha uma contratação.</p>
            <label htmlFor="edital-filter" className="sr-only">Filtrar editais</label><input id="edital-filter" name="edital-filter" autoComplete="off" type="search" value={filter} onChange={e => setFilter(e.target.value)} placeholder="Buscar órgão, estado ou compra…" disabled={busy} />
            <div className="scope-options" role="group" aria-label="Edital (opcional)">
              <button type="button" className="scope-option" aria-pressed={!selected && !documents.length} disabled={busy || loading} onClick={() => { setDocuments([]); setSelected(''); if (scopePanel.current) scopePanel.current.open = false }}><span className="scope-option-icon" aria-hidden="true">◎</span><span><strong>Toda a base de conhecimento</strong><small>Encontrar o edital a partir da sua pergunta</small></span><span aria-hidden="true">{!selected && !documents.length ? '✓' : ''}</span></button>
              {options.map(e => <button type="button" key={e.pncp_id} className="scope-option" aria-pressed={selected === e.pncp_id} disabled={busy || loading} onClick={() => { setDocuments([]); setSelected(e.pncp_id); if (scopePanel.current) scopePanel.current.open = false; input.current?.focus() }}><span className="scope-option-icon" aria-hidden="true">{e.uf}</span><span><strong>{e.agency}</strong><small>{e.object}</small><small translate="no">{e.pncp_id}</small></span><span aria-hidden="true">{selected === e.pncp_id ? '✓' : ''}</span></button>)}
              {!options.length && <p className="muted scope-no-results">Nenhum edital corresponde à busca.</p>}
            </div>
          </div>
        </details>
        <div className="connection-state"><span role="status">{loading ? 'Conectando ao serviço…' : health ? `${editais.length} ${editais.length === 1 ? 'contratação disponível' : 'contratações disponíveis'}` : 'Serviço desconectado'}</span>
          {connectionError && <p className="error">{connectionError}</p>}
          {!loading && !health && <button onClick={() => void connect()}>Tentar conectar</button>}
          {health && !health.generation_enabled && <p className="callout warn">A busca está disponível. A geração de respostas está desativada neste serviço.</p>}
        </div>
      </div>
    </>}
  </section>
}
