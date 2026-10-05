"""Verificação de trechos do holdout: offset errado, dado pessoal e aprovação sem registro falham."""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('check_holdout_cli', Path(__file__).resolve().parents[2] / 'ops/check-holdout.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SHA = 'a' * 64
TEXT = 'Item 01 Notebook UN 01 100 entrega em 10 dias úteis contato fulano@orgao.gov.br'


def pages(tmp_path):
    path = tmp_path / 'pages.json'
    path.write_text(json.dumps({'documents': [{'sha256': SHA, 'pages': [{'page': 3, 'text': TEXT}]}]}), encoding='utf-8')
    return path


def case(quote, start, **extra):
    return {'id': 'h-1', 'kind': 'answerable', 'review_status': 'pending_user_approval',
            'evidence': [{'document_sha256': SHA, 'page': 3, 'char_start': start,
                          'char_end': start + len(quote), 'quote': quote}], **extra}


def test_quote_at_declared_offset_passes(tmp_path):
    quote = 'UN 01 100'
    assert module.quote_checks({'cases': [case(quote, TEXT.index(quote))]}, pages(tmp_path)) == []


def test_shifted_offset_fails(tmp_path):
    quote = 'UN 01 100'
    problems = module.quote_checks({'cases': [case(quote, TEXT.index(quote) + 1)]}, pages(tmp_path))
    assert problems == [{'type': 'quote_not_at_declared_offset', 'value': 'h-1'}]


def test_wrong_page_fails(tmp_path):
    quote = 'UN 01 100'
    bad = case(quote, TEXT.index(quote))
    bad['evidence'][0]['page'] = 4
    assert module.quote_checks({'cases': [bad]}, pages(tmp_path))[0]['type'] == 'quote_not_at_declared_offset'


def test_email_in_quote_is_flagged(tmp_path):
    quote = 'fulano@orgao.gov.br'
    problems = module.quote_checks({'cases': [case(quote, TEXT.index(quote))]}, pages(tmp_path))
    assert {'type': 'personal_data_in_quote', 'value': 'h-1'} in problems


def test_approved_without_record_fails(tmp_path):
    quote = 'UN 01 100'
    approved = case(quote, TEXT.index(quote), review_status='approved')
    assert module.quote_checks({'cases': [approved]}, pages(tmp_path)) == [{'type': 'approved_without_record', 'value': 'h-1'}]



def _revocation(tmp_path, digest):
    (tmp_path / 'holdout-v1-approval-revocation.json').write_text(
        json.dumps({'revokes_reference_sha256': digest}), encoding='utf-8')


def test_revoked_reference_is_never_ready_even_if_all_approved(tmp_path):
    _revocation(tmp_path, SHA)
    reference = {'cases': [{'review_status': 'approved'}]}
    result = {'independent': True, 'quote_violations': []}
    revoked = module.revoked_hashes(tmp_path)
    assert module.ready(result, reference, SHA, revoked) is False
    assert module.ready(result, reference, 'b' * 64, revoked) is True


def test_pending_case_is_not_ready(tmp_path):
    reference = {'cases': [{'review_status': 'approved'}, {'review_status': 'pending_user_approval'}]}
    assert module.ready({'independent': True, 'quote_violations': []}, reference, SHA, set()) is False


def test_revocation_without_valid_hash_is_refused(tmp_path):
    _revocation(tmp_path, 'abc')
    import pytest
    with pytest.raises(SystemExit):
        module.revoked_hashes(tmp_path)
