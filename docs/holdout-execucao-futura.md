# Holdout: fluxo de execução futura (preparado, não executado)

Estado em 2026-10-03: os 46 casos de `datasets/holdout/holdout-v1-draft.json` estão em `pending_user_approval`. A aprovação em bloco congelada em `holdout-v1.json` foi revogada (`holdout-v1-approval-revocation.json`). Nada foi indexado, recuperado, embutido, gravado no PostgreSQL ou enviado à Groq.

## Script

`ops/holdout-pipeline.py <etapa> <referência>`. Toda etapa roda primeiro a pré-checagem e recusa se houver qualquer bloqueio.

| Etapa | O que faz | Exige |
|---|---|---|
| `precheck` | só leitura: aprovação, independência (PNCP, URL, hash de PDF, pergunta igual/reescrita), URL HTTPS do PNCP, hash dos PDFs privados, URL/página/offsets das evidências, trecho no offset do texto privado | nada |
| `freeze` | protocolo público `reports/holdout-protocol-<ref>.json` com hashes de 9 arquivos de código, referência, manifesto, modelo, prompt, configuração de recuperação e snapshot planejado; nunca sobrescreve | pré-checagem limpa |
| `index` | manifesto do snapshot em `datasets/holdout/snapshot-<id>.json` (fora de `datasets/manifests/`, que é desenvolvimento), `prepare` e `load_corpus` | protocolo igual ao código atual + `--confirm-index` |
| `preview` | prévia privada com o mesmo contexto que `answer()` monta; recusa se um gabarito aparecer no prompt; sem chave | protocolo + snapshot |
| `generate` | uma tentativa por caso, `max_retries=0`, intervalo ≥ 30 s, checkpoint privado; não repete casos aceitos nem barrados; para no primeiro 429 | `--confirm-free-plan` + `--max-calls N` |
| `report` | `reports/holdout-execution-<ref>.json` só com contagens, estados, tokens e latências | checkpoint |

Snapshot planejado para o rascunho atual: `cba6ca6ee0647e54`, calculado só dos ids/hashes/URLs; ele muda se o manifesto mudar e nunca pode ser `1446c44aca18011a` (o script recusa a colisão).

## Pré-checagem executada (só leitura)

- Rascunho: `ready: false`, 47 bloqueios (46 casos não aprovados + status de rascunho). Independente, PDFs presentes com hash correto, trechos nos offsets. Relatório: `reports/holdout-precheck-v1-draft.json`.
- Arquivo revogado `holdout-v1.json`: `ready: false`, único bloqueio `reference_approval_revoked`.
- `freeze` no rascunho foi recusado, como esperado.

## Testes

`backend/tests/test_holdout_pipeline.py`, 15 testes: caso pendente bloqueia; revogação e status de rascunho bloqueiam; aprovado sem registro humano bloqueia; só URLs HTTPS do PNCP; PDF ausente ou alterado bloqueia; URL/página/offset das evidências; snapshot determinístico e nunca o de desenvolvimento; protocolo recusa mudança de código ou referência; retomada sem repetir aceitos/barrados, parada no 429 e limite de chamadas.

## Limitações

- `index`, `preview` e `generate` não foram exercitados contra banco ou Groq (proibido até a aprovação). Usam as mesmas funções do desenvolvimento (`prepare`, `load_corpus`, `retrieve_with_trace`, `answer`), mas a integração no holdout só será verificada na primeira execução.
- A variante do holdout é escolhida no `freeze` (`alias_items` por padrão; `alias_items_v3` disponível). Hoje o padrão é `alias_items`.

## Para executar depois

1. Renê aprova os 46 casos (ou corrige/descarta mantendo ≥ 30 factuais, 10 recusas, 10 contratações); gera-se um arquivo aprovado novo com hash próprio.
2. `precheck` → `freeze` → `index --confirm-index` → `preview`; Renê confere a prévia e autoriza as chamadas.
3. `generate --confirm-free-plan --max-calls N`, depois revisão humana com `ops/human-review.py` e `report`.
