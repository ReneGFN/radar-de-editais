# Etapa2 — avaliação da estrutura dos itens

2026-10-01. Continuidade aprovada por Renê após a parada entre etapas1 e2. Corpus candidato1446c44aca18011a, mesmas referências aprovadas, sem promoção automática.

## Recuperação no banco real

Uma repetição por modo;240 consultas para comparar janela anterior e estrutura inicial, mais120 para verificar a correção geral. Total360 buscas locais, sem chamadas externas nessa medição. Configuração e referências congeladas antes de cada execução; não sobrescrevemos resultados ruins.

|Grupo/medida|Palavras-chave|Semântica|Híbrida|
|---|---:|---:|---:|
|Fontes conhecidas completas — antigas, janela|29/30|29/30|30/30|
|Fontes conhecidas completas — antigas, estrutura inicial|26/30|26/30|27/30|
|Fontes conhecidas completas — antigas, estrutura corrigida|28/30|28/30|29/30|
|Fontes conhecidas completas — novas, janela|5/10|5/10|5/10|
|Fontes conhecidas completas — novas, estrutura inicial|4/10|4/10|5/10|
|Fontes conhecidas completas — novas, estrutura corrigida|9/10|8/10|9/10|

A correção reconhece a abreviação UN, busca a quantidade dentro do bloco da linha (sem pegar a do próximo item) e une passagens sobrepostas na mesma página até2000 caracteres. A união confere a igualdade literal na área comum; não preenche lacunas. IDs derivados conservam as âncoras de origem. Nenhuma regra por pergunta, número de página do gabarito ou ID de caso.

Na híbrida, mediana de recuperação antiga88,99→140,64ms e nova93,29→161,19ms. Esses tempos excluem aquecimento e geração; uma repetição não permite inferir estabilidade em produção. A estrutura custa leitura adicional do documento e processamento local.

## Limitações da métrica

Esta é cobertura das passagens conhecidas, não acerto da IA. O conjunto novo foi usado para diagnóstico/ajuste e agora é desenvolvimento; exige outra reserva independente para avaliar generalização. O escopo é uma contratação selecionada por PNCP, não descoberta global de edital.

No piloto12, a fonte mudou da página15 para55: conferência visual do modelo de planilha mostra o mesmo item2, SSD240GB,80 unidades. A passagem conhecida original deixou de aparecer, mas há evidência alternativa legítima. Preservamos a nota original da métrica, sem substituir gabarito para elevar retrospectivamente o resultado. No novo06, a janela na página22 termina antes da especificação completa; outra repetição na página61 pode apoiar parte da resposta. Fonte alternativa precisa de conferência de item e unidade.

O Hit de âncora considera source_chunk_id/source_chunk_ids nas passagens derivadas; não prova relevância exaustiva. A cobertura literal permanece critério separado. Configurações congeladas anteriores são históricas; o código mudou em nova versão.

## Integridade e isolamento

Conferidas198 passagens da prévia de50 perguntas diretamente contra páginas/links/offsets do PostgreSQL: todas literais, quantidades literais e aliases correspondentes; máximo cinco fontes/2000 caracteres. Role de leitura sem superuser/createdb/createrole. Escopo SQL malicioso/inexistente não retornou fontes. Zero escrita no banco e zero alteração de vetores nesta etapa. Não é teste real de instrução maliciosa embutida em PDF.

## Geração e revisão

Lotes dos mesmos40 casos do piloto (30 factuais/10 recusas) e10 novos, autorizados anteriormente para a Groq e retomados após aprovação da etapa2. Modelo GPT-OSS120B, conta gratuita declarada pelo usuário, variante alias_items; até cinco fontes públicas por pergunta. Prévia privada/hash congelados antes das chamadas; respostas esperadas e chave não entram no prompt. Rejeições não serão retentadas para esconder falhas. Faturamento efetivo não auditado.

A execução e a revisão são consolidadas ao terminar; integridade não comprova correção, completude ou segurança das recusas. Fichas completas permanecem privadas. A taxa humana e a promoção aguardam revisão; o critério exige pelo menos100 perguntas novas/10 contratações e independência após ajuste.

## Reprodução e evidências

- [Protocolo inicial](../reports/item-validation-protocol-v1.json)
- [Protocolo corrigido](../reports/item-validation-protocol-v2.json)
- [Comparação](../reports/item-retrieval-comparison-v2.json)
- [Fontes conferidas no banco](../reports/item-source-verification-v2.json)
- [Isolamento SQL](../reports/item-scope-verification-v2.json)
- [Protocolo de geração](../reports/item-generation-protocol-v2.json)

