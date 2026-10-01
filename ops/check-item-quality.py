"""Gate das duas coortes geradas; revisão humana nunca inferida de aprovação geral."""
import json,hashlib
from radar.config import PROJECT,private_root,emit_json
from radar.quality import assess_release
manifest=json.loads((PROJECT/'datasets/manifests/1446c44aca18011a.json').read_text(encoding='utf-8'));sources={e['pncp_id']:e['documents'] for e in manifest['editais']};rows=[]
for cohort,name in [('regression','pilot-candidate-v1.json'),('new','independent-bound-v1.json')]:
 path=PROJECT/'datasets/evaluation'/name;digest=hashlib.sha256(path.read_bytes()).hexdigest();ref=json.loads(path.read_bytes())
 check=private_root()/'generation'/f'evaluation-{digest[:16]}-alias_items.json'
 checkpoint=json.loads(check.read_text(encoding='utf-8')) if check.exists() else {'answers':[],'errors':[]}
 if checkpoint.get('reference_sha256',digest)!=digest:raise ValueError('Checkpoint mismatch')
 states={a['case_id']:a['response']['status'] for a in checkpoint['answers']}
 for e in checkpoint['errors']:states.setdefault(e['case_id'],'rejected' if (e.get('cause_type') or '').startswith('ValueError: ') else 'not_run')
 for c in ref['cases']:
  hashes=sorted({e['document_sha256'] for e in c['evidence']}) or [d['sha256'] for d in sources[c['pncp_id']]]
  rows.append({'case_id':c['id'],'cohort':cohort,'kind':c['kind'],'pncp_id':c['pncp_id'],'source_hashes':hashes,'natural_question':cohort=='new','source_approved':c['review_status']=='approved','review_status':'pending','answer_state':states.get(c['id'],'not_run'),'correct':None,'complete':None,'supported':None,'refusal_safe':None})
report=assess_release(rows);report['reasons'].append('new_set_used_for_tuning_requires_another_held_out_sample');report.update(decision='blocked',snapshot_id=manifest['snapshot_id'],variant='alias_items',human_accuracy=None,new_cohort_role='development_after_tuning',promotion_performed=False)
emit_json(PROJECT/'reports/item-quality-v2.json',report)
emit_json(private_root()/'generation/item-human-review-template-v2.json',{'state':'pending_human_review_not_approval','rows':rows})
print(json.dumps({'decision':report['decision'],'reasons':report['reasons']}))
