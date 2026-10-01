"""Verificação de carga, filtro e recuperação; não calcula qualidade do RAG."""
import json
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path
from radar.config import PROJECT,private_root,emit_json
from radar.storage import connect,load_corpus
from radar.retrieval import retrieve

parser=argparse.ArgumentParser()
parser.add_argument('manifest',type=Path)
manifest=parser.parse_args().manifest
selection=json.loads(manifest.read_text(encoding='utf-8'))
snapshot=selection['snapshot_id']
edital=selection['editais'][0]['pncp_id']
with connect() as conn:
    counts={table:conn.execute(f'SELECT count(*) FROM radar.{table} WHERE snapshot_id=%s',(snapshot,)).fetchone()[0]
            for table in ('documents','pages','chunks')}
    invalid=conn.execute('''SELECT count(*) FROM radar.chunks c JOIN radar.pages p
      USING(snapshot_id,pncp_id,document_sequence,page)
      WHERE c.snapshot_id=%s AND substring(p.text FROM c.start_offset+1 FOR c.end_offset-c.start_offset)<>c.text''',(snapshot,)).fetchone()[0]
    assert invalid==0
repeat=load_corpus(manifest)
assert repeat['status']=='already_loaded' and repeat['chunks']==counts['chunks']
docs=retrieve('Qual é o prazo de entrega dos computadores?',snapshot,edital)
assert docs and all(d.metadata['pncp_id']==edital for d in docs)
assert not retrieve('computador',snapshot,'inexistente')
assert not retrieve('computador',snapshot,"' OR 1=1 --")
assert not retrieve('computador','snapshot-inexistente',edital)
# Backup com subprocess binário: nunca passa conteúdo do dump pelo terminal/Brain.
backup=private_root()/'backups'/f'{snapshot}.dump'
backup.parent.mkdir(parents=True,exist_ok=True)
with backup.open('wb') as stream:
    subprocess.run(['docker','exec','radar-de-editais-db-1','pg_dump','-U','postgres','-d','radar','-Fc'],stdout=stream,check=True)
restore='radar_restore_'+snapshot
with connect(admin=True) as conn:
    conn.autocommit=True
    from psycopg import sql
    created=not conn.execute('SELECT 1 FROM pg_database WHERE datname=%s',(restore,)).fetchone()
    if created:
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(restore)))
if created:
    with backup.open('rb') as stream:
        subprocess.run(['docker','exec','-i','radar-de-editais-db-1','pg_restore','-U','postgres','-d',restore,'--exit-on-error'],stdin=stream,check=True)
with connect(admin=True,database=restore) as conn:
    restored=conn.execute('SELECT count(*) FROM radar.chunks WHERE snapshot_id=%s',(snapshot,)).fetchone()[0]
assert restored==counts['chunks']
emit_json(PROJECT/'reports/verificacao-local.json',{'date':datetime.now(timezone.utc).isoformat(),
    'snapshot_id':snapshot,'counts':counts,'offset_errors':invalid,'idempotence':True,
    'edital_filter':True,'snapshot_filter':True,'sql_injection_scope_test':True,
    'backup_restore_chunks':int(restored),'restore_database':restore,
    'restore_executed_this_run':created,
    'retrieval_smoke_test':'passed_not_a_quality_evaluation',
    'sample_citations':[d.metadata for d in docs]})
print(json.dumps({'counts':counts,'restore_chunks':int(restored),'checks':'passed'}))
