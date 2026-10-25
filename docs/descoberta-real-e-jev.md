# Descoberta real e investigação Jev — 2026-10-05

Banco Radar encontrado saudável, contêiner radar-de-editais-db-1 em 127.0.0.1:55432. Nenhum reset, carga, inicialização, alteração de credenciais ou ação em outros contêineres.

## Resultado da primeira avaliação global

`ops/evaluate-discovery.py` executou 40 perguntas factuais existentes de desenvolvimento em toda a base, sem filtro de PNCP. Contratação esperada no top 5: **21/40 (52,5%)**; mediana de recuperação **348,23 ms**. Metadados de arquivo/página/offset/URL de todos os candidatos conferidos contra banco. Nenhuma chamada Groq ou acesso ao holdout. [Relatório por caso](../reports/discovery-development-v1.json).

Este número mede localizar uma contratação conhecida, não resposta correta. Uma execução, com perguntas escritas inicialmente para editais selecionados e algumas pistas de localização; rótulos não enumeram todas as contratações também relevantes. Nenhum ajuste foi feito para melhorar a nota depois deste teste. O mecanismo ainda não está pronto para conectar geração sem tratar falhas de descoberta. Pergunta genérica “monitores” retornou cinco candidatos, sem afirmar cobertura exaustiva.

## Jev

Identificado como modelo de decisões estruturadas da TypeSafe. Pode pontuar relevância dos candidatos, ajudar a reordenar passagens e indicar necessidade de esclarecimento. A geração da resposta continuaria no GPT-OSS 120B. Essa é uma proposta de experimento, sem ganho medido no Radar.

Nas fontes públicas consultadas, não foi confirmado plano gratuito permanente de API do Jev. A oferta Jev 1.13 na OpenRouter cobra **US$0,042 por milhão de tokens de entrada** e zero por saída. “Free” na coluna de saída não significa chamada inteira gratuita. Playground exige login, e documentação pública examinada não comprova quota gratuita utilizável via API. Conta, créditos promocionais e faturamento não acessados. Não instalar nem usar endpoint pago diante da restrição explícita de Renê.

Como embeddings e busca textual atuais são locais, um serviço remoto acrescentaria latência, dependência externa e envio de trechos. Poderia reduzir tokens de geração por selecionar melhor, mas isso precisa de comparação; custo da Groq atual é plano gratuito declarado. Recomendação: manter Jev como experimento futuro condicionado a API gratuita verificável. Priorizar a descoberta geral e, depois, comparar baseline contra reranking em candidatos congelados, com relevância rotulada e latência/consumo medidos. Um reranker não recupera um documento ausente do conjunto de candidatos. Confiança do modelo não é taxa de acerto garantida.

Fontes consultadas em 2026-10-05:
- [TypeSafe: introdução](https://docs.typesafe.ai/introduction).
- [TypeSafe: início rápido](https://docs.typesafe.ai/introduction/quickstart).
- [OpenRouter: preço Jev 1.13](https://openrouter.ai/typesafe/jev-1.13/).

## Dez grupos de segurança desta entrega

1. Segredos: scripts não imprimem credenciais; relatório contém IDs/metadados, sem perguntas/textos privados/valores de chaves.
2. APIs/frontend: nenhuma nova rota ou cliente; navegação pública para pesquisa, sem envio de documentos a Jev ou Groq.
3. Entradas: referências existentes, 40 casos; oito testes de descoberta passaram novamente; fontes conferidas no banco.
4. Autorização: etapa aprovada; snapshot fixo, sem holdout; banco em leitura.
5. Ataques: SQL parametrizado e transação READ ONLY executados; prompt injection, XSS e CSRF não exercitados nesta avaliação.
6. Logs: saída somente ID, contagem, hit; relatório preserva todos os casos, inclusive falhas; sem nota humana automática.
7. Senhas: não aplicável; nenhuma alteração de senhas/recuperação.
8. Backup: sem escrita no banco; não reexecutado restore nem comprovada periodicidade de backup privado.
9. Dependências: nenhuma nova; evidência reutilizada da auditoria de hoje na entrega de discovery, sem avisos conhecidos nos pacotes auditáveis; oito testes específicos reexecutados. Não representa auditoria integral de produção.
10. Comunicação: pesquisa em HTTPS oficial; banco local; conta e quota Jev não verificadas.

Próxima entrega proposta: diagnosticar e melhorar candidatos da busca global, com comparações preservadas, antes de conectar geração ao chat. Parada para avaliação de Renê.
