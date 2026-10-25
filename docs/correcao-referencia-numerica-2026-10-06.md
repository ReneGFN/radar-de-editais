# Referências bibliográficas e números factuais

## Diagnóstico e correção

Renê relatou nova recusa no caso comparativo e autorizou repetir o mesmo caso na Groq, GPT-OSS 120B, conta gratuita. Foram feitas três chamadas para diagnóstico e verificação, todas da mesma pergunta com até cinco trechos dos dois PDFs públicos. As respostas completas ficaram no diretório privado externo ao Brain.

A primeira execução revelou números sem apoio literal: 117 e 2026, do identificador do edital. Os prazos de 12 e 36 meses não eram os números rejeitados. Orientar o modelo a omitir identificadores no texto factual não bastou: a segunda execução repetiu a referência e foi recusada.

O verificador agora trata somente expressões explícitas no formato “edital número/ano” como referências bibliográficas: confere número/ano contra o PNCP das próprias fontes citadas naquela afirmação. Não usa os números dos metadados para validar prazos, capacidades ou quantidades. Identificador errado, ano errado, fonte não citada e “garantia de 117 meses” continuam recusados. A referência permanece no texto; apenas sua validação é separada da validação de valores factuais. Item/lote continuam sujeitos ao apoio literal.

Diagnóstico de recusa numérica pode ser habilitado com RADAR_PRIVATE_DIAGNOSTICS=1; permanece desligado por padrão. Quando habilitado, salva números rejeitados e afirmações pré-validação somente no diretório privado. Não há retenção automatizada desses diagnósticos; seu uso deve permanecer restrito à investigação local. Nenhum valor de chave foi registrado.

## Verificação

- 304 testes backend passaram, incluindo seis novos casos de identificação bibliográfica válida/inválida e proibição de usar número do edital como prazo.
- Terceira chamada real: answered, com duas afirmações: Belmonte 12 meses e equipamento com RTX 5090 do TCE-GO 36 meses de fábrica.
- Fontes retornadas: Belmonte PDF 1 páginas 35 e 26; Goiás PDF 1 página 69. A recuperação literal dessas páginas foi conferida na entrega anterior; isso não substitui a conferência humana das relações entre item e exigência.
- Backend reiniciado para ativar a correção; frontend não alterado.
- Caso de desenvolvimento corrigido, não avaliação independente, nova taxa global ou promessa de generalização. Holdout não utilizado.

## Dez grupos de segurança

1. Segredos/dados: chave só para autenticação oficial; respostas e diagnóstico fora do Brain, sem publicação bruta. Código/relatório inspecionados. Histórico completo não auditado.
2. APIs/frontend: esquema público preservado; diagnóstico não exposto pela API; nenhuma chave no navegador.
3. Entradas: referência reconhecida por expressão restrita e vinculada às fontes da afirmação; testes de número/ano incorretos.
4. Autorização: envio específico autorizado por Renê, apenas o mesmo caso; catálogo/snapshot de desenvolvimento preservados. Sem holdout/produção.
5. Ataques: nenhuma execução de texto ou SQL novo; metadados só autorizam referência bibliográfica, não números factuais. Guardrail continua recusando valores sem evidência.
6. Logs: diagnóstico privado optativo e desligado no serviço padrão. Sem nova telemetria; retenção automatizada pendente.
7. Senhas: não aplicável; nenhuma mudança de senha/autenticação.
8. Backup: sem escrita no banco; respostas de teste privadas não constituem backup; restauração não reexecutada.
9. Dependências: nenhuma mudança de pacote; suíte backend acima. Nenhuma nova auditoria de vulnerabilidades nesta entrega.
10. Comunicação: três chamadas ao endpoint HTTPS oficial Groq; serviço local em loopback. TLS/implantação pública não verificados.

## Próximo passo

Renê conferir a resposta no chatbot com os dois PDFs da mesa. Depois da aprovação dessa validação, preparar revisão dos 46 casos independentes. Mudança local, ainda sem publicação no GitHub.
