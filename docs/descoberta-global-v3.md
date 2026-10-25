# Nomes abreviados e esclarecimento — 2026-10-05

Entrega local aprovada por Renê: melhorar nomes abreviados e definir quando pedir detalhes. Esta v3 é da **descoberta global**, distinta da variante experimental de geração `alias_items_v3`, que continua sem promoção. Não há API/tela de chat conectada nesta entrega.

## Como funciona

O catálogo oficial continua sendo a única origem dos nomes. Além da cobertura de metade das palavras distintivas usada na v2, duas palavras distintivas presentes na pergunta permitem reconhecer parte de um nome oficial longo. Exemplo observado: “Fundação Alfredo da Matta” identifica o nome oficial mais extenso. A regra remove acentos e termos administrativos genéricos; não há tabela manual de respostas, IDs de casos ou exceções por edital. **Siglas como SSP/MT ou nomes comerciais não são automaticamente expandidos**; uma tabela de aliases verificados seria uma evolução própria.

A descoberta agora inclui `routing`, sem executar geração:

| Estado | Quando ocorre | Uso previsto no chat |
|---|---|---|
| `scoped` | Usuário selecionou edital ou uma única pista de órgão corresponde a candidato recuperado | Recuperar contexto desse PNCP e verificar suporte antes da geração |
| `needs_clarification` | Mais de uma correspondência no catálogo, ausência de pista ou pista fora dos cinco candidatos | Mostrar opções e permitir acrescentar órgão, município ou detalhes da compra |
| `discovery_only` | Pedido explícito como “Quais editais…” ou “Liste contratações…” | Manter busca geral e apresentar candidatos; verificar fatos separadamente por contratação |
| `no_candidates` | Recuperação vazia | Informar ausência de candidatos e solicitar detalhes |

Pontuação RRF não é probabilidade de acerto. Não decidimos responder só porque o primeiro resultado tem uma pontuação maior. `scoped` define **onde procurar**, sem garantir que exista resposta apoiada no PDF. Nenhum consumidor de geração foi conectado: na etapa de API será necessário impor esses estados, em vez de ignorá-los. A identificação de pedidos entre várias contratações usa padrões explícitos de linguagem e não cobre todas as formas possíveis de perguntar; isso pode causar esclarecimentos desnecessários.

## Resultados e limites

Snapshot de desenvolvimento `1446c44aca18011a`, mesmas 40 perguntas factuais, consulta real somente leitura. [Relatório por caso](../reports/discovery-development-v3.json), preservando [v2](../reports/discovery-development-v2.json) e [v1](../reports/discovery-development-v1.json).

| Medida | v2 | v3 global |
|---|---:|---:|
| PNCP esperado nos cinco candidatos | 35/40 (87,5%) | 37/40 (92,5%) |
| Mediana de recuperação | 398,90 ms | 393,21 ms |
| Metadados de fonte conferidos no banco | Sim | Sim |

Dois ganhos (pilot-31 e pilot-32) e nenhuma regressão frente à v2. Permanecem fora do top5 pilot-04, pilot-06 e pilot-08. As três perguntas não identificam órgão e agora recebem pedido de esclarecimento. Todas as demais perguntas sem pista suficiente ou com múltiplas correspondências também recebem esclarecimento: **22/40**, incluindo 19 cuja contratação esperada estava entre os candidatos. Isso mostra o custo de usabilidade da regra conservadora.

Em **18/40**, a contratação foi definida por pista única, e nos 18 coincidiu com o PNCP conhecido. Não apresentar isso como 100% de precisão do chatbot: é correspondência de escopo num conjunto de desenvolvimento observado, sem avaliação das respostas. Todos os casos sem definição automática permanecem pendentes de interação. O catálogo contém contratações diferentes do mesmo órgão e nomes parcialmente semelhantes; esses empates não são resolvidos arbitrariamente.

