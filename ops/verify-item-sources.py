"""Confere todas as fontes da prévia com PostgreSQL real, sem publicar texto bruto."""
import json,hashlib
from radar.config import PROJECT,private_root,emit_json
from radar.storage import connect
path=private_root()/'generation/item-validation-request-preview-v2.json';preview=json.loads(path.read_text(encoding='utf-8'));checked=0
with connect() as conn:
 conn.execute('SET TRANSACTION READ ONLY')
 role=conn.execute('SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user').fetchone()
 if any(role):raise ValueError('Loader role has excess privileges')
 for request in preview['requests']:
  docs=request['user']['documents'];metas=request['source_metadata'];aliases=request['source_alias_map']
  if not 1<=len(docs)<=5 or len(docs)!=len(metas):raise ValueError('Source count mismatch')
  for document,meta in zip(docs,metas):
   if aliases[document['chunk_id']]!=meta['id']:raise ValueError('Alias mismatch')
   row=conn.execute("SELECT p.text,d.source->>'url' FROM radar.pages p JOIN radar.documents d ON d.snapshot_id=p.snapshot_id AND d.pncp_id=p.pncp_id AND d.sequence=p.document_sequence WHERE p.snapshot_id=%s AND p.pncp_id=%s AND p.document_sequence=%s AND p.page=%s",('1446c44aca18011a',meta['pncp_id'],meta['document_sequence'],meta['page'])).fetchone()
   if not row or not 0<=meta['start']<meta['end']<=len(row[0]) or row[0][meta['start']:meta['end']]!=document['content'] or row[1]!=meta['url']:raise ValueError('Literal source mismatch')
   if len(document['content'])>2000:raise ValueError('Context bound exceeded')
   for quantity in meta.get('quantity_candidates',[]):
    if not meta['start']<=quantity['start']<quantity['end']<=meta['end'] or row[0][quantity['start']:quantity['end']]!=quantity['quote']:raise ValueError('Quantity mismatch')
   checked+=1
emit_json(PROJECT/'reports/item-source-verification-v2.json',{'snapshot_id':'1446c44aca18011a','requests':len(preview['requests']),'sources_verified':checked,'literal_offsets':'passed','quantities':'passed','aliases':'passed','loader_privilege_flags':list(role),'transaction':'read_only','preview_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'database_writes':0,'groq_calls':0,'semantic_identity':'not_certified_by_literal_check'})
print(json.dumps({'requests':len(preview['requests']),'sources_verified':checked,'passed':True}))
