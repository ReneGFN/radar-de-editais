import pytest
from radar.presentation import render_markdown,source_url


def result():
    return {'status':'answered','answer':'12 meses.','citation_integrity':'passed',
        'claims':[{'text':'A garantia é de 12 meses.','evidence':[{'chunk_id':'a','quote':'12 meses'}]}],
        'citations':[{'id':'a','quote':'12 meses','pncp_id':'edital-exemplo',
            'document_sequence':2,'page':7,'url':'https://pncp.gov.br/exemplo'}]}


def test_claim_shows_source_document_page_and_original_quote():
    rendered=render_markdown(result())
    assert 'A garantia é de 12 meses. [1]' in rendered
    assert 'edital-exemplo' in rendered and 'arquivo 2, página 7 do PDF' in rendered
    assert 'https://pncp.gov.br/exemplo#page=7' in rendered
    assert '> 12 meses' in rendered


def test_missing_claim_source_is_blocked():
    value=result();value['citations']=[]
    with pytest.raises(ValueError):render_markdown(value)


@pytest.mark.parametrize('url',['javascript:alert(1)','https://example.com/pdf','https://user:pass@pncp.gov.br/pdf'])
def test_untrusted_source_link_is_blocked(url):
    with pytest.raises(ValueError):source_url(url,1)


def test_untrusted_markup_is_escaped():
    value=result();value['claims'][0]['text']='<script>alert(1)</script>'
    assert '<script>' not in render_markdown(value)


def test_refusal_does_not_invent_sources():
    text=render_markdown({'status':'refused','answer':'O documento prevê preço de 99 reais.'})
    assert '99 reais' not in text and 'Abrir documento' not in text
    assert 'reformular' in text
