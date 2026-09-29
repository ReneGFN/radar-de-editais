# Radar de Editais

**Laboratório de avaliação de um assistente RAG para leitura de editais públicos.**

O projeto investiga uma pergunta prática: um pequeno fornecedor consegue localizar prazos, exigências e condições de um edital sem perder a referência ao texto original? O assistente proposto recupera trechos de editais e anexos, responde com citações verificáveis e declara quando a informação não foi encontrada. Um painel compara versões por qualidade da recuperação, apoio das respostas nas fontes, latência e custo.

> **Estado em 2026-09-29:** repositório e escopo inicial documentados. Ainda não há aplicação, corpus selecionado, conjunto de avaliação ou resultados medidos.

| Campo | Estado |
|---|---|
| Tipo | Agente / Dados |
| Status | Planejamento |
| Responsável | Renê |
| Início | 2026-09-29 |
| Prazo | Não informado |
| Próximo passo | Escolher um setor de fornecimento e a primeira amostra de editais |

## Problema e público

Editais e anexos podem ser extensos, espalhar condições por vários arquivos e receber retificações. O público inicial são pequenos fornecedores que precisam encontrar informações para **conferência humana**. O projeto não determina elegibilidade, recomenda participação nem substitui a leitura do edital vigente ou orientação especializada.

## Primeira versão planejada

- Selecionar um tipo de fornecimento e uma amostra limitada de editais reais publicados no [Portal Nacional de Contratações Públicas (PNCP)](https://www.gov.br/pncp/).
- Registrar, para cada documento usado na avaliação, URL oficial, identificador, data de consulta, versão ou data de publicação, e hash do arquivo. Verificar termos de reutilização antes de distribuir cópias no repositório.
- Permitir perguntas sobre **um edital selecionado por vez**. A resposta mostrará documento, página ou seção e trecho de apoio, com link para a fonte oficial.
- Tratar anexos e retificações como documentos distintos; indicar conflitos ou ausência de evidência em vez de escolher uma regra sem justificativa.
- Criar perguntas com respostas esperadas e fontes de referência para executar as mesmas provas em cada versão do sistema.
- Mostrar no painel resultados agregados e casos individuais de erro.

Exemplos de perguntas para o conjunto de avaliação, após seleção dos documentos:

- Qual é o prazo final para enviar a proposta?
- Quais documentos são exigidos para a habilitação?
- Onde estão descritas as condições de entrega?
- O documento informa algo sobre uma exigência específica? Se não, a resposta deve reconhecer a ausência.

## Como a avaliação funcionará

Cada caso de teste terá pergunta, documento ou trecho esperado, resposta de referência, critérios de aceitação e indicação de quando a resposta correta é “não consta”. As respostas de referência serão revisadas manualmente. Uma parte dos casos ficará reservada para verificar melhorias depois dos ajustes, reduzindo o risco de adaptar o sistema apenas às perguntas conhecidas.

| Medida | Definição inicial |
|---|---|
| Recuperação, Recall@k | Fração de perguntas em que ao menos um trecho necessário aparece entre os `k` primeiros trechos recuperados. O valor de `k` será fixado antes da comparação. |
| Afirmações sem apoio | Fração de respostas com pelo menos uma afirmação factual que não possa ser sustentada pelos trechos citados. Casos duvidosos terão revisão humana. |
| Latência | Tempo ponta a ponta por consulta, apresentado por mediana (p50) e percentil 95 (p95). |
| Custo por consulta | Custo calculado a partir do uso registrado e da tabela de preços do modelo na data da execução; separar custo de avaliação do custo da resposta quando houver juiz automatizado. |

As versões serão comparadas com o mesmo conjunto de perguntas e o mesmo retrato dos documentos. Cada experimento registrará a mudança feita, hipótese, parâmetros, data, modelo, resultados e exemplos de regressão. **Nenhum resultado será publicado antes de ser medido.**

## Arquitetura proposta

1. **Coleta e registro de fontes:** obtém metadados e documentos públicos do PNCP e guarda um manifesto reproduzível.
2. **Preparação e busca:** extrai o texto, preserva página ou seção, divide em trechos e recupera os mais relevantes.
3. **Resposta com fontes:** gera uma resposta somente a partir dos trechos encontrados; exibe as citações e admite falta de evidência.
4. **Avaliador:** executa as perguntas de referência, calcula métricas e conserva resultados por versão.
5. **Painel:** permite comparar métricas e inspecionar pergunta, resposta, trechos recuperados e motivo do erro.

A tecnologia de implementação ainda será escolhida conforme facilidade de reprodução, custo e qualidade da extração dos PDFs. O Codex poderá apoiar código e testes; a definição dos critérios e a análise dos resultados exigem revisão humana.

## Critérios de conclusão da primeira entrega

- [ ] Amostra de documentos reais com origem, data, versão e integridade registrados.
- [ ] Assistente funcional com citações verificáveis e resposta explícita para falta de evidência.
- [ ] Conjunto de avaliação versionado, com perguntas e respostas esperadas revisadas.
- [ ] Execução reproduzível de pelo menos duas versões nas quatro medidas acima.
- [ ] Painel com acesso aos erros individuais e relatório que explique melhorias e regressões.
- [ ] Instruções de execução local e limites de custo publicados após a implementação.

## Fontes e cuidados

- [PNCP](https://www.gov.br/pncp/) — consulta a contratações e documentos oficiais.
- [Dados abertos do PNCP](https://www.gov.br/pncp/pt-br/acesso-a-informacao/copy_of_dados-abertos) — acesso público a consultas de dados.
- [Saiba como vender para o governo](https://www.gov.br/empresas-e-negocios/pt-br/empreendedor/licitacoes-publicas) — contexto para pequenos negócios.

O corpus será formado por documentos públicos. Credenciais de serviços de IA, caso sejam necessárias, ficarão fora do repositório e serão usadas somente no servidor. Conteúdo dos documentos será tratado como dado de entrada, nunca como instrução para o assistente ou para os testes. Datas, prazos e condições sempre deverão apontar para a versão da fonte utilizada.

## Próximo passo

Escolher **um setor de fornecimento** e selecionar a primeira amostra de editais para criar o conjunto de perguntas de referência.

