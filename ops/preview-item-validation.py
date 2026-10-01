"""Prévia privada dos lotes aprovados para etapa2; não lê chave nem chama Groq."""
import json,hashlib
from radar.config import PROJECT,private_root,emit_json
from radar.retrieval import retrieve_with_trace
from radar.citations import source_aliases,alias_schema
from radar.generation import SYSTEM,SCHEMA,MODEL
refs=['pilot-candidate-v1.json','independent-bound-v1.json'];requests=[];hashes={}
for name in refs:
 path=PROJECT/'datasets/evaluation'/name;raw=path.read_bytes();ref=json.loads(raw);hashes[name]=hashlib.sha256(raw).hexdigest()
 for case in ref['cases']:
  docs,trace=retrieve_with_trace(case['question'],ref['snapshot_id'],case['pncp_id'],context_profile='item_structure')
  aliases=source_aliases(docs);reverse={v:k for k,v in aliases.items()}
  context=[]
  for d in docs:
   m=d.metadata
   context.append({'chunk_id':reverse[m['id']],'page':m['page'],'document_sequence':m['document_sequence'],'content':d.page_content,'item_context':{k:m[k] for k in ('item_number','item_header_page','item_header_start','item_recognition','item_continuation','quantity_candidates') if k in m}})
  user={'question':case['question'],'documents':context}
  if len(json.dumps(user,ensure_ascii=False))>16000:raise ValueError('Context exceeds allowed size')
  system=SYSTEM.replace('um chunk_id e quote literal do contexto','um chunk_id do contexto')
  system+='\nNeste modo evidence contém somente chunk_id, sem quote. Selecione somente fontes que sustentem cada afirmação; o servidor exibirá a passagem original completa. Não reproduza nem abrevie citações no JSON.'
  requests.append({'case_id':case['id'],'user':user,'system':system,'schema':alias_schema(SCHEMA,aliases),'source_alias_map':aliases,'source_metadata':[d.metadata for d in docs]})
preview=private_root()/'generation/item-validation-request-preview-v2.json'
emit_json(preview,{'model':MODEL,'requests':requests,'groq_calls':0,'key_included':False})
paths=['backend/src/radar/generation.py','backend/src/radar/retrieval.py','backend/src/radar/item_structure.py','backend/src/radar/citations.py','ops/evaluate-generation.py']
emit_json(PROJECT/'reports/item-generation-protocol-v2.json',{'state':'prepared_before_execution','model':MODEL,'endpoint':'https://api.groq.com/openai/v1/chat/completions','variant':'alias_items','cases':len(requests),'max_passages':5,'reference_sha256':hashes,'preview_sha256':hashlib.sha256(preview.read_bytes()).hexdigest(),'code_sha256':{f:hashlib.sha256((PROJECT/f).read_bytes()).hexdigest() for f in paths},'authorization_basis':'prior_explicit_40_pilot_and_10_new_cases_Groq_authorizations_plus_user_approved_stage2_retesting_same_questions_public_sources','free_plan':'previously_user_confirmed','key_in_prompt':False,'gold_in_prompt':False,'human_accuracy':None})
print(json.dumps({'requests_prepared':len(requests),'groq_calls':0}))
