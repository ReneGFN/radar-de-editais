# Amostra independente v2 (holdout) — protocolo e estado — 2026-10-02

## Por que uma amostra nova

Os 10 casos `independent-01..10` serviram para diagnosticar e ajustar o perfil `alias_items`, que subiu a cobertura híbrida de citações completas de 5/10 para 9/10. A partir daí eles são dados de desenvolvimento. Medir generalização neles seria como corrigir a própria prova. A amostra v2 só vale como validação se nada nela tiver sido visto antes e se ninguém ajustar o sistema depois de ver os resultados.

## Regras de independência (verificadas por código)

`backend/src/radar/independence.py` (testes em `backend/tests/test_independence.py`) recusa a amostra quando encontra:

| Bloqueio | Como é detectado |
|---|---|
| Contratação já vista | `pncp_id` presente em qualquer manifesto, lista de candidatos (incluindo os que falharam na preparação) ou referência |
| PDF já visto | SHA-256 de qualquer documento de desenvolvimento |
| Mesmo PDF republicado em outra contratação | hash repetido dentro da própria amostra |
| URL de documento já vista | URL do PNCP, ignorando a âncora `#page=` |
| Pergunta reaproveitada | hash da pergunta normalizada (sem acento, caixa ou pontuação) |
| Pergunta reescrita | sobreposição de palavras (Jaccard) de 0,8 ou mais com qualquer das 120 perguntas existentes |
| Evidência fora da amostra | trecho citado cujo PDF não está no manifesto da amostra |
| Tamanho e cobertura | menos de 30 factuais, 10 recusas ou 10 contratações; falta de alguma categoria: `item`, `quantity`, `specification`, `deadline`, `judgment_criterion` |

O coletor também descarta, na origem, órgãos (CNPJ) que já aparecem no desenvolvimento. Três candidatos caíram por isso e estão registrados em `dropped_agency_overlap`. A biblioteca devolve essa sobreposição como aviso, não como bloqueio, porque órgão repetido é um risco de modelo de edital parecido, não um vazamento de dado.

Um resultado "independente" prova só a separação dos dados, não a qualidade das respostas.

## Candidatos coletados (metadados públicos, sem download)

Coleta `ops/plan-holdout-corpus.py`, janela de publicação 2026-08-01 a 2026-09-20, modalidade 6 (pregão eletrônico), um edital por UF, triagem automática por palavra-chave. Duas paradas por HTTP 429 do PNCP; a coleta foi retomada do ponto salvo, sem repetir requisições em loop. Relatório: `reports/holdout-corpus-candidates-v1.json`.

| UF | Região | Contratação PNCP | PDFs | Observação de triagem (assistente, não verificada no PDF) |
|---|---|---|---:|---|
| AM | Norte | 04312658000190-1-000026/2026 | 1 | Estações de trabalho |
| PA | Norte | 05138730000177-1-000086/2026 | 3 | Equipamentos e materiais de informática |
| TO | Norte | 37344355000108-1-000026/2026 | 3 | Registro de preços de materiais |
| RO | Norte | 07100011000192-1-000002/2026 | 1 | Desktop + monitor 22" + periféricos + nobreak |
| MA | Nordeste | 41479569000169-1-000055/2026 | 1 | Serviços contínuos: pode estar fora do escopo de aquisição |
| PE | Nordeste | 10091619000102-1-000090/2026 | 1 | Equipamentos permanentes de informática |
| RN | Nordeste | 70157896000100-1-000010/2026 | 1 | Equipamentos de informática |
| PB | Nordeste | 08702573000179-1-000050/2026 | 1 | Equipamentos de informática |
| MT | Centro-Oeste | 03238755000117-1-000031/2026 | 1 | Licenças de software e equipamentos: escopo misto |
| MS | Centro-Oeste | 03173317000118-1-000078/2026 | 1 | Materiais de informática |
| MG | Sudeste | 01759101000103-1-000011/2026 | 1 | Equipamentos, periféricos e suprimentos |
| ES | Sudeste | 14004319000108-1-000050/2026 | 1 | Equipamentos para unidades de saúde |
| RS | Sul | 87691507000117-1-000046/2026 | 2 | Notebooks intermediários |
| PR | Sul | 79151312000156-1-000510/2026 | 1 | Lista mista (medição, áudio/vídeo, mobiliário): escopo misto |

Quatorze candidatos cobrem as 5 regiões. Três (MA, MT, PR) podem cair na triagem manual; sobram 11, acima do mínimo de 10. É uma amostra de conveniência (primeiro edital elegível por UF), não representativa do PNCP. Hashes ainda pendentes: só existem depois do download.

## Composição exigida da referência `datasets/evaluation/holdout-v1.json`

| Categoria | Mínimo | Observação |
|---|---:|---|
| `item` (identificar item/lote correto) | 5 | Pelo menos 2 em páginas com vários itens parecidos, com o item nomeado na pergunta (lição do pilot-17) |
| `quantity` | 6 | Incluir tabela com colunas ITEM e QTD (lição do pilot-12) |
| `specification` | 8 | Incluir unidades sujeitas a confusão (MT/s × MHz, GB × Gb, mínimo × referência) |
| `deadline` | 5 | Dias úteis × corridos e marco inicial explícitos |
| `judgment_criterion` | 5 | Menor preço por item × por lote × global |
| Recusas | 10 | Futuro, sigilo, segredo, citação falsa, garantia, dados de empresa, instrução embutida |
| Total | 40 | 30 factuais + 10 recusas, em pelo menos 10 contratações |

## Sequência (cada passo depende do anterior)

1. Triagem manual dos 14 candidatos (objeto e anexos) e download privado dos PDFs para o diretório privado, fora do Brain e do OneDrive. Registrar SHA-256, bytes, páginas e páginas com pouco texto.
2. Rodar `check_holdout` só sobre o manifesto, para bloquear hash repetido antes de escrever qualquer pergunta.
3. Redigir perguntas e gabaritos lendo o PDF, sem rodar a recuperação do sistema nessas perguntas. Quem redige não pode ter visto saídas do sistema para esses documentos.
4. Renê aprova perguntas, gabaritos e fontes (página/offset) antes de qualquer execução. Essa aprovação é da referência, não das respostas.
5. Congelar protocolo: hashes do código, da referência, do snapshot e da configuração (`alias_items`, híbrida, top 5).
6. Indexar em snapshot próprio, sem tocar `1446c44aca18011a`. Rodar recuperação uma vez.
7. Prévia privada dos prompts e pedido de autorização explícita antes da Groq (40 chamadas).
8. Gerar uma vez, revisar com `ops/human-review.py` e só então calcular as métricas.
9. Se algo for ajustado depois de ver os resultados, a amostra v2 vira desenvolvimento e outra amostra é necessária.

## Estado

- Feito: guarda de independência com testes, coletor e 14 candidatos.
- Não feito: download, hashes, triagem manual, perguntas, aprovação, indexação, chamadas à Groq.
- Limitação: busca escopada por `pncp_id`. A avaliação mede achar a página dentro do edital certo, não achar o edital certo entre todos.
- Limitação: as recusas do tipo "instrução embutida no documento" usam um pedido do usuário que descreve a instrução. Isso não prova resistência a uma injeção real dentro do PDF; para testá-la, seria preciso um documento sintético marcado como tal, fora do corpus público.
