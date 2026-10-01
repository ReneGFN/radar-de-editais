# Segurança — geração candidata — 2026-10-01

Escopo: dez consultas autorizadas à Groq, consolidação privada, relatório de achados e CLI de gate após geração. Não audita aplicação em produção.

| Grupo | Resultado/evidência | Limites |
|---|---|---|
|1 Segredos/dados|Verificado no escopo: credencial privada somente autenticação; prévia sem chave/gabarito; respostas e PDFs fora do Brain. Exportação por whitelist/scanner.|Não reaudita todo histórico do Brain.|
|2 APIs/frontend|Verificado: dez chamadas oficial Groq com até cinco passagens públicas, autorização específica registrada; nenhuma chamada adicional.|Frontend próprio futuro; plano gratuito declarado pelo usuário, faturamento não auditado.|
|3 Entradas|Verificado: referência/hash congelados; schema fechado S1–S5, restauração de IDs e validação literal. Dez resultados passaram;110 testes atuais passaram.|Integridade não prova correção/completude.|
|4 Autorização|Verificado: resposta explícita pode prosseguir para o lote pendente; não ampliada a outros lotes.|Revisão humana ainda pendente.|
|5 Ataques|Verificado no escopo: dados tratados como texto, SQL parametrizado sem mudança; abstenções exibidas com mensagem neutra.|Teste real de prompt injection em PDF pendente; XSS/CSRF de frontend futuro não aplicáveis.|
|6 Logs|Verificado: checkpoints privados e relatórios separados; zero falhas desta execução; primeira execução preservada. Scanner antes do push.|Tentativas de leitura no sandbox falharam; acesso autorizado elevado resolveu. Erros locais de encoding corrigidos sem alterar avaliação.|
|7 Senhas|Não aplicável: não alterou login, senha ou recuperação.|Identidade multiusuário futura.|
|8 Backup|Verificado por evidência reutilizada de hoje: independent-backup-verification-v1.json, restauração isolada de18554 trechos.|Etapa somente lê banco; nenhum novo dump necessário. Recuperação fora da máquina/rotina periódica não comprovadas.|
|9 Dependências|Verificado:110 testes passaram; pip-audit atual sem vulnerabilidades conhecidas auditáveis; sem dependências novas. Gate pós-geração executado e bloqueado.|Pacote local fora da auditoria PyPI; não é auditoria de produção.|
|10 HTTPS|Verificado no escopo: chamadas concluídas à API oficial HTTPS; credencial não enviada a outro host.|Não audita HSTS/CSP ou certificado de frontend inexistente; DB local.|

Auditoria atual privada: tmp/radar-pip-audit-generation-independent.json. Evidências públicas: generation-growth-summary-v1.json, generation-growth-review-v1.json, independent-generation-authorization-v1.json, quality-growth-generated-v1.json. Riscos restantes: informação de item incompleta, omissão do modelo, citações redundantes e ausência de revisão humana. Não houve promoção, mudanças de produção, exclusão de volumes ou rotação de credenciais.
