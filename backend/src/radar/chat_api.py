"""API de chat local sem CORS; usar proxy de mesma origem na futura tela."""
import json
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator, field_validator
from starlette.concurrency import run_in_threadpool

from .api import SECURITY_HEADERS
from .chat import ChatFailure, ChatService, purchase_parts
from .discovery import SNAPSHOT, allowed_editais

MAX_BODY = 12000
ORIGINS = {'http://127.0.0.1:5173','http://localhost:5173',
           'http://127.0.0.1:8766','http://localhost:8766'}


class DocumentSelection(BaseModel):
    model_config = ConfigDict(extra='forbid',strict=True)
    pncp_id: str = Field(max_length=40)
    document_sequence: int = Field(ge=1)


class Question(BaseModel):
    model_config = ConfigDict(extra='forbid',strict=True)
    question: str = Field(min_length=1,max_length=2000)
    pncp_id: str | None = Field(default=None,max_length=40)

    documents: list[DocumentSelection] | None = Field(default=None,min_length=1,max_length=5)

    @model_validator(mode='after')
    def scope_exclusive(self):
        if self.documents and self.pncp_id: raise ValueError('Escolha um único tipo de escopo')
        if self.documents and len({(d.pncp_id,d.document_sequence) for d in self.documents}) != len(self.documents): raise ValueError('PDF duplicado')
        return self

    @field_validator('question')
    @classmethod
    def nonempty(cls,value):
        if not value.strip():
            raise ValueError('Pergunta vazia')
        return value


class StrictOutput(BaseModel):
    model_config = ConfigDict(extra='forbid',strict=True)


class Candidate(StrictOutput):
    pncp_id: str
    agency: str
    uf: str | None
    document_sequence: int
    page: int
    url: str


class Source(Candidate):
    index: int
    quote: str


class Claim(StrictOutput):
    text: str
    source_indices: list[int]


class Confidence(StrictOutput):
    level: Literal['unavailable','review_required']
    label: str
    reasons: list[str]
    calibrated: Literal[False]


class Reply(StrictOutput):
    confidence: Confidence
    snapshot_id: str
    scope: Literal['selected','development','documents']
    candidates: list[Candidate]
    exhaustive: Literal[False]
    status: Literal['answered','refused','insufficient_evidence','needs_clarification',
                    'discovery_only','no_candidates']
    answer: str
    claims: list[Claim]
    sources: list[Source]
    semantic_support: Literal['requires_review','not_evaluated']


def create_app(*, free_plan_confirmed=False, rerank_profile="none"):
    app = FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
    app.state.chat = ChatService(free_plan_confirmed=free_plan_confirmed,rerank_profile=rerank_profile)

    @app.middleware('http')
    async def boundary(request, call_next):
        host = request.headers.get('host','')
        origin = request.headers.get('origin')
        if host not in {'127.0.0.1:8766','localhost:8766'} or (origin is not None and origin not in ORIGINS):
            response = JSONResponse({'detail':'Origem não permitida'},status_code=403)
        elif request.method not in ('GET','POST'):
            response = JSONResponse({'detail':'Método não permitido'},status_code=405)
        elif request.method=='POST' and request.headers.get('x-radar-chat')!='1':
            response = JSONResponse({'detail':'Cabeçalho de consulta ausente'},status_code=403)
        else:
            try:
                response = await call_next(request)
            except Exception:
                response = JSONResponse({'detail':'Serviço indisponível'},status_code=503)
        response.headers.update(SECURITY_HEADERS)
        return response

    @app.get('/chat/health')
    def health():
        return {'status':'service_running','snapshot_id':SNAPSHOT,
                'generation_enabled':app.state.chat.free_plan_confirmed,
                'dependencies_checked':False,'rerank_profile':app.state.chat.rerank_profile}

    @app.get('/chat/editais')
    def editais():
        result=[]
        for key,e in sorted(allowed_editais().items()):
            cnpj,year,sequence=purchase_parts(key)
            result.append({'pncp_id':key,'agency':e['agency'],'uf':e.get('uf'),'object':e.get('object',''),
                           'official_url':f'https://pncp.gov.br/app/editais/{cnpj}/{year}/{sequence}'})
        return result

    @app.get('/chat/explore')
    def explore():
        from .atlas import explore_catalog
        return explore_catalog()

    @app.post('/chat/ask',response_model=Reply)
    async def ask(request:Request):
        if request.headers.get('content-type','').split(';')[0].strip().lower()!='application/json':
            return JSONResponse({'detail':'Envie JSON'},status_code=415)
        body = bytearray()
        try:
            length = request.headers.get('content-length')
            if length is not None and (int(length)<0 or int(length)>MAX_BODY):
                return JSONResponse({'detail':'Corpo excede o limite'},status_code=413)
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body)>MAX_BODY:
                    return JSONResponse({'detail':'Corpo excede o limite'},status_code=413)
            value = Question.model_validate(json.loads(body))
            if value.pncp_id is not None and value.pncp_id not in allowed_editais():
                return JSONResponse({'detail':'Contratação não permitida'},status_code=422)
        except (ValueError,ValidationError,UnicodeDecodeError):
            return JSONResponse({'detail':'Pergunta ou JSON inválido'},status_code=422)
        try:
            return await run_in_threadpool(app.state.chat.ask,value.question,value.pncp_id,**({'document_scope':[d.model_dump() for d in value.documents]} if value.documents else {}))
        except ChatFailure as exc:
            return JSONResponse({'detail':str(exc)},status_code=exc.status)

    return app


app = create_app()
