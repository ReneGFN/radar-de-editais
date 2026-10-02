"""Executa os 40 casos, guarda respostas privadas e exige revisão de conteúdo."""
import argparse
import hashlib
import json
import time
from datetime import datetime,timezone
from pathlib import Path
from radar.config import PROJECT,private_root,emit_json
from radar.generation import answer,MODEL


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path)
    parser.add_argument('--confirm-free-plan',action='store_true')
    parser.add_argument('--limit',type=int,default=40)
    parser.add_argument('--interval',type=float,default=35)
    parser.add_argument('--variant',choices=('baseline','source_window','alias_window','alias_items','alias_items_v2'),default='baseline')
    args=parser.parse_args()
    if not args.confirm_free_plan or not 1<=args.limit<=40 or args.interval<30:
        raise ValueError('Confirme plano gratuito, até 40 casos e intervalo mínimo de 30 segundos')
    if 'holdout' in args.reference.resolve().parts:
        raise ValueError('Holdout isolado: este script só roda conjuntos de desenvolvimento')
    raw=args.reference.read_bytes();ref=json.loads(raw)
    if any(c['review_status']!='approved' for c in ref['cases']):
        raise ValueError('Conjunto não aprovado')
    digest=hashlib.sha256(raw).hexdigest()
    path=private_root()/'generation'/f"evaluation-{digest[:16]}{'-'+args.variant if args.variant!='baseline' else ''}.json"
    result=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'variant':args.variant,'model':MODEL,'reference_sha256':digest,'snapshot_id':ref['snapshot_id'],
        'free_plan_user_confirmed':True,'answers':[],'errors':[],'semantic_review':'pending'}
    if result['reference_sha256']!=digest or result['model']!=MODEL:
        raise ValueError('Checkpoint incompatível')
    done={r['case_id'] for r in result['answers']}
    # Uma resposta rejeitada é resultado do teste, não acerto nem motivo para ocultar o caso.
    rejected={e['case_id'] for e in result['errors'] if (e.get('cause_type') or '').startswith('ValueError: ')}
    done |= rejected
    remaining=[c for c in ref['cases'][:args.limit] if c['id'] not in done]
    for i,case in enumerate(remaining):
        if i:time.sleep(args.interval)
        perf_start=time.perf_counter()
        try:
            value=answer(case['question'],ref['snapshot_id'],case['pncp_id'],free_plan_confirmed=True,
                         context_profile='item_structure' if args.variant in ('alias_items','alias_items_v2') else 'page_window' if args.variant!='baseline' else 'chunk',
                         citation_mode='source_alias' if args.variant in ('alias_window','alias_items','alias_items_v2') else 'source_id' if args.variant=='source_window' else 'model_quote',
                         prompt_version='v2' if args.variant=='alias_items_v2' else 'v1')
        except Exception as exc:
            result['errors'].append({'case_id':case['id'],'error_type':type(exc).__name__,
                                     'cause_type':getattr(exc,'kind',None),'http_status':getattr(exc,'status_code',None),
                                     'date_utc':datetime.now(timezone.utc).isoformat()})
            emit_json(path,result)
            validation_failure=(getattr(exc,'kind','') or '').startswith('ValueError: ')
            print(json.dumps({'status':'rejected_validation' if validation_failure else 'stopped_on_error','case_id':case['id'],'error_type':type(exc).__name__,
                              'cause_type':getattr(exc,'kind',None),'http_status':getattr(exc,'status_code',None),
                              'private_report':str(path)}),flush=True)
            if validation_failure:continue
            raise SystemExit(1) from None
        result['answers'].append({'case_id':case['id'],'kind':case['kind'],
            'expected_answer':case['expected_answer'],'response':value,
            'total_latency_ms':(time.perf_counter()-perf_start)*1000,
            'human_review':'pending','date_utc':datetime.now(timezone.utc).isoformat()})
        result['summary']={'completed':len(result['answers']),
            'citation_integrity_passed':sum(a['response'].get('citation_integrity')=='passed' for a in result['answers']),
            'generation_calls':sum(a['response']['generation_calls'] for a in result['answers']),
            'input_tokens':sum(a['response'].get('usage',{}).get('input_tokens',0) for a in result['answers']),
            'output_tokens':sum(a['response'].get('usage',{}).get('output_tokens',0) for a in result['answers']),
            'correctness':'not_scored_pending_human_review','refusal_safety':'not_scored_pending_human_review'}
        emit_json(path,result)
        print(json.dumps({'cases_completed':len(result['answers']),'case_id':case['id'],
                          'response_status':value['status'],'private_report':str(path)}),flush=True)
    print(json.dumps(result.get('summary',{})),flush=True)


if __name__=='__main__':main()
