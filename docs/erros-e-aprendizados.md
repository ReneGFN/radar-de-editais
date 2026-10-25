# Erros e aprendizados

## Busca lexical restritiva

A linha de base tratava a pergunta como conjunção de palavras. Isso excluía documentos úteis. A combinação lexical mais permissiva melhorou a recuperação em desenvolvimento, com regressões preservadas nos relatórios. Filtros de página/item ajudam quando fornecidos, mas as medições sem essas pistas são inferiores. [Experimentos](resultados-recuperacao.md).

## Mistura de exigências e unidades

Ter uma fonte válida não garante interpretar corretamente quantidade, limite ou unidade. As variantes experimentais adicionaram regras, mas não foram promovidas só por parecerem mais seguras. A decisão preserva `alias_items` como padrão. [Métricas](metricas-atuais.md).

## Comparação com contexto desequilibrado

A primeira versão da mesa preenchia quase todo o contexto com o primeiro PDF. A garantia do segundo não chegava ao modelo. A recuperação passou a equilibrar arquivos e usar consultas derivadas de pistas técnicas e continuação limitada de página. Isso corrigiu o caso de desenvolvimento, sem comprovar ganho universal. [Registro](chat-conversa-e-comparacao-v2.md).

## Número do edital confundido com valor factual

Uma resposta com prazos de 12 e 36 meses era rejeitada porque repetia o identificador 117/2026, presente nos metadados e ausente da passagem. O verificador agora confere essa referência contra o PNCP da fonte citada. Isso não permite usar 117 como prazo nem aceitar edital/ano errados. [Diagnóstico e testes](correcao-referencia-numerica-2026-10-06.md).

## Health não prova consulta real

O processo local respondia 200, mas o ambiente em que foi iniciado bloqueava acesso à Groq. A correção foi iniciar o backend com rede disponível e distinguir serviço ativo de dependências funcionais. Uma conta própria e fontes disponíveis continuam necessárias para reproduzir geração.

## Reproduzir fora da máquina do autor

A validação do diretório privado pressupunha que todo clone estivesse dentro do Brain. Em uma pasta comum poderia bloquear armazenamento externo válido. Agora detecta o Brain por seus arquivos de instruções e sempre protege o próprio projeto e o OneDrive. Testes cobrem clone comum e diretórios protegidos.

## Resultado manual sem arquivo de revisão

O autor relatou cerca de 43 acertos em 46 casos, anotados em papel. Sem respostas, configuração da execução e marcação dos erros arquivadas, essa contagem é relato manual, não avaliação independente reproduzível. Os gates antigos permanecem bloqueados até receberem os registros necessários. O projeto expõe esse limite em vez de publicar uma taxa como comprovada.
