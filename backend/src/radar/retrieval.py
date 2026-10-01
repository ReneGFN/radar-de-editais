"""LangChain coordena busca semântica e lexical e combina os rankings."""
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda, RunnableParallel
from pgvector.psycopg import register_vector
from .storage import connect
from .embeddings import local_embeddings


def combine(rankings, limit=5):
    scores, records = {}, {}
    for ranking in rankings.values():
        for rank, row in enumerate(ranking, start=1):
            key = row[0]
            scores[key] = scores.get(key,0) + 1/(60+rank)
            records[key] = row
    return [(records[key],scores[key]) for key in sorted(scores,key=lambda k:(-scores[k],k))[:limit]]


def branch(inputs, semantic):
    with connect() as conn:
        register_vector(conn)
        columns = "c.id,c.text,c.pncp_id,c.document_sequence,c.page,c.start_offset,c.end_offset,d.source->>'url'"
        scope = " FROM radar.chunks c JOIN radar.documents d ON d.snapshot_id=c.snapshot_id AND d.pncp_id=c.pncp_id AND d.sequence=c.document_sequence WHERE c.snapshot_id=%s AND c.pncp_id=%s"
        params = (inputs["snapshot"],inputs["edital"])
        if semantic:
            return conn.execute("SELECT "+columns+scope+" ORDER BY c.embedding <=> %s::vector,c.id LIMIT 10", params+(inputs["vector"],)).fetchall()
        return conn.execute("SELECT "+columns+scope+" AND c.terms @@ websearch_to_tsquery('portuguese',%s) ORDER BY ts_rank_cd(c.terms,websearch_to_tsquery('portuguese',%s)) DESC,c.id LIMIT 10",params+(inputs["query"],inputs["query"])).fetchall()


def retrieve(query, snapshot, edital):
    if not isinstance(query,str) or not query.strip() or len(query)>1000:
        raise ValueError("Consulta inválida")
    inputs = {"query":query,"snapshot":snapshot,"edital":edital,"vector":local_embeddings().embed_query(query)}
    flow = RunnableParallel(semantic=RunnableLambda(lambda x:branch(x,True)),
                            keyword=RunnableLambda(lambda x:branch(x,False))) | RunnableLambda(combine)
    return [Document(page_content=row[1], metadata={"id":row[0],"pncp_id":row[2],
        "document_sequence":row[3],"page":row[4],"start":row[5],"end":row[6],"url":row[7],"score":score})
        for row,score in flow.invoke(inputs)]
