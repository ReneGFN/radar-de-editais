# Variante `alias_items_v3` — correções de pilot-22, pilot-36 e independent-02 (2026-10-02)

Estado: **implementada e testada offline; não executada na Groq**. Precisa de nova autorização para as 50 chamadas nos conjuntos de desenvolvimento. O holdout não foi usado.

A v3 é a v2 mais três correções. `alias_items` (v1) e `alias_items_v2` ficam preservadas: os testes conferem o hash do prompt v1 contra o que foi enviado (`acbd9874…`) e o do prompt v2 contra o publicado em `reports/generation-protocol-alias-items-v2.json`. A recuperação continua igual: as 50 cargas de usuário da prévia v3 são idênticas às da v2.

## Causa de cada falha da v2 e correção

| Caso | O que aconteceu na v2 (diagnóstico privado) | Correção na v3 |
|---|---|---|
| pilot-22 | O modelo devolveu `insufficient_evidence` **com** uma afirmação correta e citada (30 dias a partir da Autorização de Fornecimento), e disse em `reason` que faltava o marco inicial. O validador exige que só `answered` tenha afirmações, então descartou tudo. | **Resposta parcial**: na v3, `insufficient_evidence` com afirmações verificadas vira `answered` com `partial_answer: true`; a lacuna de `reason` é acrescentada ao texto e `model_status` guarda o estado original. Regra de prompt: se as fontes respondem em parte, use `answered` e diga o que falta. |
| pilot-36 | O schema obrigava recusa com `claims` vazio, então o modelo não podia citar a garantia real de 12 meses. A v1 só a mencionava em `reason`, sem fonte. | **Recusa com fato da fonte**: na v3, `refused` pode ter afirmações, cada uma com citação verificada como em qualquer resposta. O texto renderizado é `reason` + afirmações. Regra de prompt: ao recusar alterar ou omitir o documento, inclua o que a fonte realmente diz. |
| independent-02 | A tabela tem a linha do item 3 com 28 UND e a do item 4 com 7 UND, marcada "COTA 25%". O modelo tratou 28 como total e respondeu 28 − 7 = 21 para ampla concorrência. | **Guarda de quantidade** (`quantity_guard`): número seguido de unidade (unidades, UND, notebooks, computadores…) precisa aparecer isolado na fonte citada; número dentro de preço (R$ 21,50) não conta. Regra de prompt: não calcular quantidades; na tabela, a linha marcada como cota traz a cota e a outra traz a ampla concorrência. |

## Verificação

- 10 testes em `backend/tests/test_generation_v3.py`. Cada correção tem teste que falha antes (v1/v2 rejeitam, guarda barra a conta) e passa depois. Suíte completa: 178 passaram.
- Revalidação do diagnóstico privado do pilot-22 da v2 com a regra v3: aceito como `answered` parcial, com 1 afirmação citada.
- Reaplicação das guardas v3 às respostas existentes, sem Groq:
  - `alias_items`: barra só independent-06 e 08, como antes;
  - `alias_items_v2`: barra só independent-02 (o "21 unidades");
  - nenhuma outra resposta foi barrada pela guarda nova de quantidade, inclusive as julgadas corretas.
- Prévia privada `alias-items-v3-request-preview.json`: 50 pedidos, sem padrão de chave, sem a chave real, sem gabarito no prompt. Protocolo: `reports/generation-protocol-alias-items-v3.json`.

## Limitações e riscos

- A guarda de quantidade impede que o "21" passe, mas não faz o modelo acertar 28/7. Se o modelo insistir na conta, o caso 02 vira `rejected` (falha segura), não acerto.
- Resposta parcial muda a contagem: casos que antes eram abstenção podem virar `answered` parcial. A revisão humana precisa julgar se a parte respondida está completa para a pergunta; `partial_answer` fica visível para isso.
- Recusa com afirmações aumenta a superfície: o texto do modelo em recusa agora pode trazer fatos. Eles passam pela mesma verificação literal de citação, e o pedido indevido continua recusado.
- O prompt v3 é maior que o v2; o custo extra em tokens não foi medido.
- As três correções foram desenhadas olhando estes casos do desenvolvimento. Só o holdout, depois, mede generalização.

## Critério de decisão

Igual ao da v2: comparar v3 contra `alias_items` nos mesmos 50 casos (`ops/compare-variants.py --candidate alias_items_v3`) e só trocar o padrão com melhora verificável e sem regressão relevante após revisão humana.


## Execução (2026-10-03)

