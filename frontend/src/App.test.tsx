// @vitest-environment jsdom
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { path, safePncpUrl } from './data'

const DATA = join(__dirname, '..', '..', 'site', 'data')
const read = (name: string) => JSON.parse(readFileSync(join(DATA, name), 'utf-8'))
let overrides: Record<string, unknown> = {}

beforeEach(() => {
  overrides = {}
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const name = url.replace(/^data\//, '')
    const body = name in overrides ? overrides[name] : read(name)
    return { ok: true, status: 200, json: async () => body } as Response
  }))
})
afterEach(() => { cleanup(); vi.unstubAllGlobals(); window.location.hash = '' })

describe('painel', () => {
  it('mostra a variante padrão e destaca regressões da comparação', async () => {
    window.location.hash = '#/versoes'
    render(<App />)
    expect(await screen.findByText(/Variante padrão:/)).toBeTruthy()
    const regressions = await screen.findByRole('heading', { name: /Regressões \(/ })
    const box = regressions.parentElement!
    expect(within(box).getByText('independent-08')).toBeTruthy()
    expect(screen.getAllByText('não promovida').length).toBeGreaterThan(0)
    // v2 não tem revisão humana: tem de aparecer "não avaliado", nunca um número.
    expect(screen.getAllByText('não avaliado').length).toBeGreaterThan(0)
  })

  it('mostra caso com fonte oficial do PNCP e "não avaliado" para variante sem revisão', async () => {
    window.location.hash = '#/casos/pilot-17'
    render(<App />)
    expect(await screen.findByText('Gabarito aprovado')).toBeTruthy()
    const link = screen.getByRole('link', { name: 'abrir no PNCP' }) as HTMLAnchorElement
    expect(link.href.startsWith('https://pncp.gov.br/')).toBe(true)
    expect(link.rel).toBe('noopener noreferrer')
    const v2 = screen.getByRole('region', { name: 'Resultado de alias_items_v2' })
    expect(within(v2).getByText('não avaliado')).toBeTruthy()
    expect(within(v2).getByText('Sem critérios humanos registrados.')).toBeTruthy()
  })

  it('renderiza texto de relatório como texto, nunca como HTML', async () => {
    const detail = read('case-pilot-17.json')
    detail.question = '<img src=x onerror="alert(1)"><script>alert(2)</script>'
    detail.sources = [{ ...detail.sources[0], url: 'javascript:alert(3)' }]
    overrides['case-pilot-17.json'] = detail
    window.location.hash = '#/casos/pilot-17'
    const { container } = render(<App />)
    expect(await screen.findByText(detail.question)).toBeTruthy()
    expect(container.querySelector('img')).toBeNull()
    expect(container.querySelector('script')).toBeNull()
    expect(screen.queryByRole('link', { name: 'abrir no PNCP' })).toBeNull()
    expect(screen.getByText('link inválido')).toBeTruthy()
  })

  it('mostra bloqueios do gate e o holdout pendente', async () => {
    window.location.hash = '#/qualidade'
    render(<App />)
    const blockers = await screen.findByRole('region', { name: 'Bloqueios' })
    expect(within(blockers).getByText(/46 de 46 casos pendentes/)).toBeTruthy()
    expect(screen.getByText(/executado: não/)).toBeTruthy()
  })

  it('mostra corpus por região e UF separando desenvolvimento e holdout', async () => {
    window.location.hash = '#/corpus'
    render(<App />)
    expect(await screen.findByText('Distribuição por região e UF')).toBeTruthy()
    expect(screen.getAllByText('holdout (pendente)').length).toBeGreaterThan(0)
    expect(screen.getAllByText('desenvolvimento').length).toBeGreaterThan(0)
  })
})

describe('segurança do cliente', () => {
  it('só monta caminhos fixos e recusa ids e variantes inválidos', () => {
    expect(path('case', 'pilot-01')).toBe('data/case-pilot-01.json')
    expect(() => path('case', '../secrets')).toThrow()
    expect(() => path('compare', 'alias_items', 'evil')).toThrow()
    expect(() => path('compare', 'alias_items', 'alias_items')).toThrow()
  })

  it('aceita só links HTTPS do PNCP', () => {
    expect(safePncpUrl('https://pncp.gov.br/app/editais/1/2026/1')).not.toBeNull()
    for (const bad of ['http://pncp.gov.br/a', 'https://pncp.gov.br.evil.com/a', 'javascript:alert(1)']) {
      expect(safePncpUrl(bad)).toBeNull()
    }
  })

  it('o código-fonte não usa HTML livre, eval nem scripts de terceiros', () => {
    const files: string[] = []
    const walk = (dir: string) => readdirSync(dir, { withFileTypes: true }).forEach((e) =>
      e.isDirectory() ? walk(join(dir, e.name)) : /\.(tsx?|html)$/.test(e.name) && !e.name.includes('.test.') && files.push(join(dir, e.name)))
    walk(__dirname)
    files.push(join(__dirname, '..', 'index.html'))
    const source = files.map((f) => readFileSync(f, 'utf-8')).join('\n')
    expect(source).not.toMatch(/dangerouslySetInnerHTML|innerHTML|eval\(|new Function|<script src="http/)
  })

  it('os dados estáticos não trazem campos privados', () => {
    const forbidden = /"(answer|quote|quotes|claims|citations|notes_private|reviewer|text|token|password|senha|api_key|review_record)":/
    for (const name of readdirSync(DATA)) {
      expect(readFileSync(join(DATA, name), 'utf-8')).not.toMatch(forbidden)
    }
  })
})
