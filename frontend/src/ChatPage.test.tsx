import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { ChatPage } from './pages/ChatPage'

const PNCP = '12345678000100-1-000001/2026'
const candidate = { pncp_id: PNCP, agency: 'Órgão de teste', uf: 'SP', document_sequence: 1, page: 2, url: 'https://pncp.gov.br/pdf' }
const answer = { status: 'answered', answer: 'Garantia de 12 meses.', claims: [{ text: 'Garantia de 12 meses.', source_indices: [1] }],
  sources: [{ ...candidate, index: 1, quote: 'O prazo de garantia é de 12 meses.' }], candidates: [candidate] }
let result: unknown
let status: number
let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  status = 200; result = answer
  vi.stubGlobal('__CHAT_ENABLED__', true)
  fetchMock = vi.fn(async (url: string) => ({ ok: url === '/chat/ask' ? status === 200 : true,
    status: url === '/chat/ask' ? status : 200, json: async () => url === '/chat/health' ? { generation_enabled: true } :
      url === '/chat/editais' ? [{ ...candidate, object: 'Computadores', official_url: candidate.url }] : result }))
  vi.stubGlobal('fetch', fetchMock)
  Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', { configurable: true, value: vi.fn() })
})
afterEach(() => { cleanup(); Reflect.deleteProperty(HTMLElement.prototype, 'scrollIntoView'); vi.restoreAllMocks(); vi.unstubAllGlobals() })

async function ready() {
  render(<ChatPage />)
  await screen.findByText('1 contratação disponível')
}
function ask(question = 'Qual garantia?') {
  fireEvent.change(screen.getByLabelText('Sua pergunta'), { target: { value: question } })
  fireEvent.click(screen.getByRole('button', { name: 'Enviar pergunta' }))
}

it('envia pergunta geral, sem PNCP e sem credenciais, e abre a fonte', async () => {
  await ready(); ask()
  await screen.findByText('Resposta com fontes')
  const call = fetchMock.mock.calls.find(c => c[0] === '/chat/ask')!
  expect(JSON.parse(call[1].body)).toEqual({ question: 'Qual garantia?' })
  expect(call[1].credentials).toBe('omit')
  expect(call[1].headers['X-Radar-Chat']).toBe('1')
  fireEvent.click(screen.getByRole('button', { name: 'Ver fonte 1' }))
  expect(document.querySelector('details')?.open).toBe(true)
  const link = screen.getByRole('link', { name: 'Abrir PDF oficial · página 2' }) as HTMLAnchorElement
  expect(link.href).toBe('https://pncp.gov.br/pdf#page=2')
  expect(link.rel).toBe('noopener noreferrer')
})

it('candidato preenche seleção e pergunta sem enviar automaticamente', async () => {
  result = { ...answer, status: 'needs_clarification', answer: 'Informe o órgão.', claims: [], sources: [] }
  await ready(); ask()
  await screen.findByText('Precisamos de mais detalhes')
  fireEvent.click(screen.getByRole('button', { name: 'Consultar este edital' }))
  expect(screen.getByRole('button', { name: /Órgão de teste.*12345678000100/ }).getAttribute('aria-pressed')).toBe('true')
  expect(fetchMock.mock.calls.filter(c => c[0] === '/chat/ask')).toHaveLength(1)
  result = answer
  fireEvent.click(screen.getByRole('button', { name: 'Enviar pergunta' }))
  await screen.findByText('Resposta com fontes')
  const calls = fetchMock.mock.calls.filter(c => c[0] === '/chat/ask')
  expect(JSON.parse(calls[1][1].body).pncp_id).toBe(PNCP)
})

it('renderiza passagens como texto e recusa links externos', async () => {
  const unsafe = '<img src=x onerror=alert(1)>'
  result = { ...answer, claims: [{ text: unsafe, source_indices: [1] }], sources: [{ ...answer.sources[0], quote: unsafe, url: 'javascript:alert(1)' }] }
  await ready(); ask()
  await screen.findByText('Resposta com fontes')
  expect(screen.getAllByText(unsafe).length).toBe(2)
  expect(document.querySelector('img')).toBeNull()
  expect(screen.getByText('Link de fonte inválido.')).toBeTruthy()
  expect(screen.queryByRole('link', { name: /Abrir PDF/ })).toBeNull()
})

