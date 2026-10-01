# Geração na base candidata — 2026-10-01

Após autorização explícita de Renê ("pode prosseguir" para o lote solicitado), foram executados os dez novos casos na API oficial HTTPS da Groq, modelo GPT-OSS120B, conta gratuita confirmada pelo usuário. Mantidos configuração, referência, ranking e contexto congelados; até cinco passagens por pergunta. Nenhuma resposta esperada ou credencial no prompt. Sem repetição ou ajuste após observar respostas.

## Resultado operacional

- Dez chamadas, zero falhas/rejeições nesta execução.
- Seis respostas e quatro abstenções por evidência insuficiente (02,03,05,06).
- Dez resultados passaram pela validação de integridade das citações. Abstenções não contam como respostas corretas às perguntas respondíveis.
- 27.913 tokens de entrada e1.835 de saída; mediana de geração907,18ms (não inclui toda a consulta).
- Cobrança efetiva não auditada; não foi estimado custo monetário a partir da declaração de plano gratuito.
- Acerto humano permanece sem pontuação. Candidata não promovida; regra de90% bloqueada.

## O que a conferência do assistente encontrou

| Caso | Achado | Consequência |
|---|---|---|
| 02 | Não recuperou integralmente a divisão entre28 notebooks e7 da cota | Melhorar diversidade e identidade dos itens |
| 03 | A prévia enviada contém UNID02, mas o modelo declarou quantidade ausente | Melhorar representação de tabelas e interpretação, além da busca |
| 05 e06 | Informações do item alvo ausentes/incompletas no contexto | Vínculo geral de item e continuação de páginas |
| 07 | Garantia na página62 pertence à repetição do mesmo desktop21, conferida visualmente nas páginas60–62 | Referências conhecidas não enumeram toda evidência válida |
| 08 | Informou menor preço e aberto, omitiu por item | Avaliar completude campo a campo |
| 10 | Página62 identifica explicitamente Item1 Cloud Connect e repete RAM exigida | Fonte alternativa legítima, conferida visualmente |

01,04 e09 apresentam os valores esperados na conferência do assistente; não são notas de aprovação humana. No01 há citações redundantes. No07 a identidade foi conferida seguindo páginas anteriores, não está explícita na passagem enviada. No10 o texto da resposta simplifica superior performance como superior; revisar a redação na conferência humana.

A primeira cobertura conhecida permanece5/10 nos três modos; não alteramos referência nem resultados para elevar retrospectivamente a nota. Os casos07/10 mostram por que essa medida não equivale a correção: um PDF pode repetir requisitos em páginas não enumeradas pelo gabarito. A publicação mantém separados resultados automáticos, achados do assistente e revisão humana.

## Próximo passo

Conferir as respostas na ficha privada, que inclui fontes e páginas. Depois, implementar regras gerais de identidade do item, reconstrução de tabelas e diversidade das passagens; estes erros passam a desenvolvimento. Outra reserva independente e amostra ampliada são necessárias para medir a meta de90%. Não inserir páginas ou IDs especiais dessas perguntas no recuperador.

Respostas brutas e ficha permanecem fora do repositório; abstenções são apresentadas pelo produto com mensagem neutra, sem afirmar fatos não citados contidos na justificativa privada do modelo.

## Evidências

- [Autorização específica](../reports/independent-generation-authorization-v1.json)
- [Resumo da execução](../reports/generation-growth-summary-v1.json)
- [Achados do assistente](../reports/generation-growth-review-v1.json)
- [Regra de promoção após geração](../reports/quality-growth-generated-v1.json)
- [Método da recuperação congelada](avaliacao-de-crescimento.md)
- [Segurança desta etapa](../reports/seguranca-geracao-candidata-2026-10-01.md)

Reprodução: ops/evaluate-generation.py datasets/evaluation/independent-bound-v1.json --confirm-free-plan --limit 10 --interval 35 --variant alias_window (usar caminhos reais e argumentos separados); summarize-generation.py e prepare-generation-review.py com a mesma referência/variante. A reprodução requer dados privados preparados, PostgreSQL local e credencial privada; não é um comando autossuficiente de uma clonagem pública. A API pode produzir respostas diferentes entre execuções.
