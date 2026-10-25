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
        if 'document_sequences' in inputs.get('filters',{}):
            scope += ' AND c.document_sequence = ANY(%s)'
            params += (inputs['filters']['document_sequences'],)
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


def retrieve_with_trace(query, snapshot, edital, mode='hybrid', lexical_strategy=DEFAULT_LEXICAL_STRATEGY, query_profile=DEFAULT_QUERY_PROFILE, selection_profile='rrf', context_profile='chunk', document_sequences=None):
    """Mesmo núcleo da busca, com rankings para diagnóstico e comparação."""
    if not isinstance(query,str) or not query.strip() or len(query)>2000:
        raise ValueError("Consulta inválida")
    if mode not in ('keyword', 'semantic', 'hybrid'):
        raise ValueError('Modo de busca inválido')
    if lexical_strategy not in ('all', 'any'):
        raise ValueError('Estratégia lexical inválida')
    if query_profile not in ('original','focused','structured'):
        raise ValueError('Perfil de consulta inválido')
    if selection_profile not in ('rrf','coverage'):
        raise ValueError('Perfil de seleção inválido')
    if context_profile not in ('chunk','page_window','item_structure'):
        raise ValueError('Perfil de contexto inválido')
    if context_profile == 'item_structure' and selection_profile != 'rrf':
        raise ValueError('Estrutura de itens requer seleção rrf')
    started = perf_counter()
    inputs = {"query":query,"snapshot":snapshot,"edital":edital,'lexical_strategy':lexical_strategy}
    if query_profile != 'original':
        with connect() as conn:
            source = conn.execute('SELECT manifest FROM radar.snapshots WHERE id=%s',(snapshot,)).fetchone()
        agency = next((e['agency'] for e in source[0]['editais'] if e['pncp_id']==edital),'') if source else ''
        planned = plan(query,agency,query_profile=='structured')
        inputs.update(query=planned['query'],filters=planned['filters'])
    if document_sequences is not None:
        inputs.setdefault('filters',{}).pop('document_sequence',None)
        inputs['filters']['document_sequences'] = document_sequences
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
    if context_profile == 'item_structure':
        selected = combine(rankings,limit=20) if mode == 'hybrid' else [(row,None) for row in rankings[mode]]
    documents = [Document(page_content=row[1], metadata={"id":row[0],"pncp_id":row[2],
        "document_sequence":row[3],"page":row[4],"start":row[5],"end":row[6],"url":row[7],"score":score})
        for row,score in selected]
    if context_profile in ('page_window','item_structure'):
        from .context import expand_documents
        documents = expand_documents(documents,snapshot)
    if context_profile == 'item_structure':
        from .item_structure import structured_documents
        documents = structured_documents(query,snapshot,edital,documents,inputs.get('filters'))
    return documents, {'mode': mode, 'lexical_strategy':lexical_strategy,'query_profile':query_profile,
                       'context_profile':context_profile,'context_characters':sum(len(d.page_content) for d in documents),'selection_profile':selection_profile,'effective_query':inputs['query'],'filters':inputs.get('filters',{}), 'latency_ms': (perf_counter()-started)*1000,
                       'candidate_ids': {name:[row[0] for row in rows] for name,rows in rankings.items()}}


def retrieve(query, snapshot, edital):
    return retrieve_with_trace(query, snapshot, edital)[0]


