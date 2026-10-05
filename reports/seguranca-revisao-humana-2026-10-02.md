# Revisão de segurança — revisão humana e amostra independente — 2026-10-02

Escopo: `backend/src/radar/human_review.py`, `backend/src/radar/independence.py`, `ops/human-review.py`, `ops/plan-holdout-corpus.py`, os novos relatórios em `reports/` e a documentação. Não houve chamada à Groq, escrita no banco, alteração de Docker, volume ou credencial.

| Grupo | Situação | Limitação |
|---|---|---|
| 1. Segredos e dados | Verificado. Nenhum arquivo novo lê `secrets/`. Os resumos públicos foram percorridos por código: nenhuma chave `answer`, `quote`, `claims`, `citations`, `notes_private`, `reviewer`, `text` ou `question`. Teste automático barra `PRIVATE_` e o nome do revisor no resumo. As fichas com notas ficam no diretório privado. A prévia privada da Groq foi conferida por padrão `gsk_` sem ocorrência e `key_included=false`. | Hash da resposta é público. É SHA-256 de um JSON longo, sem valor prático para reconstruir o texto, mas permite confirmar uma resposta se alguém já tiver o texto. |
| 2. API/frontend | Não aplicável: nenhuma API ou interface nova. Proposta em `docs/proposta-api-painel.md` é somente leitura e estática. | Controles da proposta não implementados nem testados. |
| 3. Entradas | Verificado. A ficha é validada contra referência e checkpoint: casos na mesma ordem, critérios só `true/false/null`, etiquetas de lista fechada, data ISO não futura, nota privada até 2.000 caracteres. A resposta da API do PNCP passa por `safe_url` (só `https://pncp.gov.br`, porta descartada) e é guardada como dado, nunca executada. Objeto truncado em 300 caracteres. | Texto dos editais continua não confiável; a triagem por palavra-chave pode aceitar objeto fora do escopo (três candidatos marcados). |
| 4. Autorização | Verificado no escopo. `reviewer_kind` precisa ser `human`, e nomes de agentes são recusados. Casos não gerados não aceitam nota. Revisão parcial vira `pending` no gate. | É uma declaração: o código não autentica quem preencheu a ficha. |
| 5. Ataques comuns | Verificado. Path traversal: `summarize` só grava dentro de `reports/`. Sobrescrita: `init` recusa ficha existente e `refresh` guarda a anterior com carimbo de hora. Reaplicar nota antiga a resposta nova: bloqueado pelo hash. Vazamento entre conjuntos: `check_holdout`. | Sem proteção contra quem edite o JSON privado à mão de má-fé; o modelo de ameaça é erro, não fraude. |
| 6. Logs | Verificado. Os scripts imprimem só nomes de arquivo, contagens e estados. Erros do PNCP guardam tipo e código HTTP, sem corpo de resposta. | — |
| 7. Senhas | Não aplicável: nenhum código novo usa senha. Banco não acessado nesta etapa. | — |
| 8. Backup | Parcial. `refresh` mantém a ficha anterior. Fichas privadas não entram no backup do banco; dependem do backup do diretório privado. | O diretório privado está dentro do armazenamento do app Codex (ver observação abaixo). Não foi verificado se existe cópia fora dele. |
| 9. Dependências | Verificado. Nenhuma dependência nova. `pip-audit` em 2026-10-02: nenhuma vulnerabilidade conhecida nos pacotes auditáveis; o pacote local editável não é auditável no PyPI. | Auditoria pontual, não contínua. |
| 10. HTTPS | Verificado. Todas as chamadas ao PNCP usam HTTPS com redirecionamento manual restrito à mesma origem (`follow_redirects=False`). Nenhuma chamada à Groq nesta etapa. | Certificado e TLS são os padrões do httpx; não houve teste de interceptação. |

## Observação sobre o diretório privado

`RADAR_PRIVATE_ROOT` não está definido. O padrão é `%LOCALAPPDATA%\RadarDeEditais`, mas o app Codex do Windows é empacotado (MSIX), e o Windows redireciona as gravações dele em `AppData\Local` para `AppData\Local\Packages\OpenAI.Codex_<id>\LocalCache\Local\RadarDeEditais`. Fora do Codex, `%LOCALAPPDATA%\RadarDeEditais` não existe. O contêiner do banco declara a senha a partir desse caminho não virtualizado; não foi verificado como o Docker Desktop o resolve (o banco já inicializado continua saudável). Consequências observadas e prováveis:

- outro cliente (este, por exemplo) não encontra os dados sem apontar `RADAR_PRIVATE_ROOT` explicitamente;
- desinstalar ou redefinir o app Codex pode apagar PDFs, vetores, checkpoints, respostas e backups;
- `config.private_root()` continua recusando caminhos dentro do Brain e do OneDrive, e o caminho virtualizado passa nessa regra.

Recomendação: definir `RADAR_PRIVATE_ROOT` como variável de usuário para um caminho fixo fora do OneDrive e copiar para lá (copiar, sem mover, até conferir os hashes). Isso não foi feito, porque mexe em dados privados e na montagem do segredo do banco. A decisão é de Renê.
