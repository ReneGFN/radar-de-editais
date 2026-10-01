"""Prepara prévia privada das dez requisições, sem chamar API ou ler chave."""
import hashlib
import json
from datetime import datetime,timezone
from radar.config import PROJECT,private_root,emit_json
from radar.retrieval import retrieve_with_trace
from radar.citations import source_aliases,alias_schema
from radar.generation import SYSTEM,SCHEMA,MODEL

path=PROJECT/'datasets/evaluation/independent-bound-v1.json';reference=json.loads(path.read_text(encoding='utf-8'))
requests=[]
for case in reference['cases']:
    docs,trace=retrieve_with_trace(case['question'],reference['snapshot_id'],case['pncp_id'],
                                 query_profile='structured',context_profile='page_window')
    aliases=source_aliases(docs);reverse={v:k for k,v in aliases.items()}
    user={'question':case['question'],'documents':[{'chunk_id':reverse[d.metadata['id']],
          'page':d.metadata['page'],'document_sequence':d.metadata['document_sequence'],
          'content':d.page_content} for d in docs]}
    if len(json.dumps(user,ensure_ascii=False))>16000:raise ValueError('Context exceeds allowed size')
    system=SYSTEM.replace('um chunk_id e quote literal do contexto','um chunk_id do contexto')
    system+='\nNeste modo evidence contém somente chunk_id, sem quote. Selecione somente fontes que sustentem cada afirmação; o servidor exibirá a passagem original completa. Não reproduza nem abrevie citações no JSON.'
    requests.append({'case_id':case['id'],'user':user,'system':system,'schema':alias_schema(SCHEMA,aliases),
                     'source_alias_map':aliases,'source_metadata':[d.metadata for d in docs]})
private=private_root()/'generation/independent-request-preview-v1.json'
emit_json(private,{'state':'prepared_not_sent','endpoint':'https://api.groq.com/openai/v1/chat/completions',
                   'model':MODEL,'requests':requests,'groq_calls':0,'key_included':False})
code=['backend/src/radar/generation.py','backend/src/radar/citations.py','ops/evaluate-generation.py',
      'backend/src/radar/retrieval.py','backend/src/radar/query.py','backend/src/radar/context.py']
emit_json(PROJECT/'reports/independent-generation-plan-v1.json',{
    'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'state':'pending_specific_batch_authorization',
    'snapshot_id':reference['snapshot_id'],'reference_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'code_sha256':{p:hashlib.sha256((PROJECT/p).read_bytes()).hexdigest() for p in code},
    'preview_sha256':hashlib.sha256(private.read_bytes()).hexdigest(),'cases':len(requests),
    'max_public_passages_per_case':5,'model':MODEL,'variant':'alias_window','groq_calls':0,
    'endpoint':'https://api.groq.com/openai/v1/chat/completions','key_in_prompt':False,
    'gold_answer_in_prompt':False,'private_preview':'generation/independent-request-preview-v1.json',
    'scope':'ten_approved_independent_cases_not_the_previous_reserve_batch'})
print(json.dumps({'requests_prepared':len(requests),'groq_calls':0,'private_preview':str(private)}))
