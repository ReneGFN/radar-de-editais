from radar.reranking import rerank_coverage


def test_complete_query_coverage_can_beat_generic_rank():
    generic=('a','notebook equipamento',None)
    specific=('b','notebook memória RAM frequência 3200 MHz',None)
    assert rerank_coverage([(generic,.033),(specific,.031)],'RAM frequência')[0][0][0]=='b'


def test_empty_terms_preserve_rank_and_ties_are_deterministic():
    assert [r[0][0] for r in rerank_coverage([(('b','x'),.02),(('a','y'),.02)],'qual é')]==['a','b']


def test_only_supplied_candidates_are_selected_and_limit_is_respected():
    rows=[((str(i),'SSD'),.03) for i in range(10)]
    assert len(rerank_coverage(rows,'ssd'))==5
    assert all(row in [x[0] for x in rows] for row,score in rerank_coverage(rows,'ssd'))
