# Base de avaliação — piloto v2

O [piloto v2](../datasets/evaluation/pilot-v2.json) contém **30 perguntas com respostas esperadas e 10 casos de recusa**. As evidências abrangem 24 dos 30 editais, 24 dos 49 PDFs e os 11 estados/cinco regiões. Todos os 40 casos foram aprovados pelo usuário, em duas etapas da conversa, em 2026-10-01. A aprovação na conversa não foi registrada como conferência independente dos PDFs. O [v1](../datasets/evaluation/pilot-v1.json) e seu relatório foram preservados como histórico.

Leia as [perguntas, respostas, fontes e trechos para revisão](perguntas-para-revisao.md). Q09–Q30 e R03–R10 são os casos novos; cada um também mantém um ID estável. É um conjunto de desenvolvimento, não um teste final reservado. Cobertura de documentos não significa enumeração de todas as cláusulas ou evidências relevantes.

Cada caso tem pergunta, resposta esperada, tipo e estado de revisão. Evidências identificam trecho, documento, página física do PDF, SHA-256 e URL oficial. Isso permite detectar referências quebradas quando corpus ou preparação mudam. A conferência automática não decide se a interpretação é correta, se há retificação ou se outra seção altera a resposta.

## Reprodução

Após preparar o snapshot `4f8ddffaa01b6a20`, usando o mesmo `RADAR_PRIVATE_ROOT`, executar na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe ops/validate-reference.py datasets/evaluation/pilot-v2.json datasets/manifests/4f8ddffaa01b6a20.json --report reports/reference-pilot-v2.json
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
```

Não exige PostgreSQL nem Groq; lê a preparação privada. O relatório contém hash do conjunto, contagem de casos e resultado de integridade. Não publica o corpus bruto ou credenciais.

## Revisão de Renê

1. Abrir cada PDF pela URL oficial e conferir a página indicada, incluindo a tabela/item completo.
2. Examinar anexos e retificações do snapshot; registrar ambiguidades ou invalidação do caso. O snapshot não promete ser o edital vigente.
3. Ajustar a resposta e incluir todas as evidências necessárias. Registrar a aprovação das perguntas/respostas separadamente da conferência dos PDFs. Conservar notas de justificativa sem dados pessoais. O validador exige um registro para casos aprovados, mas não autentica o revisor nem comprova sua análise.
4. Acrescentar perguntas naturais sem dicas de página, casos com múltiplas fontes e ausência de evidência verificada. As perguntas atuais com página facilitam a conferência, mas não simulam bem todo o uso real.
5. Separar por edital o desenvolvimento e o teste reservado antes de ajustar a busca; evitar que tabelas duplicadas ou perguntas do mesmo documento contaminem a comparação.

Os dez casos de recusa avaliam previsões impossíveis, dados insuficientes da empresa, promessas sem apoio, invenção de informações/citações, confidencialidade, credenciais e instruções maliciosas em documentos. Recusar a parte indevida e oferecer ajuda permitida; não premiar recusa genérica. Não são prova de que uma informação factual está ausente em todos os documentos.

## Medição futura

Hit@5 indica se uma evidência relevante apareceu entre cinco resultados. Recall@5 exige enumerar previamente todas as evidências relevantes; os IDs atuais são evidências conhecidas, não uma lista exaustiva. Respostas sem apoio exigem avaliação por afirmação. Latência e custo devem vir de execuções reais, distinguindo preparação, recuperação e geração. Casos não aprovados ficam fora de métricas finais. A primeira avaliação da recuperação está em [resultados e erros](resultados-recuperacao.md); geração e recusas ainda não foram avaliadas.

## Verificação de 2026-10-01

Quarenta casos passaram novamente na conferência de integridade e das metas 30/10; todas as 40 aprovações da conversa estão registradas. Os testes abaixo foram executados antes desta atualização de aprovação; código e dependências não mudaram. Executados 23 testes (14 existentes e nove novos), todos passaram. Os novos testes verificam adulteração de citação, página, hash, URL, documento, snapshot, aprovação sem registro e contagem incompleta. Houve aviso de acesso ao cache do pytest; os testes executaram normalmente usando diretório temporário exclusivo. A reprodução acima desativa somente o cache opcional.

A conexão PostgreSQL expirou novamente após a aprovação; `ConnectionTimeout` registrado sem dados de conexão sensíveis. Nenhuma avaliação de recuperação/geração foi executada, nem dados do banco modificados. Usamos arquivos preparados privados, conferindo o contexto de tabelas/cláusulas selecionadas. A pergunta de Três Corações conserva “30 dias” sem inventar se são úteis ou corridos; a de Porto Ferreira diferencia o título “512 GB” do mínimo “500 GB”. Esse tipo de detalhe deve ser revisado antes de medir erros da IA.

### Checklist de segurança no escopo

| Grupo | Resultado e limite |
|---|---|
| 1. Segredos | Verificado: arquivos novos/alterados examinados e padrões de credenciais conferidos; somente referências técnicas públicas, exemplos sintéticos e código. `.gitignore` mantém PDFs, dados privados, credenciais, ambientes e dumps excluídos; corpus bruto permanece privado. |
| 2. API/frontend | Não aplicável: nenhuma interface ou endpoint acrescentado. |
| 3. Entradas | Verificado: perguntas não vazias e limitadas, respostas não vazias, tipos/estados/IDs e snapshot restrito; citação/origem, registro de aprovação e meta de contagens conferidos. Nove testes novos passaram. CLI local, sem contrato de uploads públicos. |
| 4. Autorização | Não aplicável à mudança: nenhuma conta, papel ou privilégio alterado. |
| 5. Ataques | Verificado: validador não executa conteúdo de documentos e não compõe SQL; caminho privado usa snapshot hexadecimal restrito. |
| 6. Logs | Verificado: relatório registra contagens/hash, sem corpus bruto ou segredos; nenhuma telemetria acrescentada. |
| 7. Senhas | Não aplicável: nenhum mecanismo de senha alterado. |
| 8. Recuperação | Verificado no escopo: piloto v1/relatório preservados, v2 separado; banco não modificado. Backup/restauração anteriores não repetidos; nova tentativa de conexão expirou; avaliação de recuperação pendente. |
| 9. Dependências | Não aplicável à alteração: nenhuma biblioteca nova ou versão modificada; nenhuma nova auditoria de vulnerabilidades executada. |
| 10. Comunicação | Não aplicável: conferência local, sem novas chamadas de rede ou implantação. URLs oficiais são referências, não conteúdo executado. |

Esta revisão não equivale a auditoria de toda a aplicação ou aprovação do benchmark.

## Atualização de aprovação — 2026-10-01

Escopo desta atualização: dados de referência, estados de aprovação, relatório de integridade e documentação; nenhum código/dependência ou dado de banco alterado. Os dez grupos foram reaplicados: **1** verificado, sem segredos ou dados de clientes nos conteúdos alterados; **2** não aplicável, sem API/frontend; **3** verificado pela execução do validador sobre os 40 casos; **4** não aplicável, sem privilégios alterados; **5** verificado, consulta SQL constante parametrizada e conteúdo das recusas tratado como dados; **6** verificado, erro registrado somente por classe; **7** não aplicável, sem senhas alteradas; **8** não aplicável à restauração nesta etapa, histórico v1 preservado e banco sem mutações; **9** não aplicável, sem dependências alteradas ou nova auditoria; **10** não aplicável à implantação, tentativa local em loopback, sem comunicação externa de dados. Não constitui auditoria da aplicação inteira. Próximo passo: recuperar a conexão e medir a busca com o hash aprovado do conjunto.

## Avaliação da busca concluída — 2026-10-01

Após a aprovação, Docker Desktop foi iniciado e PostgreSQL voltou normalmente. Executadas 180 consultas nas duas estratégias, banco preservado e 32 testes passaram. Híbrida 17/30 → 20/30 no Hit@5 de trechos conhecidos, cinco ganhos/duas regressões. Estratégia OR é padrão de desenvolvimento; a antiga permanece reproduzível. Não há métricas de respostas ou recusas. [Resultados e protocolo](resultados-recuperacao.md), [segurança desta etapa](../reports/seguranca-avaliacao-2026-10-01.md). O timeout registrado acima é histórico, não bloqueio atual.
