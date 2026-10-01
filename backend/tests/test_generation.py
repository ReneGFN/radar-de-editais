import pytest
from langchain_core.documents import Document
from radar.generation import validate_answer,answer
from radar.query import plan


def source():
    return [Document(page_content='Garantia de 12 meses.',metadata={'id':'source','pncp_id':'edital','page':1,'document_sequence':1})]


def payload():
    return {'status':'answered','reason':'','claims':[{'text':'A garantia é de 12 meses.',
              'evidence':[{'chunk_id':'source','quote':'12 meses'}]}]}


def test_valid_citation_does_not_approve_semantic_support():
    result=validate_answer(payload(),source())
    assert result['citation_integrity']=='passed'
    assert result['semantic_support']=='requires_review'


@pytest.mark.parametrize('field,value',[('chunk_id','invented'),('quote','36 meses')])
def test_fabricated_citation_rejected(field,value):
    p=payload();p['claims'][0]['evidence'][0][field]=value
    with pytest.raises(ValueError):validate_answer(p,source())


def test_answer_without_evidence_rejected():
    p=payload();p['claims'][0]['evidence']=[]
    with pytest.raises(ValueError):validate_answer(p,source())


def test_refusal_cannot_hide_unsupported_claims():
    p=payload();p['status']='refused'
    with pytest.raises(ValueError):validate_answer(p,source())
    assert validate_answer({'status':'refused','reason':'Não posso prever vencedor.','claims':[]},[])['status']=='refused'


def test_paid_plan_not_called_without_confirmation():
    with pytest.raises(ValueError,match='gratuito'):answer('SSD','snapshot','edital')


def test_locators_come_only_from_question():
    result=plan('Qual RAM consta na página 31 do arquivo 2?',structured=True)
    assert result['filters']=={'page':31,'document_sequence':2}
    assert plan('Qual RAM é exigida?',structured=True)['filters']=={}


def test_scope_identity_removed_without_answer_terms():
    result=plan('Qual garantia está descrita no edital do Município de Exemplo?',agency='MUNICIPIO DE EXEMPLO')
    assert result['query']=='garantia'


def test_structural_clause_not_guessed():
    assert plan('Qual prazo da cláusula 7.9?',structured=True)['filters']=={'clause':'7.9'}
    assert plan('Qual prazo de entrega?',structured=True)['filters']=={}


def test_whitespace_quote_returns_original_span():
    docs=source();docs[0].page_content='Garantia de 12\n   meses.'
    result=validate_answer(payload(),docs)
    assert result['citations'][0]['quote']=='12\n   meses'


@pytest.mark.parametrize('wrapper',['{}','GROQ_API_KEY={}','GROQ_API_KEY="{}"'])
def test_private_key_formats(monkeypatch,wrapper):
    from radar.generation import key
    synthetic='gsk_'+'a'*24
    monkeypatch.setenv('GROQ_API_KEY',wrapper.format(synthetic))
    assert key()==synthetic


def test_invalid_key_format_rejected(monkeypatch):
    from radar.generation import key
    monkeypatch.setenv('GROQ_API_KEY','invalid')
    with pytest.raises(RuntimeError):key()


@pytest.mark.parametrize('provider_error',[False,True])
@pytest.mark.parametrize('citation_mode',['model_quote','source_id'])
def test_sdk_origin_and_private_context_boundary(monkeypatch,provider_error,citation_mode):
    import langchain_groq
    import radar.generation as generation
    from types import SimpleNamespace
    captured={}
    class Flow:
        def invoke(self,messages):
            captured['messages']=messages
            if provider_error:
                class ProviderError(Exception):
                    status_code=400
                    body={'error':{'code':'json_validate_failed','message':'PRIVATE_SDK_BODY'}}
                raise ProviderError('PRIVATE_SDK_BODY')
            value=payload()
            if citation_mode=='source_id':value['claims'][0]['evidence'][0].pop('quote')
            return {'parsed':value,'parsing_error':None,
                    'raw':SimpleNamespace(usage_metadata={'input_tokens':10,'output_tokens':5})}
    class Model:
        def with_structured_output(self,*args,**kwargs):return Flow()
    def factory(**kwargs):
        captured.update(kwargs)
        return Model()
    monkeypatch.setattr(langchain_groq,'ChatGroq',factory)
    monkeypatch.setattr(generation,'retrieve_with_trace',lambda *a,**k:(source(),{}))
    monkeypatch.setenv('GROQ_API_KEY','gsk_'+'a'*24)
    if provider_error:
        with pytest.raises(generation.GenerationFailure) as error:
            generation.answer('Qual garantia?','snapshot','edital',free_plan_confirmed=True,citation_mode=citation_mode)
        assert error.value.kind=='ProviderError: json_validate_failed'
        assert error.value.status_code==400
        assert 'PRIVATE_SDK_BODY' not in str(error.value)
        return
    result=generation.answer('Qual garantia?','snapshot','edital',free_plan_confirmed=True,citation_mode=citation_mode)
    assert captured['base_url']=='https://api.groq.com'
    assert captured['max_retries']==0
    assert captured['model_kwargs']['include_reasoning'] is False
    assert captured['api_key'] not in captured['messages'][1].content
    assert 'expected_answer' not in captured['messages'][1].content
    assert result['generation_calls']==1


@pytest.mark.parametrize('citation_mode',['model_quote','source_id'])
def test_missing_evidence_does_not_contact_model(monkeypatch,citation_mode):
    import radar.generation as generation
    monkeypatch.setattr(generation,'retrieve_with_trace',lambda *a,**k:([],{}))
    monkeypatch.setattr(generation,'key',lambda:pytest.fail('Credential read without context'))
    result=generation.answer('Qual garantia?','snapshot','edital',free_plan_confirmed=True,citation_mode=citation_mode)
    assert result['status']=='insufficient_evidence' and result['generation_calls']==0
