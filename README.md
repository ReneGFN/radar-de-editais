# Radar de Editais

**Laboratório de avaliação de RAG para leitura de editais públicos de informática.**

O projeto investiga se pequenos fornecedores conseguem encontrar prazos, especificações e condições com referência verificável ao documento original. O objetivo é publicar metodologia, resultados medidos e erros encontrados ao comparar versões do sistema.

## Estado em 2026-10-01

- **Base ampliada preparada:** 30 editais/contratações, 11 estados, cinco regiões; 49 PDFs, 2.525 páginas e 15.773 trechos.
- **Carga ampliada verificada:** 15.773 vetores no PostgreSQL; repetição sem duplicação, filtros e offsets conferidos. Backup restaurado em banco separado com os mesmos 15.773 trechos. Reaproveitados 4.664 vetores compatíveis da base inicial.
- **Base inicial verificada:** 10 editais, 14 PDFs e 4.664 vetores; carga idempotente, filtros, offsets e backup/restauração conferidos. Evidências históricas em `reports/snapshots/b1ee54ef84e97078/`.
- **Implementados:** coleta, extração, embeddings locais, PostgreSQL/pgvector e busca híbrida coordenada por LangChain.
- **Avaliação em revisão:** 30 perguntas com respostas e 10 recusas; 40 casos aprovados pelo usuário. Evidências em 24 editais/24 PDFs, 11 estados; integridade conferida; 72 testes locais passaram na integração atual. [Perguntas para revisão](docs/perguntas-para-revisao.md).
- **Recuperação avaliada:** 180 buscas em 30 perguntas aprovadas. Híbrida: trecho de referência no top 5 em 17/30 na linha de base e 20/30 após mudança lexical (+10 pontos percentuais), com cinco ganhos e duas regressões. [Método, resultados e erros](docs/resultados-recuperacao.md).
- **Recuperação melhorada:** lexical 29/30, semântica 28/30, híbrida 29/30 em Hit@5 no mesmo piloto; 13 perguntas têm pistas explícitas de localização. Sem filtros de localização: 24/30, 25/30, 24/30. Ver ablação e limites nos resultados.
- **Geração implementada:** GPT-OSS 120B na Groq, JSON estruturado, verificação de citações e checkpoint privado. 40 casos testados: 38 respostas passaram pelo validador, duas rejeitadas por citações inválidas; nove tentativas com erro preservadas. Não equivale a 38 acertos. Plano gratuito confirmado pelo usuário; autenticação e acesso ao modelo verificados por resposta real.
- **Planejados:** avaliação semântica das respostas/recusas, API/interface e explorador 2D/3D.
- **Correção das respostas ainda não pontuada.** Erros de conteúdo já observados e registrados. Recuperar uma evidência não comprova resposta correta ou recusa segura.

## Arquitetura

[Arquitetura e diagramas](docs/arquitetura.md) · [Execução local](docs/base-e-operacao.md) · [Investigação 2D/3D](docs/visualizacao-3d.md)

```text
PNCP → PDFs privados → texto por página → trechos LangChain
     → embeddings locais → PostgreSQL + pgvector
Pergunta + edital + snapshot → buscas semântica e lexical
     → fusão dos rankings → trechos com página e fonte
```

Python organiza o núcleo. LangChain divide os textos e coordena as buscas em paralelo. MiniLM multilíngue gera vetores de 384 dimensões em CPU; PostgreSQL combina busca exata por cosseno e full text search. Groq fornece `openai/gpt-oss-120b` para geração com fontes; credenciais e resultados brutos ficam fora do repositório. Dify fica para uma opção futura.

API FastAPI e interface React/TypeScript estão planejadas. O mesmo núcleo servirá CLI, API e avaliador.

## Corpus e seleção

Setor: computadores, monitores e acessórios. Mantidos dez editais de SP, com dois adicionais de PR, RS, MG, RJ, BA, PE, GO, MT, PA e AM. Amostra de conveniência por cotas, **sem representatividade estatística**. Há editais mistos; a avaliação deve identificar os itens de informática. Revisão posterior encontrou dois objetos médicos falsamente selecionados; estão sinalizados para revisão em uma versão futura, sem alterar este snapshot histórico.

