import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import ExplorePage from './pages/ExplorePage'
vi.mock('./explore/Scene', () => ({ default: () => <div>Prévia 3D de teste</div> }))
afterEach(() => { cleanup(); vi.unstubAllGlobals() })
const catalog = [{pncp_id:'12345678000100-1-000001/2026',agency:'Órgão do teste',uf:'BA',object:'Compra de computadores',documents:[{sequence:1,url:'https://pncp.gov.br/pdf'}]}]
it('mostra catálogo, fontes literais, filtros e seleção sem enviar consulta', async () => {
  const fetchMock = vi.fn(async () => ({ok:true,json:async () => catalog}))
  vi.stubGlobal('fetch',fetchMock); vi.stubGlobal('__CHAT_ENABLED__',true)
  render(<ExplorePage reply={{status:'answered',answer:'12 meses',claims:[],candidates:[],sources:[{index:1,pncp_id:catalog[0].pncp_id,agency:'Órgão do teste',uf:'BA',document_sequence:1,page:26,url:'https://pncp.gov.br/pdf',quote:'GARANTIA DE 12 MESES'}]}} />)
  await screen.findByRole('heading',{name:'Órgão do teste'})
  expect(screen.getByText('GARANTIA DE 12 MESES')).toBeTruthy()
  expect(screen.getByRole('link',{name:'Conferir página 26'}).getAttribute('href')).toBe('https://pncp.gov.br/pdf#page=26')
  fireEvent.click(screen.getByRole('button',{name:'Lista',exact:true}))
  expect(screen.getByRole('button',{name:'Lista',exact:true}).getAttribute('aria-pressed')).toBe('true')
  fireEvent.change(screen.getByRole('searchbox',{name:'Buscar no explorador'}),{target:{value:'inexistente'}})
  expect(screen.getByText('Nenhum edital corresponde ao filtro.')).toBeTruthy()
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

it('seleciona um PDF para conferência sem abrir link ou enviar pergunta', async () => {
  const fetchMock = vi.fn(async () => ({ok:true,json:async () => catalog}))
  vi.stubGlobal('fetch',fetchMock); vi.stubGlobal('__CHAT_ENABLED__',true)
  Object.defineProperty(HTMLElement.prototype,'scrollIntoView',{configurable:true,value:vi.fn()})
  render(<ExplorePage reply={null} />)
  await screen.findByRole('heading',{name:'Órgão do teste'})
  const select = screen.getByRole('button',{name:'Selecionar PDF 1 para a mesa'})
  fireEvent.click(select)
  expect(select.getAttribute('aria-pressed')).toBe('true')
  expect(screen.getByText('PDF selecionado para conferência')).toBeTruthy()
  expect(fetchMock).toHaveBeenCalledTimes(1)
  expect(screen.getByRole('link',{name:'Abrir documento ↗'}).getAttribute('href')).toBe('https://pncp.gov.br/pdf')
  Reflect.deleteProperty(HTMLElement.prototype,'scrollIntoView')
})

it('seleciona edital do novo estado ao filtrar sem manter seleção fora do catálogo', async () => {
  const other = {...catalog[0], pncp_id:'22345678000100-1-000002/2026', agency:'Órgão de Santa Catarina', uf:'SC'}
  vi.stubGlobal('fetch',vi.fn(async () => ({ok:true,json:async () => [...catalog,other]})))
  vi.stubGlobal('__CHAT_ENABLED__',true)
  render(<ExplorePage reply={null} />)
  await screen.findByRole('heading',{name:'Órgão do teste'})
  fireEvent.change(screen.getByRole('combobox',{name:'UF'}),{target:{value:'SC'}})
  expect(await screen.findByRole('heading',{name:'Órgão de Santa Catarina'})).toBeTruthy()
  expect(screen.getByRole('button',{name:/SC.*Órgão de Santa Catarina/}).getAttribute('aria-pressed')).toBe('true')
})
