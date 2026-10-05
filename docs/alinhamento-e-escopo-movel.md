# Alinhamento e painel de escopo móvel

Entrega local em 2026-10-05 para revisão de Renê, após sua captura e pedido de correções.

## Mudanças e decisões

- Versões: título técnico separado do subtítulo legível, selos Padrão/Experimental com inicial maiúscula, cabeçalhos consistentes. Identificadores `alias_items` permanecem exatos.
- Conferência humana: Factuais e Recusas em blocos separados. Taxa não calculada/Revisão incompleta em área própria, sem sobreposição do texto anterior. Contagens e sentido das ressalvas preservados.
- Casos: estado técnico e selo de revisão em linhas separadas, altura reservada para estados compridos. Capitalização visual dos estados/selos e papéis.
- Seletor: barra visual escondida; rolagem por roda, trackpad, toque e navegação pelos botões permanece disponível. Não foi adicionada inércia artificial nem captura global da roda.
- Painel arrastável pelo cabeçalho com Pointer Events de React, sem nova biblioteca. Posição limitada à janela; ajuste ao redimensionar/reabrir. Setas do teclado movem 20 px e botão Restaurar posição do painel recupera o local inicial.
- Clicar fora não fecha mais o painel, permitindo escrever/consultar a pergunta ao mesmo tempo. Fechamento permanece pelo botão, Escape, seletor e seleção de uma contratação. A posição é transitória, não salva em armazenamento.

Qualidade e Corpus não receberam mudanças de estrutura ou dados. A direção visual permanece a Moon Chat aprovada; guia de foco/acabamento já lido nesta sessão aplicado. Não houve geração de imagem nova ou publicação.

## Evidências

- Build TypeScript/Vite final passou: JS 254,14 kB (78,32 kB gzip), CSS 23,60 kB (5,94 kB gzip).
- 17 testes frontend passaram, incluindo movimento por teclado, restauração, preservação da pergunta e ausência de envio automático. Testes de fontes/texto não confiável mantidos.
- npm audit com rede em 2026-10-05: zero vulnerabilidades conhecidas. Resultado offline anterior não foi usado como prova de atualização do banco de avisos.
- Navegador: arraste real mudou o painel para posição fixa, esquerda 89,98/topo 111,67; seta direita moveu mais 20 px. Pergunta preenchida com painel ainda aberto. Rolagem observada na lista (scrollTop 2662) e scrollbar-width none. Botão restaurou a posição.
- Aviso amarelo com altura própria 65,11 px e dentro do cartão; cinco estados visíveis em Casos com selo em linha separada. Versões/Casos em 390 × 844: documento 375 px, sem overflow de página. Arraste por toque implementado, não testado em dispositivo físico.
- Capturas: [Versões](../reports/ui/versions-aligned-2026-10-05.jpg), [Casos](../reports/ui/cases-aligned-2026-10-05.jpg), [painel movido](../reports/ui/scope-movable-2026-10-05.jpg). Viewport restaurado.
- Uma escrita CSS inicialmente apontou caminho duplicado e falhou; corrigida com patch/caminho correto e build repetido. Nenhuma falha considerada entrega concluída.

## Dez grupos de segurança

| Grupo | Resultado e limites |
|---|---|
| 1. Segredos/dados | Verificado no escopo: fontes/build inspecionados por padrões de chave, sem ocorrências. .gitignore e origem privada de credenciais da entrega anterior preservados, nenhuma credencial acessada ou registrada. Não auditado histórico completo. |
| 2. APIs/frontend | Verificado no escopo: apenas apresentação/interação; contratos e proxy sem mudança. Testes preservam omissão de credenciais, estático sem API. |
| 3. Entradas | Verificado no escopo: pergunta/filtro e PNCP preservados; coordenadas limitadas ao viewport e sem persistência. Testes garantem seleção/movimento sem envio automático. |
| 4. Autenticação/autorização | Não aplicável à atualização visual: nenhum login ou nova permissão. Escopo não é controle de autorização; servidor não alterado. |
| 5. Ataques comuns | Verificado no escopo: React continua escapando texto e allowlist de links preservada; testes de HTML malicioso/links inseguros passaram. Nenhuma consulta SQL/comando novo. |
| 6. Logs/auditoria | Verificado no escopo: sem telemetria ou registro de movimentos/perguntas; capturas de interface/dados públicos. Sem nova avaliação de logs externos. |
| 7. Senhas/recuperação | Não aplicável: nenhuma mudança de identidade/senhas. |
| 8. Backup/recuperação | Não aplicável ao escopo: sem escrita/migração de banco, nenhum backup/restauro novo. |
| 9. Dependências/produção | Verificado no escopo: nenhuma dependência nova, build/17 testes/audit atuais. Pendências prévias: Node 22.16 inferior a requisitos de dependências de teste existentes e imagem pesada/sem licença verificada. |
| 10. HTTPS/comunicação | Verificado no escopo: política CSP/URLs/proxy existentes preservados, sem destino externo novo. Localhost HTTP; TLS de produção não avaliado. |

## Próximo passo

Aguardar aprovação desta entrega. Persistem [pendências de imagem/runtime](interface-refinada.md); sem nova Groq real, holdout, Docker ou publicação. Após revisão, retomar a etapa funcional aprovada pelo usuário.
