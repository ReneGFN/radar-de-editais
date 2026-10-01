# Segurança — primeira avaliação de recuperação

Escopo: iniciar Docker Desktop local, conferir PostgreSQL existente, instrumentar a busca, implementar avaliador, executar linha de base/experimento e documentar resultados. Sem geração, alteração de dados, novo serviço web ou implantação. Publicação das atualizações autorizada pelo usuário na conversa; apenas arquivos revisados do projeto serão exportados, sem registros do Brain.

| Grupo | Resultado, evidência e limite |
|---|---|
| 1. Segredos e dados | Verificado no escopo: credenciais lidas do diretório privado, nunca impressas. Relatórios só têm IDs, metadados, hashes, contagens e tempos; perguntas incluem exemplos sintéticos de ataques, sem valores de segredos. Revisão de arquivos/exportação e scanner de padrões antes do push. PDFs, corpus bruto, modelos e dumps continuam excluídos. |
| 2. APIs/frontend | Não aplicável a interfaces: nenhum endpoint ou frontend acrescentado. Sem chamadas Groq; embeddings locais. Rastreamento externo permanece desativado. |
| 3. Entradas | Verificado: snapshot hexadecimal restrito, perguntas aprovadas, integridade de citações/meta de casos/modelo/banco, modos/estratégias limitados; avaliador rejeita caso não factual, não aprovado, sem evidência ou fora do edital. Testes passaram. CLI local, sem garantia de contrato para uploads públicos. |
| 4. Autorização | Verificado no escopo: avaliação conecta como `radar_loader`; consultas mantêm snapshot/edital. Verificações com IDs inexistentes e formato de SQL injection retornaram vazio. Nenhum privilégio, papel ou autenticação alterado. Usuário de carga ainda tem permissões de escrita para ingestão; avaliador executa SELECT, não é papel exclusivo de leitura. |
| 5. Ataques comuns | Verificado: SQL e estratégias fixos, entradas parametrizadas; normalização lexical via função PostgreSQL antes de converter a representação gerada a OR. Não executa instruções dos editais ou URLs das citações. Testes de filtros/adulteração e modos inválidos passaram. XSS/CSRF não aplicáveis sem interface/cookies. |
| 6. Logs/auditoria | Verificado: progresso usa contagens, sem textos/credenciais; relatórios guardam resultados individuais por ID e configuração para reprodução. Logs Docker consultados localmente, sem envio externo de diagnóstico. Retenção automatizada ainda pendente. |
| 7. Senhas | Não aplicável a mudanças: nenhum mecanismo ou senha alterado; armazenamento privado existente reutilizado, valores não registrados. |
| 8. Backup/recuperação | Verificado no escopo: Desktop iniciado, banco saudável, snapshots preservados com 15.773 e 4.664 trechos antes/depois. Sem remoção/quarentena de sockets nesta etapa ou reinicialização de volumes. Backup/restauração de 2026-10-01 já registrados, não repetidos nesta leitura. Reinicialização atual funcionou; não prova estabilidade permanente do Docker. |
| 9. Dependências/produção | Verificado no escopo: manifestos/lock sem mudança, bibliotecas instaladas e hashes do modelo registrados no relatório; 32 testes passaram. Auditoria pip-audit anterior de 2026-10-01 não repetida; nenhuma nova afirmação sobre vulnerabilidades atuais ou imagem Docker. Código avaliador é ferramenta de desenvolvimento, sem deployment. |
| 10. Comunicação | Verificado no escopo: banco em loopback `127.0.0.1:55432`, sem serviço web novo. Comunicação GitHub/consulta de documentação usa HTTPS. TLS de produção, cookies e cabeçalhos web não aplicáveis nesta etapa. |

## Limites materiais

O experimento OR ganhou cinco casos e perdeu dois; dez falhas de ID conhecido permanecem. Trinta perguntas com rótulos não exaustivos, uma repetição e conjunto de desenvolvimento não provam generalização, respostas corretas ou recusa segura. Dez casos de recusa não foram executados contra modelo. Não há auditoria integral do histórico do Brain, de outros projetos Docker ou de implantação de produção.
