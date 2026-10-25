"""Avaliação de descoberta no desenvolvimento, sem gerar respostas nem usar holdout."""
import hashlib
import json
import statistics
import argparse
from collections import Counter
from pathlib import Path

from radar.discovery import SNAPSHOT, discover
from radar.storage import connect

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--report', choices=('v3',), default='v3')
args = parser.parse_args()
cases = []
hashes = {}
for name in ('pilot-candidate-v1.json', 'independent-bound-v1.json'):
    path = root / 'datasets/evaluation' / name
    hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    cases.extend(c for c in json.loads(path.read_text(encoding='utf-8'))['cases'] if c['kind'] == 'answerable')
rows = []
for case in cases:
    result = discover(case['question'])
    candidates = result['candidates']
    verified = True
    with connect() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        for candidate in candidates:
            source = conn.execute('''SELECT start_offset,end_offset,d.source->>'url'
              FROM radar.chunks c JOIN radar.documents d ON d.snapshot_id=c.snapshot_id
              AND d.pncp_id=c.pncp_id AND d.sequence=c.document_sequence
              WHERE c.snapshot_id=%s AND c.id=%s AND c.pncp_id=%s
              AND c.document_sequence=%s AND c.page=%s''',
              (SNAPSHOT,candidate['passage_id'],candidate['pncp_id'],candidate['document_sequence'],candidate['page'])).fetchone()
            verified = verified and source is not None and tuple(source) == (candidate['start'],candidate['end'],candidate['url'])
    rows.append({'case_id': case['id'], 'expected_pncp': case['pncp_id'],
                 'candidate_pncp': [c['pncp_id'] for c in candidates],
                 'hit_at_5': case['pncp_id'] in [c['pncp_id'] for c in candidates],
                 'latency_ms': round(result['latency_ms'],2), 'source_metadata_verified': verified,
                 'routing': result['routing'],
                 'scoped_to_expected': result['routing']['status']=='scoped' and result['routing']['pncp_id']==case['pncp_id']})
    print(json.dumps({'completed':len(rows),'case_id':case['id'],'hit_at_5':rows[-1]['hit_at_5']}),flush=True)
report = {'snapshot_id':SNAPSHOT,'dataset_role':'development','holdout_used':False,'groq_calls':0,
          'reference_sha256':hashes,'cases':rows,'hits_at_5':sum(r['hit_at_5'] for r in rows),
          'total':len(rows),'median_latency_ms':statistics.median(r['latency_ms'] for r in rows),
          'source_metadata_verified':all(r['source_metadata_verified'] for r in rows),
          'routing_counts':dict(Counter(r['routing']['status'] for r in rows)),
          'scoped_correct':sum(r['scoped_to_expected'] for r in rows),
          'scoped_incorrect':sum(r['routing']['status']=='scoped' and not r['scoped_to_expected'] for r in rows),
          'limitations':['One execution; questions from development, sometimes with location clues.',
                        'Expected PNCP is one known answer, not exhaustive relevance labels.',
                        'Measures discovery of contracting record, not correctness of generated answers.']}
(root/f'reports/discovery-development-{args.report}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