- 51 chamadas à Groq no total para 50 casos: 20 na primeira tentativa (pilot-20 recebeu HTTP 429 e a execução parou) e 31 na retomada autorizada, sem 429. Nenhum caso aceito foi repetido; `max_retries=0`.
- Estados factuais (40): `alias_items` 39 respondidas, v2 38, v3 38. Na v3, `independent-02` foi barrado pela verificação de quantidade (`Quantidade sem apoio literal`) e `independent-08` pela do qualificador (`Qualificador do critério omitido`). Barrado conta como erro.
- Mudanças de estado v2 → v3: `pilot-22` passou de barrado para respondido; `independent-02` passou de respondido (21, errado) para barrado.
- Mudanças de estado `alias_items` → v3: `pilot-35` `answered` → `refused`; `pilot-36` `insufficient_evidence` → `refused`; `independent-02` e `independent-08` → barrados.
- Integridade de citação: 48/48 respostas aceitas com citação íntegra. Isso não é correção semântica.
- Tokens de entrada (total): `alias_items` 117.498, v2 128.312, v3 134.569 (+14,5% sobre `alias_items`). Saída: 8.651 / 7.815 / 8.211.
- Geração (mediana): 866 / 928 / 930 ms. Recuperação inalterada (mesmas entradas).
- Relatórios públicos: `reports/variant-comparison-alias-items-vs-alias-items-v3.json` e `reports/variant-comparison-alias-items-v2-vs-alias-items-v3.json` (só ids, estados e números).

Leitura do assistente, não nota humana: `pilot-22` e `pilot-36` parecem resolvidos; `pilot-17` agora separa os itens 29 e 30 com os números certos, mas não pede o item; `independent-06` não mistura mais unidades nem chama CL40 de mínimo, mas segue sem a compatibilidade JEDEC 4800 MT/s; `independent-02` e `independent-08` ficam seguros (barrados) mas sem resposta certa.

Decisão: `alias_items` continua padrão até a revisão humana das fichas `human-review-*-alias_items_v3.json` (privadas, em branco).


## Decisão e revisão humana — 2026-10-03

**Decisão de Renê: `alias_items` continua como variante padrão.** `alias_items_v2` e `alias_items_v3` ficam preservadas (código, protocolos, checkpoints privados, comparações, testes e documentação) como evidência de iteração. A v3 fica registrada como **variante experimental de segurança, revisada por humano e não promovida**.

| Medida (50 casos de desenvolvimento) | alias_items | v2 | v3 |
|---|---:|---:|---:|
| Factuais aceitas (de 40) | 39 | 38 | 38 |
| Tokens de entrada | 117.498 (50 casos) | 128.312 (48) | 134.569 (48) |
| Geração, mediana | 866 ms | 928 ms | 930 ms |
| Total, mediana | 1.018 ms | 1.081 ms | 1.064 ms |
| Revisão humana | 36/40 factuais, 10/10 recusas | não avaliada | casos abaixo |

Tokens e latências de v2/v3 contam só respostas aceitas; não é comparação 1:1 de custo.

Achados humanos da v3 (Renê confirmou a análise do assistente):
- Corrigiu: pilot-35 (recusa a garantia indevida), pilot-36 (recusa citando o fato documentado), pilot-22 (estado técnico de resposta parcial).
- Barrou, erro seguro mas ainda erro: independent-02 (quantidade sem apoio), independent-08 (omissão de "por item").
- Ainda falha: independent-06 (omite JEDEC 4800 MT/s), pilot-17 (não resolve a ambiguidade do item).
- Regressões frente ao padrão: uma factual aceita a menos, mais tokens, mais latência.

Como foi registrado: critérios caso a caso nas fichas privadas da v3 para os cinco casos com julgamento explícito (22, 17, 35, 36, independent-06); 02 e 08 não recebem nota porque foram barrados e contam como não aprovados. Os outros 43 ficaram sem critérios caso a caso, porque a revisão declarada não julgou cada um; por isso a taxa da v3 não é calculada. Resumos públicos: `reports/human-review-pilot-alias-items-v3-review-v1.json` e `reports/human-review-independent-alias-items-v3-review-v1.json`. Gate: `reports/quality-gate-v2.json`.

## Execução — relatório separado do protocolo

O protocolo `reports/generation-protocol-alias-items-v3.json` continua com `prepared_before_execution_awaiting_user_authorization`, sem edição: ele descreve o que foi congelado antes. O que aconteceu depois está em `reports/generation-execution-alias-items-v3.json` (gerado por `ops/report-generation-execution.py`, que lê os checkpoints privados e grava só agregados):

- 51 chamadas para 50 casos: 20 na primeira execução, parada pelo HTTP 429 na tentativa do pilot-20; 31 na retomada autorizada, incluindo nova tentativa do pilot-20.
- Nenhum caso aceito repetido; 50 casos concluídos: 48 aceitos e 2 barrados pelo validador.
- Estados no piloto: 30 respondidas, 7 recusas, 3 evidência insuficiente; nos novos: 8 respondidas e 2 barradas.
- Consumo da tentativa com 429 e das barradas não registrado; faturamento não auditado independentemente.

O script de prévia `ops/preview-generation-v3.py` reescreveria o protocolo se executado de novo. Ele não foi alterado, porque o próprio protocolo guarda o hash desse arquivo; não executar de novo.
