# Chat local — primeira entrega para revisão — 2026-10-05

Entrega atual: [tela de chatbot conectada](tela-chat-local.md), verificada em navegador com provedor simulado; serviço normal deixado ativo para revisão. Groq real pela nova interface ainda não verificada. Contrato e registros abaixo permanecem como histórico.

Estado atual 2026-10-05: [serviço de perguntas implementado](servico-chat-local.md), verificado com banco real e provedor simulado; tela pendente. Geração entre múltiplos editais ainda não implementada: pedidos desse tipo retornam candidatos, sem fatos comparativos. Contrato abaixo é proposta/histórico e deve ser lido junto das limitações da entrega atual.

Atualização 2026-10-05: descoberta global evoluiu para reconhecimento de nomes abreviados e estados explícitos de escopo/esclarecimento/pesquisa entre contratações. [Entrega atual e limites](descoberta-global-v3.md). API de chat e tela seguem pendentes; os estados precisam ser impostos na integração. Seções abaixo preservam o contrato e evidências históricas.

Estado: contrato proposto após inspeção do núcleo existente; implementação da API de chat e da tela pendentes. Renê pediu entregas individuais com parada para aprovação. Esta entrega não executa consultas, Groq ou holdout.

## Experiência proposta

A tela inicial será “Perguntar sobre editais”. Por padrão, o usuário pergunta em toda a base de desenvolvimento. Pode selecionar uma contratação para restringir a busca. A resposta mostra afirmações, fontes numeradas, órgão, UF, contratação PNCP, arquivo, página do PDF, trecho literal e link oficial. O painel de avaliação permanece acessível na navegação.

Seleção opcional: a lista permite filtrar por órgão, UF e objeto, sem pedir ao usuário que digite um identificador PNCP. No modo geral, perguntas como “Quais editais da base incluem monitores de pelo menos 23 polegadas?” podem descobrir contratações. Perguntas como “Qual é o prazo de entrega?” exigem esclarecimento se não identificarem contratação/objeto suficiente. O chat apresenta os candidatos e pede que o usuário indique qual quer consultar.

Cada fato permanece vinculado ao seu edital e item. Prazos, quantidades e especificações de contratações diferentes não podem ser fundidos como uma única exigência. Quando houver várias respostas relevantes, apresentá-las por contratação. Se o resultado for limitado aos documentos recuperados, informar “Encontrei estas contratações” em vez de afirmar que a lista abrange todos os editais. Pesquisa na base não comprova que a oportunidade continua aberta.

Perguntas seguintes podem ser enviadas, mas cada consulta será independente nesta primeira versão. O histórico fica em memória na tela. Referências como “e a garantia dele?” precisam ser reformuladas com o item; memória conversacional e resolução de referências ficam para uma entrega posterior.

## Contrato da API local

Serviço de chat em `127.0.0.1:8766`, separado da API de métricas em 8765. O servidor fixa o snapshot de desenvolvimento `1446c44aca18011a` e a variante `alias_items`. O cliente não pode escolher snapshot, prompt, variante ou acessar holdout.

- `GET /chat/health`: disponibilidade do serviço; sem valores de credenciais.
- `GET /chat/editais`: lista de contratações permitidas do manifesto de desenvolvimento.
- `POST /chat/ask`, busca geral: `{ "question": "Quais editais da base incluem monitores de pelo menos 23 polegadas?" }`.
- A mesma rota aceita `pncp_id` opcional para restringir a contratação: `{ "question": "Qual a garantia do item 1?", "pncp_id": "<contratação selecionada>" }`.

Entrada: JSON com campos extras proibidos, pergunta não vazia com teto de 2.000 caracteres e PNCP opcional pertencente ao manifesto permitido quando fornecido. Ausência de PNCP significa toda a base de desenvolvimento permitida, nunca qualquer snapshot/holdout. Limitar corpo HTTP antes do parsing. Uma consulta ativa por serviço, intervalo mínimo de 35 segundos entre chamadas ao modelo; sem repetição automática. Responder com erro claro e possibilidade de nova tentativa quando houver limite do provedor.

Saída permitida no chat local: estado, texto apresentado, afirmações com índices de fontes e lista de fontes com PNCP, arquivo, página, trecho literal e URL oficial reconstruída. Tokens agregados e latência podem ficar em uma área de detalhes. Credenciais, configuração privada, caminhos locais, exceções brutas e texto dos demais trechos recuperados não são retornados.

No modo de edital selecionado, usar `generation.answer` com `context_profile='item_structure'`, `citation_mode='source_alias'` e `prompt_version='v1'`. No modo geral, adicionar recuperação híbrida sobre o snapshot permitido, selecionar contratações candidatas e então recuperar contexto dentro delas, preservando identidade de item e diversidade entre contratações. Não executar uma chamada de modelo por edital; reunir fontes selecionadas em uma consulta limitada. A pergunta do usuário não será usada para montar SQL livre.

