# Design do chatbot — referência Moon Chat

Entrega local em 2026-10-05, aguardando revisão de Renê.

## Alterações e motivo

Aplicada a direção visual do componente Ruixen Moon Chat enviado pelo usuário: fundo lunar violeta, título centralizado, compositor escuro translúcido, botão claro e sugestões arredondadas. A seleção opcional de edital fica recolhível acima da pergunta; mensagens de conexão continuam visíveis fora desse controle. O campo cresce com o texto e a conversa reduz o espaço do cabeçalho.

React, TypeScript e CSS existentes foram suficientes; nenhuma dependência adicionada. Sugestões preenchem perguntas reais sem enviá-las automaticamente. Busca geral, seleção de edital, candidatos, referências e navegação ao painel foram preservados. O tema lunar aplica-se ao chat.

## Evidências e limites

- Build TypeScript/Vite e 15 testes de interface passaram após as alterações finais.
- npm audit: zero vulnerabilidades conhecidas; primeira tentativa bloqueada pela rede, repetição autorizada concluída.
- Navegador: escopo abriu/fechou; pergunta geral sobre prazo retornou esclarecimento e cinco candidatos com banco real, sem Groq. Navegação ao painel e retorno preservaram a conversa.
- Viewport móvel 390 × 844: largura do documento 375, sem rolagem horizontal. Captura desktop 1280 × 900 em [prévia](../reports/ui/chat-moon-2026-10-05.jpg); viewport restaurado.
- Busca de padrões de chave em fontes e build frontend não encontrou correspondências. Isso é uma verificação limitada, não garantia de ausência de todo segredo.
- Não houve nova avaliação de respostas, holdout, escrita no banco ou publicação. Os 270 testes backend da entrega anterior não foram repetidos porque o backend não mudou.
- Seletor semântico do summary não encontrou o controle; inspeção de acessibilidade e interação pelo controle exposto funcionaram. Pesquisa ampla de arquivos encontrou pastas temporárias sem acesso; não usadas como evidência.

## Imagem e publicação

Imagem da referência baixada do CDN 21st.dev e inspecionada, armazenada em `frontend/src/assets/moon-reference.png`; servida localmente pelo build, sem requisição ao CDN durante uso. Origem: https://cdn.21st.dev/assets/mirror/c3/c333918af688a4a8a3d004652e6c0ee219457a9d84d380eeb31f513d4b59a09f.png

PNG 6670 × 3752, 5.606.532 bytes. SHA256: `c333918af688a4a8a3d004652e6c0ee219457a9d84d380eeb31f513d4b59a09f`. Licença não fornecida/verificada; a entrega é para revisão local. Antes de publicar, confirmar direitos de uso ou substituir a imagem e otimizar seu tamanho. Bundle JavaScript 248,69 kB (77,09 kB gzip), CSS 12,01 kB (3,35 kB gzip). Sem medição de Core Web Vitals nesta etapa.

## Checklist de segurança — dez grupos

1. **Segredos:** inspeção de padrões em fontes/build sem correspondências; nenhum valor de credencial registrado, chave permanece no serviço privado.
2. **Superfície e rede:** proxy e API local preservados; imagem incluída no build, sem novo serviço externo no navegador.
3. **Entradas:** limite de pergunta e validações existentes preservados; testes de interface passaram. Não houve alteração no esquema do servidor.
4. **Dados e isolamento:** escopo opcional preservado; pergunta geral verificou esclarecimento. Holdout não utilizado e banco somente consultado.
5. **Injeções e saída:** renderização React e restrições de links existentes preservadas e cobertas pela suíte; não houve nova auditoria do prompt/modelo.
6. **Privacidade e registros:** conversa transitória existente, sem nova persistência ou analytics; captura contém interface e dados públicos.
7. **Identidade e acesso:** não aplicável à alteração visual: sem autenticação ou permissões novas. Não certifica acesso de produção.
8. **Integridade e recuperação:** sem migração/escrita de dados; backup/restauração não reexecutados nesta etapa.
9. **Dependências e qualidade:** nenhuma dependência nova, build/15 testes/audit concluídos. Peso da imagem é pendência de desempenho.
10. **Transporte e publicação:** origem HTTPS da imagem e arquivo local no frontend; política existente preservada. Sem publicação/TLS de produção avaliados; direitos da imagem pendentes.

## Próximo passo

Aguardar aprovação visual. Depois, retomar a proposta de teste de pergunta aprovada pela interface com Groq e conferência das fontes, observando a autorização aplicável.
