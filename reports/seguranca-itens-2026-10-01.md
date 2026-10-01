# Segurança — estrutura dos itens — 2026-10-01

Escopo: novo perfil opcional, seleção local, testes e documentação. Etapa2 parada por solicitação do usuário.

|Grupo|Resultado e evidência|Limitação|
|---|---|---|
|1 Segredos/dados|Verificado no escopo: código/testes sintéticos, nenhum PDF/resposta bruta; exportador por lista permitida e scanner antes do push.|Não reaudita todo histórico.|
|2 API/frontend|Verificado: sem chamadas Groq; somente novos metadados públicos de item no perfil opcional.|Frontend futuro; teste ponta a ponta do novo perfil pendente.|
|3 Entradas|Verificado: perfil permitido explicitamente; limite existente1000 caracteres de pergunta;5 passagens/2000 caracteres; escopo8milhões; offsets literais conferidos,119 testes.|Reconhecimento heurístico não é validação semântica.|
|4 Autorização|Verificado: escopo snapshot/PNCP e filtros parametrizados preservados; leitura somente; continuação limitada ao arquivo.|Sem identidade multiusuário; integração real do perfil pendente para etapa2.|
|5 Ataques|Verificado: SQL fixo com parâmetros, filtros em lista fechada; texto não executado; cláusula evita ampliação; testes de fronteira/IDs.|Prompt injection em PDF real pendente; sem frontend para testar XSS/CSRF.|
|6 Logs|Verificado: resultado/hashes separados, primeira execução preservada; sem gabarito na seleção.|Falha inicial de teste corrigida; não publica falsamente taxa de acerto.|
|7 Senhas|Não aplicável: nenhuma senha/login/recuperação alterada.|Identidade futura.|
|8 Backup|Não aplicável a nova escrita: perfil somente leitura, sem carga/migração; teste de restauração anterior de hoje em independent-backup-verification-v1.json continua válido porque banco não foi alterado.|Periodicidade/recuperação externa pendentes.|
|9 Dependências|Verificado:119 testes passaram; pip-audit atual sem vulnerabilidades conhecidas auditáveis; nenhuma biblioteca nova.|Pacote local não auditável por PyPI; não audita produção.|
|10 HTTPS|Não aplicável a chamadas novas: não houve Groq/download; DB local e HTTPS do cliente existente não modificados.|TLS/cabeçalhos de produção futuros.|

Auditoria privada atual: tmp/radar-pip-audit-item-structure.json. Não alterou volumes, ERP, produção, credenciais ou snapshot ativo. Perfil anterior permanece padrão; validação quantitativa, integração real e revisão humana aguardam aprovação para etapa2.
