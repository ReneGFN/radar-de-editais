"""Compara três modos no mesmo corpus aprovado, sem chamadas Groq."""
import argparse
import hashlib
import importlib.util
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from radar.config import PROJECT, private_root, emit_json
from radar.embeddings import local_embeddings
from radar.evaluation import score_case, summarize
from radar.retrieval import retrieve_with_trace
from radar.storage import connect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--lexical-strategy', choices=('all','any'), default='all')
    parser.add_argument('--query-profile',choices=('original','focused','structured'),default='original')
    parser.add_argument('--selection-profile',choices=('rrf','coverage'),default='rrf')
    parser.add_argument('--context-profile',choices=('chunk','page_window'),default='chunk')
    args = parser.parse_args()
    ref_raw = args.reference.read_bytes()
    manifest_raw = args.manifest.read_bytes()
    ref, manifest = json.loads(ref_raw), json.loads(manifest_raw)
    snapshot = ref['snapshot_id']
    if not isinstance(snapshot,str) or len(snapshot)!=16 or any(c not in '0123456789abcdef' for c in snapshot):
        raise ValueError('Snapshot inválido')
    prepared = json.loads((private_root()/'prepared'/f'{snapshot}.json').read_text(encoding='utf-8'))
    spec = importlib.util.spec_from_file_location('reference_validator', PROJECT/'ops/validate-reference.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    validator.validate(ref,prepared,manifest)
    if any(c['review_status'] != 'approved' for c in ref['cases']):
        raise ValueError('Conjunto ainda não aprovado')
    cases = [c for c in ref['cases'] if c['kind']=='answerable']
    with connect() as conn:
        # Transação explicitamente só de leitura para as pré-condições.
        conn.execute('SET TRANSACTION READ ONLY')
        db_config = conn.execute('SELECT configuration FROM radar.snapshots WHERE id=%s',(snapshot,)).fetchone()
        if not db_config or db_config[0]['embedding'] != prepared['embedding']:
            raise ValueError('Configuração do banco divergente')
        count = conn.execute('SELECT count(*) FROM radar.chunks WHERE snapshot_id=%s',(snapshot,)).fetchone()[0]
        if count != len(prepared['chunks']):
            raise ValueError('Contagem do banco divergente')
        for case in cases:
            for ev in case['evidence']:
                row = conn.execute('''SELECT c.pncp_id,c.document_sequence,c.page,c.text,d.sha256
                    FROM radar.chunks c JOIN radar.documents d ON d.snapshot_id=c.snapshot_id
                    AND d.pncp_id=c.pncp_id AND d.sequence=c.document_sequence
                    WHERE c.snapshot_id=%s AND c.id=%s''',(snapshot,ev['chunk_id'])).fetchone()
                if not row or row[:3] != (case['pncp_id'],ev['document_sequence'],ev['page']) or ev['quote'] not in row[3] or row[4]!=ev['document_sha256']:
                    raise ValueError('Evidência do banco divergente')
        db_version = conn.execute('SELECT version()').fetchone()[0]
    model_started = perf_counter()
    model = local_embeddings()
    model.embed_query('consulta de aquecimento')
    warmup_ms = (perf_counter()-model_started)*1000
    if model.provenance() != prepared['embedding']:
        raise ValueError('Modelo local divergente')
    modes = ('keyword','semantic','hybrid')
    rows = {mode:[] for mode in modes}
    for i,case in enumerate(cases):
        # Alterna ordem para reduzir vantagem sistemática de cache entre modos.
        order = modes[i%3:] + modes[:i%3]
        for mode in order:
            docs, trace = retrieve_with_trace(case['question'],snapshot,case['pncp_id'],mode,args.lexical_strategy,args.query_profile,args.selection_profile,args.context_profile)
            result = score_case(case,docs)
            rows[mode].append(dict(case_id=case['id'],pncp_id=case['pncp_id'],
                expected_chunk_ids=[e['chunk_id'] for e in case['evidence']],
                retrieved=[d.metadata for d in docs],candidate_ids=trace['candidate_ids'],
                latency_ms=trace['latency_ms'],**result))
            rows[mode][-1].update(effective_query=trace['effective_query'],filters=trace['filters'])
        print(json.dumps({'cases_done':i+1,'total':len(cases)}),flush=True)
    code_paths = ['backend/src/radar/retrieval.py','backend/src/radar/evaluation.py','backend/src/radar/query.py',
                  'ops/evaluate-retrieval.py','ops/validate-reference.py','backend/src/radar/reranking.py','backend/src/radar/context.py']
    report = {'executed_at_utc':datetime.now(timezone.utc).isoformat(),
        'snapshot_id':snapshot,'reference_sha256':hashlib.sha256(ref_raw).hexdigest(),
        'manifest_sha256':hashlib.sha256(manifest_raw).hexdigest(),
        'code_sha256':{p:hashlib.sha256((PROJECT/p).read_bytes()).hexdigest() for p in code_paths},
        'database_chunks':count,'postgresql':db_version,'python':platform.python_version(),
        'dependencies':{p:version(p) for p in ('langchain-core','fastembed','psycopg','pgvector')},
        'embedding':prepared['embedding'],'model_startup_and_warmup_ms':warmup_ms,
        'protocol':{'top_k':5,'candidates_per_branch':10,'rrf_constant':60,
            'context_profile':args.context_profile,'window_before_chars':350,'window_after_chars':650,'window_max_chars':2000,
            'selection_profile':args.selection_profile,'coverage_bonus':.02 if args.selection_profile=='coverage' else 0,
            'query_rewrite':args.query_profile!='original','query_profile':args.query_profile,'lexical_strategy':args.lexical_strategy,'model_warmup_excluded_from_query_latencies':True,
            'mode_order':'rotating_per_case','repetitions':1,'latency_percentile':'nearest_rank',
            'labels':'known_chunks_and_same_source_page_quotes_not_exhaustive',
            'dataset_role':'development_pilot_not_held_out_test'},
        'generation_calls':0,'provider_api_cost':0,'local_compute_cost':'not_estimated',
        'refusal_cases_not_executed':sum(c['kind']=='out_of_scope' for c in ref['cases']),
        'generation_quality':'not_evaluated',
        'summary':{mode:summarize(rows[mode]) for mode in modes},'results':rows}
    emit_json(args.report,report)
    print(json.dumps(report['summary']))


if __name__=='__main__':
    main()
