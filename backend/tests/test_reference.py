"""A integridade da avaliação não pode aceitar fonte ou aprovação inventada."""
import copy
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('reference_validation', Path(__file__).resolve().parents[2] / 'ops/validate-reference.py')
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


@pytest.fixture
def inputs():
    snapshot = 'a' * 16
    digest = 'b' * 64
    source = {'sequence': 1, 'sha256': digest, 'url': 'https://pncp.gov.br/example'}
    chunk = {'id': 'chunk', 'pncp_id': 'edital', 'document_sequence': 1,
             'page': 2, 'text': 'Garantia de 12 meses.', 'document_sha': digest}
    evidence = {'chunk_id': 'chunk', 'document_sequence': 1, 'page': 2,
                'quote': '12 meses', 'document_sha256': digest, 'url': source['url']}
    ref = {'snapshot_id': snapshot, 'target_counts': {'answerable': 1}, 'cases': [
        {'id': 'case', 'kind': 'answerable', 'review_status': 'draft', 'pncp_id': 'edital',
         'question': 'Qual a garantia?', 'expected_answer': '12 meses', 'evidence': [evidence]}]}
    return ref, {'snapshot_id': snapshot, 'chunks': [chunk]}, {
        'snapshot_id': snapshot, 'editais': [{'pncp_id': 'edital', 'uf': 'SP', 'documents': [source]}]}


def test_valid_reference_is_not_human_approval(inputs):
    report = validation.validate(*inputs)
    assert report['evidence_integrity'] == 'passed'
    assert report['approved'] == 0 and report['draft'] == 1
    assert report['evidence_documents'] == 1


@pytest.mark.parametrize('field,value', [
    ('quote', '36 meses'), ('page', 3), ('document_sha256', 'c' * 64),
    ('url', 'https://invalid.example'), ('document_sequence', 2),
])
def test_tampered_evidence_is_rejected(inputs, field, value):
    ref, prepared, manifest = copy.deepcopy(inputs)
    ref['cases'][0]['evidence'][0][field] = value
    with pytest.raises((ValueError, KeyError)):
        validation.validate(ref, prepared, manifest)


def test_approval_needs_record(inputs):
    ref, prepared, manifest = inputs
    ref['cases'][0]['review_status'] = 'approved'
    with pytest.raises(ValueError, match='Aprovação'):
        validation.validate(ref, prepared, manifest)


def test_missing_cases_cannot_pass_target(inputs):
    ref, prepared, manifest = inputs
    ref['target_counts']['answerable'] = 30
    with pytest.raises(ValueError, match='Quantidade'):
        validation.validate(ref, prepared, manifest)


def test_snapshot_mismatch_rejected(inputs):
    ref, prepared, manifest = inputs
    prepared['snapshot_id'] = 'd' * 16
    with pytest.raises(ValueError, match='Snapshot'):
        validation.validate(ref, prepared, manifest)
