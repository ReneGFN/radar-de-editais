# Segurança da apresentação de fontes — 2026-10-01

Escopo: renderer Markdown, saída privada da consulta CLI, testes e documentação. Sete testes novos passaram; exemplo real do checkpoint renderizado sem nova chamada externa. Não é auditoria de aplicação inteira.

| Grupo | Resultado no escopo e limites |
|---|---|
| 1. Segredos/dados | Verificado: saída Markdown privada fora do Brain; exportação inclui código e documentação, não exemplo real nem checkpoint. Nenhuma chave lida para esta conferência. Varredura da exportação antes de publicar. |
| 2. API/frontend | Verificado no CLI: metadados vêm da recuperação, referência junto da afirmação; links só PNCP. Frontend/API pública ainda não implementados. |
| 3. Entrada | Verificado: página positiva, fonte validada e vínculo de cada evidência; testes bloqueiam referência ausente e URL inválida. |
| 4. Autorização | Sem mudança de autenticação/banco; usa resultados do lote autorizado. Nenhum novo envio à Groq. Autorização multiusuário não aplicável ao CLI local. |
| 5. Ataques | Verificado: texto escapado em Markdown; URLs rejeitam esquema javascript, host estranho e credenciais. Interface futura exige verificação de seu renderizador. |
| 6. Logs | Verificado: console informa caminho/status; resposta legível em diretório privado. Reason sem citações não apresentado como conclusão factual. Retenção automática segue pendente. |
| 7. Senhas | Não aplicável: não altera leitor de chave, login, política ou recuperação. |
| 8. Backup | Sem mudança de corpus/banco ou volumes; evidência de restauração anterior continua pertinente ao corpus inalterado. Nova apresentação é regenerável do checkpoint; backup periódico do checkpoint permanece pendente. |
| 9. Dependências | pip-audit atualizado: sem vulnerabilidades conhecidas nos pacotes auditáveis, pacote local não auditável no PyPI. Nenhuma dependência acrescentada. Sete testes específicos da apresentação aprovados. |
| 10. HTTPS | Verificado na construção: só HTTPS oficial PNCP, sem credenciais. Abertura do link e suporte a fragmento de página não testados nos visualizadores; não afirmar navegação garantida. |

Pendências: interface, revisão humana do apoio semântico, links atuais dos documentos/retificações e benchmark reservado. Esta atualização não muda prompts, recuperação nem métricas do lote anterior.
