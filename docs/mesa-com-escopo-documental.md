# Mesa documental como escopo do chatbot — 2026-10-05

## Pedido e entrega para revisão

Renê aprovou as alterações anteriores e informou que a pergunta de Belmonte respondeu corretamente. Isso é uma conferência manual de um caso, sem alteração da taxa global. Pediu alinhar os documentos com a mesa, voltar à visão geral clicando fora da plataforma e reunir PDFs para uma pergunta conjunta.

Implementado: chegada do PDF com rotação zerada e altura junto ao tampo; arquivos selecionados deitados e alinhados sobre a mesa. Clique curto no fundo (deslocamento abaixo de 5 px) limpa UF/pesquisa e retorna ao conjunto completo; arraste mantém o giro. Lista da mesa acumula e remove PDFs de um ou mais editais, sem duplicação, até cinco arquivos. Estado permanece em memória entre abas do aplicativo, não depois de recarregar a página. “Perguntar sobre os N PDFs da mesa” envia seleção ao chat; este mostra os arquivos e permite reduzir o escopo ou retornar à base inteira. Há botões alternativos ao arraste.

## Funcionamento do escopo

Contrato /chat/ask agora aceita `documents` com pares PNCP/sequência. Servidor valida um a cinco arquivos, tipos estritos, duplicação, catálogo permitido e incompatibilidade com pncp_id isolado. Nenhum holdout é disponibilizado por esse caminho.

A busca semântica e lexical aplica `c.document_sequence = ANY(%s)` com parâmetros. Recuperação é feita por arquivo, reservando o primeiro trecho de cada arquivo que tiver resultado e completando até cinco passagens. Usa contexto de trechos (`chunk`), sem expansão que pudesse trazer outro PDF. O contexto do modelo identifica órgão público e PNCP para diferenciar contratações. Uma única geração usa a seleção reunida; a resposta continua submetida aos guardrails e à integridade de citação. Saída pública verifica cada par PNCP/PDF contra a seleção e reconstrói sua URL oficial.

O modo padrão de toda a base/edital permanece no fluxo anterior. A mesa é um escopo explícito novo: não herda a precisão medida do piloto, não lê integralmente todos os PDFs a cada pergunta e não garante comparação completa. Selecionar arquivos não prova evidência suficiente. Contexto continua limitado a cinco trechos e 16.000 caracteres; consultas extensas podem exigir perguntas mais específicas.

## Verificação

- 295 testes backend passaram; 12 novos cobrem encaminhamento de escopo, arquivos fora do catálogo, citações fora da seleção, identidade de fontes de outra contratação, limites/tipos/duplicação, filtragem de resultados e SQL parametrizado. Após acrescentar o nome público do órgão ao contexto, 56 testes relacionados passaram novamente.
- 21 testes frontend passaram, incluindo recepção da mesa e corpo enviado com documents/sem pncp_id. Build aprovado. Cena separada ~582 kB minificados, aviso de chunk grande permanece.
- Navegador: dois PDFs de MT e arquivo 1 de Belmonte acumulados; posições no tampo conferidas; clique no fundo retornou UF=Todas e 36 editais; botão levou ao chat com os três arquivos; voltar a Explorar preservou a mesa; adicionar novamente arquivo já presente manteve três arquivos.
- Consulta local real ao PostgreSQL/pgvector para “Qual a garantia dos computadores?” com os mesmos três arquivos: cinco passagens, zero fora do escopo, três arquivos representados. Nenhum texto bruto foi registrado no relatório e nenhuma geração Groq foi feita.
- API reiniciada somente no processo identificado como ops/serve-chat.py; health generation_enabled=true; arquivo inexistente de Belmonte rejeitado com 422 sem geração.
- Layout móvel emulado 390×844, largura documento 375, sem overflow horizontal; mesa/cartões/remoção e botão conferidos. Dispositivo físico não testado.
- npm audit --omit=dev: zero vulnerabilidades conhecidas no runtime. pip-audit --skip-editable: sem vulnerabilidades conhecidas auditáveis; pacote local editável ignorado. Tentativa anterior com --disable-pip sem -r falhou por sintaxe e não foi tratada como auditoria aprovada.
- Capturas: [mesa alinhada](images/mesa-pdfs-alinhados.png), [chat com seleção](images/chat-escopo-mesa.png).

## Segurança — dez grupos no escopo

| Grupo | Evidência e limite |
|---|---|
| 1 Segredos/dados | Verificado no escopo: arquivos desta entrega examinados para padrões de credenciais, valores reais não registrados; configurações privadas continuam fora do Brain; capturas com referências públicas. Histórico inteiro não auditado. |
| 2 APIs/frontend | Verificado: seleção chega à API, não depende só do filtro visual; servidor devolve campos públicos permitidos; nenhuma chave no cliente. Seleção não envia pergunta automaticamente. |
| 3 Entradas | Verificado: Pydantic estrito, cinco PDFs no máximo, vazio/duplicados/booleano/escopo misto recusados; documento existente validado em catálogo; limites de pergunta/corpo preservados. Testes e 422 real. |
| 4 Autorização | Verificado no ambiente local: documentos limitados ao catálogo de desenvolvimento; sem acesso ao holdout, novas permissões ou escrita. Serviço continua loopback; autenticação multiusuário não implementada. |
| 5 Ataques comuns | Verificado: filtro SQL parametrizado, React sem HTML bruto, URLs oficiais filtradas, fontes checadas contra os arquivos escolhidos. Guardrails de entrada/contexto e fronteira origem/cabeçalho preservados; testes existentes passaram. |
| 6 Logs | Verificado no escopo: não há log novo de conteúdo/pergunta; errors continuam redigidos e access_log desabilitado. Não foi criada telemetria nem resultado privado de geração. |
| 7 Senhas | Não aplicável: sem login, senha ou recuperação nesta entrega. |
| 8 Backup | Não aplicável à mudança: não houve escrita/ingestão no banco nem alteração de backup; restauração não testada. Mesa é memória transitória da sessão. |
| 9 Dependências/produção | Verificado no escopo auditável: nenhum pacote novo, npm runtime e pip auditados conforme comandos acima; testes/build aprovados. Dev npm não auditado nesta rodada; requisitos do Node, imagem preexistente e chunk grande seguem pendentes. |
| 10 Comunicação | Verificado localmente: API/frontend loopback, destino Groq oficial preservado, URLs de documentos HTTPS, CSP existente. TLS/cabeçalhos de produção não verificados. |

## Pendências

Revisão visual de Renê e conferência de uma resposta conjunta real da Groq; acerto comparativo e latência multi-PDF ainda não medidos. Mesa confirma inclusão somente quando o transporte termina: sair do explorador durante a animação pode interromper a inclusão. Arraste/toque físico e métricas instrumentais do 3D permanecem sem teste. Não houve publicação, holdout ou mudança de variante padrão.
