import { lazy, Suspense, useCallback, useEffect, useState } from 'react'
import { chatEnabled, type Reply, type DocumentSelection } from '../chat'
import { safePncpUrl } from '../data'

export type ExploreEdital = { pncp_id: string; agency: string; uf: string | null; object: string; documents: { sequence: number; url: string }[] }
const Scene = lazy(() => import('../explore/Scene'))
const normalize = (value: string) => value.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('pt-BR')

export default function ExplorePage({ reply, initialBasket = [], onBasket }: { reply: Reply | null; initialBasket?: DocumentSelection[]; onBasket?: (basket: DocumentSelection[]) => void }) {
  const [catalog, setCatalog] = useState<ExploreEdital[]>([])
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('')
  const [uf, setUf] = useState('')
  const [selected, setSelected] = useState('')
  const [basket, setBasket] = useState<DocumentSelection[]>(initialBasket)
  useEffect(() => { onBasket?.(basket) }, [basket, onBasket])
  const [basketNotice, setBasketNotice] = useState('')
  const [activeFile, setActiveFile] = useState('')
  const [view, setView] = useState<'3d' | 'list'>('3d')
  useEffect(() => {
    let disposed = false
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 15000)
    fetch(chatEnabled() ? '/chat/explore' : 'data/explore.json', { signal: controller.signal, credentials: 'omit' })
      .then(async response => { if (!response.ok) throw new Error(); return response.json() })
      .then((data: ExploreEdital[]) => { setCatalog(data); setSelected(data.find(e => reply?.sources.some(s => s.pncp_id === e.pncp_id))?.pncp_id ?? data[0]?.pncp_id ?? '') })
      .catch(() => { if (!disposed) setError('Não foi possível carregar os editais. Confira a API e recarregue esta tela.') })
      .finally(() => clearTimeout(timer))
    return () => { disposed = true; controller.abort(); clearTimeout(timer) }
  }, [])
  const visible = catalog.filter(e => (!uf || e.uf === uf) && normalize(`${e.agency} ${e.object} ${e.pncp_id}`).includes(normalize(filter)))
  useEffect(() => {
    if (visible.length && !visible.some(e => e.pncp_id === selected)) { setSelected(visible[0].pncp_id); setActiveFile('') }
  }, [filter, uf, catalog, selected])
  const chooseState = (state: string) => { setUf(state); const first = catalog.find(e => (e.uf ?? '—') === state && normalize(`${e.agency} ${e.object} ${e.pncp_id}`).includes(normalize(filter))); setSelected(first?.pncp_id ?? ''); setActiveFile('') }
  const current = visible.find(e => e.pncp_id === selected)
  const sources = reply?.sources ?? []
  const highlighted = [...new Set(sources.map(s => s.pncp_id))]
  const choose = useCallback((id: string) => setSelected(id), [])
  const inspectDocument = useCallback((id: string, sequence: number) => {
    setSelected(id); setActiveFile(`${id}:${sequence}`)
    requestAnimationFrame(() => document.getElementById(`atlas-document-${id}-${sequence}`)?.scrollIntoView?.({ block: 'nearest', behavior: 'auto' }))
  }, [])
  const placeDocument = (id: string, sequence: number) => {
    setBasketNotice('')
    if (basket.length >= 5 && !basket.some(d => d.pncp_id === id && d.document_sequence === sequence)) { setBasketNotice('A mesa aceita até cinco PDFs. Remova um para adicionar outro.'); return }
    setBasket(previous => { if (previous.some(d => d.pncp_id === id && d.document_sequence === sequence)) return previous; if (previous.length >= 5) return previous; return [...previous,{pncp_id:id,document_sequence:sequence}] })
  }
  const overview = () => { setUf(''); setFilter(''); setSelected(''); setActiveFile('') }
  return <section className="explore-page" aria-labelledby="explore-title">
    <div className="page-heading"><p className="eyebrow">ATLAS DOCUMENTAL · BASE PÚBLICA</p><h2 id="explore-title">Explore as fontes</h2><p className="muted">Do conjunto de editais à página que sustenta uma resposta.</p></div>
    <div className="explore-toolbar">
      <label className="explore-search"><span className="sr-only">Buscar no explorador</span><input type="search" name="atlas-search" autoComplete="off" placeholder="Buscar órgão, compra ou PNCP…" value={filter} onChange={e => setFilter(e.target.value)} /></label>
      <label>UF <select name="atlas-uf" value={uf} onChange={e => setUf(e.target.value)}><option value="">Todas</option>{[...new Set(catalog.map(e => e.uf).filter(Boolean))].sort().map(state => <option key={state!} value={state!}>{state}</option>)}</select></label>
      <div role="group" aria-label="Visualização"><button aria-pressed={view === '3d'} onClick={() => setView('3d')}>3D</button><button aria-pressed={view === 'list'} onClick={() => setView('list')}>Lista</button></div>
    </div>
    {error && <p role="alert" className="error">{error}</p>}
    {!error && !catalog.length && <p role="status">Carregando catálogo…</p>}
    <div className="atlas-summary"><span><strong>{visible.length}</strong> editais</span><span><strong>{visible.reduce((n, e) => n + e.documents.length, 0)}</strong> PDFs</span><span className="atlas-legend"><i className="selected-dot" />Selecionado <i className="source-dot" />Fonte da última resposta</span></div>
    <div className="atlas-layout">
      <div className="atlas-space">
        {view === '3d' && visible.length > 0 && <Suspense fallback={<p role="status">Preparando cenário 3D…</p>}><Scene editais={visible} selected={selected} highlighted={highlighted} onSelect={choose} onState={chooseState} onOverview={overview} onPlaced={placeDocument} basket={basket} onDocument={inspectDocument} documentSequence={activeFile.startsWith(`${selected}:`) ? Number(activeFile.split(':').at(-1)) : undefined} /></Suspense>}
        {!visible.length && catalog.length > 0 && <p className="callout">Nenhum edital corresponde ao filtro.</p>}
        <div className={`atlas-catalog ${view === 'list' ? 'atlas-full-list' : ''}`} aria-label="Editais acessíveis por teclado">
          {visible.map(e => <button key={e.pncp_id} aria-pressed={selected === e.pncp_id} onClick={() => choose(e.pncp_id)} className={highlighted.includes(e.pncp_id) ? 'atlas-source-item' : ''}><span className="atlas-uf">{e.uf ?? '—'}</span><span>{e.agency}<small>{e.documents.length} PDFs · {e.pncp_id}</small></span></button>)}
        </div>
      </div>
      <aside className="atlas-detail" aria-label="Detalhes do edital selecionado" aria-live="polite">
        {current ? <><p className="eyebrow">{current.uf} · EDITAL SELECIONADO</p><h3>{current.agency}</h3><p>{current.object || 'Objeto não informado no catálogo.'}</p><p className="muted source-id" translate="no">{current.pncp_id}</p>
          {chatEnabled() && <button className="primary-button" onClick={() => { window.dispatchEvent(new CustomEvent('radar-select-edital', { detail: current.pncp_id })); window.location.hash = '/chat' }}>Perguntar sobre este edital</button>}
          <h4>Documentos oficiais</h4>{current.documents.map(d => { const url = safePncpUrl(d.url); const evidence = sources.filter(s => s.pncp_id === current.pncp_id && s.document_sequence === d.sequence); return <div key={d.sequence} id={`atlas-document-${current.pncp_id}-${d.sequence}`} className={`atlas-document ${activeFile === `${current.pncp_id}:${d.sequence}` ? 'atlas-document-active' : ''}`}><span className="atlas-document-state">{activeFile === `${current.pncp_id}:${d.sequence}` ? 'PDF selecionado para conferência' : 'Documento do conjunto'}</span><strong>PDF · Arquivo {d.sequence}</strong><button type="button" className="atlas-file-select" aria-pressed={activeFile === `${current.pncp_id}:${d.sequence}`} onClick={() => inspectDocument(current.pncp_id, d.sequence)}>Selecionar PDF {d.sequence} para a mesa</button>{url && <a href={url} target="_blank" rel="noopener noreferrer">Abrir documento ↗</a>}{evidence.map(s => <details key={s.index}><summary>Fonte [{s.index}] · página {s.page}</summary><blockquote>{s.quote}</blockquote><a href={`${url}#page=${s.page}`} target="_blank" rel="noopener noreferrer">Conferir página {s.page}</a></details>)}</div> })}
          {!sources.some(s => s.pncp_id === current.pncp_id) && <p className="muted">Nenhuma fonte da última resposta neste edital. Faça uma pergunta no chat para visualizar as evidências aqui.</p>}
        </> : <p className="muted">Selecione um edital no cenário ou na lista para conferir os documentos.</p>}
      </aside>
    </div>
    <section className="atlas-basket" aria-label="Documentos na mesa"><div><p className="eyebrow">MESA DE CONFERÊNCIA · {basket.length}/5 PDFs</p><h3>Seleção para perguntar</h3><p>Reúna documentos de um ou mais editais. A pergunta usará somente esses PDFs.</p></div><div className="atlas-basket-files">{basket.map(d => <span key={`${d.pncp_id}:${d.document_sequence}`}><strong>{catalog.find(e => e.pncp_id === d.pncp_id)?.agency}</strong><small>PDF {d.document_sequence} · {d.pncp_id}</small><button aria-label={`Remover PDF ${d.document_sequence} de ${d.pncp_id}`} onClick={() => setBasket(previous => previous.filter(p => p !== d))}>×</button></span>)}{!basket.length && <p className="muted">Leve um PDF à mesa pelo leque ou pelo botão.</p>}</div>{basketNotice && <p role="status">{basketNotice}</p>}<button className="primary-button" disabled={!basket.length || !chatEnabled()} onClick={() => { window.dispatchEvent(new CustomEvent('radar-select-documents',{detail:basket})); window.location.hash='/chat' }}>Perguntar sobre os {basket.length} PDFs da mesa</button></section>
    <p className="muted atlas-note">Cada plataforma reúne uma UF; cada pasta representa um edital e suas folhas representam PDFs. Segure e puxe para levantar; solte para recolher. Abrir PDFs em leque mantém os documentos disponíveis para seleção. Ordem alfabética, sem escala geográfica ou similaridade semântica. A cor dourada indica uso como fonte, não certeza da resposta. A lista oferece as mesmas ações do 3D.</p>
  </section>
}
