import copy
from radar.independence import check_holdout, development_exclusions, normalize_question

H = lambda n: format(n, '064x')


def dev():
    manifest = {'editais': [{'pncp_id': 'old-1', 'documents': [{'sha256': H(1), 'url': 'https://pncp/old/1'}]}]}
    reference = {'cases': [{'id': 'p-1', 'kind': 'answerable', 'pncp_id': 'old-1',
        'question': 'Qual é a quantidade de notebooks do item 1?',
        'evidence': [{'document_sha256': H(1), 'url': 'https://pncp/old/1#page=3'}]}]}
    candidates = {'candidates': [{'pncp_id': 'seen-1', 'documents': [{'url': 'https://pncp/seen/1'}]}],
                  'errors': [{'pncp_id': 'failed-1'}]}
    return development_exclusions([manifest], [reference], [candidates])


CATEGORIES = ['item', 'quantity', 'specification', 'deadline', 'judgment_criterion']


def holdout(editais=10, factual=30, refusals=10):
    manifest = {'editais': [{'pncp_id': f'new-{i}', 'documents': [{'sha256': H(100 + i), 'url': f'https://pncp/new/{i}'}]}
                            for i in range(editais)]}
    cases = [{'id': f'h-{i}', 'kind': 'answerable', 'pncp_id': f'new-{i % editais}',
              'category': CATEGORIES[i % len(CATEGORIES)],
              'question': f'Pergunta distinta numero {i} sobre tema {i * 7} do edital',
              'evidence': [{'document_sha256': H(100 + i % editais)}]} for i in range(factual)]
    cases += [{'id': f'r-{i}', 'kind': 'out_of_scope', 'question': f'Recusa inedita {i} pedindo segredo {i * 3}'}
              for i in range(refusals)]
    return manifest, {'cases': cases}


def types(report):
    return {v['type'] for v in report['violations']}


def test_clean_holdout_passes_only_data_separation():
    report = check_holdout(*holdout(), dev())
    assert report['independent'] and report['factual'] == 30 and report['editais'] == 10
    assert 'answer quality' in report['scope']


def test_reused_edital_pdf_url_and_candidate_are_blocked():
    manifest, reference = holdout()
    manifest['editais'][0]['pncp_id'] = 'seen-1'
    manifest['editais'][1]['documents'][0]['sha256'] = H(1)
    manifest['editais'][2]['documents'][0]['url'] = 'https://pncp/old/1'
    manifest['editais'][3]['pncp_id'] = 'failed-1'
    found = types(check_holdout(manifest, reference, dev()))
    assert {'edital_overlap', 'pdf_hash_overlap', 'document_url_overlap'} <= found


def test_same_pdf_republished_under_new_edital_is_blocked():
    manifest, reference = holdout()
    manifest['editais'][1]['documents'][0]['sha256'] = manifest['editais'][0]['documents'][0]['sha256']
    assert 'same_pdf_in_two_editais' in types(check_holdout(manifest, reference, dev()))


def test_reused_or_reworded_question_is_blocked():
    manifest, reference = holdout()
    reference['cases'][0]['question'] = 'QUAL é a quantidade de NOTEBOOKS do ítem 1'
    reference['cases'][1]['question'] = 'Qual é a quantidade de notebooks do item 1 no edital?'
    found = check_holdout(manifest, reference, dev())['violations']
    assert {'type': 'question_reused', 'value': 'h-0'} in found
    assert {'type': 'question_near_duplicate', 'value': 'h-1'} in found


def test_minimums_and_categories_are_enforced():
    found = types(check_holdout(*holdout(editais=9, factual=29, refusals=9), dev()))
    assert {'too_few_factual', 'too_few_refusals', 'too_few_editais'} <= found
    manifest, reference = holdout()
    for case in reference['cases']:
        if case.get('category') == 'judgment_criterion':
            case['category'] = 'quantity'
    assert {'type': 'category_missing', 'value': 'judgment_criterion'} in check_holdout(manifest, reference, dev())['violations']


def test_evidence_must_come_from_holdout_documents():
    manifest, reference = holdout()
    reference['cases'][0]['evidence'][0]['document_sha256'] = H(999)
    assert 'evidence_outside_holdout_manifest' in types(check_holdout(manifest, reference, dev()))


def test_same_agency_is_warned_not_hidden():
    manifest, reference = holdout()
    manifest['editais'][0]['pncp_id'] = 'old-9'
    for case in reference['cases']:
        if case.get('pncp_id') == 'new-0':
            case['pncp_id'] = 'old-9'
    report = check_holdout(manifest, reference, dev())
    assert report['warnings'] == [{'type': 'agency_overlap', 'value': 'old-9'}]


def test_normalization_removes_accents_case_and_punctuation():
    assert normalize_question('Prazo  de ENTREGA, em dias úteis?') == 'prazo de entrega em dias uteis'
