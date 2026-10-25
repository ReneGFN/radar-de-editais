import { useState } from 'react'
import { isVariant, load } from '../data'
import { changeLabel, fmt, humanLabel, kindLabel, stateLabel } from '../labels'
import { Status, useLoad } from '../load'
import { VARIANTS, type Comparison, type Version, type VariantId } from '../types'

function HumanCell({ version }: { version: Version }) {
  const h = version.human
  if (!h) return <span className="muted">não avaliado</span>
  const total = h.answerable_reviewed + h.refusals_reviewed
  if (total === 0) return <span className="muted">não avaliado</span>
  return (
    <div className="human-results">
      <p><strong>Factuais</strong><span>{h.answerable_all_criteria_true} aprovadas entre {h.answerable_reviewed} com critérios (de {h.answerable_cases})</span></p>
      <p><strong>Recusas</strong><span>{h.refusals_all_criteria_true} aprovadas entre {h.refusals_reviewed} (de {h.refusals_cases})</span></p>
      {!h.rate_available && <div className="review-warning"><strong>Taxa não calculada</strong><span>Revisão incompleta</span></div>}
    </div>
  )
}

const ROLES: Record<string, string> = {
  default: 'padrão', experimental_preserved: 'experimental (preservada)',
  experimental_safety_variant_preserved: 'experimental de segurança (preservada)',
}

