"""LangChain coordena busca semântica e lexical e combina os rankings."""
from time import perf_counter
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda, RunnableParallel
from pgvector.psycopg import register_vector
from .storage import connect
from .embeddings import local_embeddings
from .query import plan
from .reranking import rerank_coverage

DEFAULT_LEXICAL_STRATEGY = 'any'
DEFAULT_QUERY_PROFILE = 'structured'


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
        for name in ('page','document_sequence'):
            if name in inputs.get('filters',{}):
                scope += ' AND c.'+name+'=%s'
                params += (inputs['filters'][name],)
        if 'clause' in inputs.get('filters',{}):
            scope += ' AND c.text LIKE %s'
            params += ('%'+inputs['filters']['clause']+'%',)
        if semantic:
            return conn.execute("SELECT "+columns+scope+" ORDER BY c.embedding <=> %s::vector,c.id LIMIT 10", params+(inputs["vector"],)).fetchall()
        strategy = inputs.get('lexical_strategy', DEFAULT_LEXICAL_STRATEGY)
        if strategy not in ('all', 'any'):
            raise ValueError('Estratégia lexical inválida')
        # Expressão SQL fixa; o texto do usuário continua sendo parâmetro.
        tsquery = ("websearch_to_tsquery('portuguese',%s)" if strategy == 'all' else
                   "replace(plainto_tsquery('portuguese',%s)::text, ' & ', ' | ')::tsquery")
        return conn.execute("SELECT "+columns+scope+" AND c.terms @@ "+tsquery+
                            " ORDER BY ts_rank_cd(c.terms,"+tsquery+") DESC,c.id LIMIT 10",
                            params+(inputs['query'],inputs['query'])).fetchall()


def retrieve_with_trace(query, snapshot, edital, mode='hybrid', lexical_strategy=DEFAULT_LEXICAL_STRATEGY, query_profile=DEFAULT_QUERY_PROFILE, selection_profile='rrf', context_profile='chunk'):
    """Mesmo núcleo da busca, com rankings para diagnóstico e comparação."""
    if not isinstance(query,str) or not query.strip() or len(query)>1000:
        raise ValueError("Consulta inválida")
    if mode not in ('keyword', 'semantic', 'hybrid'):
        raise ValueError('Modo de busca inválido')
    if lexical_strategy not in ('all', 'any'):
        raise ValueError('Estratégia lexical inválida')
    if query_profile not in ('original','focused','structured'):
        raise ValueError('Perfil de consulta inválido')
    if selection_profile not in ('rrf','coverage'):
        raise ValueError('Perfil de seleção inválido')
    if context_profile not in ('chunk','page_window'):
        raise ValueError('Perfil de contexto inválido')
    started = perf_counter()
    inputs = {"query":query,"snapshot":snapshot,"edital":edital,'lexical_strategy':lexical_strategy}
    if query_profile != 'original':
        with connect() as conn:
            source = conn.execute('SELECT manifest FROM radar.snapshots WHERE id=%s',(snapshot,)).fetchone()
        agency = next((e['agency'] for e in source[0]['editais'] if e['pncp_id']==edital),'') if source else ''
        planned = plan(query,agency,query_profile=='structured')
        inputs.update(query=planned['query'],filters=planned['filters'])
    if mode != 'keyword':
        inputs['vector'] = local_embeddings().embed_query(inputs['query'])
    branches = {}
    if mode != 'keyword':
        branches['semantic'] = RunnableLambda(lambda x:branch(x,True))
    if mode != 'semantic':
        branches['keyword'] = RunnableLambda(lambda x:branch(x,False))
    rankings = RunnableParallel(**branches).invoke(inputs)
    selected = combine(rankings) if mode == 'hybrid' else [(row,None) for row in rankings[mode][:5]]
    if selection_profile == 'coverage':
        candidates = combine(rankings, limit=20) if mode == 'hybrid' else [(row,1/(60+i)) for i,row in enumerate(rankings[mode],1)]
        selected = rerank_coverage(candidates, inputs['query'])
    documents = [Document(page_content=row[1], metadata={"id":row[0],"pncp_id":row[2],
        "document_sequence":row[3],"page":row[4],"start":row[5],"end":row[6],"url":row[7],"score":score})
        for row,score in selected]
    if context_profile == 'page_window':
        from .context import expand_documents
        documents = expand_documents(documents,snapshot)
    return documents, {'mode': mode, 'lexical_strategy':lexical_strategy,'query_profile':query_profile,
                       'context_profile':context_profile,'context_characters':sum(len(d.page_content) for d in documents),'selection_profile':selection_profile,'effective_query':inputs['query'],'filters':inputs.get('filters',{}), 'latency_ms': (perf_counter()-started)*1000,
                       'candidate_ids': {name:[row[0] for row in rows] for name,rows in rankings.items()}}


def retrieve(query, snapshot, edital):
    return retrieve_with_trace(query, snapshot, edital)[0]
