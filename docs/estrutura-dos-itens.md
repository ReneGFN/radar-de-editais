# Etapa1 — identidade dos itens e contexto entre páginas

Implementação de2026-10-01, solicitada por Renê com parada para aprovação antes da etapa2. Não executamos avaliação de acerto, lote Groq, novas perguntas ou promoção nesta etapa.

## Como funciona

Novo perfil experimental `context_profile="item_structure"`, disponível em `retrieve_with_trace` e `generation.answer`. Padrões anteriores preservados. O perfil exige selection_profile="rrf"; combinação coverage é rejeitada explicitamente. LangChain continua coordenando os ramos lexical e semântico.

1. Lê páginas e trechos somente da contratação/snapshot selecionados, em transação SQL somente leitura. Respeita filtros de página/arquivo; filtro de cláusula usa as fontes anteriores sem ampliar escopo. Sem alterar banco, documentos, vetores ou referências aprovadas.
2. Reconhece cabeçalhos explícitos Item N e linhas numeradas de tabela acompanhadas de unidade/quantidade. A detecção é heurística: não é um parser geométrico universal de PDFs.
3. Vincula continuação por páginas consecutivas do mesmo arquivo, até três páginas por ocorrência. Para ao próximo item, anexo/termo/lote reconhecido, salto de página ou mudança de arquivo. Continuação inferida é marcada requires_review, não certeza de identidade.
4. Quando a pergunta menciona item, prioriza cabeçalho e passagens do item encontrado. Coincidência de palavras da pergunta ordena as demais fontes; não consulta gabarito, páginas de respostas ou IDs de casos. Sem item reconhecido, mantém recuperação anterior com seleção diversa.
5. Mantém no máximo cinco passagens, cada uma até2000 caracteres, com fonte/página/offset original. Passagens de páginas diferentes permanecem separadas; não são concatenadas para formar uma citação artificial.
6. Descarta sobreposições de pelo menos60% do menor intervalo e repetições idênticas do mesmo item/arquivo. Considera até20 candidatos da fusão, preenchendo vagas com fontes diferentes disponíveis.
7. Destaca candidatos literais de unidade/quantidade com offsets (ex.: UNID 02), sem inferir que todo número é quantidade. Envia à IA metadados de item/cabeçalho/continuidade somente neste perfil. Cada passagem derivada tem ID próprio e conserva o ID do trecho de origem, evitando colisão quando um trecho cobre dois itens.

## Por que essa escolha

O modelo recebe a identificação junto da passagem e pode consultar a quantidade literal. O vínculo permite buscar especificação e garantia em páginas consecutivas. Fontes repetidas deixam de consumir todas as vagas. Mantive um perfil separado para comparar a mudança com a primeira execução, preservar reproduções históricas e permitir reversão. O índice é calculado em leitura: não exige migração ou novos embeddings.

## Verificação da implementação

119 testes passaram, incluindo continuação limitada, fronteiras de itens/arquivo/anexo, exclusão de sobreposições, referências literais, candidatos de quantidade, IDs distintos e compatibilidade com validador de citações. A primeira tentativa de teste revelou reconhecimento indevido de unidade sem quantidade; corrigido para exigir número após unidade. pip-audit atual: nenhuma vulnerabilidade conhecida nos pacotes auditáveis.

Não foi medido ganho de recuperação ou acerto em documentos reais. Integração do novo perfil com PostgreSQL real e avaliação ponta a ponta ficam na etapa2 após aprovação; os testes desta etapa verificam funções de estrutura e compatibilidade de citações. Os relatórios congelados antigos conservam seus hashes de código original; a implementação nova é outra versão, não reprodução daquele protocolo.

## Limites

Layouts com quantidade antes da unidade, tabelas muito longas, item sem cabeçalho reconhecível, continuidade além de três páginas ou cabeçalhos não reconhecidos exigem melhoria/conferência. Um cabeçalho pode ser ambíguo; marcação heurística não prova que a garantia pertence ao item. Seleção lexical local pode perder uma paráfrase relevante. O escopo permanece por PNCP; descoberta global não foi implementada. O limite de texto por escopo é8milhões de caracteres; excedê-lo gera erro explícito. Nenhuma garantia de90% nesta etapa.

## Próximo passo sujeito à aprovação

Executar etapa2: integração real, comparar regressão/recusas/completude e novas fontes com configurações versionadas; conferir respostas humanas e planejar reserva independente após ajuste. Respeitar autorizações específicas de envio à Groq; nenhum novo lote foi enviado nesta etapa.

[Segurança](../reports/seguranca-itens-2026-10-01.md) · [Evidência dos testes e hashes](../reports/item-structure-implementation-v1.json).
