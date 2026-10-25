# Conferência comparativa de dois PDFs

Estado: preparação e recuperação real verificadas; geração ainda não executada. Caso de desenvolvimento, não faz parte do holdout e não mede uma taxa global.

## Como testar

1. Em Explorar, adicione à mesa o PDF 1 do Município de Belmonte (BA), PNCP `13634977000102-1-000128/2026`.
2. Adicione o PDF 1 de Goiás Tribunal de Contas (GO), PNCP `02291730000114-1-000117/2026`.
3. Entre no chat pelo botão de perguntar sobre os dois PDFs. Confira que somente esses dois arquivos aparecem no escopo.
4. Use esta pergunta, empregada na verificação da recuperação:

> Compare as garantias: desktop item 01 lote 01 de Belmonte e equipamento descrito com RTX 5090 do edital 117/2026. Qual prazo de garantia de cada um? Cite arquivo e pagina separadamente.

## Resposta esperada a partir dos documentos

| Objeto | Garantia | Referência |
|---|---|---|
| Desktop, item 01 do lote 01 de Belmonte | 12 meses | PDF 1, página 26; texto: “GARANTIA DE 12 MESES” |
| Equipamento da lista que descreve RTX 5090 do Tribunal de Contas de Goiás | 36 meses de fábrica | PDF 1, página 69; texto: “Garantia de 36 (trinta e seis) meses de fábrica” |

[PDF oficial de Belmonte](https://pncp.gov.br/pncp-api/v1/orgaos/13634977000102/compras/2026/128/arquivos/1) · [PDF oficial do Tribunal de Contas de Goiás](https://pncp.gov.br/pncp-api/v1/orgaos/02291730000114/compras/2026/117/arquivos/1).

Não aplicar esses prazos a todos os itens dos editais. A resposta precisa distinguir as duas fontes. Se faltar apoio no contexto recuperado, o comportamento adequado é informar a limitação; isso conta como resposta incompleta na avaliação factual, mesmo sendo prudente.

## Evidência local

Snapshot `1446c44aca18011a`. Transação SQL somente leitura confirmou os textos esperados nas duas páginas. Recuperação real retornou cinco passagens e zero arquivos fora da seleção: Belmonte páginas 35, 3, 26 e 27; Goiás página 48. A página 69 de Goiás não apareceu: problema concreto de cobertura para pergunta comparativa, ainda sem correção nesta etapa. Não confundir existência da resposta na base com disponibilidade no contexto do modelo.

API iniciada em loopback; health confirma serviço e configuração de geração, sem validar o provedor. Nenhuma chamada Groq foi feita nesta preparação. Autorização específica do novo caso solicitada. Resposta real e conferência humana continuam pendentes.

## Dez grupos de segurança desta preparação

1. Segredos/dados: relatório só com identificadores públicos e referências já aprovadas do piloto; nenhuma credencial ou extração integral registrada.
2. API/frontend: consulta de health local e busca no servidor; chave não enviada ao cliente. Health não comprova disponibilidade da Groq.
3. Entradas: dois pares PNCP/PDF pertencem ao catálogo; limite de cinco preservado. Sem mudança de validação.
4. Autorização: seleção de desenvolvimento, sem holdout; envio externo aguarda autorização específica.
5. Ataques: consulta SQL parametrizada em transação somente leitura; nenhum comando construído com texto de PDF.
6. Logs: saída da verificação contém somente contagens, páginas e identificadores; conteúdo privado não registrado.
7. Senhas: não aplicável; nenhuma gestão de senha alterada.
8. Backup: não aplicável à consulta somente leitura; restauração não reexecutada.
9. Dependências: nenhuma instalação ou alteração nesta preparação; evidências da publicação precedente não constituem nova auditoria de dependências.
10. Comunicação: serviço 127.0.0.1 e referências oficiais HTTPS; produção/TLS não avaliados. Nenhum envio ao provedor nesta preparação.

## Sequência

Executar/conferir a resposta conjunta após autorização. Apresentar resultado e limitações a Renê antes da etapa 2, revisão dos 46 casos independentes. Nenhuma nova taxa de acerto atribuída.
