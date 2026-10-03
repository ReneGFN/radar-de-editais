import { useEffect, useState } from 'react'
import { CasePage, CasesPage } from './pages/CasesPage'
import { CorpusPage } from './pages/CorpusPage'
import { QualityPage } from './pages/QualityPage'
import { VersionsPage } from './pages/VersionsPage'

const TABS = [['versoes', 'Versões'], ['casos', 'Casos'], ['qualidade', 'Qualidade'], ['corpus', 'Corpus']] as const
const CASE_ROUTE = /^#\/casos\/((?:pilot|independent)-\d{2})$/

function useHash() {
  const [hash, setHash] = useState(() => window.location.hash || '#/versoes')
  useEffect(() => {
    const onChange = () => setHash(window.location.hash || '#/versoes')
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return hash
}

export function App() {
  const hash = useHash()
  const caseMatch = CASE_ROUTE.exec(hash)
  const tab = caseMatch ? 'casos' : (hash.replace('#/', '') || 'versoes')
  let page
  if (caseMatch) page = <CasePage id={caseMatch[1]} />
  else if (tab === 'casos') page = <CasesPage />
  else if (tab === 'qualidade') page = <QualityPage />
  else if (tab === 'corpus') page = <CorpusPage />
  else page = <VersionsPage />
  return (
    <>
      <header>
        <h1>Radar de Editais — avaliação</h1>
        <p className="muted">Laboratório de RAG para editais de informática do PNCP. Resultados de desenvolvimento; o holdout ainda não foi executado.</p>
        <nav aria-label="Telas">
          {TABS.map(([id, label]) => (
            <a key={id} href={`#/${id}`} aria-current={tab === id ? 'page' : undefined}>{label}</a>
          ))}
        </nav>
      </header>
      <main>{page}</main>
      <footer className="muted">Somente dados públicos: sem PDFs, texto extraído, respostas brutas ou notas de revisão.</footer>
    </>
  )
}
