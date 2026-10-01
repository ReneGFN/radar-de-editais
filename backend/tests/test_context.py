import pytest
from langchain_core.documents import Document
from radar.context import page_window
from radar.citations import attach_literal_sources,source_schema
from radar.generation import SCHEMA,validate_answer


def doc(page,start,end):
    return Document(page_content=page[start:end],metadata={'id':'anchor','start':start,'end':end,'pncp_id':'edital','document_sequence':1,'page':2})


def test_window_keeps_header_specification_and_original_offsets():
    page='Lote 3\nItem 1 desktop\nRAM 16 GB\nSSD 480 GB\nMonitor Full HD'
    d=doc(page,21,30);expanded=page_window(d,page)
    assert expanded.page_content==page
    assert expanded.metadata['anchor_start']==21 and expanded.metadata['start']==0
    assert expanded.metadata['id']=='anchor' and expanded.metadata['page']==2


def test_window_bounds_and_exact_original_substring():
    page='a'*8000;expanded=page_window(doc(page,4000,4500),page)
    assert len(expanded.page_content)<=2000
    assert expanded.page_content==page[expanded.metadata['start']:expanded.metadata['end']]


def test_wrong_page_or_offsets_rejected():
    with pytest.raises(ValueError):page_window(doc('original',0,8),'modified')


def test_server_citation_is_original_and_does_not_certify_semantics():
    page='Garantia de 12 meses.';documents=[doc(page,0,len(page))]
    payload={'status':'answered','reason':'','claims':[{'text':'Garantia de 36 meses.','evidence':[{'chunk_id':'anchor'}]}]}
    result=validate_answer(attach_literal_sources(payload,documents),documents)
    assert result['citations'][0]['quote']==page
    assert result['semantic_support']=='requires_review'
    assert 'quote' not in payload['claims'][0]['evidence'][0]


def test_unknown_source_and_model_quote_rejected_in_source_id_mode():
    for evidence in [{'chunk_id':'unknown'},{'chunk_id':'anchor','quote':'invented'}]:
        with pytest.raises(ValueError):attach_literal_sources({'claims':[{'evidence':[evidence]}]},[doc('text',0,4)])


def test_source_schema_does_not_mutate_original_schema():
    new=source_schema(SCHEMA)
    assert new['properties']['claims']['items']['properties']['evidence']['items']['required']==['chunk_id']
    assert SCHEMA['properties']['claims']['items']['properties']['evidence']['items']['required']==['chunk_id','quote']


def test_long_anchor_is_not_cut_to_make_room_for_padding():
    page='a'*5000
    original=doc(page,1000,2900)
    expanded=page_window(original,page)
    assert expanded.metadata['start']<=1000 and expanded.metadata['end']>=2900
    assert original.page_content in expanded.page_content
    assert len(expanded.page_content)<=2000
