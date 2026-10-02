"""Valida a separação de dados do holdout e grava o resultado em reports/.

Lê o manifesto do holdout e a referência em rascunho (datasets/holdout/), reúne
todo o desenvolvimento (manifestos, referências e listas de candidatos) e roda
`check_holdout`. Também confere que cada trecho citado existe na página indicada
do texto extraído privado, e que nenhum caso está marcado como aprovado sem
registro de aprovação. Não indexa, não grava no banco, não chama a Groq.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from radar.config import PROJECT, emit_json, private_root
from radar.independence import check_holdout, development_exclusions

PERSONAL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+|\d{3}\.\d{3}\.\d{3}-\d{2}|\(\d{2}\)\s?\d{4,5}-?\d{4}')


def load_exclusions():
    manifests = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((PROJECT / 'datasets/manifests').glob('*.json'))]
    references = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((PROJECT / 'datasets/evaluation').glob('*.json'))]
    listings = [json.loads((PROJECT / 'reports' / name).read_text(encoding='utf-8'))
                for name in ('independent-corpus-candidates-v1.json', 'independent-documents-v1.json')]
    return development_exclusions([m for m in manifests if 'editais' in m], references, listings)


def quote_checks(reference, pages_path):
    """Cada trecho deve estar no texto privado, na página e no intervalo de caracteres declarados."""
    documents = {d['sha256']: d for d in json.loads(pages_path.read_text(encoding='utf-8'))['documents']}
    problems = []
    for case in reference['cases']:
        for evidence in case.get('evidence', []):
            document = documents.get(evidence['document_sha256'])
            page = next((p for p in (document or {}).get('pages', []) if p['page'] == evidence['page']), None)
            if page is None or page['text'][evidence['char_start']:evidence['char_end']] != evidence['quote']:
                problems.append({'type': 'quote_not_at_declared_offset', 'value': case['id']})
            if PERSONAL.search(evidence['quote']):
                problems.append({'type': 'personal_data_in_quote', 'value': case['id']})
        if case.get('review_status') == 'approved' and not case.get('review_record'):
            problems.append({'type': 'approved_without_record', 'value': case['id']})
    return problems


def revoked_hashes(holdout_dir):
    """Hashes de referências cuja aprovação foi revogada; nunca ficam prontas para executar."""
    revoked = set()
    for path in sorted(Path(holdout_dir).glob('*-approval-revocation.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        digest = record.get('revokes_reference_sha256', '')
        if not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise SystemExit('Revogação sem hash válido: ' + path.name)
        revoked.add(digest)
    return revoked


def ready(result, reference, digest, revoked):
    return (result['independent'] and not result['quote_violations'] and digest not in revoked
            and all(c['review_status'] == 'approved' for c in reference['cases']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('reference', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    raw = args.reference.read_bytes()
    reference = json.loads(raw)
    pages_path = private_root() / 'holdout' / f"pages-{manifest['candidate_sha256'][:16]}.json"
    result = check_holdout(manifest, reference, load_exclusions())
    result['quote_violations'] = quote_checks(reference, pages_path)
    factual = [c for c in reference['cases'] if c['kind'] == 'answerable']
    digest = hashlib.sha256(raw).hexdigest()
    revoked = revoked_hashes(PROJECT / 'datasets/holdout')
    result.update({
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'reference_sha256': digest,
        'approval_revoked': digest in revoked,
        'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        'category_counts': dict(Counter(c['category'] for c in factual)),
        'factual_per_edital': dict(Counter(c['pncp_id'] for c in factual)),
        'review_status_counts': dict(Counter(c['review_status'] for c in reference['cases'])),
        'ready_to_execute': ready(result, reference, digest, revoked),
        'groq_calls': 0, 'database_changes': 0})
    emit_json(args.report, result)
    print(json.dumps({k: result[k] for k in ('independent', 'ready_to_execute', 'approval_revoked', 'factual', 'refusals', 'editais',
                                             'documents', 'category_counts', 'review_status_counts')}
                     | {'violations': result['violations'], 'quote_violations': result['quote_violations'],
                        'warnings': result['warnings']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
