import { lazy, Suspense, useEffect, useState } from 'react'
import { CasePage, CasesPage } from './pages/CasesPage'
import { CorpusPage } from './pages/CorpusPage'
import { QualityPage } from './pages/QualityPage'
import { VersionsPage } from './pages/VersionsPage'
import { ChatPage } from './pages/ChatPage'

import type { Reply, DocumentSelection } from './chat'
const ExplorePage = lazy(() => import('./pages/ExplorePage'))

const TABS = [['chat', 'Perguntar'], ['versoes', 'Versões'], ['casos', 'Casos'], ['qualidade', 'Qualidade'], ['corpus', 'Corpus'], ['explorar', 'Explorar']] as const
const CASE_ROUTE = /^#\/casos\/((?:pilot|independent)-\d{2})$/

function useHash() {
  const [hash, setHash] = useState(() => window.location.hash || '#/chat')
  useEffect(() => {
    const onChange = () => setHash(window.location.hash || '#/chat')
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return hash
}

export function App() {
  const hash = useHash()
  const [deskDocuments, setDeskDocuments] = useState<DocumentSelection[]>([])
  const [lastReply, setLastReply] = useState<Reply | null>(null)
  const caseMatch = CASE_ROUTE.exec(hash)
  const tab = caseMatch ? 'casos' : (hash.replace('#/', '') || 'chat')
  let page
  if (caseMatch) page = <CasePage id={caseMatch[1]} />
  else if (tab === 'casos') page = <CasesPage />
  else if (tab === 'qualidade') page = <QualityPage />
  else if (tab === 'explorar') page = <Suspense fallback={<p role="status">Abrindo explorador…</p>}><ExplorePage reply={lastReply} initialBasket={deskDocuments} onBasket={setDeskDocuments} /></Suspense>
  else if (tab === 'corpus') page = <CorpusPage />
  else if (tab !== 'chat') page = <VersionsPage />
  return (
    <div className={`app-shell moon-shell ${tab === 'chat' ? 'chat-shell' : 'dashboard-shell'}`}>
      <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus() }}>Ir para o conteúdo</a>
      <header>
        <h1>Radar de Editais</h1>
        <p className="muted">Consulte editais de informática e confira cada resposta no documento original.</p>
        <nav aria-label="Telas">
          {TABS.map(([id, label]) => (
            <a key={id} href={`#/${id}`} aria-current={tab === id ? 'page' : undefined}>{label}</a>
          ))}
        </nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        <div hidden={tab !== 'chat'}><ChatPage onReply={setLastReply} /></div>
        {page && <div className="dashboard-page">{page}</div>}
      </main>
      <footer className="muted">Base de documentos públicos do PNCP. Confirme as condições e a vigência no edital. Conversa mantida somente nesta sessão do navegador.</footer>
    </div>
  )
}
