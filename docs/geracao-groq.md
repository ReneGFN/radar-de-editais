# Geração com GPT-OSS 120B na Groq

## Funcionamento e limites

LangChain recupera até cinco trechos no escopo de um edital e snapshot. ChatGroq envia somente a pergunta e esses trechos para `https://api.groq.com/openai/v1/chat/completions`. As respostas esperadas não entram no prompt. Modelo `openai/gpt-oss-120b`, temperatura zero, esforço de raciocínio low, saída de até 1.600 tokens, sem raciocínio exposto e sem ferramentas externas.

O esquema JSON exige estado, justificativa e afirmações com evidências. O validador verifica IDs recuperados e passagens no documento; aceita diferenças somente de espaços/quebras de linha e devolve a passagem original. Resposta inválida é bloqueada. Citação existente não prova interpretação correta: apoio semântico e completude exigem revisão.

O usuário confirmou conta gratuita e autorizou expressamente os 40 testes com trechos públicos. A documentação [Groq de limites](https://console.groq.com/docs/rate-limits) lista o modelo no plano gratuito; limites efetivos dependem da conta. Nenhum fallback de modelo/plano pago é realizado. Intervalo mínimo de 30 segundos e nenhuma repetição automática da API; falhas de API interrompem o lote, com retomada por checkpoint. Falhas locais de validação são registradas como rejeição e o lote continua, sem aceitá-las nem repeti-las automaticamente.

A chave é lida de `GROQ_API_KEY` ou do arquivo privado `secrets/groq_api_key` no diretório de dados do aplicativo. O arquivo aceita valor puro ou atribuição `GROQ_API_KEY=...`; nunca inclua a chave no Git, prompt, relatório ou chat. O SDK acrescenta o caminho `/openai/v1/chat/completions`, por isso sua base é apenas `https://api.groq.com`.

```powershell
.\.venv\Scripts\python.exe ops/evaluate-generation.py datasets/evaluation/pilot-v2.json --confirm-free-plan --limit 40 --interval 35
```

O checkpoint fica no diretório privado, fora do OneDrive; guarda respostas para revisão, uso de tokens, tempos e códigos de falha. Não é exportado ao GitHub. Retomar pula casos concluídos e casos rejeitados pela validação; erros não contam como acertos. Contagem de tokens não comprova cobrança efetiva. Conta gratuita é confirmação do usuário, sem auditoria independente de faturamento.

## Verificação inicial

Primeiro caso respondeu e passou na integridade de citação: 1.376 tokens de entrada, 275 de saída. Houve tentativas anteriores falhas (endereço duplicado, formato de autenticação, validação de citações); consumo dessas falhas não confirmado. Este foi o registro inicial; o resultado final aparece abaixo. Não publicar taxa de correção ou recusa antes da revisão.

50 testes locais passaram, incluindo fonte/quote inventadas, ausência de evidência, estado incompatível, confirmação de plano, filtros derivados da pergunta, formatos de chave e conservação da passagem original.

## Erros observados durante o lote

Revisão preliminar por assistente (não aprovação humana independente): pilot-11 respondeu 256 GB usando evidência de outro SSD, embora a referência peça mínimo de 500 GB no item 17. É erro de escopo/item, coerente com a falha restante de recuperação. pilot-12 respondeu duas unidades em vez de 80, confundindo o número do item com a coluna de quantidade. A citação existe, mas não sustenta a conclusão. Essas falhas demonstram por que integridade de citação não equivale a acerto.

A primeira tentativa de pilot-14 foi bloqueada por citação inválida; uma repetição passou sem afrouxar a regra de palavras. Isso é recuperação operacional após falha, não prova de determinismo nem acerto na primeira tentativa. Temperatura zero não garante respostas idênticas no serviço. O relatório conserva tentativas falhas separadas.

No pilot-17, o modelo acrescentou reticências às citações e confundiu especificações distintas na mesma página. O validador bloqueou a resposta. A partir dessa observação, o avaliador continua após rejeição local e preserva o caso como falha; problemas de autenticação, quota ou rede continuam interrompendo. Não há repetição automática para selecionar uma resposta melhor.

Uma ficha privada de revisão compara cada pergunta, referência aprovada, resposta e fontes. Gere com `ops/prepare-generation-review.py datasets/evaluation/pilot-v2.json`. O resumo público é produzido por `ops/summarize-generation.py ... --report reports/generation-summary-v1.json`; por construção, não contém textos de respostas, citações ou respostas esperadas. O teste da exportação confirma essa separação.

Melhorias a avaliar em versão posterior: citar passagens sem reticências; preservar cabeçalhos/estrutura de tabelas para distinguir item e quantidade; diferenciar itens próximos e pedir esclarecimento quando houver duas especificações; conferir completude e unidades. Devem ser medidas em nova execução identificada, sem misturar resultados com este lote.

Este lote de geração usa a busca híbrida estruturada. A comparação lexical/semântica/híbrida em 30 perguntas mede recuperação; não mede três taxas de acerto de respostas geradas. O controle das recusas é examinado separadamente, sem aumentar o denominador de acerto factual.

Pilot-20 foi bloqueado por reticências no meio da citação, embora a afirmação estivesse alinhada à referência. Pilot-34 teve HTTP400 isolado e respondeu em uma repetição controlada, sem mudança de prompt/esquema; causa do primeiro HTTP400 não confirmada. Essas tentativas permanecem no relatório de falhas, sem serem tratadas como execução idêntica ou taxa de acerto na primeira tentativa.

A revisão preliminar também observa respostas que omitem condições da referência e recusas que não oferecem a alternativa útil solicitada. Ainda não foi atribuída pontuação definitiva de completude/recusa. O campo reason de uma recusa pode conter explicações factuais sem citações: a revisão semântica deve examiná-lo, além dos claims das respostas factuais.

## Resultado final do lote

40 casos testados; 38 respostas aceitas pela validação estrutural/literal e dois casos rejeitados (pilot-17 e pilot-20). Entre as aceitas: 28 answered, sete refused, três insufficient_evidence. As dez recusas não foram somadas ao acerto factual. Nove tentativas falhas preservadas, incluindo configuração inicial, validação e HTTP400; alguns casos tiveram repetição controlada. Estes totais não representam acerto na primeira tentativa.

Uso dos casos concluídos: 52.877 tokens de entrada, 8.922 de saída. Mediana de geração 1.195,66 ms, sem intervalo do lote; não é latência ponta a ponta nem teste de carga. Uso das tentativas falhas e faturamento efetivo não confirmados. Conta gratuita confirmada pelo usuário e acesso ao modelo comprovado por respostas reais.

Correção, completude, apoio semântico e qualidade da recusa ainda não pontuados definitivamente. Revisão preliminar do assistente identificou dois erros claros de conteúdo (pilot-11 e pilot-12), além de omissões e problemas de apresentação. Conferência humana fica na ficha privada; respostas/citações não foram exportadas ao GitHub. 50 testes locais passaram.

[Resumo operacional sem textos](../reports/generation-summary-v1.json) · [Configuração de reprodução](../reports/generation-protocol-v1.json).

A pergunta pilot-17 também merece revisão: a página recuperada contém especificações com SSDs de 500 GB e 512 GB, enquanto a referência seleciona 512 GB sem explicitar o item na pergunta. Não alteramos a referência aprovada; essa ambiguidade deve ser resolvida na revisão do conjunto.
