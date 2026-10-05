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
