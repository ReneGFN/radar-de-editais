"""Exporta somente métricas operacionais; não pontua correção semântica."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path
from radar.config import private_root,emit_json
from radar.generation import MODEL


def summarize(checkpoint):
    records=checkpoint['answers']
    cases=[]
    for record in records:
        response=record['response']
        usage=response.get('usage',{})
        cases.append({'case_id':record['case_id'],'kind':record['kind'],
            'response_status':response['status'],'generation_calls':response['generation_calls'],
            'citation_integrity':response.get('citation_integrity','not_applicable_no_generation'),
            'input_tokens':usage.get('input_tokens',0),'output_tokens':usage.get('output_tokens',0),
            'total_latency_ms':round(record['total_latency_ms'],2),
            'generation_latency_ms':round(response.get('generation_latency_ms',0),2)})
    latencies=[c['generation_latency_ms'] for c in cases if c['generation_calls']]
    accepted={c['case_id'] for c in cases}
    rejected={e['case_id'] for e in checkpoint['errors'] if (e.get('cause_type') or '').startswith('ValueError: ')}
    tested=accepted | rejected
    return {'model':checkpoint['model'],'snapshot_id':checkpoint['snapshot_id'],
        'reference_sha256':checkpoint['reference_sha256'],
        'free_plan':'user_confirmed_not_independently_audited',
        'completed':len(cases),'tested_cases':len(tested),
        'rejected_case_ids':sorted(rejected-accepted),
        'generation_calls':sum(c['generation_calls'] for c in cases),
        'input_tokens_successful_cases':sum(c['input_tokens'] for c in cases),
        'output_tokens_successful_cases':sum(c['output_tokens'] for c in cases),
        'median_generation_latency_ms':round(statistics.median(latencies),2) if latencies else None,
        'failed_attempts':len(checkpoint['errors']),
        'failed_attempt_usage':'not_confirmed','actual_billing':'not_independently_verified',
        'correctness':'not_scored_pending_human_review',
        'refusal_safety':'not_scored_pending_human_review',
        'cases':cases,'errors':checkpoint['errors']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    digest=hashlib.sha256(args.reference.read_bytes()).hexdigest()
    path=private_root()/'generation'/f'evaluation-{digest[:16]}.json'
    checkpoint=json.loads(path.read_text(encoding='utf-8'))
    if checkpoint['reference_sha256']!=digest or checkpoint['model']!=MODEL:
        raise ValueError('Checkpoint incompatível')
    report=summarize(checkpoint)
    emit_json(args.report,report)
    print(json.dumps({'completed':report['completed'],'report':str(args.report)}))


if __name__=='__main__':main()
