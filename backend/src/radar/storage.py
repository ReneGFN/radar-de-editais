import hashlib
import json
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from pgvector.psycopg import register_vector

from .config import PROJECT, emit_json, private_root

SCHEMA = """
CREATE TABLE IF NOT EXISTS radar.snapshots (
 id text PRIMARY KEY, manifest jsonb NOT NULL, configuration jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS radar.documents (
 snapshot_id text REFERENCES radar.snapshots(id), pncp_id text NOT NULL,
 sequence integer NOT NULL, sha256 text NOT NULL, source jsonb NOT NULL,
 PRIMARY KEY(snapshot_id,pncp_id,sequence)
);
CREATE TABLE IF NOT EXISTS radar.pages (
 snapshot_id text, pncp_id text, document_sequence integer, page integer CHECK(page>0),
 text text NOT NULL, quality text NOT NULL,
 PRIMARY KEY(snapshot_id,pncp_id,document_sequence,page),
 FOREIGN KEY(snapshot_id,pncp_id,document_sequence)
 REFERENCES radar.documents(snapshot_id,pncp_id,sequence)
);
CREATE TABLE IF NOT EXISTS radar.chunks (
 snapshot_id text, id text, pncp_id text NOT NULL, document_sequence integer NOT NULL,
 page integer NOT NULL, start_offset integer CHECK(start_offset>=0),
 end_offset integer CHECK(end_offset>start_offset), text text NOT NULL,
 embedding vector(384) NOT NULL,
 terms tsvector GENERATED ALWAYS AS
 (to_tsvector('portuguese',text) || to_tsvector('simple',text)) STORED,
 PRIMARY KEY(snapshot_id,id),
 FOREIGN KEY(snapshot_id,pncp_id,document_sequence,page)
 REFERENCES radar.pages(snapshot_id,pncp_id,document_sequence,page),
 CHECK(length(text)=end_offset-start_offset)
);
CREATE INDEX IF NOT EXISTS chunks_scope ON radar.chunks(snapshot_id,pncp_id);
CREATE INDEX IF NOT EXISTS chunks_terms ON radar.chunks USING gin(terms);
"""


def connect(admin=False, database="radar"):
    name = "admin" if admin else "loader"
    password = (private_root() / "secrets" / f"{name}_password").read_text().strip()
    return psycopg.connect(host="127.0.0.1", port=55432, dbname=database,
                           user="postgres" if admin else "radar_loader", password=password,
                           connect_timeout=10)


