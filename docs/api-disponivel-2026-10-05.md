# API disponível para consulta — 2026-10-05

## Entrega e evidências

Renê pediu API funcional antes dos controles seguintes. Uma instância antiga ocupava 127.0.0.1:8766: health e descoberta funcionavam, geração retornava 503. Reiniciado exclusivamente o processo identificado como ops/serve-chat.py, com RADAR_PRIVATE_ROOT apontando para o diretório privado existente e --free-plan-confirmed. Não atribuímos causa definitiva ao 503 antigo: sua exceção era redigida. Tentativa inicial de Stop-Process falhou; taskkill no PID confirmado liberou a porta. API iniciada em segundo plano, janela oculta, sem alteração de código.

Verificações reais pelo proxy Vite em 127.0.0.1:5173: health com generation_enabled=true; catálogo com 36 contratações; pergunta genérica retornou needs_clarification e cinco candidatos; pergunta aprovada do piloto sobre desktop item 01/lote 01 de Belmonte retornou answered, garantia de 12 meses, duas fontes do arquivo 1, páginas 26 e 35. Groq real chamada após reinício. Isso comprova disponibilidade e uma consulta, não precisão global. Citações passaram pelos validadores existentes; interpretação segue requires_review. API deixada ativa para Renê, sem promessa de sobreviver a reinício do computador.

## Segurança — dez grupos no escopo operacional

1. Segredos: chave validada sem exibir valor, mantida fora do Brain; nenhum segredo registrado.
2. API/frontend: health, catálogo e POST pelo proxy reais verificados; resposta pública com fontes. Código preservado.
3. Entradas: contratos existentes preservados; apenas consultas aprovadas/válidas nesta entrega, sem repetir suíte de limites.
4. Autorização: processo identificado antes do encerramento; catálogo de desenvolvimento preservado, sem holdout; serviço em loopback. Login de produção não validado.
5. Ataques: nenhuma entrada executada como código, sem alteração de consultas/renderização; não houve nova avaliação adversarial.
6. Logs: erros públicos redigidos; evidências agregadas, sem credenciais ou diagnósticos brutos do provedor no Brain.
7. Senhas: não aplicável, sem sistema de login ou mudança de credencial.
8. Backup: não aplicável à operação, banco consultado sem alteração/restauração.
9. Dependências: nenhuma instalação/alteração; auditoria nova não executada nesta operação. Pendências de runtime existentes permanecem.
10. Comunicação: proxy local e Groq real funcionaram; HTTP restrito a localhost, provedor HTTPS configurado. TLS de produção não avaliado.

## Próxima entrega

Pausa para conferência desta etapa, conforme pedido de revisão entre entregas. Guardrails, reranking e confiança ainda não alterados: implementar e testar separadamente, preservando baseline e sem porcentagem de confiança não calibrada. 3D explicitamente adiado até vídeo de Renê.
