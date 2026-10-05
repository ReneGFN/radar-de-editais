import { load } from '../data'
import { fmt } from '../labels'
import { Status, useLoad } from '../load'

export function QualityPage() {
  const quality = useLoad(load.quality, 'quality')
  if (quality.status !== 'ok') return <Status state={quality} />
  const q = quality.data
  return (
    <>
      <div className="page-heading"><p className="eyebrow">CRITÉRIOS DE CONFIANÇA</p><h2>Qualidade</h2><p className="muted">O que já foi verificado e o que ainda precisa passar.</p></div>
      <div className={q.decision === 'blocked' ? 'callout bad' : 'callout good'}>
        <p>Gate: <strong>{q.decision === 'blocked' ? 'bloqueado' : q.decision}</strong>. Meta: {fmt(q.target * 100)}%.</p>
        <p>Situação da meta: {q.target_status}</p>
        <p>Variante padrão: {q.default_variant}</p>
      </div>
      <div className="grid">
        <section className="callout good" aria-label="Critérios atendidos">
          <h3>Já atendido</h3><ul>{q.criteria_met.map((x) => <li key={x}>{x}</li>)}</ul>
        </section>
        <section className="callout bad" aria-label="Bloqueios">
          <h3>Bloqueios</h3><ul>{q.blockers.map((x) => <li key={x}>{x}</li>)}</ul>
        </section>
      </div>
      <h3>Holdout</h3>
      <p>{q.holdout.cases} casos; {q.holdout.cases_pending_user_approval} pendentes de aprovação; executado: {q.holdout.executed ? 'sim' : 'não'}.</p>
      <h4>Requisitos antes de alegar a meta</h4>
      <ol>{q.holdout_requirements.map((x) => <li key={x}>{x}</li>)}</ol>
      <p className="muted">{q.development_set_note}</p>
      <p className="muted">Motivos registrados no gate anterior: {q.previous_gate_reasons.join(', ')}</p>
      <p><strong>Garantia:</strong> {q.guarantee}</p>
    </>
  )
}
