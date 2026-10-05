# Seleção de estados e PDFs — 2026-10-05

Entrega para revisão após pedido de Renê: corrigir leque fora do RS, escolher/arrastar um PDF e identificar estados ao afastar a câmera. Direção visual preservada do atlas aprovado, aplicando os controles à tarefa de conferência de fontes.

## Mudanças

- Corrigida seleção de edital ao filtrar UF ou pesquisa: se o anterior não está entre os resultados, o primeiro edital visível é selecionado. Fechar o leque acompanha mudança de conjunto/catálogo.
- Abrir o leque aproxima automaticamente a câmera. Regra genérica para todos os editais, sem tratamento especial para RS.
- Rótulos HTML mantêm tamanho de texto em tela e acompanham a projeção das plataformas. Na vista distante (zoom abaixo de 0,7) ou telas estreitas, os estados se organizam em uma grade legível. Clicar no rótulo ou na base da plataforma seleciona a UF. Nome completo aparece no arquivo interativo e no seletor de PDFs.
- Leque oferece um botão/cartão para cada PDF real do edital. Dois arquivos resultam em duas opções; um arquivo permanece uma opção, sem duplicação fictícia. Os cartões podem ser selecionados ou arrastados até “Mesa de conferência”. O gesto anima o arquivo correspondente e destaca sua referência oficial. Botão oferece alternativa ao arraste.
- Rótulos não representam métricas de confiança; mesa continua ilustrativa e não altera banco/documentos. Não há PDF carregado automaticamente.

## Evidências

Build TypeScript/Vite aprovado; 20 testes em três arquivos aprovados. Teste de regressão cobre mudança BA→SC com seleção correta. Na primeira execução, o seletor do teste exigia espaços diferentes do nome acessível e havia callback de rolagem pendente no jsdom; seletor corrigido e chamada de scrollIntoView tolera ambientes sem esse método. Execução seguinte sem erros.

Navegador real: rótulo Santa Catarina selecionou SC/Porto Belo e leque apresentou um PDF; MT mudou seleção para Jaciara e escolha do Estado de Mato Grosso apresentou dois cartões; arraste do PDF 2 até a mesa iniciou seu transporte, terminou com “PDF 2 na mesa” e referência de arquivo 2. Vista distante conferida com grade de rótulos. Tela 390×844, documento 375 px, sem overflow horizontal; opções e destino visíveis. Teste móvel emulado não substitui aparelho físico.

Capturas: [seleção/transporte](images/atlas-selecao-pdfs.png), [rótulos no zoom afastado](images/atlas-rotulos-zoom.png).

## Pergunta para conferir o chatbot

“No edital de Belmonte, qual é a garantia exigida para o desktop do item 01 do lote 01?” Esperado: 12 meses; arquivo 1, páginas 26 e 35. PNCP 13634977000102-1-000128/2026. Evidência anterior: [API disponível](api-disponivel-2026-10-05.md). Não executada novamente nesta entrega; escopo global pode pedir esclarecimento, e resultado de uma pergunta não comprova precisão geral.

## Segurança — dez grupos, escopo visual

| Grupo | Resultado |
|---|---|
| 1 Segredos/dados | Verificado no escopo: quatro arquivos alterados examinados, zero padrões de chaves Groq/OpenAI/privadas; capturas apenas de metadados públicos. `.gitignore` existente preservado. Histórico completo não auditado. |
| 2 APIs/frontend | Verificado no escopo: seleção/arraste não transmite à Groq ou busca PDF; catálogo e URLs oficiais existentes preservados. Sem credenciais cliente. |
| 3 Entradas | Verificado no escopo: PDF e UF vêm do catálogo; escolha de sequência procura o arquivo do edital; mudança de filtro ajusta seleção. Teste de regressão e navegador real. |
| 4 Autorização | Verificado no escopo: interações locais sobre catálogo público, sem concessão de acesso ou gravação; autenticação de produção não avaliada. |
| 5 Ataques | Verificado no escopo: React escapa textos; URLs continuam filtradas por safePncpUrl e noopener/noreferrer; sem HTML bruto, SQL ou comando novo. |
| 6 Logs | Verificado no escopo: sem telemetria/persistência nova, sem logs de conteúdo/documentos; logs do servidor inalterados. |
| 7 Senhas | Não aplicável: nenhuma senha/login/recuperação nesta mudança. |
| 8 Backup | Não aplicável à atualização: sem escrita de banco; restauração não testada. |
| 9 Dependências | Verificado no runtime: nenhum manifesto/lockfile alterado; npm audit --omit=dev atual retornou zero vulnerabilidades conhecidas. Build e 20 testes passaram. Dev não auditado nesta rodada; aviso de chunk acima de 500 kB, imagem preexistente e requisitos do Node seguem pendentes. |
| 10 Comunicação | Verificado localmente: loopback, links oficiais HTTPS e CSP existente preservados. TLS/cabeçalhos de produção não verificados. |

Pendente: revisão de Renê, arraste/toque em aparelho físico e métricas instrumentais de desempenho. Esta atualização não executa holdout, Groq, ingestão, alterações no RAG ou publicação.