def initialize():
    with connect(admin=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='radar_loader'").fetchone():
            password = (private_root() / "secrets/loader_password").read_text().strip()
            conn.execute(sql.SQL("CREATE ROLE radar_loader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
                         .format(sql.Literal(password)))
        conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        conn.execute("CREATE SCHEMA IF NOT EXISTS radar AUTHORIZATION radar_loader")
        conn.execute("SET ROLE radar_loader")
        conn.execute(SCHEMA)
        conn.execute("RESET ROLE")
    return {"database": "radar", "extension": "vector", "schema": "radar", "loader": "schema_owner_no_superuser"}


def corpus_fingerprint(configuration,chunks):
    return hashlib.sha256(json.dumps({"configuration":configuration,"chunks":chunks},sort_keys=True).encode()).hexdigest()


def reusable_vectors(root, configuration):
    reused={}
    for path in (root/"vectors").glob("*.json"):
        source=root/"prepared"/path.name
        if not source.exists(): continue
        previous=json.loads(source.read_text(encoding="utf-8"))
        config={k:previous[k] for k in ("extractor","splitter","embedding")}
        if config!=configuration: continue
        cached=json.loads(path.read_text(encoding="utf-8"))
        if cached.get("fingerprint")!=corpus_fingerprint(config,previous["chunks"]): continue
        if len(cached["vectors"])!=len(previous["chunks"]): continue
        reused.update({c["id"]:v for c,v in zip(previous["chunks"],cached["vectors"])})
    return reused


def load_corpus(manifest: Path):
    from .embeddings import local_embeddings
    selection = json.loads(manifest.read_text(encoding="utf-8"))
    snapshot = selection["snapshot_id"]
    prepared = json.loads((private_root() / "prepared" / f"{snapshot}.json").read_text(encoding="utf-8"))
    configuration = {k: prepared[k] for k in ("extractor", "splitter", "embedding")}
    embeddings = local_embeddings()
    if embeddings.provenance() != configuration["embedding"]:
        raise ValueError("Modelo mudou desde a preparação")
    with connect() as conn:
        existing = conn.execute("SELECT manifest,configuration FROM radar.snapshots WHERE id=%s", (snapshot,)).fetchone()
        if existing:
            if existing != (selection, configuration):
                raise ValueError("Snapshot imutável diverge; criar uma nova versão")
            return {"snapshot_id": snapshot, "status": "already_loaded", "chunks": conn.execute(
                "SELECT count(*) FROM radar.chunks WHERE snapshot_id=%s", (snapshot,)).fetchone()[0]}
    cache = private_root() / "vectors" / f"{snapshot}.json"
    fingerprint = corpus_fingerprint(configuration,prepared["chunks"])
    reused_count=0
    if cache.exists():
        cached = json.loads(cache.read_text())
        if cached["fingerprint"] != fingerprint:
            raise ValueError("Cache de vetores diverge")
        vectors = cached["vectors"]
    else:
        reused=reusable_vectors(private_root(),configuration)
        checkpoint=private_root()/"checkpoints"/f"{snapshot}.json"
        if checkpoint.exists():
            partial=json.loads(checkpoint.read_text(encoding="utf-8"))
            if partial["fingerprint"]!=fingerprint: raise ValueError("Checkpoint diverge")
            reused.update(partial["vectors_by_id"])
        wanted={c["id"] for c in prepared["chunks"]}
        reused={k:v for k,v in reused.items() if k in wanted}
        reused_count=len(reused)
        missing=[c for c in prepared["chunks"] if c["id"] not in reused]
        for start in range(0,len(missing),128):
            batch=missing[start:start+128]
            values=embeddings.embed_documents([c["text"] for c in batch])
            reused.update({c["id"]:v for c,v in zip(batch,values)})
            emit_json(checkpoint,{"fingerprint":fingerprint,"vectors_by_id":reused})
            print(json.dumps({"vectors_ready":len(reused),"total":len(wanted),"reused_at_start":reused_count}),flush=True)
        vectors=[reused[c["id"]] for c in prepared["chunks"]]
        emit_json(cache, {"fingerprint": fingerprint, "vectors": vectors})
    if len(vectors) != len(prepared["chunks"]):
        raise ValueError("Quantidade de vetores divergente")
    with connect() as conn:
        register_vector(conn)
        conn.execute("INSERT INTO radar.snapshots VALUES (%s,%s,%s)", (snapshot,Jsonb(selection),Jsonb(configuration)))
        for edital in selection["editais"]:
            for source in edital["documents"]:
                conn.execute("INSERT INTO radar.documents VALUES (%s,%s,%s,%s,%s)",
                    (snapshot,edital["pncp_id"],source["sequence"],source["sha256"],Jsonb(source)))
        for doc in prepared["documents"]:
            for page in doc["pages"]:
                conn.execute("INSERT INTO radar.pages VALUES (%s,%s,%s,%s,%s,%s)",
                    (snapshot,doc["pncp_id"],doc["document_sequence"],page["page"],page["text"],page["quality"]))
        for c,v in zip(prepared["chunks"],vectors):
            conn.execute("INSERT INTO radar.chunks(snapshot_id,id,pncp_id,document_sequence,page,start_offset,end_offset,text,embedding) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (snapshot,c["id"],c["pncp_id"],c["document_sequence"],c["page"],c["start"],c["end"],c["text"],v))
    report = {"snapshot_id":snapshot,"status":"loaded","chunks":len(vectors),"dimensions":384,
              "transaction":"atomic", "cost_groq":0,"vectors_reused":reused_count,
              "embedding_model":configuration["embedding"]["model"]}
    emit_json(PROJECT / "reports/carga.json",report)
    return report


def search_corpus(query, snapshot, edital):
    from .retrieval import retrieve
    return [{k:doc.metadata[k] for k in ("id","pncp_id","document_sequence","page","start","end","url","score")}
            for doc in retrieve(query,snapshot,edital)]
