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
- Feito (2026-10-02): download privado, hashes, triagem e rascunho de 46 perguntas (ver abaixo).
- Não feito: aprovação do Renê, indexação, recuperação, chamadas à Groq.

## Atualização — PDFs e rascunho de perguntas (2026-10-02)

**Download** (`ops/prepare-holdout-documents.py`): 18 PDFs de 13 contratações, salvos só no diretório privado (`raw/<sha256>.pdf`; texto por página em `holdout/pages-*.json`). Antes de aceitar cada PDF, o script compara hash e URL com todo o desenvolvimento: 0 sobreposições com o desenvolvimento e 0 PDFs repetidos na amostra. Nenhuma página ficou abaixo de 80 caracteres de texto. O de RO (07100011000192-1-000002/2026) falhou: o arquivo não começa com `%PDF-` e foi descartado sem retentativa. Metadados públicos: `reports/holdout-documents-v1.json` e `datasets/holdout/manifest-v1.json`. Os dois ficam fora de `datasets/manifests` e `datasets/evaluation` para não entrar na lista de exclusões antes da hora.

**Triagem**: o MA é locação de computadores (serviço), mas o objeto é equipamento de informática, e por isso ficou. MS, MT e PR estão no manifesto, mas sem perguntas. No MS o texto extraído tem acentuação corrompida (`Gestªo`); no MT e no PR o escopo é misto.

**Rascunho** (`datasets/holdout/holdout-v1-draft.json`): 36 factuais e 10 recusas em 10 contratações (AM, RS, ES, PB, MG, TO, PE, PA, RN, MA), todas com `review_status: pending_user_approval`.

| Categoria | Casos | Exemplos de armadilha |
|---|---:|---|
| `item` | 6 | Dois microcomputadores (DDR4 2933 × DDR5 5600), memórias quase iguais em lista longa, extensão de 10 m × 30 m |
| `quantity` | 8 | Mínimo × máximo de registro de preços, total × parcela por secretaria, 12 meses × unidades, "05(uma)" |
| `specification` | 8 | MT/s e MHz no mesmo documento, Mbps, leitura × escrita do SSD |
| `deadline` | 7 | Dias úteis × sem indicação, 48 horas, frase que continua na página seguinte |
| `judgment_criterion` | 7 | Por item × por lote × global; edital e TR divergentes (ES) |
| Recusas | 10 | Orçamento sigiloso (2), anexos fora do PDF, vencedor futuro, CPF de servidor, senha, citação falsa, garantia de aceitação, instrução embutida, dados de empresa |

Três respostas esperadas pedem para **apontar uma contradição** em vez de escolher um valor: holdout-11 (ES, lote × item), holdout-16 (MG, "05(uma)") e holdout-28 (PA, MT/s × MHz e "expansível até 16GB"). Revisar essas três com atenção: o critério de "correta" nelas é diferente do usual.

**Como foi redigido**: quem redigiu foi o assistente (Kiro), lendo só o texto extraído. Nenhuma recuperação, nenhuma saída do sistema e nenhuma chamada à Groq foi feita sobre esses documentos. Cada trecho citado foi localizado automaticamente na página e guardado com `char_start`/`char_end`. A redação pelo assistente não substitui a aprovação humana; ela só garante que quem redigiu não viu respostas do sistema.

**Verificação** (`ops/check-holdout.py` → `reports/holdout-independence-check-v1.json`): `independent: true`, sem violações nem avisos de órgão repetido. Todos os trechos batem com o offset declarado, e nenhum trecho contém e-mail, CPF ou telefone. `ready_to_execute: false` porque nenhum caso foi aprovado. Testes: `backend/tests/test_check_holdout.py` cobre offset deslocado, página errada, e-mail no trecho e aprovação sem registro.

**Limitações**:
- Amostra de conveniência, uma contratação por UF.
- As perguntas foram escritas por uma única pessoa (o assistente) e podem trazer viés de redação.
- Os PDFs trazem nomes e e-mails de servidores, que ficam no privado e não entram nos trechos.
- O caso holdout-39 testa uma lacuna real de corpus: o Termo de Referência da POTIGÁS fica fora do PDF.
- O caso holdout-45 (instrução embutida) continua sendo um pedido do usuário, não uma injeção real dentro do PDF.

**Próximo passo**: o Renê revisa os 46 casos (pergunta, resposta esperada, página e trecho), corrige ou descarta os que quiser e registra a aprovação. Só depois: congelar o protocolo, indexar num snapshot próprio e preparar a prévia de prompts para autorização.
- Limitação: busca escopada por `pncp_id`. A avaliação mede achar a página dentro do edital certo, não achar o edital certo entre todos.
- Limitação: as recusas do tipo "instrução embutida no documento" usam um pedido do usuário que descreve a instrução. Isso não prova resistência a uma injeção real dentro do PDF; para testá-la, seria preciso um documento sintético marcado como tal, fora do corpus público.
