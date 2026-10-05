# Tela do chatbot — 2026-10-05

Entrega após aprovação de Renê: interface local conectada ao serviço de perguntas, mantendo o painel de avaliação. [Captura da tela](../reports/ui/chat-2026-10-05.jpg).

## O que foi implementado

- Tela inicial **Perguntar sobre editais**, pergunta livre e seleção opcional da contratação. Filtro por órgão, UF ou objeto tolera diferenças de acento.
- Campo até 2.000 caracteres, sugestões que apenas preenchem a pergunta, estado de espera e impedimento de envio simultâneo.
- Histórico das últimas 20 consultas em memória, preservado ao trocar de aba; desaparece ao recarregar ou fechar. Perguntas seguem independentes, sem resolver “e a garantia dele?” a partir do histórico.
- Resposta em afirmações com referências clicáveis. “[1]” abre o trecho literal, arquivo, página do PDF, PNCP, órgão, UF e link HTTPS oficial. A página é a posição no PDF, que pode diferir da numeração impressa. O fragmento `#page` ajuda leitores compatíveis, mas o portal/navegador pode baixar o arquivo ou ignorar esse posicionamento.
- Pedido de esclarecimento com candidatos; **Consultar este edital** seleciona a contratação e repõe a pergunta para edição, sem enviar automaticamente. Perguntas entre vários editais mostram candidatos; fatos comparativos ainda não são gerados.
- Mensagens próprias para conexão indisponível, limite de chamadas e erro de entrada. Erros brutos do provedor não são mostrados. Nova tentativa exige ação do usuário. Timeout do cliente em 90 segundos não cancela a execução no servidor; mensagem explica esse limite.
- Painel de versões, casos, qualidade e corpus continua acessível. Publicação estática informa que chat requer serviço local e não tenta acessar a API do visitante.

## Decisões da interface

Direção fixada antes de implementar: usar a identidade já existente no painel (fonte do sistema, fundo neutro, bordas discretas, azul para ações/referências, tema claro/escuro), sem trocar bibliotecas ou marca. Formulário é a ação principal; escopo fica ao lado no computador e acima em tela estreita. Fontes pertencem a cada resposta, com conteúdo longo recolhível e trecho rolável com foco de teclado.

Referências: painel existente e guias de craft/copywriting da skill Refero Design, complementados pelo fluxo Web Project Baseline. A skill Taste foi consultada, mas seu escopo exclui interfaces de produto/painéis; não aplicada como autoridade visual concorrente. Não foi necessária imagem gerada para esta interface construída com componentes nativos e sistema existente. Revisão com [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md): labels, foco visível, atualização anunciada, navegação por links, mensagens acionáveis, quebra de conteúdo longo e leitura das fontes por teclado. Isso é revisão no escopo alterado, não certificação de acessibilidade.

## Problema encontrado e corrigido

No navegador, a lista inteira retornava 503: seis contratações independentes não possuem `official_url`, `cnpj`, `year` ou `sequence` como campos separados no manifesto. A API anterior pressupunha sua presença. Agora os links do catálogo e dos PDFs são reconstruídos a partir do **PNCP permitido**, cujo formato é validado, e da sequência de arquivo presente no catálogo. Nada foi inferido da pergunta ou do texto do modelo.

Correção testada com manifesto mínimo sem esses campos, incluindo link de PDF, e catálogo real completo: **36 contratações carregadas**, links oficiais reconstruídos. O primeiro ajuste usando os campos separados ainda falhou; a verificação real identificou a ausência de todos eles e levou à correção pelo PNCP. Não registrar as tentativas anteriores como sucesso.

## Executar e revisar

