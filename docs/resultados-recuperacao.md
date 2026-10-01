# Primeira avaliação da busca — 2026-10-01

Executadas 180 consultas locais: 30 perguntas factuais × três modos × duas versões. Os dez casos de recusa aguardam integração da geração. O PostgreSQL voltou após iniciar o Docker Desktop; snapshots atual (15.773 trechos) e inicial (4.664) preservados. Nenhuma limpeza de dados ou restauração de volume nesta etapa.

## Resultados medidos

Hit@5 abaixo indica se o **ID do trecho de referência conhecido** apareceu entre os cinco resultados. Não é precisão das respostas, nem Recall completo. A coluna de citações também aceita um trecho sobreposto que contenha a citação na mesma fonte e página.

| Versão / modo | Trecho conhecido no top 5 | Citações conhecidas apoiadas | MRR@5 | Latência mediana / p95 |
|---|---:|---:|---:|---:|
| v1 · AND · Palavra-chave | 0/30 (0.0%) | 0.0% | 0.000 | 35.4 / 48.9 ms |
| v1 · AND · Semântica | 17/30 (56.7%) | 60.0% | 0.408 | 48.1 / 58.6 ms |
| v1 · AND · Híbrida | 17/30 (56.7%) | 60.0% | 0.408 | 42.8 / 60.6 ms |
| v2 · OR · Palavra-chave | 18/30 (60.0%) | 60.0% | 0.450 | 40.2 / 51.6 ms |
| v2 · OR · Semântica | 17/30 (56.7%) | 60.0% | 0.408 | 45.5 / 59.2 ms |
| v2 · OR · Híbrida | 20/30 (66.7%) | 66.7% | 0.479 | 43.1 / 58.0 ms |

MRR@5 é a média do inverso da posição do primeiro trecho conhecido; zero quando ele não aparece no top 5. Uma passagem com modelo aquecido e cache local, percentil por posto mais próximo e ordem dos modos alternada por pergunta. Não há significância estatística, benchmark de carga ou garantia de velocidade em outra máquina. Latências excluem inicialização do modelo; os relatórios guardam esse tempo separadamente.

## O que foi alterado e por quê