function ComparisonView({ data }: { data: Comparison }) {
  const changed = data.cases.filter((c) => c.technical_change !== 'unchanged' || ['regression', 'improvement'].includes(c.human_change))
  return (
    <section aria-label="Resultado da comparação">
      <div className="comparison-scoreboard">
        <div><span className="eyebrow">BASE · {data.a}</span><strong>{data.factual_answered[data.a]}<small>/{data.factual_answered.of}</small></strong><span>Factuais aceitas</span></div>
        <span className="comparison-arrow" aria-hidden="true">→</span>
        <div><span className="eyebrow">CANDIDATA · {data.b}</span><strong>{data.factual_answered[data.b]}<small>/{data.factual_answered.of}</small></strong><span>Factuais aceitas</span></div>
        <div className="comparison-context"><span>Recuperação <strong>{data.retrieval_changed ? 'mudou' : 'idêntica'}</strong></span><span>Holdout <strong>{data.holdout_used ? 'usado' : 'não usado'}</strong></span><small>Estado técnico; confira a revisão humana.</small></div>
      </div>
      <div className="comparison-findings"><div className="callout bad">
        <h3>Regressões ({data.regressions.length})</h3>
        {data.regressions.length === 0 ? <p>Nenhuma.</p> : (
          <ul>{data.regressions.map((id) => <li key={id}><a href={`#/casos/${id}`}>{id}</a></li>)}</ul>
        )}
      </div>
      <div className="callout good">
        <h3>Melhoras ({data.improvements.length})</h3>
        {data.improvements.length === 0 ? <p>Nenhuma.</p> : (
          <ul>{data.improvements.map((id) => <li key={id}><a href={`#/casos/${id}`}>{id}</a></li>)}</ul>
        )}
      </div></div>
      <p className="muted comparison-note">{data.note}</p>
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Tabela com rolagem horizontal"><table>
        <caption>Casos com mudança ({changed.length} de {data.cases.length})</caption>
        <thead><tr><th>Caso</th><th>Tipo</th><th>{data.a}</th><th>{data.b}</th><th>Mudança técnica</th><th>Mudança humana</th></tr></thead>
        <tbody>
          {changed.map((c) => (
            <tr key={c.case_id} className={c.technical_change === 'regression' || c.human_change === 'regression' ? 'row-bad' : undefined}>
              <td><a href={`#/casos/${c.case_id}`}>{c.case_id}</a></td>
              <td>{kindLabel(c.kind)}</td>
              <td>{stateLabel(c.state_a)} · {humanLabel(c.human_a)}</td>
              <td>{stateLabel(c.state_b)} · {humanLabel(c.human_b)}</td>
              <td>{changeLabel(c.technical_change)}</td>
              <td>{changeLabel(c.human_change)}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
    </section>
  )
}

export function VersionsPage() {
  const versions = useLoad(load.versions, 'versions')
  const [a, setA] = useState<VariantId>('alias_items')
  const [b, setB] = useState<VariantId>('alias_items_v3')
  const comparison = useLoad(() => load.compare(a, b), `${a}|${b}`)
  if (versions.status !== 'ok') return <Status state={versions} />
  const { data } = versions
  return (
    <>
      <div className="page-heading"><p className="eyebrow">LABORATÓRIO DE AVALIAÇÃO</p><h2>Versões</h2><p className="muted">Compare os resultados. Entenda cada mudança.</p></div>
      <p>
        Variante padrão: <strong>{data.default_variant}</strong> (decisão de {data.decision_record.date}). {data.decision_record.reason}.
      </p>
      <section aria-label="Métricas nos 50 casos de desenvolvimento" className="version-grid">
        {data.versions.map(v => <article key={v.id} className={`version-card ${v.is_default ? 'is-default' : ''}`}>
          <div className="version-heading"><h3>{v.id}<small>{v.is_default ? 'Versão padrão' : v.id === 'alias_items_v3' ? 'Experimento de segurança' : 'Versão experimental'}</small></h3><span className={`badge ${v.is_default ? 'good' : ''}`}>{v.is_default ? 'Padrão' : 'Experimental'}</span></div>
          <p className="muted version-role">{ROLES[v.role] ?? v.role}{!v.promoted && <> · <span>não promovida</span></>}</p>
          <div className="metric-value">{v.factual_answered_of_40}<span>/40</span></div><p className="muted">Factuais aceitas pelo estado técnico</p>
          <dl className="version-metrics"><div><dt>Geração · mediana</dt><dd>{fmt(v.generation_ms_median)} ms</dd></div><div><dt>Total · mediana</dt><dd>{fmt(v.total_ms_median)} ms</dd></div><div><dt>Tokens de entrada</dt><dd>{fmt(v.input_tokens_total)} <small>({v.input_tokens_counted_cases} casos)</small></dd></div></dl>
          <div className="human-summary"><h4>Conferência humana</h4><HumanCell version={v} /></div>
        </article>)}
      </section>
      <ul className="muted">{data.metric_caveats.map((c) => <li key={c}>{c}</li>)}</ul>
      {data.versions.filter((v) => v.findings).map((v) => (
        <section key={v.id} aria-label={`Achados humanos de ${v.id}`}>
          <h3>Achados humanos — {v.id}</h3>
          <div className="grid">
            <div className="callout good"><h4>Corrigido</h4><ul>{v.findings!.fixed.map((x) => <li key={x}>{x}</li>)}</ul></div>
            <div className="callout warn"><h4>Barrado (erro seguro)</h4><ul>{v.findings!.blocked_safely_still_wrong.map((x) => <li key={x}>{x}</li>)}</ul></div>
            <div className="callout bad"><h4>Ainda falha</h4><ul>{v.findings!.still_failing.map((x) => <li key={x}>{x}</li>)}</ul></div>
            <div className="callout bad"><h4>Regressões vs padrão</h4><ul>{v.findings!.regressions_vs_default.map((x) => <li key={x}>{x}</li>)}</ul></div>
          </div>
        </section>
      ))}
      <div className="comparison-toolbar"><div><p className="eyebrow">COMPARAÇÃO DIRETA</p><h3>Comparar versões</h3><p className="muted">Escolha a base e veja o que mudou na candidata.</p></div>
      <form className="controls comparison-selectors" onSubmit={(e) => e.preventDefault()}>
        <label>Base <select value={a} onChange={(e) => isVariant(e.target.value) && setA(e.target.value)}>
          {VARIANTS.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
        <label>Candidata <select value={b} onChange={(e) => isVariant(e.target.value) && setB(e.target.value)}>
          {VARIANTS.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
      </form>
      </div>
      {a === b ? <p>Escolha duas variantes diferentes.</p>
        : comparison.status === 'ok' ? <ComparisonView data={comparison.data} /> : <Status state={comparison} />}
    </>
  )
}
