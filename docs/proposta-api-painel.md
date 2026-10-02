# Proposta: API e painel de avaliação — 2026-10-02

Estado: proposta, nada implementado. Ordem recomendada: concluir a revisão humana e a amostra independente antes, porque o painel existe para mostrar esses resultados.

## Objetivo

Um painel de leitura para quem avalia o laboratório (Renê, recrutador, revisor técnico). Ele responde três perguntas: o que mudou entre versões, onde o sistema erra, e de qual página veio cada afirmação. O painel não é um produto de consulta aberto ao público. Quem pergunta qualquer coisa sobre editais fica para depois, porque exige autenticação, cota e custo de Groq por usuário.

## Dados: o que o painel pode e não pode ler

O painel lê só artefatos públicos já existentes em `reports/` e `datasets/`: resumos de recuperação e geração, resumos de revisão humana, manifestos e referências aprovadas. Respostas brutas, PDFs, texto extraído e vetores continuam privados.

Com isso o painel publicado não mostra o texto da resposta gerada. Ele mostra estado, notas, etiquetas de erro, citação (arquivo, página, link oficial com `#page=`) e o trecho da referência aprovada, que já é público. Uma visão local "modo privado", lendo o checkpoint do diretório privado, mostra as respostas só na máquina de Renê e nunca é publicada.

## API (FastAPI, somente leitura)

| Rota | Retorna | Origem |
|---|---|---|
| `GET /api/versions` | Perfis/variantes avaliados, snapshot, hash do protocolo, data | `*-protocol-*.json` |
| `GET /api/versions/{a}/compare/{b}` | Hit@5, cobertura completa, latência, casos que ganharam/perderam | `*-retrieval-comparison-*.json` |
| `GET /api/cases?cohort=&state=&tag=` | Lista de casos com estado, integridade de citação, nota humana, etiquetas | `human-review-*.json` |
| `GET /api/cases/{id}` | Pergunta, gabarito aprovado, fontes (arquivo/página/URL/offsets), ranking recuperado, nota | referência + relatórios |
| `GET /api/quality` | Saída de `assess_release` com motivos de bloqueio | gate |
| `GET /api/corpus` | Contratações, PDFs, hashes, páginas com pouco texto, papel (dev/holdout) | manifestos |

Decisões e motivos:

- Somente leitura e sem Groq. Sem rota que gere resposta, não há chave exposta, custo por visitante nem injeção pelo usuário chegando ao modelo.
- Publicação estática: a API gera JSON consolidado na hora do build, e o painel é servido como site estático (GitHub Pages). Assim não há servidor, banco ou credencial em produção. O FastAPI roda só localmente para desenvolvimento e para o modo privado, ligado em `127.0.0.1`.
- Esquemas Pydantic com `extra='forbid'` na saída, e um teste falha se aparecer campo de texto bruto (`answer`, `quote`, `notes_private`, `text`), seguindo a regra do exportador atual.
- O link de fonte é reconstruído por `safe_url` (só `https://pncp.gov.br`), nunca copiado de campo livre.

## Painel (React + TypeScript)

1. Versões: tabela de variantes com Hit@5, cobertura completa, latência mediana/p95 e taxa humana (vazia quando não houver revisão, com o motivo escrito). Comparação A/B lado a lado, com os casos que pioraram em destaque, não só a média.
2. Erros: matriz de etiqueta de erro × categoria de pergunta (por exemplo `unit_mix` × `specification`), clicável até os casos. É a visão que mostraria que o problema de unidades se concentra em especificação de memória.
3. Caso: pergunta, gabarito, estado, nota por critério, integridade de citação separada da correção, e as fontes com arquivo, página, link oficial e passagem aprovada. Ranking do top 5 recuperado mostrando onde a passagem conhecida ficou.
4. Corpus: contratações por UF e região, papel (desenvolvimento/holdout), páginas com pouco texto.

Os quatro são tabelas e gráficos 2D, navegáveis por teclado, com texto alternativo e contraste conferidos.

## Visualização 3D: só se responder uma pergunta que o 2D não responde

A proposta é não incluir 3D na primeira versão. As relações úteis do projeto (versão × métrica, erro × categoria, cobertura por região) são tabulares e ficam mais legíveis em 2D.

Uma vista de vizinhança de trechos (PCA, depois UMAP) só entra como experimento se passar no teste já descrito em [visualização 3D](visualizacao-3d.md): por exemplo, ajudar a explicar por que, no pilot-17, os itens 29 e 30 (SSD de 500 GB e 512 GB) caem tão perto que a recuperação os confunde. Critério de entrada: tarefas cronometradas (localizar a referência não recuperada, achar o duplicado) feitas em 2D e 3D, com o 3D mais rápido ou mais correto. Se não for, ele fica fora. A projeção nunca substitui Hit@k calculado nos vetores originais de 384 dimensões.

## Segurança do painel

- Site estático sem login: só dados públicos já revisados pelo exportador.
- Modo privado: FastAPI em `127.0.0.1`, sem CORS aberto, sem rota de escrita, lendo o diretório privado. Não é publicado.
- HTTPS garantido pelo GitHub Pages; CSP restritiva (`default-src 'self'`), sem script de terceiros nem CDN sem versão fixada.
- Dependências travadas por lockfile e auditadas (`pip-audit`, `npm audit`) a cada build.
- Texto vindo de edital é renderizado como texto, nunca como HTML (React escapa por padrão; proibir `dangerouslySetInnerHTML`).

## Primeira entrega sugerida (pequena e verificável)

1. `backend/src/radar/api.py` com as rotas `versions`, `compare` e `cases`, mais o teste que barra campos privados.
2. Script de build que grava `site/data/*.json`.
3. Painel com as telas Versões e Caso.
4. Critério de aceite: abrir o pilot-17 e ver estado, citação (arquivo 1, página 54, link oficial) e a etiqueta `ambiguous_question` assim que existir revisão; a comparação `window-v1` × `structure-v2` mostrando as regressões do piloto (Hit@5 de 29 para 28 e cobertura completa de 30 para 29) com os casos afetados.
