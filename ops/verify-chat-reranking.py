"""Comparação pareada no desenvolvimento; sem Groq ou holdout."""
import json
from pathlib import Path
from time import perf_counter
from statistics import median
from radar.config import emit_json
from radar.retrieval import retrieve_with_trace
from radar.reranking import rerank_documents
from radar.evaluation import score_case
from radar.discovery import SNAPSHOT

root=Path(__file__).resolve().parents[1]
rows=[]
for name in ('pilot-v2.json','independent-bound-v1.json'):
    data=json.loads((root/'datasets/evaluation'/name).read_text(encoding='utf-8'))
    for case in data['cases']:
        if case['kind']!='answerable' or case['review_status']!='approved':continue
        case=dict(case,evidence_format=data.get('evidence_format'))
        docs,trace=retrieve_with_trace(case['question'],SNAPSHOT,case['pncp_id'],context_profile='item_structure')
        started=perf_counter();ranked=rerank_documents(docs,case['question']);elapsed=(perf_counter()-started)*1000
        assert {d.metadata['id'] for d in docs}=={d.metadata['id'] for d in ranked}
        rows.append({'case_id':case['id'],'baseline':score_case(case,docs),'reranked':score_case(case,ranked),'rerank_ms':elapsed})
        print('casos:',len(rows),flush=True)
summary={name:{'all_quotes':sum(r[name]['all_known_quotes_supported_at_k'] for r in rows),'some_quote':sum(r[name]['some_known_quote_supported_at_k'] for r in rows),'mrr':sum(r[name]['reciprocal_rank_at_k'] for r in rows)/len(rows)} for name in ('baseline','reranked')}
emit_json(root/'reports/chat-reranking-2026-10-05.json',{'snapshot':SNAPSHOT,'cases':len(rows),'holdout_used':False,'groq_calls':0,'summary':summary,'rerank_ms_median':median(r['rerank_ms'] for r in rows),'rows':rows})
print(summary)
