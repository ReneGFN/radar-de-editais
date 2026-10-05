# Atlas interativo refinado — 2026-10-05

## Entrega para revisão de Renê

Após a avaliação de que o primeiro 3D era simples, o cenário passou a representar um arquivo documental com pastas volumétricas, cantos arredondados, iluminação, sombras e uma mesa de conferência. A organização continua sendo UF → edital → PDFs reais do catálogo, sem escala geográfica ou distância semântica.

### Interações implementadas

- Segurar uma pasta e puxar para cima levanta o conjunto e abre suas folhas; soltar recolhe os PDFs com atraso sequencial de 95 ms. O gesto pode ser cancelado.
- “Abrir PDFs em leque” mantém as folhas abertas; “Recolher PDFs” retorna ao conjunto. Cada folha corresponde a uma sequência de arquivo do edital.
- O usuário pode selecionar uma folha ou usar os botões de seleção no painel. “Levar PDF N à mesa” anima esse arquivo em uma trajetória curva por aproximadamente 1,5 segundo, destacando seu cartão e o link oficial.
- “Aproximar conjunto” desloca a câmera em aproximadamente 650 ms. Zoom, giro, deslocamento e vista geral continuam disponíveis.
- As texturas das folhas são ilustrativas: não são miniaturas renderizadas das páginas dos PDFs. O movimento é visual; não realiza ingestão, transferência de arquivo ou alteração no banco. O link oficial é aberto somente por ação explícita.

A escolha conecta a interação à conferência de fontes: identificar um edital, separar um arquivo e abrir sua referência. A seleção tem alternativa por botões e lista, além do gesto. O destaque dourado continua indicando fonte da última resposta, sem representar confiança factual.

## Código e funcionamento

`frontend/src/explore/Scene.tsx` usa Three.js, RoundedBoxGeometry, OrbitControls, raycasting e interpolação. `ExplorePage.tsx` mantém o arquivo selecionado e sua referência oficial. CSS ajusta controles, painel, responsividade e foco. Não foram adicionadas dependências nesta revisão.

Renderização solicitada por interação/animação; não há loop permanente quando a cena está estável. A aba oculta cancela o quadro agendado. A preferência de movimento reduzido remove atrasos e interpolações. Geometrias, materiais, texturas, observador, eventos e controles são liberados ao desmontar; o transporte remove o trajeto temporário ao terminar.

## Evidências

- `npm.cmd run build`: passou, incluindo TypeScript. Cena carregada separadamente: 577,91 kB minificados / 145,08 kB gzip. O aviso de chunk acima de 500 kB permanece.
- `npm.cmd test`: 19 testes passaram em três arquivos. Novo teste verifica seleção do PDF pelo painel e preservação de sua URL, sem abertura automática ou nova consulta. Testes com cena simulada não provam a animação.
- Navegador real: Jari filtrado, um edital/oito PDFs; aproximação e leque conferidos; gesto de levantar/soltar retornou ao estado de recolhimento; após recarga, seleção e transporte do PDF 8 terminaram com “PDF 8 na mesa” e referência oficial ao arquivo 8. PDF 1 também foi transportado durante a conferência.
- Atualização durante o desenvolvimento manteve um manipulador antigo na cena e inicialmente transportou PDF 1 quando o rótulo mostrava PDF 8. O botão passou a enviar a sequência explicitamente; a conferência final foi feita após recarga, com PDF 8 correto.
- Layout 390 × 844: largura útil do documento 375 px, sem overflow horizontal; controles visíveis. Override temporário do navegador removido. Isso não substitui teste em aparelho físico.
- `npm.cmd audit --omit=dev`: tentativa inicial falhou por acesso; repetida com acesso ao registro oficial, retornou zero vulnerabilidades conhecidas nas dependências de runtime. Dependências de desenvolvimento não foram auditadas nesta revisão.
- Capturas: [Leque](images/atlas-interativo-leque.png) e [Mesa](images/atlas-pdf-mesa.png).

## Segurança — dez grupos no escopo desta atualização

| Grupo | Resultado e evidência |
|---|---|
| 1. Segredos/dados | Verificado no escopo: quatro arquivos de código examinados, zero correspondências nos padrões de chave Groq/OpenAI e chave privada; `.gitignore` protege configuração/segredos e dados privados. Metadados públicos nas capturas. Inspeção de padrões não é auditoria de todo o histórico. |
| 2. APIs/frontend | Verificado no escopo: catálogo por fetch existente, credenciais omitidas; seleção/transporte não chama Groq nem abre PDF automaticamente. Não há credencial adicionada ao cliente. |
| 3. Entradas | Verificado no escopo: ações habilitadas somente para seleção presente no catálogo visível; transporte procura sequência no conjunto e tem fallback ao primeiro arquivo. Filtros locais não alteram a consulta do backend. |
| 4. Autorização | Verificado no escopo: catálogo público e interações locais, sem novas permissões, rotas administrativas ou gravação. Autenticação de publicação continua fora desta entrega local. |
| 5. Ataques comuns | Verificado no escopo: texto renderizado por React sem HTML bruto; URLs oficiais passam pelo filtro existente e links externos usam noopener/noreferrer. Nenhuma composição SQL ou comando introduzida. |
| 6. Logs/auditoria | Verificado no escopo: estados visuais não registram prompts, credenciais ou documentos. Sem nova telemetria/persistência; comportamento de logs do servidor não alterado. |
| 7. Senhas/recuperação | Não aplicável: esta entrega não cria login, senha ou recuperação. |
| 8. Backup | Não aplicável à alteração visual: sem escrita de banco ou dados privados; restauração do banco não foi testada nesta entrega. |
| 9. Dependências/produção | Verificado no escopo de runtime: sem alteração de manifesto/lockfile; build e 19 testes aprovados, audit runtime zero avisos conhecidos. Aviso de tamanho do chunk, imagem preexistente de 5,6 MB e incompatibilidade do Node 22.16 com requisitos de algumas ferramentas de desenvolvimento seguem pendentes. |
| 10. Comunicação | Verificado no escopo local: API/frontend em loopback, URLs oficiais HTTPS e CSP existente preservada. TLS/cabeçalhos de produção não foram verificados. |

## Pendências e limites

Aprovação visual de Renê; testes de toque em dispositivo físico e preferência de movimento reduzido no sistema; medição de FPS/GPU em equipamentos diferentes. A preferência e suspensão de aba foram inspecionadas no código, sem medição instrumental. Licença da imagem preexistente e runtime de desenvolvimento seguem pendentes para publicação. Nenhum resultado de precisão RAG foi recalculado, holdout executado, documento ingerido ou conteúdo publicado nesta revisão.