O núcleo atual exige PNCP: a busca geral é funcionalidade nova, não uma capacidade já verificada de `alias_items`. O conjunto de desenvolvimento deve avaliar descoberta da contratação correta, apoio da resposta, mistura de editais, ambiguidade e latência. A avaliação antiga dentro de um edital não valida busca geral. Verificar integridade antes de expor afirmações. Recusas e ausência de evidência usam a apresentação neutra já existente. Acrescentar estado `needs_clarification` com contratações candidatas quando o escopo estiver ambíguo.

## Proteção e execução

Chave Groq e senha PostgreSQL ficam no backend. O frontend acessa o chat pelo proxy local do Vite; não incorporar chaves ao JavaScript. Exigir Host e Origin locais permitidos e cabeçalho de requisição próprio para POST, com CORS fechado, mitigando chamadas de páginas externas. Nunca usar GET para disparar o modelo.

Não salvar perguntas/respostas em logs por padrão; registrar somente identificador de consulta, estado, duração e tipo seguro de erro. Não publicar o serviço de chat em GitHub Pages: o build público mantém o painel estático, com chat indisponível e explicação de execução local.

## Verificação prevista na entrega de código

Testar entradas inválidas, edital não permitido, tentativa de escolher holdout/snapshot, origem externa, limite de corpo, consultas simultâneas, HTTP429 do provedor, citação inválida e ausência de segredo na saída. Incluir busca sem PNCP, restrição com PNCP, dois editais com prazos conflitantes, pergunta ambígua, fonte de outra contratação e resposta de descoberta sem promessa de cobertura exaustiva. Usar provedor simulado nesses testes. Verificação real na Groq deve respeitar o escopo de envio autorizado e registrar a consulta executada; testes anteriores de lotes não autorizam implicitamente qualquer envio novo.

## Segurança desta entrega documental

1. Segredos: conteúdo revisto, somente caminhos/componentes e identificadores públicos; sem valores de credenciais.
2. APIs/frontend: fronteira local, campos e separação entre métricas e chat descritos; controles ainda não implementados.
3. Entradas: limites e lista permitida especificados; verificação executável pendente.
4. Autorização: usuário autorizou continuidade por entregas; holdout permanece reservado; proposta local não implementa identidade multiusuário.
5. Ataques: proteção de origem e apresentação segura propostas; nenhum teste de ataque executado nesta entrega.
6. Logs: política mínima proposta; não criada captura de respostas.
7. Senhas: não aplicável à mudança documental; nenhum login ou credencial alterado.
8. Backup: não aplicável à mudança documental; banco e arquivos privados sem escrita.
9. Dependências: nenhum pacote alterado; não realizada nova auditoria de bibliotecas para documento. Revisão necessária na entrega de código.
10. Comunicação: localhost para chat e HTTPS para Groq/PNCP; TLS de produção não verificado nem implantado.

Alteração solicitada por Renê: busca geral padrão com seleção opcional, para atender pessoas que não conhecem previamente o edital. Inspeção documental: exemplos, escopos e estados coerentes; dez grupos acima continuam aplicáveis ao escopo exclusivamente documental. Descoberta global e proteção contra mistura precisam de implementação e avaliação próprias.

Próxima entrega: implementar e verificar recuperação geral com escopo permitido e identificação de contratações; parar para revisão antes de conectar geração e tela.

## Entrega de recuperação geral — 2026-10-05

Implementada `radar.discovery.discover(question, pncp_id=None)`: snapshot fixo de desenvolvimento e contratações permitidas pelo manifesto; rankings lexical OR e semântico combinados por RRF. Cada ramo seleciona até 60 páginas distintas antes da fusão, reduzindo repetições de chunks sobrepostos. Retorna até cinco contratações únicas com passagem, arquivo, página, offsets e fonte; sem texto bruto e sem alegar cobertura exaustiva. Seleção opcional restringe o mesmo mecanismo a um edital. Fontes por contratação permanecem separadas.

Verificação: oito testes específicos passaram; suíte completa 239 testes passou. Testes usam dependências simuladas e verificam diversificação, filtro selecionado, entradas inválidas e rejeição de resultado fora do escopo. Consulta real “monitores” falhou por timeout de conexão com PostgreSQL em 127.0.0.1:55432. Portanto não há taxa de descoberta, latência real ou integração SQL aprovada nesta entrega. Não houve chamada Groq ou execução do holdout. Código anterior de recuperação preservado.

Limite: top-k de páginas ainda pode favorecer editais longos; candidatos semânticos não são provas de resposta. Não há limiar calibrado para decidir relevância ou esclarecimento automático. Próximo passo: resolver disponibilidade do banco e avaliar descoberta real antes de conectar geração e tela.

Segurança no escopo desta implementação: (1) nenhum segredo embutido ou texto privado exportado; (2) nenhuma rota/frontend novo; (3) pergunta até 2000 caracteres e contratação em lista permitida; (4) snapshot fixo e resultados conferidos contra catálogo; (5) SQL parametrizado, transação READ ONLY; testes reais de SQL e prompt injection pendentes; (6) módulo não registra perguntas/respostas; (7) sem alteração de senhas; (8) sem escrita no banco, restauração não reexecutada; (9) nenhuma dependência nova, testes atuais acima e resultado de auditoria registrado no diário; (10) conexão apenas local, sem comunicação externa de documentos. Não constitui auditoria de produção.
