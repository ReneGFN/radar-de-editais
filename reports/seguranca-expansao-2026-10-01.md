# Segurança — revisão, reserva e expansão — 2026-10-01

Escopo: triagem de setor, checador local de qualidade, referências aprovadas e 30 consultas locais de recuperação, documentação e exportação pública. Não constitui auditoria completa da aplicação. Sem alteração de dependências, banco, credenciais, serviços ERP ou produção.

| Grupo | Resultado e evidência | Limites |
|---|---|---|
| 1. Segredos/dados | Verificado no escopo: exportador por lista permitida inspeciona padrões de segredos e campos privados; referências públicas técnicas, relatórios apenas metadados. PDFs, renderizações e saídas completas continuam privados. | Regex não garante ausência de todo dado sensível; revisão manual dos arquivos alterados complementar. |
| 2. API/frontend | Não aplicável às mudanças: somente CLI local; zero chamadas novas à Groq no teste reservado. | API/interface futura não auditada. |
| 3. Entradas | Verificado: revisão exige IDs únicos, tipos booleanos reais, estados válidos, hashes, grupos e limites. CLI limita arquivo a 2 MiB; triagem limita descrição. Suite completa: 72 testes aprovados. | Validação de uploads/rotas futura. |
| 4. Autorização | Verificado no escopo: aprovação do usuário registrada para perguntas/referências; checador não promove banco. | Status humano em arquivo não autentica revisor; identidade controlada em API futura. |
| 5. Ataques comuns | Verificado no escopo: mudanças não compõem SQL/comandos com descrição do edital; recuperação existente usa parâmetros. Testes anteriores de apresentação segura continuam na suite. | Recusa a pedido malicioso não prova resistência a PDF com instrução embutida; esse cenário segue pendente. CSRF não aplicável sem navegador/sessões. |
| 6. Logs/auditoria | Verificado: hashes de referência/código, snapshot e erros por caso preservados; relatório de qualidade deixa pontuações pendentes nulas. Sem chave/resposta bruta nos novos relatórios públicos. | Retenção e auditoria multiusuário futuras. |
| 7. Senhas | Não aplicável à atualização: nenhum login/recuperação de senha implementado ou credencial alterada. | Não equivale a nova auditoria do armazenamento privado de credenciais. |
| 8. Backup | Não aplicável a nova restauração: somente leitura do banco, sem alteração de corpus. Evidência anterior em verificacao-local.json conserva restauração de 15.773 trechos. | Backup periódico automatizado e recuperação de produção não implementados. |
| 9. Dependências/produção | Verificado: 72 testes locais e pip-audit atual sem vulnerabilidades conhecidas nas dependências auditáveis; nenhum pacote novo. | Pacote local radar sem registro PyPI não é auditado pelo serviço; ausência de aviso não garante segurança. |
| 10. HTTPS | Verificado no escopo documental: referências apontam ao PNCP HTTPS; experimento reservado não enviou dados à Groq. | Certificados/cabeçalhos de uma aplicação em produção não verificáveis: aplicação web ainda inexistente. |

Problemas de qualidade encontrados: item e quantidade confundidos em respostas, ambiguidade de item/unidade, dois objetos médicos no corpus, seleção incompleta na reserva. Triagem futura corrigida com testes; os demais permanecem registrados. Não houve correção silenciosa de referência nem ajuste da busca após observar a reserva.

Evidências: reports/generation-review-v1.json, sector-review-v1.json, quality-release-v1.json, reference-reserve-v1.json, reserve-protocol-v1.json e retrieval-reserve-v1.json. Auditoria de dependências local: tmp/radar-pip-audit-quality-expansion.json no Brain, sem exportação. Resultado de qualidade bloqueado; novas respostas e revisão humana pendentes.
