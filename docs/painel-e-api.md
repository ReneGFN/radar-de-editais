# Painel e API local — primeira versão (2026-10-03)

Estado: **implementado e verificado localmente; não publicado.** Mostra só resultados de desenvolvimento já avaliados; o holdout não foi executado.

## Arquitetura

```text
reports/*.json + datasets/evaluation/*.json (aprovadas) + manifestos públicos
        │  (só leitura de arquivos; sem banco, Groq, embeddings ou diretório privado)
        ▼
backend/src/radar/public_data.py   monta cada saída por lista de campos permitidos
        │                           e passa tudo por assert_public (chaves/valores privados)
        ├──► backend/src/radar/api.py        FastAPI, só GET, esquemas extra='forbid'
        │        └─ ops/serve-api.py           uvicorn fixo em 127.0.0.1:8765
        └──► ops/export-site-data.py         grava site/data/*.json (mesmos esquemas)

frontend/ (React 19 + TypeScript + Vite)
   modo static: lê data/*.json (publicDir = ../site)  → build em frontend/dist com CSP
   modo api:    lê /api/* pelo proxy do Vite (mesmo origin, sem CORS)
```

Por que assim: a mesma função alimenta API e estático, então o painel publicado não pode mostrar algo diferente do que os testes da API conferem. Ler só arquivos públicos elimina, por construção, o risco de a API vazar PDF, resposta bruta ou nota privada: ela não tem acesso a esses dados.

## Rotas

| Rota | Conteúdo |
|---|---|
| `GET /api/versions` | variantes, papel, factuais aceitas, tokens, latência, revisão humana agregada, achados da v3 |
| `GET /api/versions/{a}/compare/{b}` | estado técnico e humano por caso, regressões e melhoras listadas, agregados |
| `GET /api/cases` | 50 casos de desenvolvimento aprovados, com estado por variante |
| `GET /api/cases/{id}` | pergunta, gabarito aprovado, fontes (hash, documento, página, link PNCP), critérios humanos |
| `GET /api/quality` | gate, meta de 90%, atendido, bloqueios, requisitos do holdout |
| `GET /api/corpus` | totais e distribuição por região/UF, desenvolvimento x holdout |

Nunca saem: `answer`, `quote`, `claims`, `citations`, `notes_private`, `reviewer`, `text`, `review_record`, `review_notes`, tokens, senhas, chaves. Trechos citados existem nas referências públicas, mas a API não os repassa. Links só `https://pncp.gov.br/…`. O holdout aparece apenas em contagens de corpus, porque está pendente de aprovação.

## Telas

1. **Versões**: tabela das três variantes, decisão de promoção, achados humanos da v3 (corrigido, barrado, ainda falha, regressões) e comparação escolhida pelo usuário com as regressões em destaque.
2. **Casos**: lista filtrável e detalhe com fonte oficial e critérios; "não avaliado" quando não há revisão humana.
3. **Qualidade**: gate bloqueado, situação da meta, o que já foi atendido e o que bloqueia.
4. **Corpus**: totais e distribuição por região/UF, com barras em SVG.

Sem 3D nesta versão.

## Como rodar

```powershell
# API (terminal 1)
$env:PYTHONPATH = 'backend/src'
& .venv/Scripts/python.exe ops/serve-api.py              # http://127.0.0.1:8765/api/versions

# Painel lendo a API (terminal 2)
cd frontend; npm ci --ignore-scripts; npm run dev:api     # http://127.0.0.1:5173

# Painel estático (sem API)
& .venv/Scripts/python.exe ops/export-site-data.py         # gera site/data/*.json
cd frontend; npm run dev        # ou: npm run build; npm run preview
```

## Verificação feita

- `backend/tests/test_api.py`: 35 testes. Todas as rotas sem campo ou valor privado, trecho real de referência ausente da saída, só links PNCP, 405 em escrita, 404/422 em entrada inválida, sem cabeçalho CORS, `/docs` e `/openapi.json` desligados, campo privado injetado falha fechado, `radar.api` não importa banco/Groq/config privada (subprocesso), export estático igual à API.
- `frontend/src/App.test.tsx`: 9 testes. Regressões destacadas, "não avaliado", link PNCP com `noopener noreferrer`, texto malicioso (`<img onerror>`, `<script>`, `javascript:`) renderizado como texto e link recusado, ids/variantes inválidos recusados, dados estáticos sem campos privados. Um teste confere o código-fonte por `dangerouslySetInnerHTML`/`innerHTML`/`eval`: é uma guarda de padrão, não prova comportamento; o comportamento é coberto pelo teste de XSS.
- Build com CSP no `index.html` gerado; capturas no Edge headless das quatro telas renderizaram com a CSP ativa.
- `npm audit`: 0 vulnerabilidades. `pip-audit` no lock: nenhuma conhecida.

## Limitações

- Sem autenticação: aceitável só porque a API é local, somente leitura e serve dados públicos. Não expor em rede.
- `jsdom 30` (só testes) declara Node ≥ 22.22; aqui roda em Node 22.16 com aviso EBADENGINE e os testes passaram.
- Páginas por UF do desenvolvimento não estão no manifesto público e aparecem como "não informado".
- Mudança técnica de estado (ex.: respondeu → barrada) não é julgamento semântico; a coluna humana é separada.
- Feedback de usuário (like/dislike) continua só na proposta (`docs/proposta-api-painel.md`).

## Próximo passo

Publicar `frontend/dist` no GitHub Pages só após decisão de Renê, com HTTPS do próprio Pages.
