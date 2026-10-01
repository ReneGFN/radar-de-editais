"""Registra código/configuração antes da primeira recuperação independente."""
import hashlib
from datetime import datetime,timezone
from radar.config import PROJECT,emit_json

paths=['backend/src/radar/retrieval.py','backend/src/radar/evaluation.py','backend/src/radar/query.py',
       'backend/src/radar/reranking.py','backend/src/radar/context.py','ops/validate-reference.py',
       'ops/evaluate-retrieval.py','ops/build-independent-snapshot.py',
       'datasets/evaluation/independent-draft-v1.json','datasets/evaluation/independent-bound-v1.json',
       'datasets/evaluation/pilot-v2.json','datasets/evaluation/pilot-candidate-v1.json',
       'datasets/manifests/4f8ddffaa01b6a20.json','datasets/manifests/1446c44aca18011a.json']
target=PROJECT/'reports/independent-retrieval-protocol-v1.json'
if target.exists():raise SystemExit('Protocol already exists; preserve first-run record.')
emit_json(target,{'frozen_at_utc':datetime.now(timezone.utc).isoformat(),
                 'sha256':{p:hashlib.sha256((PROJECT/p).read_bytes()).hexdigest() for p in paths},
                 'groups':{'parent_pilot':30,'candidate_pilot':30,'candidate_independent':10},
                 'protocol':{'query_profile':'structured','lexical_strategy':'any','selection_profile':'rrf',
                             'context_profile':'page_window','top_k':5,'candidates_per_branch':10,
                             'rrf_constant':60,'window_before_chars':350,'window_after_chars':650,
                             'window_max_chars':2000,'repetitions':1,'scope':'selected_pncp_id'},
                 'primary_independent_measure':'literal_quote_offset_coverage_not_answer_accuracy',
                 'anchor_hit_limitation':'representative_overlap_anchor_not_exhaustive_relevance',
                 'refusal_generation':'not_executed','groq_calls':0,
                 'policy':'publish_first_results_and_failures_without_tuning_this_reserved_batch'})
print('First-run protocol frozen.')
