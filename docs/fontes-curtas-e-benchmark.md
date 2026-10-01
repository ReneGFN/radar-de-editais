# Fontes com rótulos curtos e próximo conjunto independente

## Implementação

Na variante experimental `alias_window`, as até cinco janelas da consulta recebem rótulos locais S1–S5. O schema limita o modelo exatamente aos rótulos existentes. Antes de validar a resposta, o backend converte cada rótulo ao ID real e anexa a passagem original, preservando edital/arquivo/página/offsets. A saída persistida e a apresentação usam IDs reais.

Rótulos são locais à requisição. S1 em outra consulta pode apontar a outro trecho; não é identificador estável nem substitui o ID/hash na rastreabilidade. Identificador desconhecido, de outro formato, tipo inválido ou fonte duplicada é rejeitado, sem correspondência aproximada. O modelo não recebe respostas esperadas.

A variante mantém as janelas/ranking anteriores e também esclarece no prompt que quote não deve ser gerada. Mudança conjunta de representação/schema/prompt: não atribuir causalmente todo resultado apenas ao tamanho do identificador. Padrões antigos mantidos até nova avaliação humana/independente. Aprovação para prosseguir não foi tratada como conferência independente de todas as afirmações.

99 testes locais passaram, incluindo enumeração apenas das fontes atuais, restauração do ID real, rejeição de S2/s1/S01 quando não existem, isolamento entre requisições e impossibilidade de interpretar citação verdadeira como apoio semântico automático.

## Avaliação independente de itens/tabelas

A lista candidata de metadados busca novos editais fora dos 30 anteriores, por cotas nas cinco regiões. Não baixa PDFs nem altera o banco. Objetos passam por triagem heurística de informática; isso não aprova conteúdo/documento. Pesquisa limitada às primeiras cinco páginas por UF, sem representatividade estatística. Documento selecionado na listagem pode não ser PDF ou ser duplicado: essas verificações estão pendentes.

Etapas antes de chamar isso de benchmark independente:

1. Baixar edital e anexos públicos pertinentes em área privada; validar origem/tamanho/formato e hashes distintos do corpus antigo.
2. Conferir visualmente tabelas, cabeçalhos, unidades, item/lote e retificações; páginas com OCR ruim ficam pendentes.
3. Preparar dez perguntas iniciais com referência exata para Renê aprovar antes da primeira execução; não reutilizar perguntas já ajustadas.
4. Incluir casos de itens semelhantes com valores diferentes, ITEM versus QTD, unidade, cabeçalho em página anterior, anexos conflitantes e insuficiência real. Não tratar texto de uma linha vizinha como evidência do item solicitado.
5. Congelar referência e versão antes do teste. Medir recuperação, correção, completude, apoio e cobertura separadamente. Ampliar para a política proposta de 100 perguntas/dez editais novos antes de elegibilidade de promoção.

Nenhuma associação automática de células/itens foi implementada nesta etapa. Ainda não existem perguntas novas dessa lista executadas ou PDFs novos indexados. A coleta de metadados não comprova a meta90% nem crescimento testado.

## Reprodução da variante autorizada

```powershell
.\.venv\Scripts\python.exe ops/evaluate-generation.py datasets/evaluation/reserve-candidates-v1.json --confirm-free-plan --limit 10 --interval 35 --variant alias_window
.\.venv\Scripts\python.exe ops/summarize-generation.py datasets/evaluation/reserve-candidates-v1.json --variant alias_window --report reports/generation-alias-summary-repeat.json
```

Checkpoint/ficha têm sufixo alias_window e preservam as outras variantes. Só executar com autorização de envio dos casos e plano gratuito confirmado.

## Resultado dos rótulos curtos — 2026-10-01

Dez requisições nos mesmos casos de desenvolvimento: dez answered passaram pela validação literal, sem erro nesta execução. Na variante anterior, nove passaram e reserve-10 foi bloqueado por identificador inválido. O caso agora resolveu as fontes. Não repetir para ocultar falhas; checkpoints de todas as variantes permanecem separados.

Revisão do assistente encontrou valores alinhados às referências; fontes repetidas de reserve-08/09/10 ainda exigem conferir identidade do item. Correção/completude/apoio humanos não pontuados. Aprovação de continuidade não foi registrada como aprovação humana de10 acertos. Resultado não prova100% de precisão ou manutenção de90% com documentos novos.

Nos nove casos aceitos comuns, tokens de entrada passaram24.911→23.509 (-5,6%). Totais do novo lote (dez aceitos):26.089 entrada/2.229 saída; mediana modelo950,56ms. Uma execução, com saídas diferentes e prompt também esclarecido: não declarar ganho causal de velocidade ou faturamento gratuito auditado.

Lista independente: nove candidatos distintos dos30 existentes, obtidos por consultas em nove UFs abrangendo cinco regiões; dez documentos listados como edital. Meta inicial10 candidatos incompleta. PDFs não baixados, hashes/retificações/qualidade/identidade dos itens pendentes, nenhum documento indexado ou pergunta nova executada. Cotas são amostra de conveniência, não representatividade.

Coleta encontrou erros HTTP e ao menos um429 (limite do serviço). Novas solicitações foram encerradas nesta entrega; nove candidatos preservados. Uma falha de listagem não deve descartar os demais editais da página: corrigido isolamento. Relatório inicialmente não era salvo por argumento string; corrigido Path/checkpoints por UF e execução confirmou gravação. Erros históricos sem estágio/código não foram reclassificados por hipótese.

O helper agora não repete HTTP429 imediatamente e o novo planejador interrompe o lote ao recebê-lo. Teste com transporte simulado confirmou uma única requisição e ausência de sleep/retry;100 testes locais passaram. Este controle não é monitoramento automático nem retomada agendada.

[Resumo](../reports/generation-alias-summary-v1.json) · [Revisão](../reports/generation-alias-review-v1.json) · [Configuração](../reports/generation-alias-protocol-v1.json) · [Lista candidata parcial](../reports/independent-corpus-candidates-v1.json).

## Atualização: PDFs e referências preparados

Em 2026-10-01, preparação posterior à lista de metadados extraiu sete PDFs/422 páginas. Um PDF do PA tem SHA-256 idêntico a arquivo da base antiga: removido da referência independente, mesmo sob outro identificador PNCP. Seis PDFs novos em quatro regiões sustentam o [rascunho de dez perguntas](perguntas-independentes-para-revisao.md). Um arquivo GO é certidão de publicação, não edital técnico. Três falhas ValueError permaneceram sem diagnóstico específico.

Hashes armazenados e 17 passagens foram conferidos; 11 páginas foram vistas pelo assistente. Renê aprovou explicitamente as dez perguntas e referências. Não houve indexação, geração ou avaliação das respostas da IA. Esta preparação não demonstra 90% nem cumpre ainda o conjunto ampliado. Evidências em independent-documents-v1.json e independent-reference-v1.json. O estado metadata-only descrito anteriormente é histórico.
