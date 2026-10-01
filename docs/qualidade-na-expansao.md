# Como acompanhar a meta de 90% quando a base cresce

## Qual taxa queremos preservar?

Os atuais 29/30 da híbrida medem recuperação de um trecho conhecido no top 5. Não demonstram 96,7% de respostas corretas. Para o produto, o critério proposto é **respostas corretas, suficientemente completas e sustentadas / total de perguntas respondíveis**, incluindo recusas indevidas, bloqueios e falhas no denominador. Publicar também precisão entre respostas apresentadas e cobertura, para impedir que recusar quase tudo pareça qualidade alta.

Separar recuperação, correção da resposta e apoio nas fontes segue a estrutura de avaliação da [documentação LangChain](https://docs.langchain.com/langsmith/evaluate-rag-tutorial). A avaliação deste projeto permanece local, sem ativar LangSmith/tracing remoto.

A meta de 90% é critério de aceitação medido, não promessa para qualquer PDF ou garantia estatística sobre perguntas futuras. Mesmo 90/100 depende de representatividade, correlação por edital, qualidade dos rótulos e incerteza amostral. Análise de incerteza por edital ainda não implementada.

## Fluxo de expansão proposto

1. **Entrada em versão candidata:** snapshot separado e hashes; conservar versão avaliada. Arquivos novos não viram base ativa só porque foram carregados.
2. **Qualidade e domínio:** conferir item de informática, tipo de anexo, qualidade de texto/OCR, tabelas, repetições e retificações. Documento com problemas fica pendente de revisão. Um objeto médico que menciona monitores não é automaticamente informática.
3. **Escopo da pergunta:** selecionar edital; se for consulta global, localizar o edital antes de responder. Quando faltarem item/modelo ou houver fontes conflitantes, pedir esclarecimento. Adicionar editais distintos não altera a busca restrita a um edital antigo com os mesmos documentos; anexos dentro dele podem alterar seus candidatos.
4. **Busca e contexto:** manter híbrida e filtros legítimos. Comparar reranker local e contexto de seção/tabela em versão experimental, com recuperação ampla e seleção final enxuta. Não ampliar quantidade de trechos sem medir ruído, latência e custo. Não interpretar distância vetorial como probabilidade de acerto.
5. **Resposta com evidência:** afirmações vinculadas às fontes, condições/unidades preservadas; bloqueio de citações inválidas. Verificar entendimento de tabela e consistência de números. Pedir esclarecimento ou declarar insuficiência quando necessário, medindo cobertura junto da precisão.
6. **Teste antes de promoção:** regressão nos casos antigos e conjunto separado por edital com perguntas naturais nos novos documentos. Rejeitar promoção se um grupo ficar abaixo da meta; conservar a versão anterior enquanto o candidato é corrigido.
7. **Acompanhamento:** amostras revisadas por usuário, métricas por tipo de PDF/pergunta e alarmes para queda. A tela de feedback e automação da promoção ainda são futuras.

A busca atual usa cosseno exato no PostgreSQL dentro do edital. A [documentação pgvector](https://github.com/pgvector/pgvector) distingue busca exata de índices aproximados; eventual adoção de HNSW exige comparação de recuperação e velocidade. Recall de vizinhos por distância não é acerto semântico de resposta.

## Implementado nesta atualização

- Triagem de setor corrigida: diferencia monitores médicos e de vídeo; termo isolado monitor exige revisão. Objetos mistos com informática continuam candidatos com revisão do item. A triagem é heurística, não aprovação do PDF.
- Checagem local em `radar.quality.assess_release` e `ops/check-quality.py`: nenhum banco é modificado ou promovido automaticamente.
- Resultado atual bloqueado: revisão humana pendente e conjunto novo ainda insuficiente, sem qualquer nota de respostas >=90% inventada.
- Dez perguntas aprovadas por Renê de quatro editais já indexados, sem perguntas no piloto anterior; referências conferidas por texto/hash/origem. Isso inicia uma reserva, mas não simula crescimento da base.

## Política inicial de promoção implementada no checador

- Pelo menos 30 perguntas factuais de regressão e 100 perguntas naturais novas em pelo menos dez editais distintos. A escolha é uma política inicial para ampliar diversidade e reduzir o peso de cada erro; não certifica precisão populacional.
- Nenhum edital compartilhado entre os dois grupos. Perguntas novas sem pistas de localização; rótulos aprovados e revisão humana registrada.
- Pelo menos 90% de sucesso ponta a ponta em **cada grupo**, sem média conjunta que esconda regressão. Recusa indevida não é acerto; completude/apoio pendentes não são aprovados.
- Casos de recusa presentes e todos avaliados como seguros; qualidade da ajuda e resistência a PDF malicioso também precisam de casos próprios.
- Resultado elegível exige promoção manual. O checador ainda não está integrado a serviço/API de implantação; trata-se de controle local testado.

```powershell
.\.venv\Scripts\python.exe ops/check-quality.py reports/generation-review-v1.json --report reports/quality-release-v1-repeat.json
```

O arquivo de revisão guarda status explícito de assistente versus humano e pontuações booleanas; a checagem não autentica quem editou o arquivo. No futuro, registrar revisão com identidade e acesso controlados na API. A recuperação das dez perguntas foi executada após aprovação; geração concluída (seis respostas, uma insuficiência, três rejeições) e revisão humana das saídas permanece pendente; usar a reserva para ajustar transforma-a em desenvolvimento e exige outra reserva.

## Problema encontrado no corpus atual

Triagem por objeto identificou dois falsos positivos de domínio: Guapimirim/RJ (glicemia) e SESPA/PA (sinais vitais). Não tinham perguntas no piloto de 40 casos. O snapshot histórico de 30 editais/49 PDFs permanece intacto; marcar os dois para revisão/remoção em **versão futura**, não apagar documentos ou reescrever métricas. Nova coleta não aceita esses objetos como informática. Um edital misto de Imbaú permanece candidato apenas para seus itens de informática.

[Triagem dos 30 objetos](../reports/sector-review-v1.json) · [Revisão das respostas](revisao-respostas.md) · [Perguntas de reserva](perguntas-reserva-para-revisao.md).

Pendentes: confirmação humana, coleta de editais realmente novos em mais regiões, referências reservadas, OCR/tabelas estruturadas/reranker e execução comparável. Esses recursos não são apresentados como implementados ou melhoria já medida.

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

## Seleção experimental avaliada

O bônus de cobertura lexical não melhorou cobertura completa da híbrida nem do conjunto novo. RRF continua padrão. Ganho semântico reserve-08 veio com regressão de completude reserve-06. As dez perguntas agora são desenvolvimento, pois os erros orientaram o experimento; reservar novos editais para avaliar a próxima mudança. [Comparação e reprodução](resultados-recuperacao.md#experimento-cobertura-de-termos-na-seleção--2026-10-01).
