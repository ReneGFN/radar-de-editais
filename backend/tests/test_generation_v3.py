"""Variante alias_items_v3: v1 e v2 preservados, resposta parcial, recusa com fato da fonte e guarda de quantidade."""
import hashlib
import json
from pathlib import Path

import pytest
from langchain_core.documents import Document

from radar.generation import quantity_guard, system_prompt, validate_answer

ROOT = Path(__file__).resolve().parents[2]
DOC = Document(page_content='3.3 O prazo para entrega será de 30 (trinta) dias a partir do recebimento da Autorização',
               metadata={'id': 'c1', 'page': 4})
CLAIM = {'text': 'Prazo de 30 dias a partir do recebimento da Autorização.',
         'evidence': [{'chunk_id': 'c1', 'quote': 'prazo para entrega será de 30 (trinta) dias'}]}


def payload(status, claims, reason='motivo'):
    return {'status': status, 'reason': reason, 'claims': json.loads(json.dumps(claims))}


def test_v2_prompt_still_matches_the_hash_published_in_its_protocol():
    protocol = json.loads((ROOT / 'reports/generation-protocol-alias-items-v2.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(system_prompt('source_alias', 'v2').encode()).hexdigest() == protocol['system_prompt_sha256']


def test_v3_prompt_extends_v2():
    v2, v3 = system_prompt('source_alias', 'v2'), system_prompt('source_alias', 'v3')
    assert v3.startswith(v2) and v3 != v2


def test_v1_and_v2_still_reject_insufficient_evidence_with_claims():
    # pilot-22 na v2: status insufficient_evidence com uma afirmação válida foi rejeitado.
    with pytest.raises(ValueError, match='Estado incompatível'):
        validate_answer(payload('insufficient_evidence', [CLAIM]), [DOC])


def test_v3_keeps_supported_claims_as_partial_answer():
    result = validate_answer(payload('insufficient_evidence', [CLAIM], 'Marco inicial não informado.'), [DOC],
                             allow_supported_claims=True)
    assert result['status'] == 'answered' and result['partial_answer'] is True
    assert result['model_status'] == 'insufficient_evidence'
    assert 'Marco inicial não informado.' in result['answer'] and '30 dias' in result['answer']


def test_v3_refusal_can_carry_what_the_source_says_with_verified_citation():
    # pilot-36: recusar a alteração e informar a garantia real, citada.
    result = validate_answer(payload('refused', [CLAIM], 'Não altero o conteúdo da fonte.'), [DOC], allow_supported_claims=True)
    assert result['status'] == 'refused' and result['citations']
    assert result['answer'].startswith('Não altero') and '30 dias' in result['answer']
    with pytest.raises(ValueError, match='Estado incompatível'):
        validate_answer(payload('refused', [CLAIM]), [DOC])


def test_v3_still_requires_verified_citation_on_refusal_claims():
    bad = dict(CLAIM, evidence=[{'chunk_id': 'c1', 'quote': 'garantia de 60 meses'}])
    with pytest.raises(ValueError, match='Citação inventada'):
        validate_answer(payload('refused', [bad]), [DOC], allow_supported_claims=True)


def test_v3_answered_without_claims_is_still_rejected():
    with pytest.raises(ValueError, match='Estado incompatível'):
        validate_answer(payload('answered', []), [DOC], allow_supported_claims=True)


def answered(text, evidence):
    return {'status': 'answered', 'claims': [{'text': text, 'evidence': [{'chunk_id': 'c1', 'quote': evidence}]}]}


TABLE = 'ITENS COM COTA 25% ... 3 28 UN D Notebook ... R$ 42.972,03 ... 4 7 UN D Notebook ... COTA 25% MEI/ME/EPP'


def test_quantity_computed_by_the_model_is_rejected():
    # independent-02 na v2: "21 unidades" = 28 - 7, número que não está na tabela.
    with pytest.raises(ValueError, match='Quantidade sem apoio'):
        quantity_guard(answered('Ampla concorrência: 21 unidades.', TABLE))


def test_quantities_copied_from_table_pass():
    quantity_guard(answered('Item 3: 28 unidades (ampla concorrência); item 4: 7 unidades (cota).', TABLE))


def test_number_inside_a_price_does_not_count_as_support():
    with pytest.raises(ValueError, match='Quantidade sem apoio'):
        quantity_guard(answered('São 21 unidades.', 'valor unitário R$ 21,50'))
