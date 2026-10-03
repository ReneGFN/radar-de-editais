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
    <span>
      factuais: {h.answerable_all_criteria_true} aprovadas entre {h.answerable_reviewed} com critérios (de {h.answerable_cases});{' '}
      recusas: {h.refusals_all_criteria_true} aprovadas entre {h.refusals_reviewed} (de {h.refusals_cases})
      {!h.rate_available && <span className="badge warn"> taxa não calculada: revisão incompleta</span>}
    </span>
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
      <p>
        Factuais aceitas: <strong>{data.factual_answered[data.a]}</strong> ({data.a}) →{' '}
        <strong>{data.factual_answered[data.b]}</strong> ({data.b}) de {data.factual_answered.of}.
        {' '}Recuperação {data.retrieval_changed ? 'mudou' : 'idêntica'}; holdout {data.holdout_used ? 'usado' : 'não usado'}.
      </p>
      <div className="callout bad">
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
      </div>
      <p className="muted">{data.note}</p>
      <table>
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
      </table>
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
      <h2>Versões</h2>
      <p>
        Variante padrão: <strong>{data.default_variant}</strong> (decisão de {data.decision_record.date}). {data.decision_record.reason}.
      </p>
      <table>
        <caption>Métricas nos 50 casos de desenvolvimento</caption>
        <thead>
          <tr><th>Variante</th><th>Papel</th><th>Factuais aceitas</th><th>Revisão humana</th>
            <th>Tokens de entrada</th><th>Geração (mediana)</th><th>Total (mediana)</th></tr>
        </thead>
        <tbody>
          {data.versions.map((v) => (
            <tr key={v.id}>
              <th scope="row">{v.label}{v.is_default && <span className="badge good"> padrão</span>}</th>
              <td>{ROLES[v.role] ?? v.role}{!v.promoted && <span className="badge"> não promovida</span>}</td>
              <td>{v.factual_answered_of_40}/40</td>
              <td><HumanCell version={v} /></td>
              <td>{fmt(v.input_tokens_total)} <span className="muted">({v.input_tokens_counted_cases} casos)</span></td>
              <td>{fmt(v.generation_ms_median)} ms</td>
              <td>{fmt(v.total_ms_median)} ms</td>
            </tr>
          ))}
        </tbody>
      </table>
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
      <h3>Comparar versões</h3>
      <form className="controls" onSubmit={(e) => e.preventDefault()}>
        <label>Base <select value={a} onChange={(e) => isVariant(e.target.value) && setA(e.target.value)}>
          {VARIANTS.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
        <label>Candidata <select value={b} onChange={(e) => isVariant(e.target.value) && setB(e.target.value)}>
          {VARIANTS.map((v) => <option key={v} value={v}>{v}</option>)}</select></label>
      </form>
      {a === b ? <p>Escolha duas variantes diferentes.</p>
        : comparison.status === 'ok' ? <ComparisonView data={comparison.data} /> : <Status state={comparison} />}
    </>
  )
}
