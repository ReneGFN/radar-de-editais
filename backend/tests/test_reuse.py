from radar.config import emit_json
from radar.storage import corpus_fingerprint,reusable_vectors

def test_reuse_requires_matching_model_and_integrity(tmp_path):
    config={"extractor":"example","splitter":{"size":120},"embedding":{"model":"one"}}
    chunks=[{"id":"chunk","text":"example"}]
    emit_json(tmp_path/"prepared/one.json",{**config,"chunks":chunks})
    emit_json(tmp_path/"vectors/one.json",{"fingerprint":corpus_fingerprint(config,chunks),"vectors":[[1,2,3]]})
    assert reusable_vectors(tmp_path,config)=={"chunk":[1,2,3]}
    assert reusable_vectors(tmp_path,{**config,"embedding":{"model":"two"}})=={}
    emit_json(tmp_path/"vectors/one.json",{"fingerprint":"corrupt","vectors":[[1,2,3]]})
    assert reusable_vectors(tmp_path,config)=={}
