import pytest
from langchain_core.documents import Document
from radar.evaluation import score_case, summarize
from radar import retrieval


def case():
    return {'kind':'answerable','review_status':'approved','pncp_id':'edital',
            'evidence':[{'chunk_id':'expected','document_sequence':1,'page':2,'quote':'12 meses'}]}


def doc(key, pncp='edital', text='Garantia de 12 meses.', page=2):
    return Document(page_content=text,metadata={'id':key,'pncp_id':pncp,'document_sequence':1,'page':page})


def test_rank_and_cutoff():
    docs=[doc('other'),doc('expected')]
    score=score_case(case(),docs)
    assert score['first_known_rank']==2 and score['reciprocal_rank_at_k']==.5
    assert not score_case(case(),docs,k=1)['known_chunk_hit_at_k']


def test_overlapping_chunk_preserves_quote_without_exact_id():
    score=score_case(case(),[doc('overlap')])
    assert not score['known_chunk_hit_at_k']
    assert score['all_known_quotes_supported_at_k']
    assert not score_case(case(),[doc('overlap',page=3)])['all_known_quotes_supported_at_k']


def test_other_edital_cannot_count_as_success():
    with pytest.raises(ValueError,match='edital'):
        score_case(case(),[doc('expected',pncp='another')])


def test_refusal_excluded_from_retrieval_accuracy():
    c=case();c['kind']='out_of_scope'
    with pytest.raises(ValueError):score_case(c,[])


def test_summary_counts_and_nearest_rank_percentile():
    rows=[]
    for hit,latency in [(True,10),(False,30)]:
        rows.append(dict(known_chunk_hit_at_k=hit,reciprocal_rank_at_k=1.0 if hit else 0,
                         all_known_quotes_supported_at_k=hit,latency_ms=latency))
    result=summarize(rows)
    assert result['known_chunk_hit_at_5']==.5 and result['latency_median_ms']==20
    assert result['latency_p95_ms']==30


def test_keyword_does_not_initialize_embedding(monkeypatch):
    monkeypatch.setattr(retrieval,'local_embeddings',lambda:pytest.fail('keyword initialized embedding'))
    seen=[]
    def branch(inputs,semantic):
        seen.append((inputs['lexical_strategy'],semantic))
        return [('expected','text','edital',1,2,0,4,'https://pncp.gov.br/example')]
    monkeypatch.setattr(retrieval,'branch',branch)
    docs,trace=retrieval.retrieve_with_trace('SSD','snapshot','edital','keyword','any')
    assert seen==[('any',False)] and docs[0].metadata['id']=='expected'
    assert trace['candidate_ids']=={'keyword':['expected']}


@pytest.mark.parametrize('query,mode,strategy', [('','hybrid','all'),('SSD','invalid','all'),('SSD','hybrid','invalid')])
def test_invalid_search_request_rejected(query,mode,strategy):
    with pytest.raises(ValueError):retrieval.retrieve_with_trace(query,'snapshot','edital',mode,strategy)
