import httpx
import pytest
from radar.ingestion import safe_url,get,split_pages,matches_sector
from radar.config import private_root,PROJECT
from radar.retrieval import combine

@pytest.mark.parametrize("url",["http://pncp.gov.br/a","https://evil.test/a","https://pncp.gov.br.evil.test/a","https://user:pass@pncp.gov.br/a"])
def test_reject_unsafe_origin(url):
    with pytest.raises(ValueError): safe_url(url)

def test_old_port_is_canonicalized():
    assert safe_url("https://pncp.gov.br:1477/a#b")=="https://pncp.gov.br/a"

def test_redirect_cannot_escape():
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(302,headers={"location":"https://evil.test/a"}))) as client:
        with pytest.raises(ValueError): get(client,"https://pncp.gov.br/a")

def test_download_limit(monkeypatch):
    monkeypatch.setattr("radar.ingestion.MAX_DOWNLOAD",5)
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b"123456"))) as client:
        with pytest.raises(ValueError): get(client,"https://pncp.gov.br/a",binary=True)

def test_offsets_and_short_pages():
    text="Computadores com memória de 16 GB e SSD. "*40
    meta={"pncp_id":"example","document_sha":"abc","document_sequence":1}
    chunks=split_pages([{"page":2,"text":text,"quality":"text"},{"page":3,"text":"","quality":"needs_review"}],meta)
    assert len(chunks)>1
    assert all(c["page"]==2 and text[c["start"]:c["end"]]==c["text"] for c in chunks)
    assert len({c["id"] for c in chunks})==len(chunks)

def test_private_data_cannot_enter_brain(monkeypatch):
    monkeypatch.setenv("RADAR_PRIVATE_ROOT",str(PROJECT/"private"))
    with pytest.raises(ValueError): private_root()

def test_rank_fusion_deduplicates():
    ranked=combine({"semantic":[("a",),("b",)],"keyword":[("b",),("c",)]})
    assert [row[0][0] for row in ranked]==["b","a","c"]

def test_sector():
    assert matches_sector("Aquisição de computadores e acessórios de informática")
    assert not matches_sector("Materiais para manutenção de automação industrial")
    assert not matches_sector("Papelaria, expediente e suprimentos de informática")


def test_rate_limit_is_not_retried_immediately(monkeypatch):
    calls=[]
    def respond(request):
        calls.append(request)
        return httpx.Response(429,headers={'Retry-After':'60'})
    monkeypatch.setattr('radar.ingestion.time.sleep',lambda *a:pytest.fail('Must not retry HTTP 429'))
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(httpx.HTTPStatusError):get(client,'https://pncp.gov.br/a')
    assert len(calls)==1
