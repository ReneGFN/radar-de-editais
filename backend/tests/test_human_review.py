import copy
import json
import pytest
from radar.human_review import (answer_sha256, build_form, public_summary, quality_rows, refresh_form,
                                validate_form)
from radar.quality import assess_release

DIGEST = 'a' * 64


def reference():
    return {'cases': [
        {'id': 'c-1', 'kind': 'answerable', 'category': 'quantity'},
        {'id': 'c-2', 'kind': 'answerable', 'category': 'specification'},
        {'id': 'c-3', 'kind': 'answerable', 'category': 'warranty'},
        {'id': 'r-1', 'kind': 'out_of_scope', 'category': 'secret_exfiltration'}]}


def response(status, answer):
    return {'status': status, 'answer': answer, 'claims': [], 'citations': [{'quote': 'PRIVATE_QUOTE'}],
            'citation_integrity': 'passed'}


def checkpoint():
    return {'reference_sha256': DIGEST, 'snapshot_id': 'snap', 'model': 'm',
        'answers': [{'case_id': 'c-1', 'response': response('answered', 'PRIVATE_ANSWER_1')},
                    {'case_id': 'c-2', 'response': response('answered', 'PRIVATE_ANSWER_2')},
                    {'case_id': 'r-1', 'response': response('refused', 'PRIVATE_REFUSAL')}],
        'errors': [{'case_id': 'c-3', 'cause_type': 'ValueError: Citação inventada'}]}


def filled():
    form = build_form(reference(), DIGEST, checkpoint(), cohort='new', variant='alias_items')
    for row in form['rows']:
        if row['answer_state'] in ('not_run', 'rejected'):
            continue
        row.update(reviewer='Rene', reviewer_kind='human', reviewed_on='2026-10-01',
                   criteria={k: True for k in row['criteria']}, notes_private='PRIVATE_NOTE')
    return form


def validate(form, cp=None):
    import datetime
    return validate_form(form, reference(), DIGEST, cp or checkpoint(), today=datetime.date(2026, 10, 2))


def test_blank_form_has_no_scores_and_marks_blocked_case():
    form = build_form(reference(), DIGEST, checkpoint(), cohort='new', variant='alias_items')
    assert all(v is None for r in form['rows'] for v in r['criteria'].values())
    states = {r['case_id']: r['answer_state'] for r in form['rows']}
    assert states == {'c-1': 'answered', 'c-2': 'answered', 'c-3': 'rejected', 'r-1': 'refused'}
    summary = public_summary(validate(form), form)
    assert summary['answerable']['rate'] is None and summary['refusals']['rate'] is None


def test_public_summary_never_contains_answers_quotes_notes_or_reviewer():
    form = filled()
    text = json.dumps(public_summary(validate(form), form), ensure_ascii=False)
    assert 'PRIVATE_' not in text and 'Rene' not in text


def test_rejected_answer_counts_against_rate_and_citation_is_separate():
    form = filled()
    form['rows'][1]['criteria']['correct'] = False
    form['rows'][1]['error_tags'] = ['unit_mix']
    summary = public_summary(validate(form), form)
    group = summary['answerable']
    assert group['citation_integrity_passed'] == 2 and group['all_criteria_true'] == 1
    assert group['rate'] == round(1 / 3, 4)
    assert summary['error_tag_counts'] == {'unit_mix': 1}


def test_changed_answer_invalidates_previous_review():
    form = filled()
    cp = checkpoint()
    cp['answers'][0]['response']['answer'] = 'outra resposta'
    with pytest.raises(ValueError, match='Resposta mudou'):
        validate(form, cp)


def test_assistant_or_undeclared_reviewer_is_not_human():
    for reviewer, kind in [('assistant', 'human'), ('Kiro', 'human'), ('Rene', None)]:
        form = filled()
        form['rows'][0].update(reviewer=reviewer, reviewer_kind=kind)
        with pytest.raises(ValueError, match='humana'):
            validate(form)


def test_cannot_score_case_without_generated_answer():
    form = filled()
    form['rows'][2].update(reviewer='Rene', reviewer_kind='human', reviewed_on='2026-10-01')
    form['rows'][2]['criteria']['correct'] = True
    with pytest.raises(ValueError, match='Não há resposta'):
        validate(form)


@pytest.mark.parametrize('mutate', [
    lambda r: r['criteria'].update(correct='true'),
    lambda r: r.update(error_tags=['texto livre com trecho do edital']),
    lambda r: r.update(reviewed_on='2027-01-01'),
    lambda r: r['criteria'].pop('no_mixing')])
def test_malformed_review_is_rejected(mutate):
    form = filled()
    mutate(form['rows'][0])
    with pytest.raises(ValueError):
        validate(form)


def test_not_run_case_keeps_rate_unavailable():
    cp = checkpoint()
    cp['errors'] = [{'case_id': 'c-3', 'cause_type': 'RateLimitError: rate_limit_exceeded'}]
    form = build_form(reference(), DIGEST, cp, cohort='new', variant='alias_items')
    for row in form['rows']:
        if row['answer_state'] != 'not_run':
            row.update(reviewer='Rene', reviewer_kind='human', reviewed_on='2026-10-01',
                       criteria={k: True for k in row['criteria']})
    summary = public_summary(validate(form, cp), form)
    assert summary['answerable']['not_run'] == 1 and summary['answerable']['rate'] is None


def test_partial_review_is_pending_for_quality_gate():
    form = filled()
    form['rows'][0]['criteria']['complete'] = None
    rows = validate(form)
    assert rows[0]['review_status'] == 'partial'
    sources = {r['case_id']: {'pncp_id': 'p', 'hashes': ['b' * 64]} for r in rows}
    gate = quality_rows(rows, sources=sources, approved={r['case_id']: True for r in rows}, natural=True)
    assert gate[0]['review_status'] == 'pending' and gate[0]['correct'] is None
    assert 'references_or_human_reviews_pending' in assess_release(gate)['reasons']


def test_mixing_error_makes_gate_answer_incorrect():
    form = filled()
    form['rows'][0]['criteria']['no_mixing'] = False
    rows = validate(form)
    sources = {r['case_id']: {'pncp_id': 'p', 'hashes': ['b' * 64]} for r in rows}
    gate = quality_rows(rows, sources=sources, approved={r['case_id']: True for r in rows}, natural=True)
    assert gate[0]['correct'] is False and gate[1]['correct'] is True


def test_refresh_keeps_identical_reviews_and_reopens_changed_answer():
    form = filled()
    cp = checkpoint()
    cp['answers'][0]['response']['answer'] = 'nova resposta'
    cp['errors'] = []
    cp['answers'].append({'case_id': 'c-3', 'response': response('answered', 'nova')})
    fresh = refresh_form(form, reference(), DIGEST, cp)
    rows = {r['case_id']: r for r in fresh['rows']}
    assert fresh['reopened_after_answer_change'] == ['c-1']
    assert all(v is None for v in rows['c-1']['criteria'].values())
    assert rows['c-2']['criteria']['correct'] is True and rows['c-3']['answer_state'] == 'answered'
    assert validate(fresh, cp)[1]['review_status'] == 'human_reviewed'


def test_answer_hash_ignores_operational_fields_but_not_citations():
    a = response('answered', 'x')
    b = copy.deepcopy(a); b['generation_latency_ms'] = 5
    c = copy.deepcopy(a); c['citations'][0]['quote'] = 'y'
    assert answer_sha256(a) == answer_sha256(b) != answer_sha256(c)
