"""Confere rascunho contra páginas privadas e corpus antigo, sem testar o RAG."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from radar.config import emit_json, private_root


def validate(reference, existing, prepared, root):
    oldids={e['pncp_id'] for e in existing['editais']}
    oldhashes={d['sha256'] for e in existing['editais'] for d in e['documents']}
    documents={(d['pncp_id'],d['sha256']):d for d in prepared['documents']}
    ids=set();hashes=set();pncp=set();pages=set();raw_checked=set();spans=0
    if reference['candidate_sha256']!=prepared['candidate_sha256']:
        raise ValueError('Candidate checkpoint mismatch')
    if reference['status'] not in ('draft_pending_user_review','approved_reference_not_executed') or reference['indexed'] or reference['snapshot_id'] is not None:
        raise ValueError('Draft state mismatch')
    for case in reference['cases']:
        expected_status='approved' if reference['status']=='approved_reference_not_executed' else 'draft'
        if case['id'] in ids or case['review_status']!=expected_status or not case['question'] or not case['expected_answer']:
            raise ValueError('Case metadata invalid')
        ids.add(case['id']);pncp.add(case['pncp_id'])
        if case['pncp_id'] in oldids or not case['evidence']:
            raise ValueError('PNCP overlap or evidence missing')
        for e in case['evidence']:
            sha=e['document_sha256'];hashes.add(sha)
            if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{64}',sha):
                raise ValueError('Invalid PDF hash')
            if any(type(e[k]) is not int for k in ('page','start','end')) or e['page']<1:
                raise ValueError('Invalid page or offset type')
            if sha in oldhashes:raise ValueError('PDF hash overlap with existing corpus')
            d=documents[(case['pncp_id'],sha)]
            if e['document_sequence']!=d['document_sequence'] or e['url']!=d['url']:
                raise ValueError('Document identity mismatch')
            url=urlparse(e['url'])
            if url.scheme!='https' or url.hostname!='pncp.gov.br' or url.username or url.password:
                raise ValueError('Source URL invalid')
            if sha not in raw_checked:
                if hashlib.sha256((root/'raw'/f'{sha}.pdf').read_bytes()).hexdigest()!=sha:
                    raise ValueError('Stored PDF integrity mismatch')
                raw_checked.add(sha)
            p=d['pages'][e['page']-1]
            if p['page']!=e['page'] or not 0<=e['start']<e['end']<=len(p['text']):
                raise ValueError('Page or offset invalid')
            if p['text'][e['start']:e['end']]!=e['quote']:
                raise ValueError('Literal evidence mismatch')
            if e['human_review']!='pending':raise ValueError('Human approval cannot be inferred')
            pages.add((sha,e['page']));spans+=1
    if len(ids)!=10:raise ValueError('Expected ten cases')
    return {'cases':len(ids),'distinct_pncp':len(pncp),'distinct_pdf_hashes':len(hashes),
            'reference_pages':len(pages),'literal_spans_checked':spans,
            'pncp_overlap_existing':0,'pdf_hash_overlap_existing':0,'stored_pdf_hashes_verified':len(raw_checked)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path);parser.add_argument('existing',type=Path)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    ref=json.loads(args.reference.read_text(encoding='utf-8'));root=private_root()
    if not re.fullmatch(r'[0-9a-f]{64}',ref['candidate_sha256']):
        raise ValueError('Invalid candidate hash')
    prepared=json.loads((root/'independent'/f"pages-{ref['candidate_sha256'][:16]}.json").read_text(encoding='utf-8'))
    metrics=validate(ref,json.loads(args.existing.read_text(encoding='utf-8')),prepared,root)
    emit_json(args.report,{'checked_at_utc':datetime.now(timezone.utc).isoformat(),
                          'reference_sha256':hashlib.sha256(args.reference.read_bytes()).hexdigest(),
                          'state':'reference_integrity_verified','checks':metrics,
                          'reference_approval':ref['status'],
                          'retrieval_calls':0,'groq_calls':0,'database_changes':0,
                          'does_not_certify':['semantic_correctness','full_document_review','90_percent_accuracy','user_approval']})
    print(json.dumps(metrics))


if __name__=='__main__':main()
