import hashlib
import pytest
from radar.config import emit_json
from radar.ingestion import hydrate

def test_hydration_rejects_changed_source_and_verifies_cache(tmp_path,monkeypatch):
    payload=b"%PDF-1.7\nexample"
    digest=hashlib.sha256(payload).hexdigest()
    manifest=tmp_path/"manifest.json"
    emit_json(manifest,{"snapshot_id":"example","editais":[{"pncp_id":"example","documents":[
        {"sha256":digest,"url":"https://pncp.gov.br/file"}]}]})
    monkeypatch.setattr("radar.ingestion.private_root",lambda:tmp_path/"private")
    monkeypatch.setattr("radar.ingestion.get",lambda *a,**kw:b"%PDF-1.7\nchanged")
    with pytest.raises(ValueError,match="Fonte mudou"): hydrate(manifest)
    assert not (tmp_path/"private/raw"/f"{digest}.pdf").exists()
    monkeypatch.setattr("radar.ingestion.get",lambda *a,**kw:payload)
    assert hydrate(manifest)["downloaded"]==1
    assert hydrate(manifest)["downloaded"]==0

def test_hydration_rejects_path_in_hash(tmp_path,monkeypatch):
    manifest=tmp_path/"manifest.json"
    emit_json(manifest,{"snapshot_id":"example","editais":[{"pncp_id":"example","documents":[
        {"sha256":"../../outside","url":"https://pncp.gov.br/file"}]}]})
    monkeypatch.setattr("radar.ingestion.private_root",lambda:tmp_path/"private")
    with pytest.raises(ValueError,match="Hash inválido"): hydrate(manifest)
