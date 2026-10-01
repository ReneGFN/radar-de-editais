"""Publica resultados iniciais e regressões, sem ajustar busca às perguntas."""
import json
import hashlib
from radar.config import PROJECT,emit_json

parent=json.loads((PROJECT/'reports/retrieval-growth-parent-v1.json').read_text(encoding='utf-8'))
pilot=json.loads((PROJECT/'reports/retrieval-growth-pilot-v1.json').read_text(encoding='utf-8'))
new=json.loads((PROJECT/'reports/retrieval-growth-independent-v1.json').read_text(encoding='utf-8'))
frozen=json.loads((PROJECT/'reports/independent-retrieval-protocol-v1.json').read_text(encoding='utf-8'))
for name,digest in frozen['sha256'].items():
    if hashlib.sha256((PROJECT/name).read_bytes()).hexdigest()!=digest:
        raise ValueError('Frozen protocol code/reference changed: '+name)
changes={}
for mode in parent['results']:
    before={r['case_id']:r for r in parent['results'][mode]}
    changes[mode]=[r['case_id'] for r in pilot['results'][mode]
                   if [(m['id'],m['page'],m['start'],m['end']) for m in r['retrieved']]
                   !=[(m['id'],m['page'],m['start'],m['end']) for m in before[r['case_id']]['retrieved']]]
report={'parent_snapshot':parent['snapshot_id'],'candidate_snapshot':pilot['snapshot_id'],
        'first_run_frozen_hashes_verified':True,'evaluation_queries':210,
        'historical_rank_changes':changes,'historical_summary':pilot['summary'],
        'independent_summary':new['summary'],
        'independent_fully_covered_cases':{mode:[r['case_id'] for r in rows if r['all_known_quotes_supported_at_k']]
                                             for mode,rows in new['results'].items()},
        'primary_metric':'known_literal_quote_coverage_not_generated_answer_accuracy',
        'limitations':['selected_edital_scope_not_global_discovery','10_new_cases_6_new_documents',
                       'representative_chunk_anchor_hit_not_exhaustive_recall','one_run_no_latency_causal_claim',
                       'generation_and_refusals_not_evaluated','larger_sample_and_human_answer_review_pending'],
        'release_decision':'candidate_not_promoted','human_answer_accuracy':None,'groq_calls':0}
emit_json(PROJECT/'reports/retrieval-growth-comparison-v1.json',report)
print(json.dumps({'rank_changes':changes,'new_full_quote_coverage':{m:s['all_known_quotes_supported_at_5'] for m,s in new['summary'].items()}}))
