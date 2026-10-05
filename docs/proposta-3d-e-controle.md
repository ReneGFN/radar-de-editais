# Proposta — exploração 3D e decisões por código

2026-10-05 — análise solicitada por Renê; nenhuma implementação nova aprovada/executada nesta entrega.

## Referências examinadas

Publicação enviada: https://www.linkedin.com/posts/felipe-serra_software-corporativo-com-intera%C3%A7%C3%A3o-visual-ugcPost-7512500493991170048-FWW_/

Ferramenta web falhou ao abrir e a pesquisa não localizou resultado útil; navegador público permitiu ler a publicação e inspecionar quadro do vídeo aos 13 segundos. Armazém isométrico, objetos selecionáveis e detalhes sobrepostos. Post informa React/React Three Fiber. Não examinados código do demo ou vídeo inteiro; não comprovada melhora de produtividade. Nenhum login realizado, nenhum dado de conta copiado ao relatório, mídia não baixada.

Imagem enviada: separação entre LLM que interpreta/gera e código que decide/controla. Tratada como referência conceitual, não como regra de autoridade nem prova de desempenho/segurança.

Documentação oficial: https://r3f.docs.pmnd.rs/getting-started/introduction — renderer React para Three.js; ramo 9 corresponde a React 19, ramo 10 alpha não recomendado para esta proposta. Dependências/licenças finais serão verificadas na implementação; não instaladas.

## Proposta funcional

Adicionar aba Explorar como laboratório opcional, carregada sob demanda. Mapa semântico de trechos com PCA 3D, ponto selecionável abre documento/página/link oficial. Filtrar PNCP, UF e documentos; destacar trechos recuperados, citados e referência aprovada de caso de desenvolvimento. Manter projeção 2D e lista acessível; configurações/snapshot/variância explicada registrados. Coordenadas calculadas a partir dos vetores existentes, não inventadas por LLM. Agrupamento/zoom e amostragem declarada para evitar despejar todos os trechos de uma vez. Sem holdout nesta primeira entrega.

Aproveitar da referência a navegação, seleção de objetos e painel de detalhe. Objetos de armazém não representam nosso domínio; geometria deve representar os dados. Fluxo de consulta pode ter uma visão auxiliar das etapas/tempos reais, sem fingir eventos ainda não registrados.

Validar utilidade em tarefas: localizar fonte esperada não recuperada, encontrar trecho genérico concorrente, conferir repetição. Comparar acerto/tempo/dificuldade em 2D e 3D. Não prometer ganho de recuperação pela simples visualização; distâncias projetadas não equivalem à relevância nos vetores originais.

## Aplicação da imagem ao RAG

- Roteamento: já há descoberta e política de escopo por código, que evita chamar o modelo quando pede esclarecimento. Escolha entre modelos futuros exige experimento; manter modelo aprovado agora.
- Guardrails: validação de entrada/limites, escopo permitido e validação de citações existem. Prompt de recusa e validators não equivalem a filtro perfeito de entradas perigosas nem garantem correção semântica.
- Tool call: chat atual não dá ferramentas arbitrárias ao modelo. Banco/catálogo/fontes são acessados pelo código. Futuras ferramentas deverão ter lista permitida e regras no servidor.
- Reranking: combinação/ranking existentes não são um reranker semântico dedicado. Propor experimento separado de reordenação local dos candidatos, medir gains/regressions/custo/latência antes de promover.
- Confiança: regras auditáveis para fonte/escopo/ambiguidade; limiar numérico só após calibração com conjunto adequado. Não exibir pontuação arbitrária como probabilidade de correção.
- Tempo real: validações/controle de concorrência/intervalo executados pelo código. Não há requisito ou evidência de resposta em 300 ms do sistema completo.

## Dez grupos — atualização documental

1. Segredos/dados: conteúdo escrito inspecionado; sem credenciais, dados de conta ou textos privados. Referências públicas e caminhos relativos.
2. APIs/frontend: proposta prevê endpoints de leitura/limites de exportação e carregamento sob demanda; não implementados/verificados.
3. Entradas: proposta exige PNCP/snapshot/filtros permitidos no servidor; implementação futura, não aprovada como teste.
4. Autorização: proposta não concede acessos; nenhuma nova permissão. Regras futuras precisam de verificação própria.
5. Ataques: documentos tratados como dados não confiáveis; reuso da renderização segura proposto. Sem nova superfície executável.
6. Logs: não copiados dados pessoais da página nem screenshot de sessão externa ao Brain; telemetria futura minimizada.
7. Senhas: não aplicável a documento/proposta, sem login.
8. Backup: não aplicável, sem dados/banco alterados.
9. Dependências: nenhuma instalada; escolha futura sujeita a licença/auditoria/compatibilidade, não aprovação de produção.
10. HTTPS: fontes consultadas HTTPS; sem mudança de comunicação/produção. Nenhum certificado de produção auditado.

Próxima entrega proposta: protótipo pequeno de Explorar com dados reais de desenvolvimento e modo 2D/lista, após Renê revisar o conceito. Guardrails/reordenação e medição do 3D em entregas separadas para atribuir resultados corretamente. Resultado do teste manual de chatbot de Renê ainda não informado.
