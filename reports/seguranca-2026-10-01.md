# Segurança — expansão e publicação em 2026-10-01

Escopo: seleção de 30 editais em vários estados, preparação, reutilização de vetores e publicação do projeto público. Publicação autorizada explicitamente pelo responsável; visibilidade PUBLIC conferida pelo GitHub CLI. Nenhuma publicação de PDFs/textos extraídos, modelos, senhas ou dumps.

| Grupo | Resultado, evidência e limite |
|---|---|
| 1. Segredos e dados | Verificado no escopo de publicação: checkout limpo, lista explícita de arquivos de código/documentação/metadados, `.gitignore` ampliado, revisão manual e scanner de padrões antes do push. Manifestos não contêm texto de PDF, CPF, contatos ou campos de credenciais. Não há auditoria integral do histórico do ambiente de trabalho. |
| 2. API/frontend | Não aplicável a aplicação web: API e interface ainda não existem. Cliente PNCP mantém origem controlada e tracing externo desativado. Nenhum texto enviado ao Groq. |
| 3. Entradas | Verificado no escopo: limite de até 50 contratações por coleta, UF/datas validadas, cotas de dois editais por estado adicional e deduplicação de IDs. Limites de downloads/PDFs preservados. Filtro refinado exclui simples papelaria/suprimentos sem indicação de equipamentos. Testes de entradas e limites passaram. |
| 4. Autenticação/autorização | Banco local com papel de carga limitado conforme inicialização. Filtros por snapshot/edital reaplicados na verificação da nova base; evidência em verificacao-local.json quando concluída. Não há autenticação de aplicação. A publicação é pública e não expõe o banco. |
| 5. Ataques comuns | Verificado no código: SQL parametrizado; nome de banco de restauração construído com Identifier; URLs restritas ao PNCP/HTTPS; teste de redirecionamento externo. Fingerprints e configuração impedem reutilização de cache de outro modelo. XSS/CSRF não aplicáveis sem web/cookies. |
| 6. Logs/auditoria | Verificado no escopo: progresso apenas com IDs/contagens, relatórios sem texto bruto e logs Docker limitados. Histórico da base inicial arquivado para distinguir execuções. Logs de diagnóstico do Docker não publicados. Retenção operacional automatizada ainda pendente. |
| 7. Senhas/recuperação | Configuração mantida: senhas aleatórias fora do repositório, arquivos privados e SCRAM-SHA-256. Não houve rotação. Recuperação de senha de aplicação não aplicável. |
| 8. Backup/recuperação | Procedimento corrigido para verificar o snapshot solicitado na restauração, pois o banco pode conter mais de um snapshot. Dump inteiro privado; banco separado de restauração. Resultado da nova execução em verificacao-local.json; relatório antigo preservado. Retenção, criptografia e restauração em outra máquina pendentes. |
| 9. Dependências/produção | Auditoria pip-audit atual sem vulnerabilidades conhecidas nas dependências auditáveis; pip check sem conflitos. 14 testes passaram. Teste de integridade/modelo do cache adicionado; teste teve falha de permissão no TEMP do Windows e foi repetido com diretório temporário exclusivo, passando. Pacote local fora do catálogo PyPI; imagem Docker não passou por scanner de CVEs. |
| 10. HTTPS/comunicação | HTTPS validado pelos clientes nas consultas/downloads; GitHub acessado com autenticação local, sem exportar credenciais. PostgreSQL loopback local sem TLS obrigatório. Produção, cookies e cabeçalhos web não aplicáveis nesta etapa. |

## Recuperação do Docker e limites

Docker Desktop falhou na inicialização com sockets locais inacessíveis em Ingest e Secrets Engine. Reinício simples e movimento do arquivo falharam. Com Desktop encerrado e engine indisponível, pastas de sockets temporários foram isoladas reversivelmente; a pasta Secrets Engine foi conferida como contendo apenas um socket vazio. Diretórios originais preservados; nenhum volume, imagem, banco, configuração ou credencial removido.

Após a recuperação, PostgreSQL voltou saudável e o snapshot inicial continuou com 4.664 trechos. É uma recuperação local observada; persistência após futuras reinicializações não foi verificada. Há relatos semelhantes no [rastreador do Docker](https://github.com/docker/desktop-feedback/issues/554); isso não prova causa ou correção definitiva.

Os controles desta atualização não aprovam produção nem auditam outros projetos que compartilham o Docker. Revisão visual dos PDFs é amostral; páginas sem texto suficiente continuam sinalizadas. Geração e visualização 3D ainda não implementadas, sem métricas de qualidade publicadas.
