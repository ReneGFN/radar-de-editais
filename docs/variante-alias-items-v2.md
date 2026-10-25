# Variante `alias_items_v2` — correções gerais antes do holdout (2026-10-02)

Estado: **implementada e testada offline; não executada na Groq**. A execução nos 50 casos de desenvolvimento depende de autorização explícita. O holdout não foi usado em nada: nem para escrever regras, nem para testar, nem para recuperar trechos.

## O que muda em relação a `alias_items`

A recuperação é a mesma (perfil `item_structure`, busca híbrida, 5 trechos, snapshot `1446c44aca18011a`). A prévia privada confirmou que as 50 cargas de usuário (pergunta + trechos) são idênticas às de `alias_items`. Portanto Hit@5 e tempo de recuperação não mudam por construção; a comparação real será só na geração.

Mudam duas coisas:

1. **Prompt v2** (`system_prompt(..., 'v2')` em `backend/src/radar/generation.py`). Acrescenta regras para os padrões observados:

| Problema observado | Regra nova |
|---|---|
| Respostas repetitivas ("o item 1 tem SSD…", "o item 1 tem RAM…") | uma afirmação por item, agrupando atributos com as fontes de todos |
| independent-06: MT/s tratado como MHz; CL40 lido como mínimo; JEDEC 4800 omitido | copiar unidade literal; não equiparar MT/s e MHz; só dizer mínimo/máximo se o documento disser; incluir compatibilidade/padrão citado |
| independent-08: "menor preço" sem "por item" | manter qualificador literal (por item, por lote, por grupo, global) |
| independent-02: abstenção na divisão ampla concorrência × cota | ler tabela de cota e informar cada parte por item |
| pilot-17: SSD de dois itens juntados | sem item identificado e valores diferentes: listar por item e pedir o item |
| pilot-35: recusa de garantia saiu como `answered` | garantia de resultado/aceitação/ausência de risco é `refused` |

2. **Guardas determinísticas** (`semantic_guards`, só na v2). Rejeitam a resposta, como o validador de citação já faz, quando:
   - um número com MHz/MT/s na resposta aparece na fonte só com a outra unidade, ou a resposta equipara as duas unidades sem que a fonte faça o mesmo;
   - a resposta chama CL de mínimo/máximo sem essa palavra perto do CL na fonte;
   - a resposta diz "menor preço" sem qualificador, mas a fonte tem o qualificador ao lado ou marcado no quadro ("Por item ( X )").

Uma resposta rejeitada conta como falha, não como acerto. As guardas não reescrevem o texto do modelo.

Para pilot-35, além da regra no prompt, o resumo da revisão humana passou a separar o estado técnico do comportamento: `effective_behavior` por caso e `technical_status_mismatch` no grupo de recusas (`backend/src/radar/human_review.py`).

`alias_items` está preservada: o prompt v1 é reproduzido byte a byte (o teste compara o hash com o prompt efetivamente enviado, `acbd9874…`), e os checkpoints de `alias_items` não foram tocados. A v2 grava em arquivos próprios (`evaluation-<hash>-alias_items_v2.json`).

## Como foi verificado

- 14 testes em `backend/tests/test_generation_v2.py`. Cada guarda tem um teste que falha com o erro e um que passa com a forma correta.
- **Reaplicação offline** das guardas às 50 respostas já geradas por `alias_items`: barraram exatamente independent-06 (unidade) e independent-08 (qualificador), e nenhuma das outras 48, inclusive as 46 julgadas corretas. A primeira versão das guardas não barrou nada; foi corrigida depois de ver que a fonte do 06 tem "5600MHz" em outro ponto e que o 08 marca "Por item ( X )" num quadro.
- `ops/evaluate-generation.py` recusa qualquer referência dentro de `datasets/holdout/` (teste de subprocesso).
- Prévia privada `alias-items-v2-request-preview.json`: 50 pedidos, sem padrão de chave, sem a chave real, sem gabarito no prompt. Protocolo público: `reports/generation-protocol-alias-items-v2.json` (hashes de código, referências, prompt e prévia).

## Limitações

- As regras de prompt para 02, 17, 35 e para o tamanho das respostas não têm teste de comportamento sem chamar o modelo. Instrução de prompt já falhou antes em defeitos de coerência; só a execução e a revisão humana dirão se funcionaram.
- As guardas foram escritas olhando os erros do desenvolvimento. Elas só barram o erro; não fazem a resposta ficar certa.
- O prompt v2 tem 2.803 caracteres contra 1.397 do v1: cerca de 400 tokens de entrada a mais por chamada (estimativa, não medida).
- Possível regressão: uma resposta correta que use "por item" escrito de outro jeito ("item a item") seria barrada. Não ocorreu nos 50 casos.

## Critério de decisão após a execução

Comparar `alias_items_v2` contra `alias_items` nos mesmos 50 casos, com revisão humana só das respostas que mudarem. Se não houver melhora verificável em correção/completude, ou houver regressão relevante (acertos perdidos, recusas inseguras, rejeições novas, latência), `alias_items` continua padrão.


## Execução autorizada — 50 chamadas (2026-10-02)

Renê autorizou "as 50 chamadas Groq da v2". Uma tentativa por caso, `max_retries=0`, 35 s de intervalo, nenhum HTTP 429. Comparação: [`reports/variant-comparison-alias-items-v2.json`](../reports/variant-comparison-alias-items-v2.json) (só ids, estados e números; as respostas ficam na ficha privada `comparacao-alias-items-v2.md`).

| Medida (50 casos de desenvolvimento) | alias_items | alias_items_v2 |
|---|---:|---:|
| Factuais respondidas (de 40) | 39 | 38 |
| Rejeitadas pelo validador | 0 | 2 (pilot-22 estado incoerente; independent-08 qualificador omitido) |
| Mediana de afirmações por resposta | 1 | 1 (17 casos com menos afirmações, 1 com mais) |
| Mediana de caracteres da resposta | 115,5 | 111,5 |
| Tokens de entrada / saída (total) | 117.498 / 8.651 | 128.312 / 7.815 |
| Mediana de geração / total por caso | 866 / 1.018 ms | 928 / 1.081 ms |
| Respostas idênticas | — | 1 de 50 |

Mudanças de estado: pilot-35 `answered` → `refused`; pilot-36 `insufficient_evidence` → `refused`; independent-02 `insufficient_evidence` → `answered`; pilot-22 e independent-08 → `rejected`.

Leitura do assistente, que **não é nota humana**:

- melhorou: pilot-35 recusa a garantia; independent-06 não mistura mais unidades nem chama CL40 de mínimo; respostas mais agrupadas (ex.: 06 numa linha só);
- não resolveu: independent-06 ainda omite JEDEC 4800 MT/s; independent-08 ainda omitiu "por item" (a guarda barrou); pilot-17 agora separa os itens, mas os chama de "Item 1/Item 2" em vez de 29/30 e não pede o item;
- piorou: independent-02 trocou abstenção por valor errado (21 em ampla concorrência; a referência diz 28), que é pior que abster-se; pilot-22, correto na v1, foi rejeitado; pilot-36 deixou de informar a garantia de 12 meses que a fonte dá;
- custo: +9% de tokens de entrada e +7% na mediana de geração.

Decisão: **`alias_items` continua padrão**. Não há melhora verificável sem revisão humana, e há regressões visíveis (02, 22). Fichas em branco da v2 criadas no privado (`human-review-*-alias_items_v2.json`); a revisão humana decide o resultado final.
