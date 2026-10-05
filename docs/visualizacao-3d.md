# Investigação da recuperação em 2D e 3D

Direção aprovada em 2026-10-01; implementação futura, depois das perguntas de referência.

## Objetivo analítico

Investigar por que a recuperação trouxe certos trechos e deixou referências esperadas de fora. Cada ponto representa um trecho; cores e filtros alternam documento, categoria revisada e resultado da avaliação. Uma pergunta destaca recuperados e referências; clique abre texto autorizado, página e fonte. Possíveis repetições são confirmadas no conteúdo.

## Método e limites

- PCA como baseline: dois ou três componentes da mesma transformação, com variância explicada e configuração registradas. Eixos não são tópicos nomeados automaticamente.
- UMAP como alternativa posterior, registrando versão, parâmetros e seed. Distâncias e grupos projetados não comprovam agrupamentos reais.
- Comparações com mesmo modelo mantêm transformação e referência fixas quando aplicável. Projeções recalculadas separadamente não permitem interpretar movimento diretamente.
- Mudanças do modelo de embeddings exigem análise própria: espaços diferentes não compartilham coordenadas por definição.
- Busca e conclusões usam vetores originais de 384 dimensões e fontes. Conferir preservação dos vizinhos e distorções da projeção; mapa não substitui Recall@k/Hit@k.

## Benefício a verificar

Repetir tarefas em 2D/3D: localizar referência não recuperada, identificar candidato duplicado e explicar recuperação de cláusula genérica. Registrar conclusão correta, tempo e dificuldade relatada. Avaliação pequena feita pelo autor é exploratória, sem generalização.

Manter modo 2D e tabela/lista para leitura e acessibilidade; o 3D pode sofrer com oclusão e navegação. Documentar visualização → erro → hipótese → mudança → resultado medido e regressões.

Ainda não há mapa, teste de utilidade ou comparação. Referências: [Embedding Projector](https://projector.tensorflow.org/), [limitações do UMAP](https://umap-learn.readthedocs.io/en/latest/clustering.html).

Análise 2026-10-05: [referência de interface 3D e separação código/modelo](proposta-3d-e-controle.md). Protótipo novo proposto, aguardando revisão; nenhuma implementação ou utilidade medida.
