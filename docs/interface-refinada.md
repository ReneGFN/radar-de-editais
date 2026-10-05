# Interface refinada — chat e laboratório

2026-10-05 — entrega local para aprovação visual de Renê.

## Pedido, decisões e resultado

Renê apontou desalinhamento nas sugestões, uma segunda caixa ao focar a pergunta, aparência de formulário no escopo e inconsistência visual nas quatro telas do laboratório.

- **Sugestões:** texto centralizado horizontal e verticalmente, altura e espaçamento consistentes; quebram em linhas no celular.
- **Pergunta:** sem contorno interno nem alça de redimensionamento. Campo cresce como antes; o foco é indicado na borda suave do compositor inteiro, preservando orientação de teclado.
- **Escopo:** botão compacto abre lista pesquisável, com órgão, UF, objeto e PNCP. Seleção fecha o painel e não envia a pergunta. Fechamento por botão, Escape e clique fora. No celular, painel junto à borda inferior com rolagem própria.
- **Versões:** métricas principais em três cartões, variante padrão destacada, latências/tokens e conferência humana separados. Números e ressalvas existentes preservados.
- **Casos, Qualidade e Corpus:** identidade escura compartilhada, cabeçalhos e cartões, estados com texto/cor, tabelas em painéis com rolagem local e foco de teclado. Mantidos critérios, filtros, links e dados.

Referência principal: Moon Chat enviada pelo usuário e visual já aprovado parcialmente; inspiração ChatGPT indicada por Renê para fluidez da consulta/seletor. Sem reprodução de marca. Refero MCP não disponível; utilizados referência do usuário e guia local de acabamento/foco. Referência local ChatGPT não encontrada no catálogo; isso não foi tratado como pesquisa concluída. Novas imagens não necessárias para refinamento do alvo existente.

React 19.3.0 preservado. Tailwind 4.3.3 e plugin Vite 4.3.3 adicionados como ferramentas de desenvolvimento, seguindo [documentação oficial](https://tailwindcss.com/docs/installation/using-vite). Utilitários usados em alinhamentos e espaçamentos; CSS existente mantém os tokens e componentes específicos. Sem Preflight para evitar mudanças globais indesejadas nos controles existentes. Tailwind compila para CSS estático, sem CDN no navegador.

## Verificação

- Build TypeScript/Vite final concluído: JavaScript 252,07 kB (77,79 kB gzip); CSS 21,07 kB (5,35 kB gzip).
- 16 testes frontend passaram. Novo teste confirma filtro sem resultado, normalização sem acentos, seleção sem envio, Escape e PNCP enviado corretamente na consulta posterior; provedor simulado.
- Um teste anterior dependia do texto isolado “não promovida”; marcação preservada corrigiu a falha sem remover a verificação.
- npm install auditou 110 pacotes e encontrou zero vulnerabilidades conhecidas. Primeira instalação falhou por rede/permissão; repetição autorizada concluiu.
- Avisos EBADENGINE: Node local 22.16.0 inferior ao requisito de jsdom 30.1.1 e dependências já existentes (22.22.2 para jsdom, 22.19.0 para undici). Build/testes concluíram, mas ambiente de testes não está numa versão Node suportada por todos esses pacotes. Atualização do runtime permanece pendente; não efetuada nesta entrega visual.
- Navegador: campo ativo sem outline interno; filtro Uniflor e seleção funcionaram sem envio; Escape fechou e retornou foco; filtro de recusas mostrou dez casos; cinco telas inspecionadas. Corpus/Versões/seletor/chat em 390 × 844 sem overflow horizontal de página (largura observada 375). Tabelas preservam rolagem local.
- Capturas: [chat](../reports/ui/chat-refined-2026-10-05.jpg) e [versões](../reports/ui/versions-refined-2026-10-05.jpg). Viewport temporário restaurado.
- Revisão pelas [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md): foco composto substitui contorno interno, controles rotulados, fechamento acessível, movimentos reduzidos, tabelas semânticas em regiões roláveis, selects escuros e cor de tema. Não constitui auditoria completa WCAG.
- Inspeção de padrões de chave em src, dist e manifestos sem correspondências. Tentativa inicial usou caminhos duplicados e foi corrigida; resultados só considerados após repetição.
- Nenhuma nova consulta Groq real, holdout, migração ou publicação. Backend não modificado; sua suíte não foi repetida.

## Dez grupos de segurança

| Grupo | Resultado nesta entrega |
|---|---|
| 1. Segredos e dados sensíveis | Verificado no escopo: .gitignore preserva credenciais/artefatos; fontes, build e manifestos sem padrões de chaves procurados. Sem valores de credencial nos registros. Não é varredura completa do histórico. |
| 2. APIs e frontend | Verificado no escopo: contratos/proxy existentes preservados; Tailwind compilado localmente. Testes mantêm credenciais omitidas e publicação estática sem API local. |
| 3. Validação de entrada | Verificado no escopo: pergunta até 2000 caracteres e validação existentes preservadas; busca local, estado vazio e seleção testados. Servidor não alterado. |
| 4. Autenticação e autorização | Não aplicável à mudança visual: sem novo login, permissão ou endpoint. Seleção de escopo não é autorização; controles locais existentes preservados, produção não avaliada. |
| 5. Ataques comuns | Verificado no escopo: React renderiza passagens como texto; teste de conteúdo HTML malicioso e rejeição de links inseguros passou. Não houve alteração de SQL/comandos/backend nem teste externo. |
| 6. Logs e auditoria | Verificado no escopo: sem novo analytics ou persistência; conversa transitória preservada. Registros da entrega contêm evidências públicas e limitações, sem conteúdo privado/provedor bruto. |
| 7. Senhas e recuperação | Não aplicável: nenhuma mudança de identidade ou senha; não auditada configuração externa. |
| 8. Backup e recuperação | Não aplicável ao escopo: nenhuma escrita/migração de banco. Restauração histórica não reexecutada nem apresentada como evidência atual. |
| 9. Dependências e produção | Verificado parcialmente: Tailwind oficial/lockfile, audit zero, build e 16 testes. Problema encontrado: Node abaixo dos requisitos de pacotes de teste existentes; atualizar runtime antes de padronizar CI. Imagem de 5,6 MB ainda exige otimização/licença antes de publicação. |
| 10. HTTPS e comunicação | Verificado no build: CSP self preservada e imagem local; sem novo CDN/chamadas externas no frontend. Localhost HTTP; TLS/certificados de produção não avaliados. |

## Pendências e próxima etapa

Aguardar aprovação visual. Direitos e otimização da imagem lunar continuam pendentes conforme [entrega anterior](design-moon-chat.md). Depois da revisão, retomar teste real de pergunta aprovada/Groq e conferência das fontes; não alegar nova taxa de acerto a partir desta mudança de interface.