it('filtra o seletor, escolhe escopo sem envio e fecha por Escape', async () => {
  await ready()
  const panel = screen.getByLabelText('Escopo da consulta') as HTMLDetailsElement
  panel.open = true
  fireEvent.change(screen.getByLabelText('Filtrar editais'), { target: { value: 'nao existe' } })
  expect(screen.getByText('Nenhum edital corresponde à busca.')).toBeTruthy()
  fireEvent.change(screen.getByLabelText('Filtrar editais'), { target: { value: 'orgao' } })
  fireEvent.click(screen.getByRole('button', { name: /Órgão de teste.*12345678000100/ }))
  expect(panel.open).toBe(false)
  expect(fetchMock.mock.calls.filter(c => c[0] === '/chat/ask')).toHaveLength(0)
  panel.open = true
  fireEvent.keyDown(screen.getByLabelText('Filtrar editais'), { key: 'Escape' })
  expect(panel.open).toBe(false)
  ask()
  await screen.findByText('Resposta com fontes')
  expect(JSON.parse(fetchMock.mock.calls.find(c => c[0] === '/chat/ask')![1].body).pncp_id).toBe(PNCP)
})

it('move o painel pelo teclado, restaura posição e mantém a pergunta', async () => {
  await ready()
  const panel = screen.getByLabelText('Escopo da consulta') as HTMLDetailsElement
  panel.open = true
  fireEvent.change(screen.getByLabelText('Sua pergunta'), { target: { value: 'Minha pergunta' } })
  fireEvent.keyDown(screen.getByRole('button', { name: /Mover painel de escopo/ }), { key: 'ArrowRight' })
  expect(document.querySelector<HTMLElement>('.scope-picker')!.style.position).toBe('fixed')
  expect(panel.open).toBe(true)
  fireEvent.click(screen.getByRole('button', { name: 'Restaurar posição do painel' }))
  expect(document.querySelector('.scope-picker')!.hasAttribute('style')).toBe(false)
  expect((screen.getByLabelText('Sua pergunta') as HTMLTextAreaElement).value).toBe('Minha pergunta')
  expect(fetchMock.mock.calls.filter(c => c[0] === '/chat/ask')).toHaveLength(0)
})

it('mostra limite de chamadas com ação manual e sem expor erro bruto', async () => {
  status = 429; result = { detail: 'PRIVATE RAW PROVIDER ERROR' }
  await ready(); ask()
  await screen.findByText(/intervalo de 35 segundos/)
  expect(screen.queryByText(/PRIVATE/)).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: 'Editar e tentar novamente' }))
  expect((screen.getByLabelText('Sua pergunta') as HTMLTextAreaElement).value).toBe('Qual garantia?')
  expect(fetchMock.mock.calls.filter(c => c[0] === '/chat/ask')).toHaveLength(1)
})

it('não envia pergunta vazia e mostra aviso de geração desativada', async () => {
  fetchMock.mockImplementation(async (url: string) => ({ ok: true, status: 200, json: async () =>
    url === '/chat/health' ? { generation_enabled: false } : [{ ...candidate, object: '', official_url: candidate.url }] }))
  await ready()
  expect(screen.getByText(/geração de respostas está desativada/)).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Enviar pergunta' }))
  expect(screen.getByText('Escreva sua pergunta antes de enviar.')).toBeTruthy()
  expect(fetchMock.mock.calls.filter(c => c[0] === '/chat/ask')).toHaveLength(0)
})

it('publicação estática não chama a API local', async () => {
  vi.stubGlobal('__CHAT_ENABLED__', false)
  render(<ChatPage />)
  expect(screen.getByText(/Nesta publicação/)).toBeTruthy()
  await waitFor(() => expect(fetchMock).not.toHaveBeenCalled())
})

it('recebe seleção da mesa e envia somente o escopo dos arquivos', async () => {
  await ready()
  const documents=[{pncp_id:PNCP,document_sequence:1}]
  fireEvent(window,new CustomEvent('radar-select-documents',{detail:documents}))
  expect(screen.getByText('Consulta limitada aos PDFs da mesa')).toBeTruthy()
  ask()
  await screen.findByText('Resposta com fontes')
  const body=JSON.parse(fetchMock.mock.calls.find(c=>c[0]==='/chat/ask')![1].body)
  expect(body.documents).toEqual(documents)
  expect(body.pncp_id).toBeUndefined()
})
