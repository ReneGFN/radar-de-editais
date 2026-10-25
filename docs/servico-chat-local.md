# Serviço local de perguntas — 2026-10-05

Entrega após aprovação de Renê: API ligada à descoberta e à geração existentes. **Implementada e testada localmente com banco real e provedor simulado; nova API ainda não testada contra a Groq real. Tela de chatbot pendente.**

## Fluxo implementado

1. `POST /chat/ask` recebe pergunta e PNCP opcional. O servidor fixa snapshot de desenvolvimento e variante padrão `alias_items`: contexto `item_structure`, citações `source_alias`, prompt `v1`.
2. Busca geral com órgão identificável define o escopo; edital selecionado restringe a busca. Pergunta ambígua retorna `needs_clarification`, sem chamar o modelo.
3. Pedido explícito entre contratações, como “Quais editais incluem monitores?”, retorna `discovery_only` com candidatos e aviso de cobertura limitada. **Nesta entrega não gera fatos comparativos entre vários editais.** Essa capacidade precisa de recuperação de evidências por contratação e avaliação própria, sem misturar condições.
4. Em escopo definido, `generation.answer` recupera contexto e prepara uma chamada ao GPT-OSS 120B da Groq. Citações são resolvidas e verificadas pelo núcleo existente; o serviço converte as evidências em índices de fontes.
5. A saída contém resposta, afirmações e fontes com PNCP, órgão, UF, número do arquivo, página, trecho literal e link oficial. A URL do arquivo é reconstruída pelo catálogo, sem confiar na URL retornada pelo modelo. Traços privados, aliases, parâmetros, caminhos locais e exceções brutas não são enviados ao cliente.

Integridade literal da fonte não comprova interpretação correta. O resultado mantém `semantic_support=requires_review`; não declara 90% de precisão factual. Histórico e memória conversacional não implementados; perguntas são independentes.

## Executar

Na pasta do projeto, usando o ambiente Python existente:

```powershell
$env:RADAR_PRIVATE_ROOT='C:\RadarDeEditais-private'
.venv/Scripts/python.exe ops/serve-chat.py --free-plan-confirmed
```

O parâmetro registra a confirmação do plano gratuito já informada pelo usuário; não consulta cobrança ou garante a permanência da gratuidade. A chave existente permanece no diretório privado, lida somente pelo backend no momento da geração. Sem o parâmetro, descoberta/esclarecimento continuam disponíveis e geração retorna 503. Não copiar a chave para frontend ou Brain. Porta fixa `127.0.0.1:8766`; métricas permanecem em 8765 e tela Vite em 5173.

Rotas:

- `GET /chat/health`: processo ativo e configuração de geração; **não testa chave, banco ou provedor**.
- `GET /chat/editais`: catálogo público do desenvolvimento, com órgão, UF, objeto e link.
- `POST /chat/ask`: JSON `{"question":"Qual a garantia em Uniflor?"}` ou `{"question":"Qual a garantia do item 1?","pncp_id":"<PNCP do catálogo>"}`. Exige `Content-Type: application/json` e `X-Radar-Chat: 1`.

Exemplo de descoberta sem geração em PowerShell, com o serviço iniciado:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8766/chat/ask' -Method Post `
  -ContentType 'application/json' -Headers @{'X-Radar-Chat'='1'} `
  -Body '{"question":"Qual prazo de entrega?"}'
```

Instalação reproduzível da dependência opcional: `.venv/Scripts/python.exe -m pip install -e "backend[chat]"`. FastAPI e Uvicorn já estavam instalados no ambiente verificado; foram declarados no manifesto, sem instalar bibliotecas novas nesta entrega. Faixas declaradas: FastAPI `>=0.142.2,<0.143`, Uvicorn `>=0.54,<0.55`; versões verificadas 0.142.2 e 0.54.0. Não é um lock exato de todo o ambiente.

## Controles e limites

Somente loopback; Host restrito a localhost/127.0.0.1:8766 e Origin, quando presente, aos endereços locais de chat e Vite. Sem CORS aberto; a futura tela usará proxy da mesma origem. Cabeçalho obrigatório no POST impede formulários simples; não é autenticação contra outros processos locais. Sem login multiusuário, não expor na rede ou produção.

JSON com campos extras proibidos e tipos estritos, pergunta não vazia até 2.000 caracteres, PNCP permitido, corpo até 12.000 bytes verificado durante leitura. Esquema explícito de saída rejeita campos inesperados. Ajustado o limite do núcleo de recuperação de 1.000 para 2.000 caracteres para corresponder ao contrato; permanece o teto de 16.000 caracteres do contexto preparado para o modelo.

Uma consulta ativa por processo e intervalo mínimo conservador de 35 segundos entre tentativas de geração; falhas também consomem o intervalo. O núcleo mantém timeout de 40 segundos da chamada Groq e nenhuma repetição automática. Não há prazo total garantido para recuperação/embedding; banco/modelo local lento pode manter a consulta ocupada. Escalar para mais processos exigiria controle compartilhado, não implementado. Erros retornam mensagens fixas; chamadas excessivas retornam 429, provedor indisponível/validação retornam 503.

