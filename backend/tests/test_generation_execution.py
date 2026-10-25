import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'generation_execution', Path(__file__).resolve().parents[2] / 'ops/report-generation-execution.py')
execution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(execution)


def _answer(case_id, status='answered', tokens=100, ms=900.0):
    return {'case_id': case_id, 'expected_answer': 'GABARITO SECRETO', 'total_latency_ms': ms + 100,
            'response': {'status': status, 'answer': 'TEXTO BRUTO', 'claims': [{'text': 'x'}],
                         'citations': [{'quote': 'trecho'}], 'citation_integrity': 'passed',
                         'usage': {'input_tokens': tokens, 'output_tokens': 10},
                         'generation_latency_ms': ms, 'billing': 'free'}}


def test_counts_retry_after_429_and_validator_rejection_without_copying_text():
    checkpoint = {'answers': [_answer('a'), _answer('b', 'refused', 300)],
                  'errors': [{'case_id': 'b', 'http_status': 429, 'cause_type': 'RateLimitError: x'},
                             {'case_id': 'c', 'cause_type': 'ValueError: Quantidade sem apoio literal'}]}
    summary = execution.summarize_checkpoint(checkpoint)
    assert summary['calls_attempted'] == 4
    assert summary['cases_completed'] == 3
    assert summary['accepted_answers'] == 2
    assert summary['rate_limited_then_accepted'] == ['b']
    assert summary['rejected_by_validator_case_ids'] == ['c']
    assert summary['states'] == {'answered': 1, 'refused': 1, 'rejected_by_validator': 1}
    assert summary['input_tokens_accepted'] == {'n': 2, 'median': 200.0, 'total': 400}
    text = repr(summary)
    for private in ('TEXTO BRUTO', 'GABARITO', 'trecho'):
        assert private not in text
    execution.assert_public(summary)


def test_repeated_accepted_case_is_refused():
    with pytest.raises(ValueError, match='repetido'):
        execution.summarize_checkpoint({'answers': [_answer('a'), _answer('a')], 'errors': []})


def test_private_field_in_report_is_refused():
    with pytest.raises(ValueError, match='Campo privado'):
        execution.assert_public({'groups': {'x': [{'answer': 'vazou'}]}})
