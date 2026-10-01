# Primeira avaliação com PDFs novos

## Método

Em 2026-10-01 foi criado o snapshot candidato `1446c44aca18011a`, com os documentos da base `4f8ddffaa01b6a20` mais seis PDFs novos aprovados. O anterior permanece disponível e a candidata não foi promovida.

| Conteúdo | Base anterior | Candidata |
|---|---:|---:|
| Contratações | 30 | 36 |
| PDFs | 49 | 55 |
| Páginas | 2.525 | 2.895 |
| Trechos/vetores | 15.773 | 18.554 |

Foram reutilizados os 15.773 vetores antigos e calculados localmente 2.781 novos, com o mesmo modelo e configuração. Igualdade dos textos, offsets e vetores antigos foi verificada no banco. Nenhum offset inválido; repetição da carga retornou already_loaded. Backup privado restaurado em outro banco com 18.554 trechos da candidata. As 71 páginas sinalizadas por pouco texto são preservadas, sem declarar revisão integral.

As dez perguntas e referências foram aprovadas antes do teste. Mantive perguntas, respostas esperadas e citações; associei cada passagem a uma âncora de trecho sobreposta, sem mudar o gabarito. A referência principal é arquivo/página/posição, evitando depender de uma divisão específica dos trechos.

Configuração e hashes congelados antes da execução: busca estruturada, lexical any, fusão RRF, até dez candidatos por ramo, cinco fontes finais e janela da mesma página (350 caracteres antes, 650 depois, teto 2.000). Uma execução por grupo; 210 buscas nos três modos, com 30 perguntas antigas na base anterior, as mesmas 30 na candidata e dez novas na candidata.

## Resultados da primeira execução

| Medida | Palavras-chave | Semântica | Híbrida |
|---|---:|---:|---:|
| Âncora conhecida entre os cinco — antigas, antes/depois | 29/30 →29/30 | 28/30 →28/30 | 29/30 →29/30 |
| Passagens de referência completas — antigas, antes/depois | 29/30 →29/30 | 29/30 →29/30 | 30/30 →30/30 |
| Âncora representativa entre os cinco — novas | 6/10 | 6/10 | 5/10 |
| Passagens de referência completas — novas | 5/10 | 5/10 | 5/10 |

Os rankings/offsets dos resultados antigos não mudaram em nenhum caso. A busca seleciona uma contratação por PNCP: os PDFs de outro edital não disputam essas posições. Portanto, isso comprova preservação no escopo selecionado, não robustez de descoberta global quando a base cresce.

**A cobertura de 50% nos novos casos não é uma nota de respostas da IA.** Exige recuperação integral das passagens conhecidas; apoio semântico e correção/completude da resposta são outra avaliação. Não prova que toda resposta com cobertura incompleta seria errada, mas evidencia risco antes da geração. Nenhuma taxa humana de 90% foi demonstrada.

A âncora é apenas um trecho representativo escolhido por sobreposição. No caso03, a híbrida recuperou toda a passagem por janelas combinadas mesmo sem recuperar essa âncora. Logo, Hit@5 dessa âncora não é recall exaustivo de documentos relevantes. Para referências com offsets, o avaliador soma somente intervalos literais contínuos da mesma fonte/página, sem preencher lacunas ou misturar páginas. As antigas preservam seu critério anterior de citação contida em uma passagem.

## Falhas da híbrida

| Caso | O que faltou na cobertura conhecida | Risco para a resposta |
|---|---|---|
| 02 — Volta Redonda | Item4/cota na página46; retornaram páginas45 e53, entre outras | Informar apenas a ampla concorrência ou confundir os quantitativos |
| 05 — Porto Belo | SSD item20 na página21; retornaram descrições/garantias de outras páginas | Usar garantia ou quantidade de outro equipamento |
| 06 — Porto Belo | RAM na página22 e identidade do item21 | Transferir especificação de um equipamento parecido |
| 07 — Porto Belo | Identidade do item21 e garantia nas páginas21/23 | Confundir garantia de componente, equipamento e cláusula geral |
| 10 — Serpro | Bloco Cloud Connect do item1 na página39 | Obter RAM de outro bloco de roteadores, ainda que algum valor coincida |

Não foram acrescentadas páginas/IDs de caso à busca para esconder essas falhas. A janela é limitada à página: não reconstrói automaticamente uma tabela que continua na página seguinte. Passagens sobrepostas também podem ocupar várias das cinco vagas finais.

## Próxima mudança proposta

Preservar a identidade do item em cada trecho e ligar continuações de tabelas entre páginas. Em seguida, selecionar passagens com diversidade de evidências, reduzindo repetição e verificando se quantidade, especificação e garantia pertencem ao mesmo item. Essas regras devem valer para qualquer edital; não usar condições para estas perguntas específicas.

Depois de ajustar o sistema com estes erros, este conjunto passa a ser desenvolvimento. É necessário outra reserva independente e a amostra ampliada para avaliar a meta, além de revisão humana das respostas e testes de recusa. A candidata continua sem promoção; a regra de qualidade permanece bloqueada.

## Evidências e reprodução

- [Protocolo congelado](../reports/independent-retrieval-protocol-v1.json)
- [Comparação e casos](../reports/retrieval-growth-comparison-v1.json)
- [Detalhes das novas perguntas](../reports/retrieval-growth-independent-v1.json)
- [Integridade da carga](../reports/independent-load-verification-v1.json)
- [Backup e restauração](../reports/independent-backup-verification-v1.json)
- [Referência aprovada](perguntas-independentes-para-revisao.md)

Operações novas: build-independent-snapshot.py --stage prepare/load/verify; evaluate-retrieval.py com lexical-strategy any, query-profile structured, selection-profile rrf e context-profile page_window; summarize-independent-retrieval.py confere os hashes congelados. PDFs, extração, modelos, vetores e backups são privados. Relatórios históricos de preparação/carga não foram sobrescritos.

Geração deste novo lote na Groq: prévia privada pronta, autorização específica solicitada; nenhuma chamada realizada ao preparar esta comparação. A aprovação das perguntas não é aprovação de respostas ainda não produzidas.
