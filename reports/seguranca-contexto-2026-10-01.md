# Segurança — seleção de contexto e geração da reserva — 2026-10-01

Escopo: alternativa de reordenação, comparações locais e dez perguntas enviadas à Groq após autorização explícita de Renê neste chat. Não constitui auditoria de aplicação em produção.

| Grupo | Resultado/evidência | Limites |
|---|---|---|
| 1. Segredos/dados | Verificado no escopo: exportação por lista permitida, padrões de segredos/campos privados e revisão dos arquivos. Chave somente autenticação; respostas e PDFs privados. | Scanner não é garantia universal; sem publicação de saídas completas. |
| 2. API/frontend | Verificado: novas chamadas autorizadas à API oficial Groq, GPT-OSS 120B, até cinco trechos públicos por pergunta. | Nenhuma interface web/bundle implementado ou auditado. Plano gratuito confirmado pelo usuário, cobrança não auditada. |
| 3. Entradas | Verificado: perfil de seleção limitado a rrf/coverage; busca conserva validação de pergunta/escopo. 75 testes locais aprovados. | Reordenação opera somente em candidatos internos; uploads/API futuros. |
| 4. Autorização | Verificado: consentimento explícito dos dez casos na Groq; nenhuma promoção de banco. | Revisão humana não autenticada por arquivo; serviço multiusuário futuro. |
| 5. Ataques comuns | Verificado no escopo: bônus usa tokens, não executa conteúdo; SQL parametrizado existente preservado. | Resistência a instruções embutidas em PDF ainda pendente; CSRF não aplicável sem sessões web. |
| 6. Logs/auditoria | Verificado: relatórios por caso preservam ganhos/regressões, hashes e parâmetros. SDK continua com erros sanitizados; checkpoint privado. | Conteúdo correto exige conferência humana. Nome da ficha agora inclui hash da referência, evitando sobrescrever revisão do piloto. |
| 7. Senhas | Não aplicável: login/recuperação de senha não alterados; sem rotação. | Não constitui auditoria de gerenciador de credenciais. |
| 8. Backup | Não aplicável a nova restauração: banco somente consultado; snapshot intacto. Evidência anterior: reports/verificacao-local.json. | Nenhuma rotina periódica nova; restore anterior não prova produção futura. |
| 9. Dependências/produção | Verificado: nenhum pacote novo; 75 testes; pip-audit atual sem vulnerabilidades conhecidas auditáveis. | Primeira tentativa falhou por rede/cache do sandbox; repetição autorizada concluiu. Pacote local não auditável no PyPI. |
| 10. HTTPS | Verificado no escopo: SDK aponta à origem HTTPS oficial Groq; PNCP HTTPS preservado. | Cabeçalhos/certificados de aplicação própria em produção não aplicáveis ainda. |

Comparação: 120 buscas, referências e corpus preservados; sem ganho de cobertura completa da híbrida, RRF continua padrão. Dez perguntas passaram a desenvolvimento depois de orientar o experimento; não são mais teste independente da reordenação. Sem alterações destrutivas, ERP, volumes ou credenciais.

Auditoria de dependências: tmp/radar-pip-audit-context-selection.json no Brain, não exportado. Erro inicial de acesso não foi contado como aprovação. Geração mantém validação literal e revisão semântica pendente; citações existentes não provam interpretação correta.
