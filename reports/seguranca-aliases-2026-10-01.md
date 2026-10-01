# Segurança — aliases e seleção candidata — 2026-10-01

Escopo: rótulos de fonte por requisição, comparação autorizada na Groq, metadados PNCP e documentação; não auditoria de aplicação em produção.

| Grupo | Resultado e evidência | Limites |
|---|---|---|
| 1. Segredos/dados | Verificado: exportação por lista permitida/scanner; respostas, passagens, PDFs e credenciais privados. Metadados públicos sem campos de pessoas/contatos. | Lista candidata não aprova PDF; nenhuma extração nova publicada. |
| 2. APIs/frontend | Verificado: mesmos dez casos Groq autorizados; até cinco passagens e alias sem ID longo no prompt. PNCP somente GET de metadados. | Plano gratuito informado, cobrança não auditada; frontend/API própria futuros. |
| 3. Entradas | Verificado: enum só dos aliases atuais, tipo/string/exatidão, no máximo cinco fontes e rejeição de duplicatas;100 testes passaram. CLI corrige argumento Path e preserva parciais. | Coleta real parcial, casos inválidos futuros podem exigir revisão; não associa tabela automaticamente. |
| 4. Autorização | Verificado no escopo: continuidade aprovada, casos anteriores explicitamente autorizados, mapping local por requisição. Banco não alterado. | Alias S1 não é identidade estável nem autenticação; revisão humana não inferida da aprovação de continuar. |
| 5. Ataques comuns | Verificado: conteúdo não executado; rótulos não ampliam fontes, desconhecidos rejeitados sem aproximação; origem PNCP restrita. | Fonte verdadeira pode sustentar afirmação errada; prompt injection real em PDF continua pendente. CSRF não aplicável à CLI. |
| 6. Logs/auditoria | Verificado: checkpoints/fichas por variante, mapa real privado, resumo de erros/tokens/hashes. Falhas iniciais de CLI e coleta registradas. | Erros históricos sem status/estágio não reinterpretados; hash por requisição não registrado. |
| 7. Senhas | Não aplicável: nenhum login/recuperação de senha ou credencial alterados. | Não audita identidade multiusuário futura. |
| 8. Backup | Não aplicável a novo restore: nenhum PDF/banco novo carregado, snapshots anteriores preservados. Evidência anterior em verificacao-local.json. | Backup periódico futuro. |
| 9. Dependências/produção | Verificado:100 testes, nenhum pacote novo, pip-audit atual sem avisos conhecidos auditáveis. | Pacote local não auditável PyPI; resultados do CLI externo não cobertos integralmente pela suite. |
| 10. HTTPS/comunicação | Verificado: origens oficiais HTTPS Groq/PNCP preservadas. HTTP429 observado; helper não repete imediatamente, novo planejador interrompe lote; teste confirma uma chamada. | Coleta parou incompleta; produção/cabeçalhos próprios não existem. Outros coletores legados não foram reexecutados nesta atualização. |

Limites: nove candidatos/dez arquivos listados, sem download/hash/PDF independente aprovado; perguntas novas ainda não preparadas.10/10 de integridade não é100% de precisão. Regressão de conteúdo e outra reserva permanecem necessárias. Auditoria local de dependências: tmp/radar-pip-audit-aliases.json, não exportada. Sem alterações ERP, produção, credenciais ou volumes.
