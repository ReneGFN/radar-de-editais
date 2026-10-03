"""API local, somente leitura, do painel do Radar de Editais.

- Lê apenas `radar.public_data` (relatórios e referências publicáveis). Não importa
  banco, Groq, embeddings nem o diretório privado.
- Só rotas GET; sem CORS (o painel usa o mesmo origin via proxy do Vite).
- Esquemas de saída com `extra='forbid'`: um campo novo e inesperado falha a resposta.
- Cabeçalhos de segurança em toda resposta; documentação interativa desligada
  (ela carregaria scripts de terceiros).
- Iniciar com `ops/serve-api.py`, que só aceita 127.0.0.1.
"""
from typing import Literal

from fastapi import FastAPI, HTTPException, Path, Request
from pydantic import BaseModel, ConfigDict

from . import public_data

VariantId = Literal['alias_items', 'alias_items_v2', 'alias_items_v3']
SECURITY_HEADERS = {
    'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
    'X-Frame-Options': 'DENY', 'Cache-Control': 'no-store', 'Cross-Origin-Resource-Policy': 'same-origin'}


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Human(Strict):
    answerable_reviewed: int
    answerable_cases: int
    answerable_all_criteria_true: int
    refusals_reviewed: int
    refusals_cases: int
    refusals_all_criteria_true: int
    rate_available: bool
    error_tag_counts: dict[str, int]


class Findings(Strict):
    fixed: list[str]
    blocked_safely_still_wrong: list[str]
    still_failing: list[str]
    regressions_vs_default: list[str]


class Version(Strict):
    id: VariantId
    label: str
    role: str
    status: str
    is_default: bool
    promoted: bool
    factual_answered_of_40: int
    input_tokens_total: int
    input_tokens_counted_cases: int
    generation_ms_median: float
    total_ms_median: float
    human: Human | None
    findings: Findings | None


class DecisionRecord(Strict):
    date: str
    basis: list[str]
    reason: str


class Versions(Strict):
    default_variant: VariantId
    decision_record: DecisionRecord
    metric_caveats: list[str]
    versions: list[Version]


class Metrics(Strict):
    input_tokens: float | None
    output_tokens: float | None
    generation_ms: float | None
    total_ms: float | None


class CompareCase(Strict):
    case_id: str
    kind: str
    category: str | None
    state_a: str
    state_b: str
    technical_change: str
    human_a: str
    human_b: str
    human_pass_a: bool | None
    human_pass_b: bool | None
    human_change: str
    metrics_a: Metrics | None
    metrics_b: Metrics | None


class Comparison(Strict):
    a: VariantId
    b: VariantId
    retrieval_changed: bool
    holdout_used: bool
    factual_answered: dict[str, int]
    aggregate: dict[str, dict[str, dict[str, float | int | None]]]
    regressions: list[str]
    improvements: list[str]
    cases: list[CompareCase]
    note: str


class CaseSummary(Strict):
    id: str
    set: str
    kind: str
    category: str | None
    pncp_id: str
    states: dict[str, str]
    human: dict[str, str]
    human_pass: dict[str, bool | None]


class Source(Strict):
    document_sha256: str
    document_sequence: int | None
    page: int
    url: str


class VariantState(Strict):
    technical_state: str
    human_status: str
    human_pass: bool | None
    criteria: dict[str, bool | None] | None
    error_tags: list[str]


class CaseDetail(Strict):
    id: str
    set: str
    kind: str
    category: str | None
    pncp_id: str
    question: str
    expected_answer: str | None
    sources: list[Source]
    variants: dict[str, VariantState]


class HoldoutState(Strict):
    cases: int
    cases_pending_user_approval: int
    status: str
    executed: bool


class Quality(Strict):
    decision: str
    target: float
    target_status: str
    default_variant: VariantId
    criteria_met: list[str]
    blockers: list[str]
    previous_gate_reasons: list[str]
    holdout: HoldoutState
    holdout_requirements: list[str]
    development_set_note: str
    guarantee: str


class CorpusTotals(Strict):
    snapshot_id: str | None
    editais: int
    documents: int
    pages: int
    chunks: int | None = None
    status: str | None = None


class UfRow(Strict):
    role: str
    region: str
    uf: str | None
    editais: int
    documents: int
    pages: int | None
    pages_known: bool


class Edital(Strict):
    pncp_id: str
    uf: str | None
    region: str
    role: str
    documents: int
    pages: int | None
    official_url: str | None
    document_urls: list[str]


class Corpus(Strict):
    development: CorpusTotals
    holdout: CorpusTotals
    by_uf: list[UfRow]
    editais: list[Edital]
    note: str


app = FastAPI(title='Radar de Editais (somente leitura)', docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware('http')
async def security_headers(request: Request, call_next):
    if request.method not in ('GET', 'HEAD'):
        from fastapi.responses import JSONResponse
        response = JSONResponse({'detail': 'somente leitura'}, status_code=405)
    else:
        response = await call_next(request)
    response.headers.update(SECURITY_HEADERS)
    return response


@app.get('/api/versions', response_model=Versions)
def get_versions():
    return public_data.versions()


@app.get('/api/versions/{a}/compare/{b}', response_model=Comparison)
def get_compare(a: VariantId, b: VariantId):
    try:
        return public_data.compare(a, b)
    except KeyError:
        raise HTTPException(404, 'comparação inexistente') from None


@app.get('/api/cases', response_model=list[CaseSummary])
def get_cases():
    return public_data.cases()


@app.get('/api/cases/{case_id}', response_model=CaseDetail)
def get_case(case_id: str = Path(pattern=r'^(pilot|independent)-\d{2}$', max_length=16)):
    try:
        return public_data.case(case_id)
    except KeyError:
        raise HTTPException(404, 'caso inexistente') from None


@app.get('/api/quality', response_model=Quality)
def get_quality():
    return public_data.quality()


@app.get('/api/corpus', response_model=Corpus)
def get_corpus():
    return public_data.corpus()
