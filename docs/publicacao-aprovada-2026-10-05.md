# Publicação aprovada — 2026-10-05

Renê aprovou o chat, painel e exploração 3D e autorizou commit/push. Inclui guardrails, confiança categórica sem probabilidade calibrada, reranking opcional e mesa de até cinco PDFs com escopo validado no servidor. A navegação por UF abre somente pelo rótulo; retorno à visão geral tem animação.

Publicação na branch existente `feat/human-review-holdout`, sem merge automático. Exportação por lista permitida, excluindo registros do Brain, PDFs, textos brutos, credenciais, modelos, vetores e dumps. Imagem de fundo de terceiros sem licença confirmada excluída; versão pública usa gradiente CSS. Capturas mostram metadados públicos e interface.

## Verificações e dez grupos de segurança

1. Segredos/dados: scanner da exportação e revisão do diff; sem padrões de chaves privadas ou credenciais. Histórico inteiro não auditado.
2. API/frontend: chave permanece no backend privado; cliente envia pergunta e identificadores de PDFs. Exportação estática contém metadados permitidos.
3. Entradas: evidência da entrega anterior, 295 testes backend, incluindo limite de cinco PDFs, duplicatas, formato e arquivo inexistente; publicação não altera lógica.
4. Autorização: catálogo documental validado no servidor. API local; autenticação e limites para produção continuam pendentes.
5. Ataques: SQL parametrizado, links filtrados e renderização React; controles/testes registrados nas entregas de mesa e guardrails, preservados.
6. Logs: sem respostas brutas/chaves na exportação; contexto/conversa transitórios. Retenção operacional de produção não verificada.
7. Senhas: não aplicável; nenhuma gestão de senha criada.
8. Backup: Git publica código, não backup de banco; restauração não reexecutada nesta publicação.
9. Dependências: lockfiles incluídos; 21 testes frontend e build passaram na entrega aprovada; runtime npm audit sem vulnerabilidades conhecidas nessa entrega. Node e chunk grande permanecem pendências; imagem sem licença não distribuída.
10. Comunicação: GitHub via HTTPS; API permanece loopback. TLS/CSP de uma implantação pública da API não verificados.

## Próximos passos

Validar respostas combinando PDFs e conferir cada referência. Concluir revisão independente do holdout antes de executar; preservar a variante padrão até evidência comparativa. Preparar execução reproduzível e demonstração para portfólio. Geração conjunta real, desempenho em dispositivos físicos e implantação pública continuam pendentes; não há nova promessa de taxa de acerto.

Verificação adicional do checkout publicado: npm ci --ignore-scripts concluiu com zero vulnerabilidades; build passou, mantendo aviso de chunk (~583 kB). Caminho pessoal no exemplo de operação substituído por caminho genérico. Finais de linha normalizados para LF; hashes de relatórios referem-se aos bytes originais das execuções locais.
