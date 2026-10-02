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