Os 92,5% superam 90% **somente em recuperação top5 deste desenvolvimento**. Não são acerto factual, validação independente nem garantia para novos PDFs. Perguntas eram originalmente vinculadas a editais, referências não rotulam todas as alternativas válidas e limiares foram escolhidos após diagnóstico do desenvolvimento. Holdout não usado, documentos não ampliados, Groq/Jev não chamados. Latência de uma execução por versão, sem controle de cache: diferenças pequenas não provam ganho de desempenho.

Verificação: avaliação real de 40 consultas e integridade dos metadados; 251 testes totais, incluindo 20 específicos de descoberta, passaram. Testes cobrem nome abreviado real e sintético, acentos, órgãos homônimos, pergunta genérica, seleção explícita, pista fora dos candidatos, recuperação vazia e pedido de busca entre editais. O padrão de busca entre contratações foi acrescentado após o benchmark: conferido que nenhuma das 40 perguntas ativa esse ramo; resultados do benchmark não foram alterados. Não foi repetido o lote só por essa mudança sem impacto nos casos. Reexecução da versão atual: `.venv/Scripts/python.exe ops/evaluate-discovery.py --report v3`, com configuração privada existente; substitui somente o relatório v3.

## Segurança — dez grupos

1. **Segredos: verificado no escopo.** Código, testes, relatório e documentação novos revisados; `.gitignore` mantém credenciais, PDFs/dumps e diretórios privados excluídos. Nenhum valor de segredo ou pergunta/texto bruto no relatório. Histórico completo não reauditado.
2. **API/frontend: não aplicável à mudança.** Nenhum endpoint, bundle ou acesso do navegador foi adicionado. Estados são dados do módulo interno.
3. **Entradas: verificado.** Mantidos limite de 2.000 caracteres, tipo, vazio e PNCP permitido. Testes de roteamento inválido/ambíguo e ausência de candidatos. Nomes são dados, nunca comandos.
4. **Autorização: verificado no escopo.** Snapshot e catálogo permitidos, PNCP selecionado validado, resultado externo rejeitado. Holdout isolado. Login multiusuário/produção não implementado nem auditado.
5. **Ataques: verificado no código alterado.** SQL parametrizado preservado; mudança é comparação local de palavras e padrões fixos. Não executa instruções de documentos. Proteções de prompt/SQL completas e XSS/CSRF da futura interface não foram testadas nesta etapa.
6. **Logs: verificado.** Progresso contém ID/acerto; relatório inclui métricas, IDs públicos e mensagens fixas de roteamento, sem credenciais ou conteúdo bruto. Retenção de produção não examinada.
7. **Senhas: não aplicável.** Nenhum login, recuperação ou credencial alterado.
8. **Backup: não aplicável à mudança.** Banco somente leitura, relatórios anteriores preservados. Restauração não repetida, sem nova alegação de recuperação validada.
9. **Dependências: verificado no escopo, com evidência reaproveitada.** Nenhum pacote/lock modificado; 251 testes atuais. `pip check` e auditoria PyPI da entrega imediatamente anterior em 2026-10-05 permanecem a evidência recente, sem nova auditoria nesta etapa; nenhum problema conhecido nos pacotes auditáveis naquela execução, pacote local fora do índice. Não constitui vigilância contínua de vulnerabilidades.
10. **Comunicação: verificado no escopo.** Embeddings e banco locais, sem envio de perguntas/PDFs para provedores. Nenhuma alteração em TLS/certificados; HTTPS/cabeçalhos de produção não aplicáveis à entrega local.

## Próxima entrega proposta

Aguardar revisão. Conectar o serviço local de perguntas ao roteamento, à recuperação de contexto e à geração com fontes, impondo esclarecimento quando necessário. Tratar pesquisa entre editais como candidatos ou fatos verificados individualmente, sem combinar exigências e sem prometer cobertura completa. Testar inicialmente com provedor simulado; chamadas reais novas à Groq dependem do escopo de autorização correspondente. Tela de chat será uma entrega posterior.
