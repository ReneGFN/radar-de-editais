"""Aplica o gate à candidata sem inventar revisão de respostas não executadas."""
import json
import argparse
import hashlib
from radar.config import PROJECT,emit_json,private_root
from radar.quality import assess_release

manifest=json.loads((PROJECT/'datasets/manifests/1446c44aca18011a.json').read_text(encoding='utf-8'))
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--after-generation',action='store_true');args=parser.parse_args()
states={}
if args.after_generation:
    ref_path=PROJECT/'datasets/evaluation/independent-bound-v1.json'
    digest=hashlib.sha256(ref_path.read_bytes()).hexdigest()
    checkpoint=json.loads((private_root()/'generation'/f'evaluation-{digest[:16]}-alias_window.json').read_text(encoding='utf-8'))
    if checkpoint['reference_sha256']!=digest:raise ValueError('Checkpoint reference mismatch')
    states={a['case_id']:a['response']['status'] for a in checkpoint['answers']}
    for error in checkpoint['errors']:
        if (error.get('cause_type') or '').startswith('ValueError: '):states.setdefault(error['case_id'],'rejected')
sources={e['pncp_id']:e['documents'] for e in manifest['editais']};rows=[]
for cohort,name in [('regression','pilot-candidate-v1.json'),('new','independent-bound-v1.json')]:
    ref=json.loads((PROJECT/'datasets/evaluation'/name).read_text(encoding='utf-8'))
    for c in ref['cases']:
        hashes=sorted({e['document_sha256'] for e in c['evidence']}) or [d['sha256'] for d in sources[c['pncp_id']]]
        rows.append({'case_id':c['id'],'cohort':cohort,'kind':c['kind'],'pncp_id':c['pncp_id'],
                     'source_hashes':hashes,'natural_question':cohort=='new','source_approved':c['review_status']=='approved',
                     'review_status':'pending','answer_state':states.get(c['id'],'not_run'),'correct':None,'complete':None,
                     'supported':None,'refusal_safe':None})
report=assess_release(rows)
report.update(snapshot_id=manifest['snapshot_id'],scope='new_generation_human_review_pending_historical_candidate_generation_not_run' if args.after_generation else 'candidate_generation_not_yet_executed',
              retrieval_coverage_not_used_as_answer_accuracy=True)
emit_json(PROJECT/'reports'/('quality-growth-generated-v1.json' if args.after_generation else 'quality-growth-v1.json'),report)
print(json.dumps({'decision':report['decision'],'reasons':report['reasons']}))
