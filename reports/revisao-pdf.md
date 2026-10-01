# Revisão amostral de PDFs — 2026-09-30

Snapshot: `b1ee54ef84e97078`. Renderização com Poppler e inspeção visual de quatro páginas, de três contratações. Imagens e documentos permanecem no diretório privado, fora do Brain.

| Contratação | Página física | Observação |
|---|---|---|
| Santa Ernestina, `45374469000129-1-000030/2026` | 1 | Tabela com datas e horários; objeto de informática e correlatos. Texto e tabela legíveis na imagem. |
| Nova Odessa, `01626427000162-1-000010/2026` | 1 | Capa informa locação de notebooks e monitores, instalação/configuração, valor e sessão. Caso deve ser classificado como locação, não compra. |
| USP, `63025530000104-1-003836/2026`, primeiro documento do manifesto | 1 e 2 | O conteúdo é estudo técnico preliminar, apesar da classificação de Termo de Referência recebida pela API. Inclui condições gerais, quantidade e estimativa. Não é a capa do edital. |

## Problemas e correções

- Metadados de tipo não bastam para determinar o conteúdo real do anexo. Preservamos o tipo informado pelo PNCP; a revisão das referências de avaliação deverá registrar o título real e sua função. Não presumir que o primeiro anexo é o edital.
- Poppler emitiu avisos sobre fontes de substituição; as quatro imagens inspecionadas ficaram legíveis. Isso não valida outras páginas.
- pypdf identificou fontes CFF que precisavam de FontTools. A dependência foi adicionada e a preparação repetida antes da carga.
- O splitter do LangChain calculava offsets como se a sobreposição fosse em caracteres; esta base usa tokens. Corrigida a localização do trecho no texto da página, com conferência de substring. O banco também é verificado para divergências dos offsets.

Não houve revisão integral das 682 páginas, validação jurídica, revisão de todas as tabelas ou criação de respostas esperadas. Páginas sem texto suficiente são preservadas e sinalizadas, não convertidas automaticamente em evidência de ausência. OCR e extração estruturada de tabelas continuam pendentes.
