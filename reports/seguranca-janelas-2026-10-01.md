# Segurança — janelas e fontes literais — 2026-10-01

Escopo: ampliação de contexto na página original, seleção de identificador pelo modelo, inserção literal pelo servidor, comparação e fichas privadas. Não é auditoria de aplicação web/produção.

| Grupo | Resultado e evidência | Limites |
|---|---|---|
| 1. Segredos/dados | Verificado no escopo: exportador por lista permitida com scanner; PDFs, páginas, janelas e respostas completas privadas. Chave só autentica API. | Janelas são maiores e podem conter texto vizinho; não publicar conteúdo bruto. |
| 2. API/frontend | Verificado: mesma API Groq oficial, mesmos dez casos autorizados, até cinco janelas públicas; checkpoint distinto preserva primeiro lote. | Custo/faturamento não auditado; navegador/API própria inexistente. |
| 3. Entradas | Verificado: perfis em listas permitidas, limite de janela, coincidência exata do trecho/offsets com página, fonte desconhecida rejeitada. 85 testes locais passaram. | Não interpreta tabelas nem garante item correto. |
| 4. Autorização | Verificado: continuidade solicitada após autorização explícita dos dez casos; banco somente leitura. | Fonte selecionada pelo modelo não aprova significado; revisão humana pendente. |
| 5. Ataques comuns | Verificado: consulta de página parametrizada por snapshot/edital/arquivo/página, transação READ ONLY; nenhum comando vem do texto. | Injeção embutida em PDF continua cenário a testar; CSRF não aplicável à CLI. |
| 6. Logs/auditoria | Verificado: offsets de âncora e janela, perfis, hashes e comparação por caso; fichas/checkpoints separados por variante. | Hash por requisição não registrado; protocolo informa hash capturado durante lote. |
| 7. Senhas | Não aplicável: nenhum login, senha ou recuperação alterados. | Não audita provedor de identidade futuro. |
| 8. Backup | Não aplicável a novo restore: corpus/banco intactos; só leitura. Evidência anterior permanece em verificacao-local.json. | Rotina periódica futura. |
| 9. Dependências/produção | Verificado: nenhum pacote novo; pip-audit atual sem avisos conhecidos auditáveis. 85 testes locais passaram; correções documentadas. | Pacote radar local não auditável no PyPI; ausência de aviso não garante segurança. |
| 10. HTTPS | Verificado no escopo: SDK mantém origem oficial HTTPS Groq e links PNCP. | Certificados/cabeçalhos de implantação própria não se aplicam ainda. |

Riscos: ampliar texto pode misturar itens; quote inserida pelo servidor comprova origem literal, não apoio a cada afirmação. Demonstração testada: uma afirmação propositalmente errada pode citar fonte verdadeira e continua marcada requires_review. Não reduzir validação nem anunciar precisão humana com base em integridade literal.

Auditoria local de dependências: tmp/radar-pip-audit-window.json no Brain. Sem exclusão de dados, alterações de ERP/volumes/produção/credenciais ou promoção automática. Padrões anteriores preservados; novas opções experimentais.

Diagnóstico de reserve-10 do lote anterior foi sobrescrito pelo novo; checkpoints antigos intactos. Nomeação de futuros diagnósticos corrigida com variante e sufixo único. Padding prioriza conservar âncora longa; os trechos avaliados (máximo638) não foram afetados. Limitações constam do protocolo, sem alegação de preservação retroativa de diagnóstico.
