"""Prepara/carga snapshot candidato separado a partir das fontes já aprovadas."""
import argparse
import copy
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from radar.config import PROJECT, emit_json, private_root
from radar.ingestion import prepare
from radar.storage import load_corpus, connect

OLD='4f8ddffaa01b6a20'


def build_manifest():
    old=json.loads((PROJECT/f'datasets/manifests/{OLD}.json').read_text(encoding='utf-8'))
    ref=json.loads((PROJECT/'datasets/evaluation/independent-draft-v1.json').read_text(encoding='utf-8'))
    if ref['status']!='approved_reference_not_executed':raise ValueError('Reference not approved')
    plan=json.loads((PROJECT/'reports/independent-index-plan-v1.json').read_text(encoding='utf-8'))
    ref_hash=hashlib.sha256((PROJECT/'datasets/evaluation/independent-draft-v1.json').read_bytes()).hexdigest()
    if ref_hash!=plan['approved_reference_sha256']:raise ValueError('Reference differs from approved plan')
    editais=copy.deepcopy(old['editais'])
    oldids={e['pncp_id'] for e in editais};oldhashes={d['sha256'] for e in editais for d in e['documents']}
    seen=set()
    for doc in plan['new_documents']:
        if doc['pncp_id'] in oldids or doc['sha256'] in oldhashes or doc['pncp_id'] in seen:
            raise ValueError('Candidate overlaps existing sources')
        seen.add(doc['pncp_id']);case=next(c for c in ref['cases'] if c['pncp_id']==doc['pncp_id'])
        editais.append({'pncp_id':doc['pncp_id'],'agency':doc['agency'],'uf':doc['uf'],'region':doc['region'],
                        'source_kind':case['source_kind'],'documents':[{'sequence':doc['document_sequence'],
                        'sha256':doc['sha256'],'url':doc['url'],'bytes':doc['bytes']}],
                        'selection_note':'approved_source_subset_not_complete_attachment_inventory'})
    identity=[{'pncp_id':e['pncp_id'],'documents':e['documents']} for e in editais]
    snapshot=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:16]
    manifest={'sector':'informatica','uf':'MULTI','snapshot_id':snapshot,'editais':editais,
              'role':'candidate_growth_snapshot_not_promoted','parent_snapshot':OLD,
              'captured_at':plan['new_documents'][0].get('captured_at',old['captured_at']),
              'selection_complete':False,'sampling':{'method':'approved_independent_source_subset',
              'new_contracts':6,'new_pdfs':6,'new_regions':4,'representative':False},
              'limitations':['new_sources_not_full_attachment_or_amendment_inventory',
                             'historical_parent_includes_two_medical_sector_false_positives']}
    path=PROJECT/f'datasets/manifests/{snapshot}.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8'))!=manifest:
        raise ValueError('Immutable candidate manifest differs')
    if not path.exists():emit_json(path,manifest)
    return path,manifest,ref


def bind(manifest,reference):
    prepared=json.loads((private_root()/f"prepared/{manifest['snapshot_id']}.json").read_text(encoding='utf-8'))
    bound=copy.deepcopy(reference);bound['snapshot_id']=manifest['snapshot_id']
    for key in ('indexed','retrieval_calls','groq_calls'):bound.pop(key,None)
    bound['status']='approved_bound_reference';bound['evidence_format']='page_offsets_v1'
    bound['dataset_role']='first_independent_document_growth_reference'
    bound['approved_source_reference_sha256']=hashlib.sha256((PROJECT/'datasets/evaluation/independent-draft-v1.json').read_bytes()).hexdigest()
    bound['binding_note']='original approved quotes unchanged; chunk IDs are representative overlapping anchors'
    bound['limitations']=[note for note in bound['limitations'] if not note.startswith('Referências ainda sem chunk_id')]
    for case in bound['cases']:
        case['evidence_format']='page_offsets_v1'
        case['review_record']=reference['review_record']
        for ev in case['evidence']:
            options=[c for c in prepared['chunks'] if c['pncp_id']==case['pncp_id']
                     and c['document_sequence']==ev['document_sequence'] and c['document_sha']==ev['document_sha256']
                     and c['page']==ev['page'] and max(c['start'],ev['start'])<min(c['end'],ev['end'])]
            if not options:raise ValueError('Reference has no overlapping indexed anchor')
            anchor=min(options,key=lambda c:(-min(c['end'],ev['end'])+max(c['start'],ev['start']),c['start'],c['id']))
            ev['chunk_id']=anchor['id']
    spec=importlib.util.spec_from_file_location('reference_validator',PROJECT/'ops/validate-reference.py')
    validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
    checked=validator.validate(bound,prepared,manifest)
    emit_json(PROJECT/'datasets/evaluation/independent-bound-v1.json',bound)
    pilot=json.loads((PROJECT/'datasets/evaluation/pilot-v2.json').read_text(encoding='utf-8'))
    pilot['original_snapshot_id']=pilot['snapshot_id'];pilot['snapshot_id']=manifest['snapshot_id']
    pilot['dataset_role']='historical_development_regression_on_candidate'
    validator.validate(pilot,prepared,manifest)
    emit_json(PROJECT/'datasets/evaluation/pilot-candidate-v1.json',pilot)
    checked.update(snapshot_id=manifest['snapshot_id'],source_reference_unchanged=True,
                   binding='representative_chunk_anchor_for_original_page_offsets',generation_calls=0)
    emit_json(PROJECT/'reports/independent-bound-reference-v1.json',checked)
    return prepared


