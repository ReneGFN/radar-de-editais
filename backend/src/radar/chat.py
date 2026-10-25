"""Serviço de perguntas: escopo antes da geração; saídas públicas explícitas."""
import re
import threading
from time import monotonic

from .discovery import SNAPSHOT, allowed_editais, discover
from .generation import answer
from .guardrails import input_reason, evidence_confidence


class ChatFailure(RuntimeError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def purchase_parts(pncp_id):
    match=re.fullmatch(r'(\d{14})-1-(\d{6})/(\d{4})',pncp_id)
    if not match:
        raise ValueError('Identificador PNCP inválido')
    cnpj, sequence, year=match.groups()
    return cnpj,year,int(sequence)


def official_document(catalog, pncp_id, sequence):
    edital = catalog[pncp_id]
    if not any(d['sequence']==sequence for d in edital['documents']):
        raise ValueError('Documento fora do catálogo')
    cnpj,year,purchase_sequence=purchase_parts(pncp_id)
    return (f"https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/"
            f"{year}/{purchase_sequence}/arquivos/{sequence}")


def public_answer(result, catalog, pncp_id, document_scope=None):
    """Lista permitida de campos; nunca repassa trace, aliases ou erro do provedor."""
    if result['status'] not in ('answered','refused','insufficient_evidence'):
        raise ValueError('Estado inválido')
    sources, indices = [], {}
    for citation in result['citations']:
        permitted = (citation['pncp_id'], citation['document_sequence']) in {(d['pncp_id'],d['document_sequence']) for d in document_scope} if document_scope else citation['pncp_id'] == pncp_id
        if not permitted or citation['page']<1:
            raise ValueError('Fonte fora do escopo')
        identity = (citation['id'], citation['quote'])
        if identity in indices:
            continue
        indices[identity] = len(sources)+1
        sources.append({'index':len(sources)+1,'pncp_id':citation['pncp_id'],
                        'agency':catalog[citation['pncp_id']]['agency'],'uf':catalog[citation['pncp_id']].get('uf'),
                        'document_sequence':citation['document_sequence'],'page':citation['page'],
                        'quote':citation['quote'],
                        'url':official_document(catalog,citation['pncp_id'],citation['document_sequence'])})
    claims = [{'text':c['text'],'source_indices':list(dict.fromkeys(
        indices[(e['chunk_id'],e['quote'])] for e in c['evidence']))} for c in result['claims']]
    if result['status']=='answered' and (not claims or any(not c['source_indices'] for c in claims)):
        raise ValueError('Resposta sem fonte')
    output = {'status':result['status'],'answer':result['answer'],'claims':claims,'sources':sources,
              'semantic_support':'requires_review'}
    # Também examina passagens literais, que não passaram pelo filtro do texto final.
    strings = [output['answer']] + [s['quote'] for s in sources]+[c['text'] for c in claims]
    if any(not isinstance(s,str) or len(s)>16000 or
           re.search(r'\b(?:gsk_|sk-|ghp_)[A-Za-z0-9_-]{20,}',s) for s in strings):
        raise ValueError('Conteúdo não publicável')
    return output


class ChatService:
    def __init__(self, *, free_plan_confirmed=False, rerank_profile="none"):
        if rerank_profile not in ("none", "coverage_v1"):
            raise ValueError("Perfil de reranking inválido")
        self.rerank_profile = rerank_profile
        self.free_plan_confirmed = free_plan_confirmed
        self.lock = threading.Lock()
        self.last_generation = None

    def ask(self, question, pncp_id=None, document_scope=None):
        if not self.lock.acquire(blocking=False):
            raise ChatFailure(429,'Há uma consulta em andamento. Tente novamente depois.')
        try:
            catalog = allowed_editais()
            if document_scope is not None:
                if pncp_id or not 1 <= len(document_scope) <= 5: raise ChatFailure(422,'Selecione de um a cinco PDFs.')
                for d in document_scope:
                    if d['pncp_id'] not in catalog or not any(f['sequence'] == d['document_sequence'] for f in catalog[d['pncp_id']]['documents']):
                        raise ChatFailure(422,'PDF fora do catálogo permitido.')
            reason = input_reason(question)
            if reason:
                return {'snapshot_id':SNAPSHOT,'scope':'documents' if document_scope else 'selected' if pncp_id else 'development','candidates':[], 'exhaustive':False,'status':'refused','answer':reason,'claims':[],'sources':[], 'semantic_support':'not_evaluated','confidence':evidence_confidence('refused',[])}
            discovery = {'scope':'documents','candidates':[], 'routing':{'status':'scoped','pncp_id':document_scope[0]['pncp_id']}} if document_scope else discover(question,pncp_id)
            candidates = [{'pncp_id':c['pncp_id'],'agency':c['agency'],'uf':c.get('uf'),
                           'document_sequence':c['document_sequence'],'page':c['page'],
                           'url':official_document(catalog,c['pncp_id'],c['document_sequence'])}
                          for c in discovery['candidates']]
            route = discovery['routing']
            base = {'snapshot_id':SNAPSHOT,'scope':discovery['scope'],'candidates':candidates,
                    'exhaustive':False}
            if route['status']!='scoped':
                return dict(base,status=route['status'],answer=route['message'],claims=[],sources=[],
                            semantic_support='not_evaluated',confidence=evidence_confidence(route['status'],[]))
            if not self.free_plan_confirmed:
                raise ChatFailure(503,'Inicie o serviço com confirmação do plano gratuito para gerar respostas.')
            if self.last_generation is not None and monotonic()-self.last_generation<35:
                raise ChatFailure(429,'Aguarde 35 segundos entre chamadas ao modelo.')
            self.last_generation = monotonic()
            resolved = route['pncp_id']
            extra = {'document_scope':document_scope} if document_scope else {}
            result = answer(question,SNAPSHOT,resolved,free_plan_confirmed=True,
                            context_profile='item_structure',citation_mode='source_alias',prompt_version='v1',rerank_profile=self.rerank_profile,guardrails=True,**extra)
            public = public_answer(result,catalog,resolved,document_scope)
            public['confidence'] = evidence_confidence(public['status'],public['sources'],bool(pncp_id or document_scope))
            return dict(base,**public)
        except ChatFailure:
            raise
        except Exception:
            # Não exportar mensagens de banco/SDK, caminhos, payloads ou credenciais.
            raise ChatFailure(503,'Não foi possível concluir a consulta. Tente novamente depois.') from None
        finally:
            self.lock.release()
