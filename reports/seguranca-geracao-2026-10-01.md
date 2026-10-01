# Segurança no escopo de recuperação e geração — 2026-10-01

Escopo: planejamento de consultas, integração Groq, avaliadores, testes e documentação. Não é auditoria completa nem aprovação de produção.

| Grupo | Resultado e evidência | Limite / pendência |
|---|---|---|
| 1. Segredos/dados | Credencial e checkpoints ficam no diretório privado fora do Brain. ACL da chave conferida: duas regras, usuário e sistema; nenhum principal permitido inesperado. Leitor aceita valor puro/atribuição sem imprimir segredo. Exportação por lista permitida e varredura de padrões. | Exportação por lista revisada e padrões de segredo conferidos; não comprova inexistência de dados sensíveis em todo o histórico. |
| 2. API/frontend | Chamada exclusivamente do núcleo Python; não existe frontend nesta entrega. Modelo fixo, até cinco trechos, sem resposta esperada no prompt. | API/interface e autenticação multiusuário futuras. |
| 3. Entradas | Consulta até 1.000 caracteres; perfis/modos validados; contexto até 16.000 caracteres; esquema JSON e limites de claims/evidências. Testes rejeitam fontes/citações inventadas. | Integridade literal não prova interpretação. |
| 4. Autorização | Usuário confirmou plano gratuito e autorizou expressamente os 40 casos com trechos públicos após bloqueio da revisão automática. Chave apenas para autenticação; papel limitado no banco. | Faturamento/limites específicos da conta não auditados independentemente. |
| 5. Ataques | SQL parametrizado; colunas de filtro em lista fixa. Fonte tratada como dado não confiável; sem ferramentas externas. | Recusa e resistência semântica exigem avaliação; não existe UI para avaliar XSS/CSRF nesta etapa. |
| 6. Logs | Erros registram classe/status e mensagens locais em lista permitida; nunca corpo bruto do SDK. Respostas completas e candidatos rejeitados somente em arquivos privados. Tracing remoto desativado. | Retenção automática e auditoria de serviço multiusuário não implementadas. |
| 7. Senhas | Nenhum login/sistema de recuperação novo. Chave de provedor armazenada fora do repositório; nenhum valor documentado. | Gestão da conta Groq pertence ao usuário; política da conta não examinada. |
| 8. Backup | Entrega lê corpus/banco; não muda dados persistentes nem volumes. Evidência anterior de restauração em reports/verificacao-local.json continua pertinente ao corpus inalterado. | Restauração do novo checkpoint não testada; rotina periódica ainda pendente. |
| 9. Dependências | pip-audit executado nesta atualização: sem vulnerabilidades conhecidas nas dependências auditáveis. 50 testes passaram. Pacote local radar-de-editais não auditável via PyPI, código examinado no escopo. | Resultado limitado à base de avisos consultada; não garante ausência de vulnerabilidades. |
| 10. Comunicação | Endpoint HTTPS oficial fixo; chamada autenticada retornou resposta real. Validação TLS padrão do SDK, sem verify=false. Banco continua local. | Headers/certificados de implantação própria não aplicáveis: serviço público não implantado. |

Problemas encontrados/corrigidos: endereço duplicado gerou HTTP404; formato de arquivo com atribuição gerou HTTP401; diferenças de espaços em citações causaram bloqueio. Ajuste do validador só permite espaços diferentes e conserva a passagem original; não aceita troca de palavras. Falhas permanecem separadas de respostas concluídas no checkpoint; 40 casos testados, 38 validados e dois bloqueados. 50 testes passaram. Custos/uso de tentativas falhas não confirmados.

Pendências: revisão semântica dos 40 casos, teste reservado sem pistas de localização, revisão independente de PDFs/retificações e preparação de controles quando houver API/interface pública.
