# Revisão preliminar das respostas — 2026-10-01

## Estado e critérios

Revisados localmente os 40 casos: pergunta, referência aprovada, resposta aceita e citações. Revisão do assistente, com confirmação de Renê pendente; não é pontuação humana independente. Corpus/perguntas/prompt e resultados anteriores preservados.

| Perguntas factuais (30) | Casos |
|---|---:|
| Sem divergência aparente nesta revisão | 20 |
| Detalhes de completude a conferir | 5 |
| Referência/unidade e completude a conferir | 1 |
| Erro claro de conteúdo | 2 |
| Resposta bloqueada por citação | 2 |

Os 20 não são acertos oficialmente aprovados; os seis pontos de conferência não são automaticamente erros. Definir completude pelo que a pergunta exige e confirmar condições da referência. Correção, completude e sustentação devem ser pontuadas separadamente; recusa/bloqueio em pergunta respondível entra no denominador de sucesso ponta a ponta.

## Diagnóstico e prioridades

| Caso | Observação | Tratamento para versão futura |
|---|---|---|
| pilot-11 | Respondeu 256 GB do item 16 quando a pergunta pede item 17, mínimo 500 GB. Tabela original visualmente conferida: título 512 GB, mínimo 500 GB. | Preservar identidade do item e contexto do cabeçalho; pedir esclarecimento se houver conflito. |
| pilot-12 | Respondeu duas unidades, referência 80. PDF visualmente conferido: 2 na coluna ITEM e 80 na coluna QTD. | Extrair tabela com cabeçalhos e células vinculados; não resolver quantidade pelo primeiro número da linha. |
| pilot-17 | Bloqueado por reticências; pergunta não identifica item. Página visualmente conferida contém item 29 com SSD 500 GB e item 30 com SSD 512 GB. | Revisar a pergunta/referência com Renê antes de alterar qualquer rótulo; distinguir os itens. |
| pilot-20 | Afirmação do candidato alinhada à referência, mas quote abreviada com reticências foi rejeitada. | Melhorar seleção/apresentação de evidências, mantendo o bloqueio de citações alteradas. |
| pilot-23 | Fonte escreve 512Gb; referência normaliza para GB, e formato 2280 não apareceu na resposta. | Conferir grafia/unidade no documento e alcance da pergunta; não corrigir silenciosamente o rótulo. |
| pilot-01/02/24/27/32 | Detalhes de módulo, compatibilidade, frequência, fabricante ou condições não aparecem na resposta. | Revisão humana decide se são necessários à pergunta; critérios consistentes para completude. |

As dez recusas evitaram o pedido indevido na leitura preliminar, mas utilidade/alternativa segura e explicações factuais do reason precisam de revisão. pilot-40 é pedido do usuário descrevendo instrução maliciosa; não comprova resistência a uma injeção realmente embutida em PDF. A apresentação atual usa avisos neutros para recusas, enquanto o lote original permanece registrado.

## Fontes e rastreabilidade

Revisão visual por assistente em páginas físicas: pilot-11 arquivo 2/página 26, pilot-12 arquivo 1/página 15 e pilot-17 arquivo 1/página 54. Não equivale à revisão de todos os PDFs ou retificações. Renderizações, respostas completas e dados brutos continuam privados.

- [Porto Ferreira — PDF oficial](https://pncp.gov.br/pncp-api/v1/orgaos/45339363000194/compras/2026/286/arquivos/2#page=26)
- [SSP/SP — PDF oficial](https://pncp.gov.br/pncp-api/v1/orgaos/46377800000127/compras/2026/4170/arquivos/1#page=15)
- [Descalvado — PDF oficial](https://pncp.gov.br/pncp-api/v1/orgaos/46732442000123/compras/2026/103/arquivos/1#page=54)

[Classificações sem textos brutos](../reports/generation-review-v1.json) · [Resultado do critério de promoção](../reports/quality-release-v1.json) · [Dez perguntas naturais aprovadas](perguntas-reserva-para-revisao.md).

## Dez perguntas novas na Groq — 2026-10-01

Autorização explícita de Renê registrada antes das dez chamadas ao GPT-OSS 120B. Seleção padrão RRF, até cinco trechos por pergunta; rótulos não entram no prompt. Uma tentativa por caso, sem repetição para esconder falhas.

- Seis respostas answered passaram pelo validador literal.
- Uma insufficient_evidence passou: reserve-07 não recebeu ligação explícita entre especificação e lote 3.
- Três respostas rejeitadas: reserve-08/09/10 abreviaram citações com reticências; o bloqueio foi mantido.
- Revisão do assistente: reserve-01–04 sem divergência aparente; reserve-05 exige conferir completude de peças/mão de obra/atendimento local; reserve-06 responde valores esperados, mas usa páginas repetidas sem identidade do lote clara e uma citação incompleta de capacidade.

Não publicar 7/10 como acerto: são sete saídas aceitas pelo validador, incluindo insuficiência. Correção/completude/apoio humano permanecem sem nota. As seis respostas não são automaticamente seis acertos.

Mediana da geração das sete saídas aceitas: 1.022,92 ms. Tokens das saídas aceitas: 10.273 entrada e 2.185 saída; consumo das três rejeições não incluído nesse total. Foram dez requisições tentadas, embora `generation_calls` do resumo conte somente as sete aceitas. Plano gratuito confirmado pelo usuário; faturamento não auditado independentemente.

Respostas completas/ficha de revisão privadas, sem sobrescrever a ficha do piloto: nome contém hash da referência. [Resumo operacional](../reports/generation-reserve-summary-v1.json) · [Achados por caso](../reports/generation-reserve-review-v1.json) · [Configuração/autorização](../reports/generation-reserve-protocol-v1.json).

Prioridade seguinte: preservar cabeçalhos/identidade de item ao montar contexto e testar seleção de passagens literais sem abreviação. Não relaxar validador para aceitar citações alteradas. Qualquer ajuste exige regressão e outra reserva independente; extração de tabelas e essa mudança de citação ainda não foram implementadas.
