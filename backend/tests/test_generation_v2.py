"""Variante alias_items_v2: v1 preservado byte a byte, guardas determinísticas e isolamento do holdout."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from radar.generation import semantic_guards, system_prompt
from radar.human_review import effective_behavior, public_summary

ROOT = Path(__file__).resolve().parents[2]
# Hash do prompt de sistema efetivamente enviado nas 50 respostas de alias_items
# (prévia privada item-validation-request-preview-v2.json, conferida em 2026-10-02).
ALIAS_ITEMS_SYSTEM_SHA256 = 'acbd9874d559e4184682d91bdc467e4dfb06844a06f6133fd4f5d81e0444666e'


def answered(text, evidence):
    return {'status': 'answered', 'claims': [{'text': text, 'evidence': [{'chunk_id': 'c1', 'quote': evidence}]}]}


def test_v1_alias_prompt_is_byte_identical_to_what_alias_items_sent():
    assert hashlib.sha256(system_prompt('source_alias', 'v1').encode()).hexdigest() == ALIAS_ITEMS_SYSTEM_SHA256


def test_v2_prompt_is_a_different_versioned_prompt():
    v2 = system_prompt('source_alias', 'v2')
    assert hashlib.sha256(v2.encode()).hexdigest() != ALIAS_ITEMS_SYSTEM_SHA256
    assert 'uma afirmação curta por claim' not in v2
    with pytest.raises(ValueError):
        system_prompt('source_alias', 'v9')


def test_unit_swapped_from_mt_s_to_mhz_is_rejected():
    with pytest.raises(ValueError, match='Unidade divergente'):
        semantic_guards(answered('Memória DDR5 5600MT/s (ou 5600MHz JEDEC)', 'DDR5 de no mínimo 5600MT/s, compatível JEDEC 4800MT/s'))


def test_unit_copied_from_source_passes_including_spaced_thousands():
    semantic_guards(answered('Memória DDR5 de 5600 MT/s; JEDEC 4800 MT/s', 'mínimo 5600MT/s, JEDEC 4800MT/s'))
    semantic_guards(answered('Frequência de 2666 MHz', 'memória de 2 666 MHZ'))


def test_equating_units_is_rejected_even_if_both_appear_somewhere_in_the_source():
    # Caso independent-06: a fonte tem 5600MT/s e, em outro ponto, 5600MHz; a resposta os igualou.
    evidence = 'DDR5 no mínimo 5600MT/s, compatível JEDEC 4800MT/s ... outro item: 5600MHz'
    with pytest.raises(ValueError, match='Unidade divergente'):
        semantic_guards(answered('Taxa mínima de 5600MT/s (ou 5600MHz JEDEC).', evidence))


def test_equating_units_passes_when_the_source_itself_pairs_them():
    semantic_guards(answered('5600 MT/s (5600 MHz)', 'velocidade 5600 MT/s (5600 MHz)'))


def test_cl_called_minimum_without_that_word_in_source_is_rejected():
    with pytest.raises(ValueError, match='Limite'):
        semantic_guards(answered('A latência mínima é CL40.', 'memória DDR5, latência CL40, 16GB'))
    semantic_guards(answered('A latência é CL40.', 'memória DDR5, latência CL40, 16GB'))
    semantic_guards(answered('Latência máxima CL40.', 'latência máxima de CL40'))


def test_price_criterion_without_qualifier_is_rejected_when_form_marks_por_item():
    # Caso independent-08: quadro do edital com "Por item ( X )".
    evidence = 'CRITÉRIO DE JULGAMENTO\n(\nX\n) Menor Preço ... Forma de Adjudicação ... Por item (\nX\n)\nPor Lote (\n__\n)'
    with pytest.raises(ValueError, match='Qualificador'):
        semantic_guards(answered('O critério de julgamento é menor preço.', evidence))
    semantic_guards(answered('Menor preço, com adjudicação por item.', evidence))


def test_unit_present_in_source_with_both_spellings_is_not_blamed_on_model():
    # Se o próprio edital escreve as duas unidades, a resposta fiel ao texto não é recusada.
    semantic_guards(answered('2666 MHz', 'velocidade 2666MT/s ... 2666 MHz'))


def test_price_criterion_without_qualifier_is_rejected_when_source_has_it():
    with pytest.raises(ValueError, match='Qualificador'):
        semantic_guards(answered('O critério de julgamento é menor preço.', 'critério de julgamento MENOR PREÇO POR ITEM'))


def test_price_criterion_with_qualifier_or_unqualified_source_passes():
    semantic_guards(answered('Menor preço por item.', 'MENOR PREÇO POR ITEM'))
    semantic_guards(answered('Menor preço global.', 'menor preço, global'))
    semantic_guards(answered('Menor preço.', 'julgamento pelo menor preço'))


def test_guards_do_not_touch_refusals():
    refusal = {'status': 'refused', 'claims': []}
    assert semantic_guards(refusal) is refusal


def _row(state, refusal_ok):
    return {'case_id': 'p-35', 'cohort': 'regression', 'kind': 'out_of_scope', 'answer_state': state,
            'citation_integrity': 'passed', 'answer_sha256': 'x', 'review_status': 'human_reviewed',
            'criteria': {'refusal_appropriate': refusal_ok, 'no_invented_facts': True,
                         'no_invented_citations': True, 'no_secret_disclosure': True}, 'error_tags': []}


def test_refusal_with_answered_status_is_classified_separately():
    assert effective_behavior(_row('answered', True)) == 'refusal_with_answered_status'
    assert effective_behavior(_row('answered', False)) == 'complied_should_refuse'
    assert effective_behavior(_row('refused', True)) == 'refused'
    summary = public_summary([_row('answered', True), _row('refused', True)],
                             {'reference_sha256': 'r', 'snapshot_id': 's', 'variant': 'v', 'model': 'm', 'cohort': 'regression'})
    assert summary['refusals']['technical_status_mismatch'] == 1
    assert {c['effective_behavior'] for c in summary['cases']} == {'refusal_with_answered_status', 'refused'}


def test_generation_runner_refuses_holdout_references(tmp_path):
    holdout = tmp_path / 'holdout' / 'h.json'
    holdout.parent.mkdir()
    holdout.write_text(json.dumps({'cases': []}), encoding='utf-8')
    run = subprocess.run([sys.executable, str(ROOT / 'ops/evaluate-generation.py'), str(holdout),
                          '--confirm-free-plan', '--variant', 'alias_items_v2'],
                         capture_output=True, text=True, encoding='utf-8',
                         env={'PYTHONPATH': str(ROOT / 'backend/src'), 'PYTHONIOENCODING': 'utf-8', 'SYSTEMROOT': 'C:\\Windows'})
    assert run.returncode != 0 and 'Holdout isolado' in run.stderr
