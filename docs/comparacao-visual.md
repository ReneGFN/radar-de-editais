# Comparar versões — acabamento visual

2026-10-05 — chat aprovado visualmente por Renê. Esta entrega altera apenas o bloco Comparar versões para revisão.

Seletores Base/Candidata reunidos em um painel, placar com contagens factuais lado a lado e contexto de recuperação/holdout separado. Regressões e melhoras em cartões paralelos com links para os casos. Ressalva de que estado técnico não equivale a correção humana preservada. Tabela Casos com mudança e chat sem alterações.

Arquivos: frontend/src/pages/VersionsPage.tsx e frontend/src/styles.css. Mesma direção visual já aprovada; CSS responsivo e React existentes, nenhuma biblioteca nova. Escolha favorece leitura rápida sem alterar a interpretação dos dados.

Build TypeScript/Vite passou; 17 testes frontend passaram. Navegador verificou troca v3→v2→v3, contagens e casos correspondentes; mobile 390 × 844 com largura de documento 375, sem overflow de página. Captura em [comparação](../reports/ui/comparison-refined-2026-10-05.jpg). Viewport restaurado. Sem Groq, holdout, backend ou publicação.

## Dez grupos de segurança

1. Segredos: fontes/build/documentação examinados por padrões de chave, sem ocorrências; nenhuma credencial acessada. .gitignore preservado; não auditado histórico completo.
2. APIs/frontend: carga de dados e contratos existentes preservados; apenas apresentação, sem destino novo.
3. Entrada: selects continuam validando variantes permitidas; troca real verificada e testes passaram. Sem nova entrada/backend.
4. Autenticação/autorização: não aplicável à mudança visual, sem novos acessos ou endpoints.
5. Ataques comuns: React renderiza texto; links locais seguem IDs permitidos existentes. Testes de conteúdo não confiável preservados. Sem novo SQL/comando.
6. Logs/auditoria: sem novo log ou analytics; relatórios contêm dados públicos e evidências.
7. Senhas/recuperação: não aplicável, identidade não alterada.
8. Backup/recuperação: não aplicável, nenhuma escrita/migração de banco.
9. Dependências/produção: manifestos/lockfile sem alteração; build/17 testes atuais. Reutilizada auditoria npm com rede desta sessão 2026-10-05, zero vulnerabilidades conhecidas, por não haver mudança de dependências desde sua execução. Node de testes e imagem continuam com pendências registradas na entrega anterior.
10. HTTPS/comunicação: CSP/proxy preservados, sem serviço novo. Localhost; TLS de produção não avaliado.

Próximo passo: aprovação do bloco Comparar versões. Chat marcado como aprovado; pendências anteriores de runtime/imagem permanecem e a etapa funcional posterior não foi iniciada.

## Aprovação
Renê aprovou esta entrega em 2026-10-05. Revisão visual concluída; próxima entrega funcional ainda não executada. Registro documental revisado sem segredos (grupo 1); grupos 2–10 não aplicáveis a esta anotação, sem mudança técnica.
