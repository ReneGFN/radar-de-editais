from langchain_core.documents import Document
from radar.item_structure import index_items,select_items,diverse


def row(page,text,start=0,end=None,ident=None):
    end=len(text) if end is None else end
    return (ident or f'p{page}-{start}',text[start:end],'pncp',1,page,start,end,'https://pncp.gov.br/source')


def test_continuation_stops_at_next_item_and_preserves_literal_pages():
    pages={(1,1):'Item 4 Desktop\nUNID 02\nRAM16GB', (1,2):'Garantia12meses\nItem 5 Monitor\nUNID 10'}
    docs=select_items('Garantia do item4'.replace('item4','item 4'),pages,[row(n,t) for (_,n),t in pages.items()],[])
    assert len(docs)==2
    assert 'Item 5' not in ''.join(d.page_content for d in docs)
    assert docs[1].metadata['item_continuation']=='inferred_requires_review'
    for d in docs:
        m=d.metadata;assert d.page_content==pages[(1,m['page'])][m['start']:m['end']]


def test_no_continuation_across_file_page_gap_reset_or_fourth_page():
    pages={(1,1):'Item 1 desktop',(1,2):'continua',(1,3):'continua',(1,4):'nao ligar',(1,6):'gap',(2,1):'outro arquivo'}
    assert [s[0] for s in index_items(pages)[0]['spans']]==[1,2,3]
    assert index_items({(1,1):'Item 1 x',(1,2):'ANEXO II\noutro assunto'})[0]['spans']==[(1,0,8)]


def test_table_row_recognition_requires_unit_not_arbitrary_number():
    blocks=index_items({(1,1):'04\nCOMPUTADOR\nUNID 02\nRAM16GB'})
    assert blocks[0]['item']=='4' and blocks[0]['recognition']=='table_row'
    assert index_items({(1,1):'04\ntexto sem unidade'})==[]


def test_overlap_dedup_keeps_other_pages_and_files():
    def doc(seq,page,a,b):return Document(page_content='x'*(b-a),metadata={'pncp_id':'a','document_sequence':seq,'page':page,'start':a,'end':b})
    assert len(diverse([doc(1,1,0,100),doc(1,1,10,110),doc(1,2,0,100),doc(2,1,0,100)]))==3


def test_unknown_item_falls_back_and_clause_is_not_item_identity():
    fallback=[Document(page_content='x',metadata={'pncp_id':'a','document_sequence':1,'page':1,'start':0,'end':1})]
    assert select_items('item 1.2',{},[],fallback)==fallback
    assert select_items('item 999',{},[],fallback)==fallback


def test_two_requested_items_and_offsets_no_false_join():
    text='Item 1 desktop\nUNID02\nItem 2 notebook\nUNID07'
    docs=select_items('item 1 e item 2', {(1,1):text},[row(1,text)],[])
    assert {d.metadata['item_number'] for d in docs}=={'1','2'}
    assert all(not ('Item 1' in d.page_content and 'Item 2' in d.page_content) for d in docs)


def test_segments_of_same_chunk_have_distinct_ids_and_literal_quantity_offsets():
    text='Item 1 desktop\nUNID 02\nItem 2 notebook\nUNID 07'
    docs=select_items('item 1 e item 2',{(1,1):text},[row(1,text)],[])
    assert len({d.metadata['id'] for d in docs})==2
    assert {d.metadata['source_chunk_id'] for d in docs}=={'p1-0'}
    for d in docs:
        for q in d.metadata['quantity_candidates']:
            assert q['quote']==text[q['start']:q['end']]
    assert docs[0].metadata['quantity_candidates'][0]['quote']=='UNID 02'


def test_literal_sources_validate_with_derived_passage_ids():
    from radar.generation import validate_answer
    from radar.citations import attach_literal_sources
    text='Item 1 Desktop\nUNID 02'
    docs=select_items('item 1',{(1,1):text},[row(1,text)],[])
    payload={'status':'answered','reason':'','claims':[{'text':'Duas unidades.', 'evidence':[{'chunk_id':docs[0].metadata['id']}]}]}
    validated=validate_answer(attach_literal_sources(payload,docs),docs)
    assert validated['citations'][0]['quote']==text
    assert validated['citations'][0]['source_chunk_id']=='p1-0'


def test_repeated_identical_item_passage_dedup_but_not_another_item():
    def d(page,item):return Document(page_content='Garantia 12 meses.',metadata={'pncp_id':'a','document_sequence':1,'page':page,'start':0,'end':18,'item_number':item})
    assert len(diverse([d(1,'4'),d(2,'4'),d(3,'5')]))==2
