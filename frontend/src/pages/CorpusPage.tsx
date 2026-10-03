import { load } from '../data'
import { fmt } from '../labels'
import { Status, useLoad } from '../load'
import type { UfRow } from '../types'

const ROLES: Record<string, string> = { development: 'desenvolvimento', holdout_pending: 'holdout (pendente)' }

/** Barra em SVG com largura por atributo: compatível com CSP sem `style` inline. */
function Bar({ value, max, role }: { value: number; max: number; role: string }) {
  const width = max > 0 ? Math.max(2, Math.round((value / max) * 160)) : 0
  return (
    <svg width="164" height="12" role="img" aria-label={`${value} editais`}>
      <rect x="0" y="1" width={width} height="10" className={role === 'development' ? 'bar-dev' : 'bar-holdout'} />
    </svg>
  )
}

export function CorpusPage() {
  const corpus = useLoad(load.corpus, 'corpus')
  if (corpus.status !== 'ok') return <Status state={corpus} />
  const c = corpus.data
  const max = Math.max(...c.by_uf.map((r: UfRow) => r.editais))
  return (
    <>
      <h2>Corpus</h2>
      <div className="grid">
        <section className="card" aria-label="Desenvolvimento">
          <h3>Desenvolvimento</h3>
          <p>Snapshot {c.development.snapshot_id}</p>
          <p>{c.development.editais} editais · {c.development.documents} PDFs · {fmt(c.development.pages)} páginas · {fmt(c.development.chunks)} trechos</p>
        </section>
        <section className="card" aria-label="Holdout">
          <h3>Holdout</h3>
          <p>Sem snapshot (não indexado; pendente de aprovação)</p>
          <p>{c.holdout.editais} contratações · {c.holdout.documents} PDFs · {fmt(c.holdout.pages)} páginas</p>
        </section>
      </div>
      <table>
        <caption>Distribuição por região e UF</caption>
        <thead><tr><th>Papel</th><th>Região</th><th>UF</th><th>Editais</th><th></th><th>PDFs</th><th>Páginas</th></tr></thead>
        <tbody>{c.by_uf.map((r) => (
          <tr key={`${r.role}-${r.uf}`}>
            <td>{ROLES[r.role] ?? r.role}</td><td>{r.region}</td><td>{r.uf ?? '—'}</td><td>{r.editais}</td>
            <td><Bar value={r.editais} max={max} role={r.role} /></td><td>{r.documents}</td>
            <td>{r.pages_known ? fmt(r.pages) : 'não informado'}</td>
          </tr>
        ))}</tbody>
      </table>
      <p className="muted">{c.note}</p>
    </>
  )
}