[Manifesto final](datasets/manifests/4f8ddffaa01b6a20.json) · [Distribuição da amostra](reports/amostra-30.json) · [Preparação](reports/preparacao.json) · [Qualidade por documento](reports/qualidade-30.json)

[Carga](reports/carga.json) · [Verificação e restauração](reports/verificacao-local.json) · [Busca em outros estados](reports/buscas.json). O relatório de preparação registra essa etapa; a carga e verificação registram o estado posterior. Nenhum desses testes mede acerto das respostas.

Metadados registram fonte oficial, data e hash do PDF. Consulta da API não comprova vigência ou oportunidade aberta; datas e condições exigem conferência no documento. Anexos/retificações são preservados sem presumir substituição automática.

PDFs, textos extraídos, modelos, vetores, credenciais e backups **não são publicados**. O comando hydrate baixa documentos oficiais e confere hashes; fonte alterada é sinalizada, sem substituir silenciosamente o snapshot.

## Protocolo de avaliação

| Medida | O que será examinado |
|---|---|
| Hit@k / Recall@k | Presença e cobertura dos trechos esperados na recuperação. |
| Afirmações sem apoio | Alegações não sustentadas pelas citações, com correção/completude e recusa correta como auxiliares. |
| Latência | Tempo ponta a ponta, p50/p95, repetição, falhas e cache. |
| Custo por consulta | Uso reportado e preços na data da execução; separar ingestão, consulta e avaliação. |

Perguntas e respostas de referência terão revisão humana e fontes identificadas; parte dos casos ficará reservada. Comparações usarão mesmo corpus/perguntas e alteração de um fator por experimento. Não publicar ganhos antes de medir regressões e erros.

## Investigação 2D/3D

O explorador permitirá inspecionar trechos recuperados e referências esperadas, possíveis repetições e casos de erro. PCA será a referência inicial; UMAP poderá ser comparado depois. Projeções perdem informação: conclusões devem ser confirmadas nos textos e vetores originais. Compararemos tarefas em 2D/3D para verificar se o terceiro eixo ajuda. **Ainda não implementado.**

## Reprodução

Requer PowerShell 7, Python 3.12, Docker Desktop e internet nos downloads iniciais.

```powershell
py -3.12 -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements-lock.txt
& .venv/Scripts/python.exe -m pip install --no-deps -e ./backend
& ./ops/start-db.ps1 -Initialize
& .venv/Scripts/python.exe -m radar.cli hydrate datasets/manifests/4f8ddffaa01b6a20.json
& .venv/Scripts/python.exe -m radar.cli prepare datasets/manifests/4f8ddffaa01b6a20.json
& .venv/Scripts/python.exe -m radar.cli load datasets/manifests/4f8ddffaa01b6a20.json
& .venv/Scripts/python.exe -m radar.cli search 'prazo entrega' --snapshot 4f8ddffaa01b6a20 --edital 02291730000114-1-000117/2026
& .venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider
```

Banco apenas em `127.0.0.1:55432`, rede e volume exclusivos. Dados privados em `%LOCALAPPDATA%\RadarDeEditais`; `RADAR_PRIVATE_ROOT` permite escolher outro diretório fora da pasta do projeto e da sincronização OneDrive. Usar o mesmo diretório nas etapas.

[Comandos de expansão, verificação e limites](docs/base-e-operacao.md).

## Erros e limites conhecidos

- 71 páginas com pouco texto exigem revisão/OCR; nenhuma afirmação de extração integral.
- Tipo de anexo da API pode divergir do conteúdo.
- Linha de base lexical exigia todos os termos e retornou zero candidatos nas 30 perguntas. Consulta OR passou a ser padrão de desenvolvimento; melhorou o Hit@5 híbrido, mas perdeu dois casos sobre RAM. Dez erros de ID conhecido permanecem; relevâncias equivalentes não estão totalmente rotuladas.
- PDFs com tabelas podem perder relações; revisão visual é amostral.
- Ainda sem geração, autenticação de aplicação, API pública ou implantação.
- Docker Desktop exigiu recuperação de sockets temporários anteriormente; nesta etapa estava fechado, iniciou normalmente e os dois snapshots foram preservados. Funcionamento nesta reinicialização não comprova estabilidade permanente.

