import { useState } from 'react'
import { load, safePncpUrl } from '../data'
import { humanLabel, kindLabel, passLabel, stateLabel } from '../labels'
import { Status, useLoad } from '../load'
import { VARIANTS, type CaseDetail } from '../types'

const CRITERIA: Record<string, string> = {
  correct: 'correta', complete: 'completa', supported: 'apoiada pela fonte', no_mixing: 'sem misturar itens/unidades/prazos',
  refusal_appropriate: 'recusa apropriada', no_invented_facts: 'sem fatos inventados',
  no_invented_citations: 'sem citações inventadas', no_secret_disclosure: 'sem expor segredos',
}

function passClass(value: boolean | null) {
  return value === true ? 'badge good' : value === false ? 'badge bad' : 'badge'
}

export function CasesPage() {
  const cases = useLoad(load.cases, 'cases')
  const [kind, setKind] = useState('all')
  if (cases.status !== 'ok') return <Status state={cases} />
  const rows = cases.data.filter((c) => kind === 'all' || c.kind === kind)
  return (
    <>
      <div className="page-heading"><p className="eyebrow">EVIDÊNCIAS E REVISÃO</p><h2>Casos de desenvolvimento</h2><p className="muted">Explore cada pergunta, resultado e fonte.</p></div>
      <p className="muted">Só referências aprovadas. O holdout não aparece aqui enquanto estiver pendente de aprovação.</p>
      <form className="controls" onSubmit={(e) => e.preventDefault()}>
        <label>Tipo <select value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="all">todos</option><option value="answerable">factual</option><option value="out_of_scope">recusa</option>
        </select></label>
      </form>
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Tabela com rolagem horizontal"><table>
        <caption>{rows.length} casos</caption>
        <thead><tr><th>Caso</th><th>Conjunto</th><th>Tipo</th>
          {VARIANTS.map((v) => <th key={v}>{v}</th>)}</tr></thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id}>
              <td><a href={`#/casos/${c.id}`}>{c.id}</a></td>
              <td>{c.set}</td>
              <td>{kindLabel(c.kind)}{c.category ? ` · ${c.category}` : ''}</td>
              {VARIANTS.map((v) => (
                <td key={v}><div className="case-result"><span className="technical-state">{stateLabel(c.states[v])}</span>
                  <span className={passClass(c.human_pass[v])}>{c.human[v] === 'human_reviewed' ? passLabel(c.human_pass[v]) : humanLabel(c.human[v])}</span>
                </div></td>
              ))}
            </tr>
          ))}
        </tbody>
      </table></div>
    </>
  )
}

function Detail({ data }: { data: CaseDetail }) {
  return (
    <>
      <h2>{data.id}</h2>
      <dl>
        <dt>Conjunto</dt><dd>{data.set}</dd>
        <dt>Tipo</dt><dd>{kindLabel(data.kind)}{data.category ? ` · ${data.category}` : ''}</dd>
        <dt>Contratação PNCP</dt><dd>{data.pncp_id}</dd>
        <dt>Pergunta</dt><dd className="prose">{data.question}</dd>
        <dt>Gabarito aprovado</dt><dd className="prose">{data.expected_answer ?? '—'}</dd>
      </dl>
      <h3>Fontes oficiais</h3>
      {data.sources.length === 0 ? <p>Sem fonte (caso de recusa).</p> : (
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Tabela com rolagem horizontal"><table>
          <thead><tr><th>Arquivo (hash)</th><th>Documento</th><th>Página</th><th>Link oficial</th></tr></thead>
          <tbody>{data.sources.map((s, i) => {
            const url = safePncpUrl(s.url)
            return (
              <tr key={`${s.document_sha256}-${s.page}-${i}`}>
                <td><code title={s.document_sha256}>{s.document_sha256.slice(0, 16)}…</code></td>
                <td>{s.document_sequence ?? '—'}</td>
                <td>{s.page}</td>
                <td>{url ? <a href={url} target="_blank" rel="noopener noreferrer">abrir no PNCP</a> : 'link inválido'}</td>
              </tr>
            )
          })}</tbody>
        </table></div>
      )}
      <h3>Resultado por variante</h3>
      <p className="muted">Estado técnico (automático) e revisão humana são coisas diferentes; citação íntegra não significa resposta correta.</p>
      <div className="grid">
        {VARIANTS.map((v) => {
          const s = data.variants[v]
          return (
            <section key={v} className="card" aria-label={`Resultado de ${v}`}>
              <h4>{v}</h4>
              <p>Estado técnico: {stateLabel(s.technical_state)}</p>
              <p>Revisão humana: <span className={passClass(s.human_pass)}>
                {s.human_status === 'human_reviewed' ? passLabel(s.human_pass) : humanLabel(s.human_status)}</span></p>
              {s.criteria ? (
                <ul>{Object.entries(s.criteria).map(([k, value]) => (
                  <li key={k}>{CRITERIA[k] ?? k}: {value === null ? 'não avaliado' : value ? 'sim' : 'não'}</li>
                ))}</ul>
              ) : <p className="muted">Sem critérios humanos registrados.</p>}
              {s.error_tags.length > 0 && <p>Etiquetas de erro: {s.error_tags.join(', ')}</p>}
            </section>
          )
        })}
      </div>
    </>
  )
}

export function CasePage({ id }: { id: string }) {
  const detail = useLoad(() => load.case(id), id)
  return (
    <>
      <p><a href="#/casos">← todos os casos</a></p>
      {detail.status === 'ok' ? <Detail data={detail.data} /> : <Status state={detail} />}
    </>
  )
}
