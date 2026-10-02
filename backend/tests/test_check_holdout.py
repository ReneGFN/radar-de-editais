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
