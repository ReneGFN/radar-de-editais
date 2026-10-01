# Radar de Editais

**Laboratório de avaliação de RAG para leitura de editais públicos de informática.**

O projeto investiga se pequenos fornecedores conseguem encontrar prazos, especificações e condições com referência verificável ao documento original. O objetivo é publicar metodologia, resultados medidos e erros encontrados ao comparar versões do sistema.

## Estado em 2026-10-01

- **Base ampliada preparada:** 30 editais/contratações, 11 estados, cinco regiões; 49 PDFs, 2.525 páginas e 15.773 trechos.
- **Carga ampliada verificada:** 15.773 vetores no PostgreSQL; repetição sem duplicação, filtros e offsets conferidos. Backup restaurado em banco separado com os mesmos 15.773 trechos. Reaproveitados 4.664 vetores compatíveis da base inicial.
- **Base inicial verificada:** 10 editais, 14 PDFs e 4.664 vetores; carga idempotente, filtros, offsets e backup/restauração conferidos. Evidências históricas em `reports/snapshots/b1ee54ef84e97078/`.
- **Implementados:** coleta, extração, embeddings locais, PostgreSQL/pgvector e busca híbrida coordenada por LangChain.
- **Avaliação em revisão:** 30 perguntas com respostas e 10 recusas; 40 casos aprovados pelo usuário. Evidências em 24 editais/24 PDFs, 11 estados; integridade conferida, 32 testes passaram. [Perguntas para revisão](docs/perguntas-para-revisao.md).
- **Recuperação avaliada:** 180 buscas em 30 perguntas aprovadas. Híbrida: trecho de referência no top 5 em 17/30 na linha de base e 20/30 após mudança lexical (+10 pontos percentuais), com cinco ganhos e duas regressões. [Método, resultados e erros](docs/resultados-recuperacao.md).
- **Planejados:** geração com Groq, avaliação de respostas/recusas, API/interface e explorador 2D/3D.
- **Qualidade das respostas ainda não medida.** Recuperar uma evidência não comprova resposta correta ou recusa segura.

## Arquitetura

[Arquitetura e diagramas](docs/arquitetura.md) · [Execução local](docs/base-e-operacao.md) · [Investigação 2D/3D](docs/visualizacao-3d.md)

```text
PNCP → PDFs privados → texto por página → trechos LangChain
     → embeddings locais → PostgreSQL + pgvector
Pergunta + edital + snapshot → buscas semântica e lexical
     → fusão dos rankings → trechos com página e fonte
```

Python organiza o núcleo. LangChain divide os textos e coordena as buscas em paralelo. MiniLM multilíngue gera vetores de 384 dimensões em CPU; PostgreSQL combina busca exata por cosseno e full text search. Groq será usado na geração; modelo específico ainda a definir. Dify fica para uma opção futura.

API FastAPI e interface React/TypeScript estão planejadas. O mesmo núcleo servirá CLI, API e avaliador.

## Corpus e seleção

Setor: computadores, monitores e acessórios. Mantidos dez editais de SP, com dois adicionais de PR, RS, MG, RJ, BA, PE, GO, MT, PA e AM. Amostra de conveniência por cotas, **sem representatividade estatística**. Há editais mistos; a avaliação deve identificar os itens de informática.

[Manifesto final](datasets/manifests/4f8ddffaa01b6a20.json) · [Distribuição da amostra](reports/amostra-30.json) · [Preparação](reports/preparacao.json) · [Qualidade por documento](reports/qualidade-30.json)

[Carga](reports/carga.json) · [Verificação e restauração](reports/verificacao-local.json) · [Busca em outros estados](reports/buscas.json). O relatório de preparação registra essa etapa; a carga e verificação registram o estado posterior. Nenhum desses testes mede acerto das respostas.

Metadados registram fonte oficial, data e hash do PDF. Consulta da API não comprova vigência ou oportunidade aberta; datas e condições exigem conferência no documento. Anexos/retificações são preservados sem presumir substituição automática.

PDFs, textos extraídos, modelos, vetores, credenciais e backups **não são publicados**. O comando hydrate baixa documentos oficiais e confere hashes; fonte alterada é sinalizada, sem substituir silenciosamente o snapshot.

## Avaliação planejada

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