def retrieve_document_scope(query, snapshot, scope):
    """Até cinco passagens exclusivamente dos arquivos escolhidos; uma por arquivo antes de completar."""
    import re
    from .query import fold, STOP
    # Decompose explicit comparisons from the user's words, without expected answers.
    parts = re.split(r'\s+(?:e|versus|vs\.?|comparado a)\s+', query, flags=re.I)
    topic = query.split(':', 1)[0] if ':' in query else ''
    probes = [query]
    technical = re.findall(r'\b[A-Z]{2,8}\s+\d{3,5}\b', query)
    if len(scope) > 1 and len(parts) > 1:
        probes += [f'{topic} {part}'.strip()[:2000] for part in parts[:5]]
        probes += technical[:2]
    pools = []
    for selection in scope:
        candidates = {}
        for probe in probes:
            docs, _ = retrieve_with_trace(probe, snapshot, selection['pncp_id'],
                                         context_profile='chunk', document_sequences=[selection['document_sequence']])
            for doc in docs:
                if doc.metadata['pncp_id'] == selection['pncp_id'] and doc.metadata['document_sequence'] == selection['document_sequence']:
                    candidates.setdefault(doc.metadata['id'], doc)
        anchors = {t.rstrip('s') for t in re.findall(r'\w+', fold(query)) if t not in STOP and len(t) > 2}
        def relevance(doc):
            tokens = {t.rstrip('s') for t in re.findall(r'\w+', fold(doc.page_content))}
            return len(anchors & tokens) + 20 * sum(fold(term) in fold(doc.page_content) for term in technical)
        ranked = sorted(candidates.values(), key=relevance, reverse=True) if len(probes) > 1 else list(candidates.values())
        if len(probes) > 1:
            # A specification may continue on the next page. Fetch bounded neighbours
            # of the two strongest anchors, always in the same selected PDF.
            neighbours = adjacent_scope_pages(ranked[:2], snapshot, relevance)
            for doc in neighbours:
                candidates.setdefault(doc.metadata['id'], doc)
            ranked = sorted(candidates.values(), key=lambda d: d.metadata.get('continuation_score', relevance(d)), reverse=True)
            distinct = []
            for doc in ranked:
                m = doc.metadata
                def overlaps(old):
                    n = old.metadata
                    if not all(k in m and k in n for k in ('page','start','end')) or m['page'] != n['page']: return False
                    intersection = max(0, min(m['end'],n['end']) - max(m['start'],n['start']))
                    return intersection >= .8 * min(m['end']-m['start'],n['end']-n['start'])
                if not any(overlaps(old) for old in distinct): distinct.append(doc)
            ranked = distinct
        pools.append(ranked)
    selected = [pool[0] for pool in pools if pool]
    seen = {d.metadata['id'] for d in selected}
    for rank in range(1, 5):
        for pool in pools:
            if len(selected) >= 5: break
            if rank >= len(pool): continue
            doc = pool[rank]
            if doc.metadata['id'] not in seen:
                selected.append(doc); seen.add(doc.metadata['id'])
    return selected[:5], {'context_profile':'document_scope','selected_document_count':len(scope),
                         'query_count':len(probes), 'selection':'balanced_query_coverage_v2'}


def adjacent_scope_pages(anchors, snapshot, relevance):
    """Bounded next-page evidence; its own literal offsets and source identity."""
    import hashlib
    import re
    from .query import fold
    result = []
    with connect() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        for anchor in anchors:
            m = anchor.metadata
            if 'page' not in m: continue
            if re.search(r'\bgarantia\b', fold(anchor.page_content)): continue
            row = conn.execute('SELECT text FROM radar.pages WHERE snapshot_id=%s AND pncp_id=%s AND document_sequence=%s AND page=%s',
                               (snapshot, m['pncp_id'], m['document_sequence'], m['page'] + 1)).fetchone()
            if not row: continue
            text = row[0][:2000]
            # Only follow an apparent specification continuation, not arbitrary pages.
            if not re.search(r'\b(?:garantia|prazo|entrega|memoria|capacidade|quantidade)\b', fold(text)): continue
            metadata = dict(m, page=m['page'] + 1, start=0, end=len(text),
                            id=hashlib.sha256(f"{snapshot}:{m['pncp_id']}:{m['document_sequence']}:{m['page']+1}:0:{len(text)}".encode()).hexdigest(),
                            context_profile='selected_pdf_continuation', continuation_score=relevance(anchor) + .1)
            result.append(Document(page_content=text, metadata=metadata))
    return result
