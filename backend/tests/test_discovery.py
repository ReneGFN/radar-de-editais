import pytest
from radar import discovery


def row(identifier, edital):
    return (identifier, 'texto', edital, 1, 2, 0, 5, 'https://pncp.gov.br/pdf')


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(discovery, 'allowed_editais', lambda: {'A': {'agency': 'Órgão A'}, 'B': {}})
    class Embeddings:
        def embed_query(self, query):
            return [0.1]
    monkeypatch.setattr(discovery, 'local_embeddings', Embeddings)


def test_global_diversifies_and_never_claims_exhaustive(setup, monkeypatch):
    monkeypatch.setattr(discovery, 'search_branch', lambda q, allowed, vector=None:
                        [row('a1', 'A'), row('a2', 'A'), row('b', 'B')])
    result = discovery.discover('monitores')
    assert [c['pncp_id'] for c in result['candidates']] == ['A', 'B']
    assert result['exhaustive'] is False
    assert 'text' not in result['candidates'][0]


def test_selected_scope(setup, monkeypatch):
    calls = []
    def branch(q, allowed, vector=None):
        calls.append(allowed)
        return [row('b', 'B')]
    monkeypatch.setattr(discovery, 'search_branch', branch)
    assert discovery.discover('garantia', 'B')['scope'] == 'selected'
    assert calls == [['B'], ['B']]


@pytest.mark.parametrize('question', ['', ' ', None, 'x' * 2001])
def test_invalid_question(setup, question):
    with pytest.raises(ValueError):
        discovery.discover(question)


def test_holdout_or_unknown_edital_rejected(setup):
    with pytest.raises(ValueError):
        discovery.discover('garantia', 'holdout')


def test_result_scope_fails_closed(setup, monkeypatch):
    monkeypatch.setattr(discovery, 'search_branch', lambda *a: [row('foreign', 'holdout')])
    with pytest.raises(ValueError):
        discovery.discover('monitores')


def test_many_pages_do_not_add_contract_votes():
    catalog = {'A': {}, 'B': {}}
    result = discovery.rank_contracts({'keyword':[row(str(i),'A') for i in range(50)]+[row('b','B')],
                                      'semantic':[row('b','B'),row('a','A')]}, catalog, 'monitor')
    assert result[0][1] == result[1][1]


def test_explicit_agency_hint_uses_catalog_without_labels():
    catalog = {'A': {'agency':'MUNICIPIO DE UNIFLOR'}, 'B': {'agency':'MUNICIPIO DE PORTO BELO'}}
    rows = [row('b','B'),row('a','A')]
    result = discovery.rank_contracts({'keyword':rows,'semantic':rows},catalog,'Qual monitor em Uniflor?')
    assert result[0][0][2] == 'A'


def test_generic_agency_words_do_not_boost():
    catalog = {'A': {'agency':'MUNICIPIO DE UNIFLOR'}, 'B': {'agency':'MUNICIPIO DE PORTO BELO'}}
    rows = [row('b','B'),row('a','A')]
    assert discovery.rank_contracts({'keyword':rows},catalog,'Qual prefeitura compra monitores?')[0][0][2] == 'B'


def test_shortened_name_matches_two_distinctive_words():
    catalog = {'A': {'agency':'FUNDACAO DE DERMATOLOGIA TROPICAL E VENEREOLOGIA ALFREDO DA MATTA'}}
    assert discovery.agency_matches(catalog,'Qual garantia na Fundação Alfredo da Matta?')[0][0] == 'A'


def test_shortened_synthetic_name_without_accents():
    catalog = {'A':{'agency':'INSTITUTO DE CIENCIA E TECNOLOGIA JOSE ALVARES'}}
    assert discovery.agency_matches(catalog,'Qual prazo no José Álvares?')[0][0] == 'A'


def test_homonymous_agencies_need_clarification():
    catalog = {'A':{'agency':'CAMARA MUNICIPAL DE PORTO BELO'},
               'B':{'agency':'MUNICIPIO DE PORTO BELO'}}
    candidates = [{'pncp_id':'A'},{'pncp_id':'B'}]
    decision = discovery.route_discovery('monitor em Porto Belo',catalog,candidates)
    assert decision['status']=='needs_clarification'
    assert decision['pncp_id'] is None


def test_generic_question_never_chooses_top_ranked_edital(setup,monkeypatch):
    monkeypatch.setattr(discovery,'search_branch',lambda *a:[row('a','A'),row('b','B')])
    assert discovery.discover('Qual prazo de entrega?')['routing']['status']=='needs_clarification'


def test_selected_scope_bypasses_missing_agency_hint(setup,monkeypatch):
    monkeypatch.setattr(discovery,'search_branch',lambda *a:[row('a','A')])
    assert discovery.discover('Qual prazo de entrega?','A')['routing']=={
        'status':'scoped','reason':'user_selected','pncp_id':'A','message':None}


def test_unique_agency_hint_can_scope_without_selection():
    catalog={'A':{'agency':'MUNICIPIO DE UNIFLOR'},'B':{'agency':'MUNICIPIO DE PORTO BELO'}}
    decision=discovery.route_discovery('monitor em Uniflor',catalog,[{'pncp_id':'B'},{'pncp_id':'A'}])
    assert decision['status']=='scoped'
    assert decision['pncp_id']=='A'


def test_empty_candidates_are_not_evidence():
    assert discovery.route_discovery('garantia',{},[])['status']=='no_candidates'


def test_agency_missing_from_candidates_cannot_be_scoped():
    catalog={'A':{'agency':'MUNICIPIO DE UNIFLOR'},'B':{}}
    assert discovery.route_discovery('Uniflor',catalog,[{'pncp_id':'B'}])['status']=='needs_clarification'


def test_cross_contract_request_keeps_global_discovery():
    decision=discovery.route_discovery('Quais editais incluem monitores?',{},[{'pncp_id':'A'}])
    assert decision['status']=='discovery_only'
    assert decision['pncp_id'] is None