def verify(manifest,prepared):
    snapshot=manifest['snapshot_id']
    with connect() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        oldcount=conn.execute('SELECT count(*) FROM radar.chunks WHERE snapshot_id=%s',(OLD,)).fetchone()[0]
        count=conn.execute('SELECT count(*) FROM radar.chunks WHERE snapshot_id=%s',(snapshot,)).fetchone()[0]
        if oldcount!=15773 or count!=len(prepared['chunks']):raise ValueError('Corpus count mismatch')
        missing=conn.execute('SELECT count(*) FROM radar.chunks o LEFT JOIN radar.chunks n ON n.snapshot_id=%s AND n.id=o.id WHERE o.snapshot_id=%s AND (n.id IS NULL OR n.text<>o.text OR n.embedding<>o.embedding OR n.start_offset<>o.start_offset OR n.end_offset<>o.end_offset)',(snapshot,OLD)).fetchone()[0]
        invalid=conn.execute('SELECT count(*) FROM radar.chunks c JOIN radar.pages p USING(snapshot_id,pncp_id,document_sequence,page) WHERE c.snapshot_id=%s AND substring(p.text FROM c.start_offset+1 FOR c.end_offset-c.start_offset)<>c.text',(snapshot,)).fetchone()[0]
        if missing or invalid:raise ValueError('Preservation or offset verification failed')
        config=conn.execute('SELECT configuration FROM radar.snapshots WHERE id=%s',(snapshot,)).fetchone()[0]
        oldconfig=conn.execute('SELECT configuration FROM radar.snapshots WHERE id=%s',(OLD,)).fetchone()[0]
        if config!=oldconfig:raise ValueError('Configuration changed across snapshots')
        role=conn.execute('SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user').fetchone()
        if any(role):raise ValueError('Loader has unnecessary elevated privileges')
    again=load_corpus(PROJECT/f'datasets/manifests/{snapshot}.json',PROJECT/'reports/independent-load-v1.json')
    if again['status']!='already_loaded' or again['chunks']!=count:raise ValueError('Load not idempotent')
    report={'verified_at_utc':datetime.now(timezone.utc).isoformat(),'snapshot_id':snapshot,'parent_snapshot':OLD,
            'candidate_chunks':count,'parent_chunks_preserved':oldcount,'historical_chunk_or_vector_mismatches':missing,
            'invalid_offsets':invalid,'same_configuration':True,'idempotent_load':'already_loaded',
            'loader_role':'no_superuser_no_createdb_no_createrole','new_chunks':count-oldcount,
            'candidate_not_promoted':True,'generation_calls':0,'new_backup_restore':'not_executed'}
    emit_json(PROJECT/'reports/independent-load-verification-v1.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=('prepare','load','verify'),required=True)
    args=parser.parse_args();path,manifest,reference=build_manifest()
    print(json.dumps({'stage':args.stage,'candidate_snapshot':manifest['snapshot_id']}),flush=True)
    if args.stage=='prepare':
        value=prepare(path,PROJECT/'reports/independent-preparation-v1.json');bind(manifest,reference)
    else:
        prepared=json.loads((private_root()/f"prepared/{manifest['snapshot_id']}.json").read_text(encoding='utf-8'))
        value=load_corpus(path,PROJECT/'reports/independent-load-v1.json') if args.stage=='load' else verify(manifest,prepared)
    print(json.dumps(value),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__}),flush=True)
        raise SystemExit(1) from None