[Revisão inicial dos PDFs](reports/revisao-pdf.md) · [Revisão da ampliação](reports/revisao-pdf-2026-10-01.md) · [Segurança dos dez grupos](reports/seguranca-2026-10-01.md).

## Próximo passo

Definir modelo/orçamento Groq, integrar resposta com fontes e recusa e avaliar os 40 casos. Manter as falhas de recuperação registradas para separar falta de contexto de erro de interpretação. A aprovação das perguntas/respostas não equivale à conferência independente de PDFs/retificações. O assistente será ferramenta de conferência humana; não determina elegibilidade nem substitui leitura do edital vigente. [Método de avaliação](docs/avaliacao.md) · [Primeiros resultados reproduzíveis](docs/resultados-recuperacao.md).

Fontes: [PNCP](https://www.gov.br/pncp/), [API de consulta](https://pncp.gov.br/api/consulta/swagger-ui/index.html).

## Geração: primeiro lote concluído

GPT-OSS 120B funcionou na conta confirmada como gratuita pelo usuário. Busca híbrida: 28 respostas factuais geradas, sete recusas e três respostas por falta de evidência; dois casos factuais bloqueados. Citações existentes não impediram erros de capacidade de SSD e quantidade de tabela. Mediana de geração de 1.195,66 ms nos casos concluídos; 52.877 tokens de entrada e 8.922 de saída, sem contabilizar consumo não confirmado das nove tentativas falhas. Faturamento efetivo não auditado.

[Integração, erros e reprodução](docs/geracao-groq.md) · [Resumo operacional](reports/generation-summary-v1.json) · [Segurança desta entrega](reports/seguranca-geracao-2026-10-01.md). Próximo passo: revisar as respostas/recusas e corrigir interpretação de tabelas, escopo de item e formatação de citações; medir novamente em versão separada.

**Fontes na resposta:** consulta individual salva Markdown privado com referências por afirmação: edital PNCP, arquivo, página física do PDF, link oficial e passagem original. Metadados vêm da recuperação validada. Interface web continua planejada. [Funcionamento e limites](docs/geracao-groq.md).

## Revisão e expansão controlada — 2026-10-01

Revisão do assistente nos 40 casos anteriores: dois erros claros de conteúdo, duas respostas bloqueadas e pendências de completude/unidades/ambiguidade. Isso não substitui avaliação humana. [Achados e critérios](docs/revisao-respostas.md).

Dez perguntas novas aprovadas pelo usuário, sem pistas de localização: palavras-chave 8/10, semântica 7/10 e híbrida 9/10 em Hit@5; cobertura de todas as passagens esperadas na híbrida 8/10. Quatro editais já indexados, separados do piloto; ainda não é teste de crescimento do corpus nem nota de geração. [Execução registrada](docs/resultados-recuperacao.md#primeira-execução-das-dez-perguntas-reservadas--2026-10-01).

Triagem encontrou dois objetos médicos selecionados pelo termo monitores. A seleção futura foi corrigida; o snapshot histórico permanece intacto. [Triagem e limites](reports/sector-review-v1.json).

Implementado checador local de qualidade: exige revisão humana, pelo menos 90% de respostas corretas, completas e apoiadas em cada grupo antigo/novo, cobertura separada e ausência de sobreposição de editais/PDFs. Política inicial: 30 perguntas antigas e 100 novas em dez editais; não garante precisão futura. Estado atual: bloqueado por avaliações pendentes e amostra nova insuficiente. Sem promoção automática de banco. [Plano para manter qualidade](docs/qualidade-na-expansao.md).

Verificação da atualização: 72 testes locais passaram; pip-audit sem vulnerabilidades conhecidas nas dependências auditáveis. API/interface, OCR de tabelas, reranker, painel e 3D permanecem planejados.

## Seleção de contexto experimental

Alternativa opcional `coverage` avaliada em 120 buscas, com 75 testes locais aprovados. Antigas: Hit@5 29/28/29 preservado. Novas: 8/8/9, cobertura completa 7/7/8; ganho semântico acompanhado de regressão de completude. **RRF continua padrão**, porque cobertura da híbrida não melhorou. Essas dez perguntas agora são desenvolvimento; outro conjunto independente será necessário. [Resultados por caso](docs/resultados-recuperacao.md#experimento-cobertura-de-termos-na-seleção--2026-10-01).

## Dez perguntas novas na Groq — 2026-10-01

Autorização explícita de Renê registrada antes das dez chamadas ao GPT-OSS 120B. Seleção padrão RRF, até cinco trechos por pergunta; rótulos não entram no prompt. Uma tentativa por caso, sem repetição para esconder falhas.

- Seis respostas answered passaram pelo validador literal.
- Uma insufficient_evidence passou: reserve-07 não recebeu ligação explícita entre especificação e lote 3.
- Três respostas rejeitadas: reserve-08/09/10 abreviaram citações com reticências; o bloqueio foi mantido.
- Revisão do assistente: reserve-01–04 sem divergência aparente; reserve-05 exige conferir completude de peças/mão de obra/atendimento local; reserve-06 responde valores esperados, mas usa páginas repetidas sem identidade do lote clara e uma citação incompleta de capacidade.

Não publicar 7/10 como acerto: são sete saídas aceitas pelo validador, incluindo insuficiência. Correção/completude/apoio humano permanecem sem nota. As seis respostas não são automaticamente seis acertos.

Mediana da geração das sete saídas aceitas: 1.022,92 ms. Tokens das saídas aceitas: 10.273 entrada e 2.185 saída; consumo das três rejeições não incluído nesse total. Foram dez requisições tentadas, embora `generation_calls` do resumo conte somente as sete aceitas. Plano gratuito confirmado pelo usuário; faturamento não auditado independentemente.

Respostas completas/ficha de revisão privadas, sem sobrescrever a ficha do piloto: nome contém hash da referência. [Resumo operacional](reports/generation-reserve-summary-v1.json) · [Achados por caso](reports/generation-reserve-review-v1.json) · [Configuração/autorização](reports/generation-reserve-protocol-v1.json).

Prioridade seguinte: preservar cabeçalhos/identidade de item ao montar contexto e testar seleção de passagens literais sem abreviação. Não relaxar validador para aceitar citações alteradas. Qualquer ajuste exige regressão e outra reserva independente; extração de tabelas e essa mudança de citação ainda não foram implementadas.

## Contexto ampliado e fonte literal — experimental

Implementadas opções de janela da página original e evidência selecionada por ID, com passagem literal inserida pelo servidor. Mesmo corpus e ranking: cobertura completa híbrida 29/30 →30/30 nas antigas e 8/10 →9/10 no desenvolvimento; Hit@5 igual. Nova geração dos mesmos dez casos: nove respostas aceitas e uma fonte inválida bloqueada, antes seis respostas/uma insuficiência/três rejeições. **Não equivale a 90% de acerto humano.**

Tokens de entrada nos sete casos aceitos comuns: 10.273 →18.994. Revisão humana/independência pendentes, padrão anterior preservado. 85 testes passaram; pip-audit sem avisos conhecidos auditáveis. [Método, custos operacionais e limitações](docs/contexto-e-citacoes.md) · [Segurança desta atualização](reports/seguranca-janelas-2026-10-01.md).

## Rótulos curtos — experimental

Fonte enviada à IA como S1–S5, schema com lista fechada, restaurada ao ID real antes da validação/apresentação. Nova execução nos mesmos dez casos: dez respostas passaram pelo validador literal, sem erro nesta execução; referência humana de correção ainda pendente. Padrões anteriores mantidos. 100 testes locais passaram e pip-audit sem avisos conhecidos auditáveis.

Lista candidata independente: nove contratações distintas das 30 atuais, obtidas por consultas nas cinco regiões; dez arquivos listados. A seleção de metadados foi parcial por erros/HTTP429. Na preparação posterior, sete PDFs foram extraídos e um foi excluído por hash repetido na base antiga. [Implementação e comparação](docs/fontes-curtas-e-benchmark.md).

## Preparação inicial das dez referências — histórico

[Perguntas, respostas esperadas e páginas oficiais](docs/perguntas-independentes-para-revisao.md): dez perguntas em seis contratações/seis PDFs novos, RJ/PR/SC/CE/GO/DF, quatro regiões. Cinco PDFs de editais com anexos e uma certidão de publicação de GO. Caso Serpro inclui roteador, ampliando a amostra de informática para equipamento de rede.

Verificados os hashes de seis arquivos e 17 passagens literais; 11 páginas conferidas visualmente pelo assistente. PDF do PA reutiliza conteúdo já existente, portanto não conta como nova fonte. Três arquivos não preparados (ValueError; motivo específico não registrado). Renê aprovou explicitamente as dez perguntas e referências. Nenhuma pergunta nova executada, nenhum vetor/carga de banco; avaliação das respostas da IA ainda não realizada. 100 testes passaram e pip-audit atual sem avisos conhecidos auditáveis.

A amostra ainda não satisfaz o protocolo de 100 perguntas/10 novas contratações nem demonstra 90% de acerto. [Preparação](reports/independent-documents-v1.json) · [Integridade da referência](reports/independent-reference-v1.json) · [Segurança e limites](reports/seguranca-independente-2026-10-01.md).

[Plano inicial do snapshot separado](reports/independent-index-plan-v1.json): seis PDFs novos/370 páginas. Preparação, vínculo e carga foram concluídos posteriormente, conforme a seção abaixo. A avaliação atual seleciona a contratação por PNCP; não mede descoberta global do edital entre toda a base.

## Snapshot candidato carregado e primeira comparação

Candidata `1446c44aca18011a`: 36 contratações, 55 PDFs, 2.895 páginas e 18.554 trechos. Reutilizados 15.773 vetores e calculados localmente 2.781 novos. Carga idempotente, offsets e igualdade dos textos/vetores antigos verificados; backup restaurado em outro banco com 18.554 trechos. A base anterior permanece disponível; nenhum relatório histórico de preparação/carga foi substituído.

Configuração congelada antes das 210 buscas: resultados/rankings antigos preservados; nas dez perguntas novas, cobertura integral das passagens conhecidas em 5/10 em cada um dos três modos. **Não equivale a50% de acerto de respostas.** À data desta comparação, geração e revisão humana estavam pendentes; a geração posterior está registrada abaixo. Regra de promoção bloqueada; candidata não promovida. 110 testes passaram; pip-audit atual sem avisos conhecidos auditáveis.

As falhas envolvem item errado, tabela entre páginas e repetição de passagens. Próxima melhoria proposta: identidade do item persistida nos trechos e continuações entre páginas; qualquer ajuste baseado nestes erros exige outra reserva. [Método, resultados e falhas](docs/avaliacao-de-crescimento.md) · [Gate](reports/quality-growth-v1.json) · [Segurança](reports/seguranca-candidata-2026-10-01.md).

O plano acima descreve a etapa anterior; a carga/conferência agora está concluída. À data do plano, a geração tinha prévia privada e aguardava autorização. A execução posterior está registrada abaixo.

## Geração candidata executada — 2026-10-01

Dez novos casos autorizados e executados na Groq: seis respostas/quatro abstenções, integridade10/10; correção humana pendente. Quantidade presente mas não interpretada no03; omissão de por item no08; fontes alternativas legítimas07/10. Gate permanece bloqueado, sem promoção ou garantia de90%. [Resultados, método e próximo passo](docs/geracao-na-base-candidata.md). 110 testes passaram e auditoria atual sem avisos conhecidos auditáveis.

## Etapa1 implementada — aguardando aprovação para etapa2

Perfil opcional item_structure vincula itens/continuações, destaca quantidade literal e reduz repetição de fontes.119 testes passaram; pip-audit atual sem avisos conhecidos auditáveis. Sem Groq, avaliação de acerto ou escrita no banco nesta etapa; integração real e avaliação quantitativa aguardam aprovação explícita conforme pedido de Renê. [Funcionamento, limites e evidências](docs/estrutura-dos-itens.md).
