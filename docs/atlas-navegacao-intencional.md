# Navegação intencional no atlas — 2026-10-05

Renê aprovou a parte 3D anterior com dois últimos ajustes: retorno suave à visão geral e entrada na visão do estado somente pelo rótulo sigla/contagem. Entrega para conferência.

## Implementação

Scene.tsx conserva pose/zoom/frustum relativo da câmera durante a reconstrução de estados filtrados. Ao trocar o catálogo, interpola posição, alvo e zoom até a visão geral em 900 ms, com aceleração/desaceleração suave. A geometria do catálogo troca ao mudar o filtro; a câmera transita, não há crossfade completo do conteúdo. Prefers-reduced-motion continua removendo a transição.

Superfície de plataforma não chama onState. O botão/rótulo de estado continua sendo o alvo explícito para filtrar. Clique simples em pasta não seleciona/levanta; arraste vertical de seis pixels inicia o gesto de levantamento. Um PDF já aberto em leque continua selecionável por clique. Fundo com clique curto retorna à base geral; arraste mantém controles da câmera. Lista e seletor UF permanecem alternativas acessíveis.

## Verificação

Build TypeScript/Vite e 21 testes frontend passaram. Testes com cena simulada não cobrem gesto/câmera. Navegador real: rótulo PR abriu três editais/cinco PDFs; clique na superfície e clique simples em uma pasta mantiveram seleção e estado; fundo retornou UF Todas/36 editais e captura mostrou quadro intermediário de câmera aproximada na transição. Conferência visual do estado final concluída. Sem medição de FPS ou teste físico de toque.

npm audit --omit=dev atual: zero vulnerabilidades conhecidas no runtime. Nenhum pacote novo. Aviso de chunk grande permanece (~583 kB minificados). Backend e RAG não alterados/testados novamente nesta atualização; geração conjunta da mesa continua pendente conforme entrega anterior.

## Dez grupos de segurança

1. **Segredos — verificado no escopo:** código alterado inspecionado, zero padrões de chaves; relatório e captura apenas metadados públicos. Histórico inteiro não auditado.
2. **APIs/frontend — verificado:** mudança exclusivamente na interação da cena; nenhum novo fetch, endpoint ou credencial.
3. **Entradas — verificado:** plataforma não dispara navegação; clique/arraste separados por limiares locais; estado escolhido por botão do catálogo. Não há nova entrada de servidor.
4. **Autorização — verificado no escopo:** escopo do catálogo e API inalterados; nenhum acesso novo. Produção multiusuário não examinada.
5. **Ataques — verificado no escopo:** React/renderização segura e filtro de URL existentes não alterados; sem SQL, HTML bruto ou comandos novos.
6. **Logs — verificado:** pose de câmera mantida em memória, sem persistência/telemetria ou registro de documentos.
7. **Senhas — não aplicável:** nenhuma autenticação/recuperação criada.
8. **Backup — não aplicável à alteração:** não há escrita no banco nem alteração de dados persistentes; restauração não testada.
9. **Dependências — verificado no runtime:** manifesto/lockfile inalterados; build/testes/audit acima. Desenvolvimento npm não auditado; pendências de Node/imagem/chunk da entrega anterior continuam.
10. **Comunicação — verificado localmente:** loopback/CSP/links HTTPS existentes preservados. TLS de produção não verificado.

Aguardar avaliação de Renê. Sem Groq, holdout, ingestão ou publicação. [Captura final](images/atlas-navegacao-final.png).