Logs de acesso do Uvicorn desativados e mensagens brutas não exportadas. Falhas de validação do núcleo podem gerar diagnóstico no diretório privado conforme mecanismo já existente; respostas não são gravadas no Brain. Textos são dados: a futura tela deverá renderizá-los como texto seguro, sem HTML livre.

## Verificação executada

- **269 testes passaram**, incluindo 18 novos do chat: variante fixa, campos privados removidos, reconstrução da URL, esclarecimento sem modelo, intervalo, exclusão de consulta simultânea, falha redigida, plano não confirmado, fonte externa rejeitada, padrão de segredo em passagem bloqueado, entradas inválidas, Host/Origin/cabeçalho, corpo, JSON, catálogo e fontes.
- [Integração registrada](../reports/chat-local-integration.json): TestClient HTTP → serviço → PostgreSQL/embeddings/recuperação reais → geração com ChatGroq simulado → resolução de aliases/validação reais → fonte conferida contra página no banco. Uma pergunta aprovada do desenvolvimento com edital selecionado; segunda pergunta genérica gerou esclarecimento e nenhuma chamada extra. Chave real não lida e Groq não chamada. Isso verifica ligação e rastreabilidade, não qualidade factual.
- Script reproduzível `ops/verify-chat-local.py` substitui explicitamente o provedor e a função de chave. Relatório contém só fatos operacionais agregados, sem pergunta, resposta ou trecho bruto.
- Processo real iniciado por `ops/serve-chat.py`, sem habilitar geração: GET de health em 127.0.0.1:8766 respondeu 200 e `Cache-Control: no-store`; encerrado após teste. **Serviço não deixado rodando.**
- `pip check`: sem conflitos. Auditoria atual PyPI: sem vulnerabilidades conhecidas nas dependências auditáveis; pacote local não consta do índice e foi excluído dessa análise automática.
- Um teste inicial falhou por inconsistência entre citação e evidência do fixture de segredo sintético; fixture corrigido para testar efetivamente a filtragem, suíte repetida com sucesso.

Sem execução do holdout, escrita no banco, alteração de Docker, envio de PDFs a provedores ou publicação nesta entrega. Nova chamada real à Groq permanece uma verificação separada, com escopo de autorização correspondente; não confundir simulação com aprovação do provedor.

## Segurança — dez grupos

1. **Segredos — verificado no escopo:** arquivos novos/alterados examinados, configuração privada preservada e `.gitignore` exclui credenciais/dumps/PDFs. Saída por lista permitida; teste de padrão de segredo em passagem. Histórico completo não reauditado; padrões não são detector universal de dados sensíveis.
2. **APIs/frontend — verificado no backend:** schemas estritos, remoção de trace/aliases, Host/Origin/cabeçalho, ausência de CORS aberto, sem chaves no cliente. Interface futura não auditada; proteção local não equivale autenticação multiusuário.
3. **Entradas — verificado:** tipo, vazio, comprimento, extras, JSON, corpo e PNCP testados no servidor. Teto de corpo aplicado durante streaming, não somente Content-Length.
4. **Autorização — verificado no escopo local:** snapshot/variante fixos, catálogo permitido, holdout não acessível, fonte estrangeira rejeitada. Produção/login não aplicáveis à entrega e não validados.
5. **Ataques — verificado no escopo:** SQL parametrizado existente preservado; textos nunca viram comandos. Testes de Host/Origin e rejeição de formulários/cabeçalho ausente; sem cookies. Núcleo existente instrui tratar documentos como não confiáveis. Avaliação exaustiva de prompt injection e XSS da tela pendentes.
6. **Logs — verificado no escopo:** sem logs de acesso ou exceções brutas no cliente, relatório agregado. Diagnósticos de geração somente no diretório privado preexistente. Retenção e auditoria multiusuário/produção não implementadas.
7. **Senhas — não aplicável:** nenhum sistema de login/recuperação ou credencial alterado.
8. **Backup — não aplicável à mudança:** banco somente leitura; sem dump ou escrita nos dados. Restauração não repetida nesta entrega.
9. **Dependências — verificado no ambiente:** dependências de chat declaradas, sem novas instalações; 269 testes, pip check e auditoria atuais, pacote local não auditável pelo índice. Sem lock integral, versões futuras dentro das faixas exigirão nova verificação.
10. **Comunicação — verificado no escopo:** servidor testado em loopback, no-store/cabeçalhos restritivos; consultas reais só ao banco local. Auditoria via HTTPS PyPI; Groq HTTPS configurada mas não chamada nesta entrega. TLS/certificados de produção não implementados nem validados.

## Próximo passo

Aguardar revisão de Renê. Próxima proposta: tela de chatbot com pergunta livre, seleção opcional, estados de esclarecimento/candidatos e fontes acessíveis, mantendo painel de métricas. Teste real da API contra Groq e perguntas comparativas entre editais precisam permanecer identificados como verificações/capacidades pendentes.