Na v1, o ramo lexical retornou zero candidatos em todas as 30 perguntas. A conversão de texto comum por `websearch_to_tsquery` usa AND entre termos, conforme a [documentação PostgreSQL 17](https://www.postgresql.org/docs/17/textsearch-controls.html). Exigir todos os termos de uma pergunta longa no mesmo trecho de aproximadamente 120 tokens restringiu a recuperação neste conjunto.

Na v2, a consulta é normalizada por `plainto_tsquery` e os conectores AND da representação gerada são substituídos por OR. O conteúdo da pergunta continua parametrizado; o SQL é fixo. `ts_rank_cd` ordena os resultados. Corpus, perguntas, embeddings, top 10 por ramo, top 5 final e RRF com constante 60 foram mantidos. Não houve reescrita por LLM ou uso das respostas esperadas na busca.

A consulta lexical OR tornou-se o padrão de desenvolvimento. O comportamento antigo continua disponível via `--lexical-strategy all` para reprodução. OR descarta a semântica de operadores de busca explícitos e pode aumentar ruído; não se declara uma solução geral nem aprovação de produção.

## Ganhos e regressões

A híbrida ganhou cinco casos e perdeu dois: aumento líquido de três casos (+10 pontos percentuais no Hit@5 dos IDs conhecidos). O suporte das citações conhecidas passou de 18/30 para 20/30; alguns trechos equivalentes explicam a diferença em relação aos IDs.

| Movimento | ID | Pergunta |
|---|---|---|
| Ganho | pilot-04 | Qual garantia está descrita para o desktop do item 01 do lote 01? |
| Ganho | pilot-07 | Na lista da página 69 que descreve RTX 5090, qual garantia de fábrica é indicada? |
| Ganho | pilot-13 | No edital de Assis de sequência 443, qual prazo máximo de entrega e a partir de qual evento ele é contado? |
| Ganho | pilot-18 | Qual resolução de impressão é especificada para a multifuncional laser colorida do item 15 da Câmara de Itapetininga? |
| Ganho | pilot-27 | Em Caçu, qual autonomia mínima da bateria é exigida para uso moderado e quais atividades exemplificam esse uso? |
| Regressão | pilot-01 | Na especificação de memória RAM da página 31, qual capacidade instalada e tecnologia são exigidas? |
| Regressão | pilot-02 | Na especificação de RAM da página 31, qual é a velocidade mínima? |

As duas regressões são sobre RAM do mesmo trecho do edital de SP. Compartilham fonte e não representam duas evidências independentes de generalização. A fusão dos rankings retirou o trecho esperado do top 5; reduzir ruído lexical, lidar com referências a páginas/itens e agregar trechos sobrepostos são hipóteses para outra versão, não correções já demonstradas.

### Dez erros restantes da v2

| ID | Trecho esperado no top 10 lexical / semântico | Diagnóstico observado |
|---|---|---|
| pilot-01 | 8 / 3 | Entrou nos candidatos, mas ficou fora do top 5 final |
| pilot-02 | ausente / 3 | Entrou nos candidatos, mas ficou fora do top 5 final |
| pilot-06 | ausente / 7 | Entrou nos candidatos, mas ficou fora do top 5 final |
| pilot-11 | ausente / ausente | Não entrou no conjunto de candidatos |
| pilot-16 | ausente / ausente | Não entrou no conjunto de candidatos |
| pilot-17 | ausente / ausente | Não entrou no conjunto de candidatos |
| pilot-19 | ausente / ausente | Não entrou no conjunto de candidatos |
| pilot-21 | ausente / ausente | Não entrou no conjunto de candidatos |
| pilot-23 | ausente / ausente | Não entrou no conjunto de candidatos |
| pilot-32 | 4 / ausente | Entrou nos candidatos, mas ficou fora do top 5 final |

Um erro de ID conhecido não prova que todos os resultados eram irrelevantes: há tabelas/anexos repetidos e os rótulos não enumeram todas as evidências equivalentes. Mesmo encontrar uma citação não garante interpretação correta. Revisão de fontes/retificações, rótulos completos e teste reservado por edital continuam pendentes.

## Reprodução

Na raiz do projeto, com o mesmo corpus preparado/carregado e diretório privado:

```powershell
.\.venv\Scripts\python.exe ops/evaluate-retrieval.py datasets/evaluation/pilot-v2.json datasets/manifests/4f8ddffaa01b6a20.json --lexical-strategy all --report reports/retrieval-baseline-v1.json
.\.venv\Scripts\python.exe ops/evaluate-retrieval.py datasets/evaluation/pilot-v2.json datasets/manifests/4f8ddffaa01b6a20.json --lexical-strategy any --report reports/retrieval-experiment-v2.json
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
```

Para conservar as evidências originais, escolha nomes novos em `--report` ao repetir. Relatórios registram hashes do conjunto, manifesto, código/modelo, bibliotecas, protocolo, resultados individuais e candidatos. O código atual pode reproduzir as duas estratégias; os hashes de código originais diferem porque foram registrados antes das alterações seguintes. Os dados aprovados e embeddings permaneceram iguais.

## Verificação e custo

32 testes passaram; verificações no banco confirmaram filtros por edital/snapshot, entrada semelhante a SQL injection e os dois snapshots preservados. As 30 evidências também foram conferidas contra texto, página e hash no PostgreSQL antes da avaliação. As pesquisas usaram o papel `radar_loader`, não administrador. Não houve chamadas Groq: custo de API nesta etapa igual a zero; custo de CPU/energia local não estimado. Nenhuma resposta gerada, taxa de alucinação ou desempenho de recusa foi avaliado.

[Linha de base](../reports/retrieval-baseline-v1.json) · [Experimento v2](../reports/retrieval-experiment-v2.json) · [Comparação e erros](../reports/retrieval-comparison-v1-v2.json) · [Segurança no escopo](../reports/seguranca-avaliacao-2026-10-01.md)

Próximo passo: integrar geração com fontes e recusa, definir modelo/orçamento Groq e avaliar as respostas nos 40 casos. Manter o registro das dez falhas de busca para distinguir contexto insuficiente de erro de interpretação.

## Evolução v3 e v4 — 2026-10-01

Mesmos 30 casos aprovados, snapshot, embeddings, dez candidatos por ramo e cinco resultados finais. Nenhuma resposta esperada alimenta a busca. Acrescentado planejamento determinístico da consulta: retirar palavras de pergunta e identidade do órgão já delimitado pelo edital; usar página, número de arquivo ou cláusula somente quando escritos na pergunta.

| Versão | Lexical Hit@5 | Semântica Hit@5 | Híbrida Hit@5 |
|---|---:|---:|---:|
| v2: OR, pergunta original | 18/30 | 17/30 | 20/30 |
| v3: consulta focada, sem filtros de localização | 24/30 | 25/30 | 24/30 |
| v4: consulta focada + localização explícita | **29/30** | **28/30** | **29/30** |

Metas solicitadas: pelo menos 25/30 em cada ramo e 28/30 na híbrida. v4 atende às três neste conjunto de desenvolvimento. 28/30 = 93,3%; 29/30 = 96,7%. Não são taxas de respostas corretas nem garantia de desempenho em novas perguntas.

Treze perguntas contêm pistas de localização. A comparação v3/v4 mostra quanto essas pistas ajudam; sem os filtros, lexical e híbrida ainda não atingem a meta. É necessário um conjunto reservado por edital, com perguntas naturais sem indicação de página, antes de afirmar generalização. Não alteramos perguntas/rótulos para aumentar o resultado.

v4: mediana lexical 59,9 ms, semântica 63,2 ms e híbrida 63,4 ms; p95 80,3 / 80,2 / 77,8 ms. Medição local aquecida, uma passagem, sem geração. Apoio da citação conhecida: 29/30 nos três modos; a semântica pode recuperar passagem equivalente na mesma página sem acertar o ID rotulado.

Erros restantes de ID conhecido: lexical e híbrida pilot-11; semântica pilot-04 e pilot-21. Anexos repetidos e referências não exaustivas exigem revisão antes de considerar evidência alternativa correta. O perfil estruturado passa a ser o padrão; original e focused permanecem disponíveis para comparação.

```powershell
.\.venv\Scripts\python.exe ops/evaluate-retrieval.py datasets/evaluation/pilot-v2.json datasets/manifests/4f8ddffaa01b6a20.json --query-profile focused --report reports/retrieval-focused-v3-repeat.json
.\.venv\Scripts\python.exe ops/evaluate-retrieval.py datasets/evaluation/pilot-v2.json datasets/manifests/4f8ddffaa01b6a20.json --query-profile structured --report reports/retrieval-structured-v4-repeat.json
```

[Experimento v3](../reports/retrieval-focused-v3.json) · [Experimento v4](../reports/retrieval-structured-v4.json). Os hashes registram o código no momento de cada execução; a promoção posterior do padrão modifica o hash do arquivo, sem alterar a configuração explícita desses experimentos.

## Primeira execução das dez perguntas reservadas — 2026-10-01

Renê aprovou as perguntas e referências antes da execução. Foram 30 buscas locais, dez por modo, usando a versão congelada do pipeline. Nenhuma chamada nova à Groq. Perguntas sem página/arquivo/cláusula, em quatro editais e quatro PDFs ausentes do piloto anterior, SP/PR/RS. Os documentos já estavam indexados: este teste **não mede crescimento da base**.

| Modo | Referência conhecida no top 5 | Todas as passagens esperadas no top 5 | Mediana local |
|---|---:|---:|---:|
| Palavras-chave | 8/10 (80%) | 7/10 (70%) | 71,33 ms |
| Semântico | 7/10 (70%) | 7/10 (70%) | 71,33 ms |
| Híbrido | 9/10 (90%) | 8/10 (80%) | 82,37 ms |

Na híbrida, reserve-06 recuperou uma das duas referências: ambas estavam entre os candidatos, mas uma ficou fora dos cinco trechos finais. Em reserve-08 a referência estava entre candidatos semânticos e ficou fora da seleção final. São problemas observados de seleção/cobertura, não evidência de documento ausente. Um reranker ou contexto de tabela/seção será experimento futuro; nenhum ganho dessas alternativas foi medido.

O protocolo e os rótulos foram preservados após observar resultados. O campo genérico `dataset_role` do avaliador ainda diz desenvolvimento; o registro específico da reserva documenta separação por edital/PDF e congelamento antes da primeira execução. Depois de usar esses erros para ajustar o sistema, outra reserva será necessária.

A amostra é pequena e concentrada em três estados. Hit@5 de 90% não é 90% de respostas completas/corretas nem garantia em documentos futuros. Geração das dez perguntas e conferência independente dos PDFs seguem pendentes.

[Resultados por caso](../reports/retrieval-reserve-v1.json) · [Protocolo congelado](../reports/reserve-protocol-v1.json) · [Referências aprovadas](perguntas-reserva-para-revisao.md).

## Experimento: cobertura de termos na seleção — 2026-10-01

Implementada opção `coverage`, mantendo `rrf` como padrão. Aos mesmos candidatos (dez por ramo) acrescenta bônus 0,02 × fração dos termos distintos da pergunta presentes no trecho. Usa somente pergunta/trechos, com normalização de acentos e stopwords. Não usa respostas esperadas, IDs de casos ou regras por edital. É uma heurística lexical de reordenação, não modelo cross-encoder nem extração de tabelas.

Executadas 120 consultas: 30 perguntas antigas + dez da antiga reserva, cada uma em três modos. Referências e corpus preservados.

| Grupo | Modo | Hit@5 anterior → experimento | Todas as passagens anterior → experimento |
|---|---|---:|---:|
| Antigas (30) | Palavras-chave | 29 → 29 | 29 → 29 |
| Antigas (30) | Semântico | 28 → 28 | 29 → 29 |
| Antigas (30) | Híbrido | 29 → 29 | 29 → 29 |
| Novas (10) | Palavras-chave | 8 → 8 | 7 → 7 |
| Novas (10) | Semântico | 7 → 8 | 7 → 7 |
| Novas (10) | Híbrido | 9 → 9 | 8 → 8 |

Na semântica, reserve-08 ganhou evidência, mas reserve-06 perdeu cobertura completa. O total de completude ficou igual. A híbrida não resolveu reserve-06/reserve-08. **Decisão: manter RRF como padrão; alternativa apenas experimental.** Não ajustar peso repetidamente buscando nota nesses casos. Uma próxima intervenção deverá avaliar contexto com identidade de item/cabeçalho e preservação de tabela, além de outra reserva realmente nova.

Como os erros da reserva agora orientaram a criação do experimento, as dez perguntas passam a conjunto de desenvolvimento; não apresentar o resultado posterior como teste independente. Nenhum novo documento foi adicionado. Latências vêm de execução única em momentos diferentes, sem controle da carga; não afirmar ganho de velocidade.

[Comparação por caso](../reports/retrieval-coverage-comparison-v1.json) · [Execução antigas](../reports/retrieval-coverage-pilot-v1.json) · [Execução novas](../reports/retrieval-coverage-reserve-v1.json).

```powershell
.\.venv\Scripts\python.exe ops/evaluate-retrieval.py datasets/evaluation/reserve-candidates-v1.json datasets/manifests/4f8ddffaa01b6a20.json --query-profile structured --lexical-strategy any --selection-profile coverage --report reports/retrieval-coverage-reserve-repeat.json
```

## Ampliação de contexto na página original

120 consultas locais: híbrida preservou Hit@5 29/30 e 9/10; cobertura de todas as passagens passou 29/30 →30/30 e 8/10 →9/10, sem regressões nessa medida. Sem novo vetor/corpus/ranking. Janela acrescenta texto vizinho na mesma página e mantém offsets originais. Não reconstrói tabela e não prova ligação correta entre todos os itens. [Implementação, reprodução e limites](contexto-e-citacoes.md) · [Comparação](../reports/retrieval-window-comparison-v1.json).
