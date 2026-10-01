import pytest
from langchain_core.documents import Document
from radar.citations import source_aliases,alias_schema,resolve_aliases,attach_literal_sources
from radar.generation import SCHEMA,validate_answer


def docs():
    return [Document(page_content='RAM 16 GB.',metadata={'id':'a'*64,'pncp_id':'edital','page':1,'document_sequence':1})]


def test_alias_resolves_exactly_to_original_source_and_literal_text():
    documents=docs();aliases=source_aliases(documents)
    payload={'status':'answered','reason':'','claims':[{'text':'RAM 16 GB.','evidence':[{'chunk_id':'S1'}]}]}
    result=validate_answer(attach_literal_sources(resolve_aliases(payload,aliases),documents),documents)
    assert result['claims'][0]['evidence'][0]['chunk_id']=='a'*64
    assert result['citations'][0]['quote']=='RAM 16 GB.'
    assert payload['claims'][0]['evidence'][0]['chunk_id']=='S1'
    assert result['semantic_support']=='requires_review'


@pytest.mark.parametrize('identifier',['S2','s1','S01','S1extra','a'*64,None,[],1])
def test_unrecognized_alias_is_never_guessed(identifier):
    with pytest.raises(ValueError):resolve_aliases({'claims':[{'evidence':[{'chunk_id':identifier}]}]},source_aliases(docs()))


def test_enum_contains_only_current_request_sources():
    schema=alias_schema(SCHEMA,source_aliases(docs()))
    field=schema['properties']['claims']['items']['properties']['evidence']['items']['properties']['chunk_id']
    assert field['enum']==['S1']
    assert 'enum' not in SCHEMA['properties']['claims']['items']['properties']['evidence']['items']['properties']['chunk_id']


def test_duplicate_sources_rejected_and_mapping_is_request_local():
    with pytest.raises(ValueError):source_aliases(docs()*2)
    other=docs();other[0].metadata['id']='b'*64
    assert source_aliases(other)['S1']=='b'*64
    assert source_aliases(docs())['S1']=='a'*64
