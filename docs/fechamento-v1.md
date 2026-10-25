# Fechamento técnico da versão 1.0.0

Data: 2026-10-25. Escopo: aplicação de portfólio para execução local, sem hospedagem pública. A conclusão técnica não certifica a meta de precisão de um benchmark independente.

## Incluído

Chat com descoberta geral, seleção de edital/PDFs, fontes por página, guardrails, verificação numérica, histórico visual, painel de experimentos e atlas 3D com mesa de seleção. Nenhuma rota direta nova por edital/lote/item foi adicionada neste fechamento; continua proposta futura.

## Correções finais

- Diretório privado validado tanto em clone comum quanto dentro do Brain. A restrição não presume mais a posição do repositório no disco.
- README reorganizado e guia local correspondente ao snapshot do chatbot (`1446c44aca18011a`), em vez de misturar a base histórica de 30 documentos com o corpus atual.
- Fundo CSS próprio; build não depende da imagem externa de 5,6 MB sem licença confirmada.
- Atualizados certifi, filelock, opentelemetry-api, Pypdf e Pillow para versões corrigidas indicadas pela auditoria. FastEmbed atualizado a 0.9.1 para aceitar Pillow 13; a incompatibilidade intermediária foi identificada por pip check e corrigida.
- Node mínimo documentado, versão verificada 24.22.1. Workflow Windows com Python 3.12/Node 24 e ações oficiais fixadas por SHA, sem credenciais de provedor.
- Estado dos resultados manuais descrito sem inventar registros de revisão. Gates históricos preservados.

## Verificado localmente

- 306 testes backend passaram com temporário novo fora do OneDrive. A rodada inicial no temporário do ambiente restrito ficou sem progresso e foi interrompida; outra rodada teve erros de permissão em fixtures e não foi contada como aprovação.
- 22 testes frontend e build passaram com Node 24.22.1. A rodada frontend inicial teve falha de arquivos temporários do ambiente restrito; nova execução fora dessa restrição passou.
- pip check sem conflitos; pip-audit sem vulnerabilidades conhecidas no ambiente auditável, pacote local editável ignorado.
- npm audit --omit=dev na pasta frontend: zero vulnerabilidades conhecidas. Uma consulta anterior na raiz não correspondia ao manifesto frontend e foi descartada dessa evidência.
- Cinco páginas de referência reextraídas com Pypdf atualizado e comparadas com citações esperadas, sem divergência nessa amostra.
- 61 JSONs públicos do painel reexportados e validados por lista de campos permitidos. Build mantém aviso de cena 3D de aproximadamente 583 kB, carregada separadamente.

## Avaliação humana e limites

Renê informou que os testes recentes funcionaram e relatou cerca de 43 acertos em 46 casos, anotados em papel. Não há respostas, marcação de erros ou configuração arquivadas dessa rodada. O número é relato manual aproximado, não benchmark reproduzível; a avaliação formal do holdout permanece pendente nos arquivos do avaliador. Não publicar a meta de 90%/95% como atingida por evidência independente.

Esta entrega não adiciona autenticação multiusuário, hospedagem, OCR, prova de vigência, memória semântica de conversa, interpretação robusta de tabelas ou garantia de desempenho em novos documentos. A gravação para LinkedIn é uma tarefa de divulgação posterior; existe um [roteiro](demonstracao.md).

## Segurança: dez grupos

1. **Segredos/dados:** publicação por lista permitida, sem PDFs, modelos, vetores, dumps, respostas brutas ou arquivos privados. Varredura de credenciais no conjunto alterado; histórico completo não é uma auditoria de segurança.
2. **API/frontend:** chave no backend, JSON público por lista permitida, build sem imagem externa e sem credenciais. API de perguntas deve continuar local.
3. **Entradas:** limites e schemas existentes preservados; novos testes de diretório privado. Sem novo upload ou leitura de caminhos fornecidos por usuário.
4. **Autorização:** serviço em loopback, origem/cabeçalho e catálogo de desenvolvimento verificados pelos testes; não há login multiusuário e não se recomenda expor a API na internet. Nenhum uso novo de holdout/Groq nesta entrega.
5. **Ataques:** SQL parametrizado, citações literais, React sem HTML bruto e bibliografia vinculada às próprias fontes mantidos. Controles não são um detector universal de prompt injection.
6. **Logs:** diagnóstico de respostas desligado por padrão; dados privados continuam externos; relatório público só com resultados e limitações. Retenção operacional de produção não aplicável ao escopo local.
7. **Senhas:** senhas do banco existentes não rotacionadas; script cria aleatórias somente na instalação inicial; não há login/senha de aplicação.
8. **Backup:** nenhum volume removido ou resetado; o fechamento não reexecutou restauração de backup. A restauração histórica não garante recuperação de um novo ambiente.
9. **Dependências:** correções, lockfiles, pip check, testes e auditorias atuais acima. Auditoria de dev npm não incluída na alegação runtime. Aviso de chunk grande documentado.
10. **Comunicação:** URLs oficiais HTTPS, serviços loopback e nenhuma nova transmissão de pergunta ao modelo. Certificados/cabeçalhos de uma implantação pública não avaliados porque não há deploy.

## Verificações externas

Publicação, workflow remoto e estado final do banco são registrados após suas verificações. Uma configuração escrita não equivale a execução aprovada. O [guia local](execucao-local.md) diferencia painel sem serviços de chatbot completo.

### Verificação real de banco e integração

Docker recuperado após falhas em dois sockets de runtime. Diretórios antigos preservados fora do projeto; nenhum volume/banco/credencial removido. Estabilidade após uma futura reinicialização do Docker não demonstrada. Container Radar saudável; SQL confirmou 36 contratações/55 PDFs no snapshot do chat. Busca real com FastEmbed 0.9.1 retornou cinco trechos, incluindo os prazos de 12 e 36 meses. Integração da API com banco/recuperação reais e Groq simulada respondeu answered e confirmou páginas/citações; zero chamadas novas à Groq.

### Dependências frontend de desenvolvimento

A instalação limpa também apontou dois avisos em Vite/Undici. Vite atualizado de 8.3.2 para 8.3.5 e Undici atualizado dentro da faixa permitida, sem force. Auditoria completa npm após essas correções: zero vulnerabilidades conhecidas. Manifesto e lockfile sincronizados.
