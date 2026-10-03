import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('holdout_pipeline', Path(__file__).resolve().parents[2] / 'ops/holdout-pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)

SHA = 'a' * 64
URL = 'https://pncp.gov.br/pncp-api/v1/orgaos/1/compras/2026/1/arquivos/1'


def _case(case_id, status='approved', record=True):
    case = {'id': case_id, 'kind': 'answerable', 'review_status': status, 'question': 'q',
            'evidence': [{'document_sha256': SHA, 'url': URL, 'page': 2, 'char_start': 0, 'char_end': 5}]}
    if record:
        case['review_record'] = {'reviewer_kind': 'human', 'reviewed_on': '2026-10-03'}
    return case


def _manifest(url=URL, sha=SHA):
    return {'editais': [{'pncp_id': 'x', 'documents': [{'sequence': 1, 'sha256': sha, 'url': url, 'page_count': 3}]}]}


def test_pending_case_blocks_everything():
    reference = {'status': 'approved', 'cases': [_case('h-01'), _case('h-02', 'pending_user_approval')]}
    assert pipeline.approval_blockers(reference, 'd', set()) == ['case_not_approved:h-02']


def test_current_draft_status_and_revocation_block():
    reference = {'status': 'draft_pending_user_approval', 'cases': [_case('h-01')]}
    blockers = pipeline.approval_blockers(reference, 'd', {'d'})
    assert 'reference_approval_revoked' in blockers and 'reference_status_not_approved' in blockers


def test_approved_without_human_record_blocks():
    reference = {'status': 'approved', 'cases': [_case('h-01', record=False)]}
    assert pipeline.approval_blockers(reference, 'd', set()) == ['case_without_human_review_record:h-01']


def test_fully_approved_reference_has_no_approval_blockers():
    assert pipeline.approval_blockers({'status': 'approved', 'cases': [_case('h-01')]}, 'd', set()) == []


@pytest.mark.parametrize('url', ['http://pncp.gov.br/a', 'https://pncp.gov.br.evil.com/a', 'https://evil.com/pncp.gov.br/'])
def test_only_https_pncp_urls_are_accepted(url):
    assert pipeline.source_blockers(_manifest(url=url)) == ['source_url_not_https_pncp:x']


def test_private_pdf_must_exist_and_match_hash(tmp_path):
    content = b'%PDF-1.4 teste'
    digest = hashlib.sha256(content).hexdigest()
    assert pipeline.source_blockers(_manifest(sha=digest), tmp_path) == ['private_pdf_missing:' + digest[:16]]
    (tmp_path / f'{digest}.pdf').write_bytes(b'%PDF-alterado')
    assert pipeline.source_blockers(_manifest(sha=digest), tmp_path) == ['private_pdf_hash_mismatch:' + digest[:16]]
    (tmp_path / f'{digest}.pdf').write_bytes(content)
    assert pipeline.source_blockers(_manifest(sha=digest), tmp_path) == []


def test_evidence_must_match_manifest_url_page_and_offsets():
    case = _case('h-01')
    case['evidence'][0].update(url=URL + '0', page=9, char_start=5, char_end=5)
    blockers = pipeline.evidence_blockers({'cases': [case]}, _manifest())
    assert blockers == ['evidence_url_differs_from_manifest:h-01', 'evidence_page_out_of_range:h-01',
                        'evidence_offsets_invalid:h-01']


def test_evidence_url_may_carry_only_its_own_page_anchor():
    case = _case('h-01')
    case['evidence'][0]['url'] = URL + '#page=2'
    assert pipeline.evidence_blockers({'cases': [case]}, _manifest()) == []
    case['evidence'][0]['url'] = URL + '#page=3'
    assert pipeline.evidence_blockers({'cases': [case]}, _manifest()) == ['evidence_url_differs_from_manifest:h-01']


def test_snapshot_is_deterministic_and_never_the_development_one(monkeypatch):
    first = pipeline.planned_snapshot_id(_manifest())
    assert first == pipeline.planned_snapshot_id(_manifest()) and first != pipeline.DEVELOPMENT_SNAPSHOT
    monkeypatch.setattr(pipeline, 'DEVELOPMENT_SNAPSHOT', first)
    with pytest.raises(ValueError, match='colidiu'):
        pipeline.planned_snapshot_id(_manifest())


def test_protocol_refuses_code_or_reference_drift():
    check = {'reference_sha256': 'r', 'manifest_sha256': 'm', 'planned_snapshot_id': 's'}
    protocol = dict(check, code_sha256={'ops/a.py': '1'})
    pipeline.assert_protocol(protocol, check, current_code={'ops/a.py': '1'})
    with pytest.raises(SystemExit, match='Código mudou'):
        pipeline.assert_protocol(protocol, check, current_code={'ops/a.py': '2'})
    with pytest.raises(SystemExit, match='reference_sha256'):
        pipeline.assert_protocol(protocol, dict(check, reference_sha256='x'), current_code={'ops/a.py': '1'})


def test_protocol_records_hashes_model_and_snapshot():
    check = {'reference_sha256': 'r', 'manifest_sha256': 'm', 'planned_snapshot_id': 's'}
    protocol = pipeline.build_protocol(check, variant='alias_items', system_prompt_sha256='p', model='m1')
    assert protocol['development_snapshot_untouched'] == '1446c44aca18011a'
    assert set(protocol['code_sha256']) == set(pipeline.CODE)
    assert protocol['retrieval']['max_passages'] == 5 and protocol['gold_in_prompt'] is False
    with pytest.raises(SystemExit):
        pipeline.build_protocol(check, variant='desconhecida', system_prompt_sha256='p', model='m1')


class RateLimited(Exception):
    status_code = 429
    kind = 'RateLimitError: rate_limit_exceeded'


class Rejected(Exception):
    kind = 'ValueError: Quantidade sem apoio literal'


def test_resume_skips_accepted_and_rejected_and_stops_on_429():
    cases = [{'id': f'h-0{i}', 'kind': 'answerable'} for i in range(1, 6)]
    checkpoint = {'answers': [{'case_id': 'h-01'}], 'errors': [{'case_id': 'h-02', 'cause_type': Rejected.kind}]}
    called = []

    def fake(case):
        called.append(case['id'])
        if case['id'] == 'h-04':
            raise RateLimited()
        return {'status': 'answered'}
    outcome = pipeline.run_cases(cases, checkpoint, fake, max_calls=10, interval=0, sleep=lambda s: None, now=lambda: 't')
    assert outcome == 'stopped_on_error' and called == ['h-03', 'h-04']
    assert [a['case_id'] for a in checkpoint['answers']] == ['h-01', 'h-03']
    assert checkpoint['errors'][-1] == {'case_id': 'h-04', 'error_type': 'RateLimited',
        'cause_type': RateLimited.kind, 'http_status': 429, 'date_utc': 't'}
    called.clear()
    outcome = pipeline.run_cases(cases, checkpoint, lambda c: called.append(c['id']) or {'status': 'answered'},
                                 max_calls=1, interval=0, sleep=lambda s: None)
    assert outcome == 'call_budget_reached' and called == ['h-04']


def test_validator_rejection_is_recorded_and_run_continues():
    cases = [{'id': 'h-01', 'kind': 'answerable'}, {'id': 'h-02', 'kind': 'answerable'}]
    checkpoint = {'answers': [], 'errors': []}

    def fake(case):
        if case['id'] == 'h-01':
            raise Rejected()
        return {'status': 'answered'}
    assert pipeline.run_cases(cases, checkpoint, fake, max_calls=5, interval=0, sleep=lambda s: None) == 'completed'
    assert [e['case_id'] for e in checkpoint['errors']] == ['h-01']
    assert [a['case_id'] for a in checkpoint['answers']] == ['h-02']
    assert 'expected_answer' not in json.dumps(checkpoint)
