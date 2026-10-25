"""Conjunto de validação realmente separado do desenvolvimento.

Tudo que já apareceu em manifesto, candidato, referência ou pergunta do projeto é
desenvolvimento. A amostra nova só é independente se não compartilhar contratação,
hash de PDF, URL de documento nem pergunta (exata ou quase idêntica).
"""
import hashlib
import re
import unicodedata

REQUIRED_CATEGORIES = ('item', 'quantity', 'specification', 'deadline', 'judgment_criterion')
REFUSAL_KIND = 'out_of_scope'


def normalize_question(text):
    text = unicodedata.normalize('NFKD', text.casefold())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', text))


def question_hash(text):
    return hashlib.sha256(normalize_question(text).encode('utf-8')).hexdigest()


def _tokens(text):
    return set(normalize_question(text).split())


def agency_of(pncp_id):
    """CNPJ do órgão: mesmo órgão tende a reutilizar o mesmo modelo de edital."""
    return pncp_id.split('-')[0]


def development_exclusions(manifests, references, candidate_lists=()):
    """Reúne identificadores de desenvolvimento a partir de dados públicos do projeto."""
    out = {'pncp_ids': set(), 'document_sha256': set(), 'document_urls': set(), 'questions': []}
    for manifest in manifests:
        for edital in manifest['editais']:
            out['pncp_ids'].add(edital['pncp_id'])
            for document in edital['documents']:
                out['document_sha256'].add(document['sha256'])
                out['document_urls'].add(document['url'])
    for listing in candidate_lists:
        entries = [v for value in listing.values() if isinstance(value, list) for v in value if isinstance(v, dict)]
        for candidate in entries:
            if candidate.get('pncp_id'):
                out['pncp_ids'].add(candidate['pncp_id'])
            for document in candidate.get('documents', []) + [candidate]:
                if isinstance(document.get('sha256'), str) and len(document['sha256']) == 64:
                    out['document_sha256'].add(document['sha256'])
                if isinstance(document.get('url'), str):
                    out['document_urls'].add(document['url'])
    for reference in references:
        for case in reference['cases']:
            if case.get('pncp_id'):
                out['pncp_ids'].add(case['pncp_id'])
            out['questions'].append(case['question'])
            for evidence in case.get('evidence', []):
                if evidence.get('document_sha256'):
                    out['document_sha256'].add(evidence['document_sha256'])
                if evidence.get('url'):
                    out['document_urls'].add(evidence['url'].split('#')[0])
    out['agencies'] = {agency_of(p) for p in out['pncp_ids']}
    return out


def check_holdout(manifest, reference, exclusions, *, min_factual=30, min_refusals=10, min_editais=10,
                  similarity_limit=0.8):
    """Devolve violações; lista vazia não aprova respostas, só a separação dos dados."""
    violations = []
    editais = {e['pncp_id']: e for e in manifest['editais']}
    hashes = {d['sha256'] for e in editais.values() for d in e['documents']}
    urls = {d['url'] for e in editais.values() for d in e['documents']}
    for kind, values, excluded in [('edital_overlap', set(editais), exclusions['pncp_ids']),
                                   ('pdf_hash_overlap', hashes, exclusions['document_sha256']),
                                   ('document_url_overlap', urls, exclusions['document_urls'])]:
        for value in sorted(values & excluded):
            violations.append({'type': kind, 'value': value})
    seen_hashes = {}
    for edital in editais.values():
        for document in edital['documents']:
            if not isinstance(document.get('sha256'), str) or len(document['sha256']) != 64:
                violations.append({'type': 'document_hash_missing', 'value': edital['pncp_id']})
            elif seen_hashes.setdefault(document['sha256'], edital['pncp_id']) != edital['pncp_id']:
                violations.append({'type': 'same_pdf_in_two_editais', 'value': document['sha256']})
    old_hashes = {question_hash(q) for q in exclusions['questions']}
    old_tokens = [_tokens(q) for q in exclusions['questions']]
    factual = [c for c in reference['cases'] if c['kind'] == 'answerable']
    refusals = [c for c in reference['cases'] if c['kind'] == REFUSAL_KIND]
    ids = [c['id'] for c in reference['cases']]
    if len(ids) != len(set(ids)):
        violations.append({'type': 'duplicate_case_id', 'value': None})
    for case in reference['cases']:
        if case['kind'] not in ('answerable', REFUSAL_KIND):
            violations.append({'type': 'invalid_kind', 'value': case['id']})
        if case['kind'] == 'answerable' and case.get('pncp_id') not in editais:
            violations.append({'type': 'case_outside_holdout_manifest', 'value': case['id']})
        for evidence in case.get('evidence', []):
            if evidence.get('document_sha256') not in hashes:
                violations.append({'type': 'evidence_outside_holdout_manifest', 'value': case['id']})
        if question_hash(case['question']) in old_hashes:
            violations.append({'type': 'question_reused', 'value': case['id']})
            continue
        tokens = _tokens(case['question'])
        for old in old_tokens:
            if tokens and old and len(tokens & old) / len(tokens | old) >= similarity_limit:
                violations.append({'type': 'question_near_duplicate', 'value': case['id']})
                break
    if len(factual) < min_factual:
        violations.append({'type': 'too_few_factual', 'value': len(factual)})
    if len(refusals) < min_refusals:
        violations.append({'type': 'too_few_refusals', 'value': len(refusals)})
    if len({c['pncp_id'] for c in factual}) < min_editais or len(editais) < min_editais:
        violations.append({'type': 'too_few_editais', 'value': len({c['pncp_id'] for c in factual})})
    present = {c.get('category') for c in factual}
    for category in REQUIRED_CATEGORIES:
        if category not in present:
            violations.append({'type': 'category_missing', 'value': category})
    warnings = [{'type': 'agency_overlap', 'value': p} for p in sorted(editais)
                if agency_of(p) in exclusions.get('agencies', set())]
    return {'independent': not violations, 'violations': violations, 'warnings': warnings,
            'factual': len(factual), 'refusals': len(refusals), 'editais': len(editais),
            'documents': len(hashes), 'categories': sorted(c for c in present if c),
            'scope': 'data separation only; says nothing about answer quality'}
