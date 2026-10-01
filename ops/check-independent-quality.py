"""Aplica o gate à candidata sem inventar revisão de respostas não executadas."""
import json
from radar.config import PROJECT,emit_json
from radar.quality import assess_release

manifest=json.loads((PROJECT/'datasets/manifests/1446c44aca18011a.json').read_text(encoding='utf-8'))
sources={e['pncp_id']:e['documents'] for e in manifest['editais']};rows=[]
for cohort,name in [('regression','pilot-candidate-v1.json'),('new','independent-bound-v1.json')]:
    ref=json.loads((PROJECT/'datasets/evaluation'/name).read_text(encoding='utf-8'))
    for c in ref['cases']:
        hashes=sorted({e['document_sha256'] for e in c['evidence']}) or [d['sha256'] for d in sources[c['pncp_id']]]
        rows.append({'case_id':c['id'],'cohort':cohort,'kind':c['kind'],'pncp_id':c['pncp_id'],
                     'source_hashes':hashes,'natural_question':cohort=='new','source_approved':c['review_status']=='approved',
                     'review_status':'pending','answer_state':'not_run','correct':None,'complete':None,
                     'supported':None,'refusal_safe':None})
report=assess_release(rows)
report.update(snapshot_id=manifest['snapshot_id'],scope='candidate_generation_not_yet_executed',
              retrieval_coverage_not_used_as_answer_accuracy=True)
emit_json(PROJECT/'reports/quality-growth-v1.json',report)
print(json.dumps({'decision':report['decision'],'reasons':report['reasons']}))
