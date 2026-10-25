from langchain_core.documents import Document
from radar import retrieval


def test_document_scope_excludes_other_files_and_represents_each_choice(monkeypatch):
    scope=[{'pncp_id':'a','document_sequence':1},{'pncp_id':'b','document_sequence':2}]
    def fake(query,snapshot,pncp,**kwargs):
        seq=kwargs['document_sequences'][0]
        assert kwargs['context_profile']=='chunk'
        return [Document(page_content='real',metadata={'id':pncp,'pncp_id':pncp,'document_sequence':seq}),
                Document(page_content='fora',metadata={'id':'outside','pncp_id':pncp,'document_sequence':99})],{}
    monkeypatch.setattr(retrieval,'retrieve_with_trace',fake)
    docs,_=retrieval.retrieve_document_scope('pergunta','snapshot',scope)
    assert [(d.metadata['pncp_id'],d.metadata['document_sequence']) for d in docs]==[('a',1),('b',2)]


def test_sql_scope_is_parameterized(monkeypatch):
    calls=[]
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def execute(self,query,params):calls.append((query,params));return self
        def fetchall(self):return []
    monkeypatch.setattr(retrieval,'connect',Connection)
    monkeypatch.setattr(retrieval,'register_vector',lambda conn:None)
    retrieval.branch({'snapshot':'snap','edital':'pncp','query':'garantia','filters':{'document_sequences':[1,2]}},False)
    assert 'c.document_sequence = ANY(%s)' in calls[0][0]
    assert calls[0][1][2]==[1,2]


def test_scope_balances_extra_passages_instead_of_filling_first_pdf(monkeypatch):
    def fake(query,snapshot,pncp,**kwargs):
        return [Document(page_content='texto',metadata={'id':f'{pncp}{i}','pncp_id':pncp,'document_sequence':1}) for i in range(5)],{}
    monkeypatch.setattr(retrieval,'retrieve_with_trace',fake)
    scope=[{'pncp_id':p,'document_sequence':1} for p in ['a','b']]
    docs,_=retrieval.retrieve_document_scope('pergunta', 'snapshot',scope)
    assert [d.metadata['pncp_id'] for d in docs]==['a','b','a','b','a']


def test_continuation_uses_selected_pdf_and_literal_offsets(monkeypatch):
    calls=[]
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def execute(self,query,params=None):calls.append((query,params));return self
        def fetchone(self):return ('Garantia de 24 meses.',)
    monkeypatch.setattr(retrieval,'connect',Connection)
    anchor=Document(page_content='GPU ABC 1234',metadata={'id':'anchor','pncp_id':'chosen','document_sequence':3,'page':8,'start':100,'end':112,'url':'https://pncp.gov.br/file'})
    docs=retrieval.adjacent_scope_pages([anchor],'snapshot',lambda d:10)
    assert calls[1][1]==('snapshot','chosen',3,9)
    assert docs[0].metadata['start']==0 and docs[0].metadata['end']==len(docs[0].page_content)
    assert docs[0].metadata['page']==9 and docs[0].metadata['document_sequence']==3


def test_comparison_probes_come_from_query_not_expected_answers(monkeypatch):
    queries=[]
    def fake(query,snapshot,pncp,**kwargs):queries.append(query);return [],{}
    monkeypatch.setattr(retrieval,'retrieve_with_trace',fake)
    monkeypatch.setattr(retrieval,'adjacent_scope_pages',lambda *args:[])
    scope=[{'pncp_id':p,'document_sequence':1} for p in ['a','b']]
    retrieval.retrieve_document_scope('Compare capacidades: GPU ABC 1234 e memória XYZ 5678','snapshot',scope)
    assert 'ABC 1234' in queries and 'XYZ 5678' in queries
    assert len(queries)<=16
