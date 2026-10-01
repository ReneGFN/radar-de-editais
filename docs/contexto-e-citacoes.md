# Contexto por página e citação selecionada pelo servidor

## O que foi implementado

Duas opções experimentais, mantendo o padrão antigo:

1. `context_profile=page_window`: busca os mesmos cinco trechos e amplia cada um na mesma página original, até 350 caracteres antes e 650 depois, limitado a 2.000 caracteres. Consulta por snapshot/edital/arquivo/página parametrizada, só leitura. Preserva ID do trecho âncora e registra seus offsets antigos, mais offsets da janela. Verifica que o trecho original coincide com a página antes de ampliar. Não junta páginas nem altera PDF, embeddings ou snapshot.
2. `citation_mode=source_id`: o modelo seleciona identificadores de fontes para as afirmações; o backend insere a passagem original completa daquela janela. A validação literal existente continua ativa. Não há reparo de citação inventada, geração de quote por IA ou aprovação automática da interpretação. Fonte verdadeira pode acompanhar afirmação errada; o teste explicitamente conserva esse limite.

Isso recupera texto vizinho que a divisão em trechos deixou de fora e elimina a necessidade de o modelo copiar uma passagem longa sem abreviar. Os IDs continuam identificando âncoras, não hashes da nova janela: conteúdo/offsets/context_profile precisam acompanhar o resultado para reprodução.

## O que ainda não faz

A janela não é um extrator de tabelas: não reconstrói células nem demonstra qual especificação pertence a qual item. Pode trazer outro item vizinho e aumentar ruído/consumo. Não atravessa páginas; cabeçalho distante pode continuar ausente. Leitura humana da tabela e associação explícita de itens ainda são necessárias.

A passagem exibida em `source_id` é escolhida pelo servidor como contexto da fonte selecionada; não é uma citação curta escolhida pelo modelo para demonstrar cada afirmação. Sustentação semântica continua pendente. Citações maiores tornam a conferência mais trabalhosa; a apresentação futura poderá destacar a passagem pertinente sem alterar o original.

## Resultado local de recuperação

120 consultas nos mesmos 30+10 casos, três modos. Sem reordenação, sem geração nesta etapa e sem alterar referências.

| Grupo | Modo | Hit@5 | Todas as passagens esperadas: antes → janela |
|---|---|---:|---:|
| Antigas | Palavras-chave | 29/30 | 29/30 → 29/30 |
| Antigas | Semântico | 28/30 | 29/30 → 29/30 |
| Antigas | Híbrido | 29/30 | 29/30 → 30/30 |
| Desenvolvimento (10) | Palavras-chave | 8/10 | 7/10 → 9/10 |
| Desenvolvimento (10) | Semântico | 7/10 | 7/10 → 7/10 |
| Desenvolvimento (10) | Híbrido | 9/10 | 8/10 → 9/10 |

Ganho híbrido em pilot-11 e reserve-06, sem regressões na cobertura destas referências. A coluna Hit@5 acompanha IDs de âncora e não muda por ampliar texto. 100% de cobertura nas antigas não é 100% de respostas corretas. As dez perguntas já são desenvolvimento; crescimento real e nova reserva ainda não avaliados. Não comparar latências como ganho causal: são execuções únicas em momentos diferentes; a janela acrescenta leitura de páginas.

[Resultados por caso](../reports/retrieval-window-comparison-v1.json).

## Reprodução

```powershell
.\.venv\Scripts\python.exe ops/evaluate-retrieval.py datasets/evaluation/reserve-candidates-v1.json datasets/manifests/4f8ddffaa01b6a20.json --query-profile structured --lexical-strategy any --context-profile page_window --report reports/retrieval-window-reserve-repeat.json
# Executar somente com plano gratuito confirmado e autorização de envio dos casos:
.\.venv\Scripts\python.exe ops/evaluate-generation.py datasets/evaluation/reserve-candidates-v1.json --confirm-free-plan --limit 10 --interval 35 --variant source_window
```

Checkpoint e ficha privadas da variante têm sufixo `source_window`, preservando o primeiro lote. A geração compara contexto e modo de citação juntos; não atribuir eventual ganho exclusivamente a um deles. O corpus e as perguntas permanecem iguais.

## Resultado da geração com janela e fonte literal — 2026-10-01

Nos mesmos dez casos autorizados: nove answered aceitos e um bloqueado por identificadores de fonte abreviados/inválidos (reserve-10). Antes: seis answered, uma insufficient_evidence e três bloqueios. Sem tentativas extras para esconder falha. Não houve bloqueio por quote abreviada na nova variante; passage original é inserida pelo servidor. Isso não certifica sustentação semântica.

Revisão do assistente observou referência e condições alinhadas em reserve-01–07/09, incluindo condições completas da garantia em reserve-05 e citações na página do lote 3 em reserve-06/07. reserve-08 responde os valores esperados mas cita páginas repetidas; identidade do item exige conferência. Nenhuma nota humana atribuída. Nove saídas aceitas não comprovam 90% de precisão de respostas.

Nas sete saídas aceitas comuns às duas execuções, tokens de entrada passaram de 10.273 para 18.994 (+84,9%). São medições de uma execução, sem repetições; quantidade exata de fontes escolhidas varia. Totais da variante (nove aceitas): 24.911 entrada e 2.987 saída; mediana modelo 1.314,38 ms. Consumo da rejeição/faturamento não confirmado. Plano gratuito informado pelo usuário. Não chamar volume de tokens de custo monetário comprovado.

A geração mudou contexto e modo de evidência conjuntamente. O experimento de recuperação isolou a janela; a geração não separa causalmente o efeito das duas mudanças. Referências, corpus e checkpoint antigo preservados, sem crescimento real da base. Novas opções permanecem experimentais; padrão anterior mantido até avaliação humana e outro conjunto independente.

Após o lote, corrigido caso limite: o preenchimento anterior da janela podia cortar âncoras maiores que 1.650 caracteres. Padding agora prioriza conservar a âncora inteira dentro de 2.000. Âncoras avaliadas tinham no máximo 638 caracteres, portanto as janelas medidas não mudam com essa correção. 85 testes passaram. Protocolo registra hashes usados durante lote e hashes finais.

Diagnóstico privado de rejeição era nomeado só pela pergunta e o candidato de reserve-10 do primeiro lote foi sobrescrito pelo segundo. Checkpoints/métricas antigos permaneceram íntegros. Corrigida nomeação futura com contexto, modo de citação e sufixo único; não afirmar preservação retroativa daquele diagnóstico.

Próximo experimento: rótulos curtos de fonte mapeados pelo servidor, mantendo IDs reais na rastreabilidade; vínculo explícito de itens/cabeçalhos e teste independente de tabelas em nova reserva. Ainda não implementados.

[Resumo operacional](../reports/generation-window-summary-v1.json) · [Revisão e comparação](../reports/generation-window-review-v1.json) · [Protocolo](../reports/generation-window-protocol-v1.json).