A versão inicial pode ser reconstruída a partir do commit895f838 com reports/reproduction/item-retrieval-v1.patch (git apply --ignore-space-change; check executado); os hashes das reconstruções de evaluation.py e evaluate-retrieval.py foram conferidos com os relatórios. Para execução quantitativa são necessários banco/modelos e PDFs privados preparados; a clonagem pública contém metadados e código, não os dados brutos.

## Ambiguidade identificada no piloto17

Conferência visual da página54 confirmou dois computadores: item29 com SSD500GB e item30 com SSD512GB. A pergunta original não identifica o item; gabarito512GB é incompleto como especificação da pergunta. A IA retornou dois valores sem os associar aos itens. [Proposta de esclarecimento](esclarecimento-piloto-17.md), ainda não executada; gabarito histórico preservado.

## O que a comparação permite concluir

Quando reconhece um item, a estrutura lê o escopo completo e ordena os trechos desse item por palavras da pergunta; essa etapa é compartilhada pelos três modos. Os ramos lexical/semântico seguem no fluxo e servem ao fallback. Portanto, a coluna semântica com estrutura não representa uma busca exclusivamente semântica nem comprova melhoria dos embeddings.

No lote novo, janela/estrutura usam o mesmo snapshot, modelo e mecanismo de aliases; mudam seleção/contexto e metadados de item. No piloto antigo, o histórico original usava citação gerada pelo modelo e contexto menor: sua comparação com alias_items também muda o mecanismo de citação. Não atribuir todo ganho à estrutura de itens. Todas as medições têm uma repetição; temperatura zero não garante geração idêntica no provedor.

## Resultado parcial da geração

39/50 casos concluídos: dez novos e29 do piloto. Todos39 resultados aceitos passaram na integridade literal; isso não mede correção. Novos: nove respostas/uma abstenção, antes seis respostas/quatro abstenções. Piloto executado:27 respostas factuais, uma abstenção segura aparente e uma recusa; restam três perguntas factuais/oito recusas. No piloto30 ocorreram dois HTTP429, incluindo uma única retomada após55 segundos; falhas preservadas, sem retentar respostas rejeitadas para melhorar a nota. Não há horário de liberação confirmado.

Novos: entrada27913→20659 tokens, redução de aproximadamente26%; saída1835→2089. Mediana da etapa de geração907,18→954,89ms, incluindo HTTP e processamento/validação local. Piloto parcial:69116 tokens de entrada/4979 de saída, mediana864,58ms. Uso das tentativas com erro e cobrança efetiva não confirmados; não extrapolar ao lote completo. Não há comparação monetária aprovada.

Conferência do assistente:03 e05 passaram a fornecer os campos esperados;06 misturou5600MT/s e5600MHz, qualificou CL40 como mínimo e omitiu compatibilidade4800MT/s;08 omitiu por item;02 continuou sem responder a divisão ampla/cota. No piloto11/12 apareceram mínimo500GB e quantidade80 corretamente vinculados;17 revelou ambiguidade da pergunta. Outros qualificadores ausentes nos casos02/24/27 devem ser avaliados conforme os campos efetivamente perguntados. [Achados](../reports/item-generation-review-v2.json).

Segundo a [documentação oficial da Groq](https://console.groq.com/docs/rate-limits), limites podem incidir sobre solicitações/tokens por minuto ou dia e se aplicam à organização. O HTTP429 indica limite atingido. Não identificamos neste checkpoint qual limite específico nem seu reset; os limites exatos devem ser conferidos na conta. Não alteramos plano, modelo ou credenciais para contornar a restrição.

[Resumo novo](../reports/item-generation-new-summary-v2.json) · [Resumo piloto parcial](../reports/item-generation-pilot-summary-v2.json) · [Gate bloqueado](../reports/item-quality-v2.json) · [Segurança](../reports/seguranca-validacao-itens-2026-10-01.md).

**Pendências:** retomar somente piloto30–40 quando a quota estiver disponível, mantendo este checkpoint e protocolo; revisão humana das fichas privadas; esclarecer piloto17 com aprovação; corrigir unidades/completude e avaliar outra reserva independente após ajustes. Etapa2 parcial, sem comprovação de90% ou promoção do candidato. Interface/painel não iniciados nesta entrega.

Hashes de código/referências reconferidos após a execução parcial: nenhuma mudança durante as chamadas. Hashes são dos bytes locais (Windows); finais CRLF/LF normalizados pelo Git podem exigir reconstrução dos finais de linha ao comparar com registros históricos. Não confundir diferença de bytes com mudança de conteúdo. [Estado preciso e casos pendentes](../reports/item-validation-state-v2.json).