Serviço normal e frontend foram deixados ativos localmente nesta sessão, em 8766 e 5173. [Abrir chatbot](http://127.0.0.1:5173/#/chat). O servidor temporário com provedor simulado foi encerrado; a tela final foi recarregada, sem manter a conversa de simulação. Geração foi habilitada com a confirmação do plano gratuito já informada por Renê; **nenhuma pergunta foi enviada pelo assistente ao provedor real nesta entrega**. Health informa configuração, sem confirmar chave, cobrança ou disponibilidade da Groq.

Para reiniciar, abra dois terminais na pasta do projeto:

```powershell
# Terminal 1
$env:RADAR_PRIVATE_ROOT='C:\RadarDeEditais-private'
.venv/Scripts/python.exe ops/serve-chat.py --free-plan-confirmed
```

```powershell
# Terminal 2
Set-Location frontend
npm.cmd run dev
```

Nesse modo, o painel usa relatórios estáticos existentes e o chat usa proxy local. `npm.cmd run dev:api` continua disponível para métricas via API 8765, que exige seu próprio serviço. Build estático não hospeda o backend do chat. Processos locais não são instalação de serviço persistente e podem encerrar quando a sessão terminar.

## Verificações executadas

- Build TypeScript/Vite passou. Bundle final aproximadamente 248 kB, 76,90 kB gzip, sem sourcemap. Nenhuma dependência adicionada ao frontend.
- **15 testes de frontend passaram**, seis novos: POST geral sem PNCP/credenciais, fontes abrindo, seleção de candidato sem envio automático, texto malicioso escapado/link inseguro rejeitado, erro 429 sem erro bruto, vazio/geração desativada e build estático sem API local.
- **270 testes de backend passaram**, incluindo regressão de catálogo sem campos separados.
- Integração banco/recuperação reais e provedor simulado reexecutada após a correção: fonte/página conferidas e esclarecimento sem geração. [Evidência](../reports/chat-local-integration.json).
- Navegador real, via proxy: carregamento das 36 contratações; pergunta genérica resultou em esclarecimento sem Groq; resposta explicitamente marcada **SIMULAÇÃO** exibiu fonte real; referência abriu passagem, arquivo 1, página 31 e link PNCP. A fonte e a interpretação simulada não foram apresentadas como resultado factual da IA real.
- Navegação para Versões e volta preservou a conversa. Revisão de layout em viewport 1280×900 e 390×844; na largura estreita, documento tinha 375 px úteis e 375 px de conteúdo, sem transbordamento horizontal no chat examinado. Override restaurado após revisão. O navegador de revisão pode reduzir a qualidade das capturas; acesso à tela é a evidência interativa preferível.
- `npm audit`: zero vulnerabilidades conhecidas. Auditoria Python/pip check da entrega imediatamente anterior em 2026-10-05 reaproveitados, sem mudança em pacotes/manifestos Python nesta entrega.
- Falhas iniciais dos testes de frontend decorreram de `scrollIntoView` ausente no JSDOM; adaptação do fixture de teste e controle da flag de chat no modo test, seguida de execução bem-sucedida. Esse fixture não entra no build.

## Segurança — dez grupos

1. **Segredos — verificado no escopo:** fontes/bundle/arquivos alterados examinados, sem valores de chave, cookie ou senha. Chave permanece no backend privado, não em `VITE_*`. Captura contém interface vazia, sem texto de documento ou resposta privada; histórico não persistido/exportado.
2. **APIs/frontend — verificado:** chamadas somente `/chat` via proxy de mesma origem, sem cookies (`credentials: omit`), POST com cabeçalho obrigatório. Proxy troca Host pelo alvo local, mantém Origin para validação no backend. Build estático não chama API. Sem CORS aberto, serviços em loopback.
3. **Entradas — verificado:** campo/validação de vazio e 2.000 caracteres no cliente, mantendo validação efetiva do servidor; seletor deriva do catálogo permitido; seleção de candidato desconhecido não é aplicada. Testes de envio e não envio automático.
4. **Autorização — verificado no escopo local:** frontend não escolhe snapshot/variante/holdout, PNCP revalidado no servidor. Sem autenticação de produção ou isolamento entre usuários; não expor serviços na rede.
5. **Ataques — verificado:** React renderiza respostas/passagens como texto; sem HTML livre. Link validado como HTTPS PNCP, rel noopener/noreferrer; teste com HTML malicioso e javascript URL. SQL existente parametrizado; Host/Origin/cabeçalho do backend preservados. Prompt injection completo não auditado nesta entrega.
6. **Logs — verificado no escopo:** conversa só em estado React, últimas 20; sem localStorage, analytics ou registro de perguntas no Brain. Logs brutos de servidor não expostos no cliente. Diagnósticos privados do núcleo permanecem conforme documentação anterior; retenção de produção não validada.
7. **Senhas — não aplicável:** nenhum login/recuperação ou credencial alterado.
8. **Backup — não aplicável à mudança:** banco somente leitura, sem dados alterados ou dumps. Sem teste de restauração nesta entrega. Conversa em memória é deliberadamente transitória.
9. **Dependências/produção — verificado no escopo:** build, 15 testes frontend/270 backend, npm audit atuais. Pacotes Python sem mudança, evidência recente identificada acima. Script de QA separado em ops e testes excluídos do frontend compilado; build não oferece flag pública para respostas simuladas.
10. **Comunicação — verificado no escopo local:** proxy e API loopback; links externos HTTPS PNCP. CSP do build preservada (connect-src self), referrer restrito. Durante QA não houve Groq real. Certificados/cabeçalhos de hospedagem de produção não implantados nem validados.

## Pendências e próximo passo

Aguardar revisão da tela por Renê. Próxima proposta: validar uma pergunta aprovada pela interface e Groq real, conferindo resposta/fontes e tratamento de limites do plano gratuito. Permanecem pendentes geração comparativa entre editais, avaliação independente e manutenção da precisão ao ampliar o corpus. O número anterior de 92,5% é recuperação top5 de desenvolvimento, não taxa de acerto deste chatbot.
