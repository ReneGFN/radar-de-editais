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


def offset_inputs(inputs):
    ref,prepared,manifest=copy.deepcopy(inputs)
    chunk=prepared['chunks'][0];chunk.update(start=0,end=len(chunk['text']))
    page=chunk['text']+' Atendimento no local após o chamado.'
    prepared['documents']=[{'pncp_id':'edital','document_sequence':1,'pages':[{'page':2,'text':page}]}]
    ref['evidence_format']='page_offsets_v1'
    ref['cases'][0]['evidence'][0].update(start=0,end=len(page),quote=page)
    return ref,prepared,manifest


def test_page_quote_can_span_multiple_chunks_without_changing_gold(inputs):
    ref,prepared,manifest=offset_inputs(inputs)
    assert ref['cases'][0]['evidence'][0]['quote'] not in prepared['chunks'][0]['text']
    assert validation.validate(ref,prepared,manifest)['evidence_integrity']=='passed'


@pytest.mark.parametrize('field,value',[('quote','Invented'),('start',True),('end',9999),('start',-1)])
def test_offset_gold_tampering_rejected(inputs,field,value):
    ref,prepared,manifest=offset_inputs(inputs)
    ref['cases'][0]['evidence'][0][field]=value
    with pytest.raises(ValueError):validation.validate(ref,prepared,manifest)


def test_anchor_outside_reference_span_rejected(inputs):
    ref,prepared,manifest=offset_inputs(inputs)
    prepared['chunks'][0].update(start=100,end=120)
    with pytest.raises(ValueError):validation.validate(ref,prepared,manifest)
