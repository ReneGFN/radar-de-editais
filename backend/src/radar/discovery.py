"""Descoberta híbrida de contratações somente no snapshot de desenvolvimento."""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from time import perf_counter

from pgvector.psycopg import register_vector

from .embeddings import local_embeddings
from .storage import connect

SNAPSHOT = '1446c44aca18011a'


def allowed_editais():
    project = Path(__file__).resolve().parents[3]
    manifest = json.loads((project / 'datasets/manifests' / f'{SNAPSHOT}.json').read_text(encoding='utf-8'))
    return {e['pncp_id']: e for e in manifest['editais']}


def search_branch(question, allowed, vector=None):
    """Ranqueia páginas antes do limite para reduzir domínio de chunks sobrepostos."""
    scope = ''' FROM radar.chunks c JOIN radar.documents d
      ON d.snapshot_id=c.snapshot_id AND d.pncp_id=c.pncp_id
      AND d.sequence=c.document_sequence
      WHERE c.snapshot_id=%s AND c.pncp_id=ANY(%s)'''
    columns = "c.id,c.text,c.pncp_id,c.document_sequence,c.page,c.start_offset,c.end_offset,d.source->>'url' AS url"
    if vector is not None:
        score = '1 - (c.embedding <=> %s::vector)'
        params = (vector, SNAPSHOT, list(allowed))
        condition = ''
    else:
        tsquery = "replace(plainto_tsquery('portuguese',%s)::text, ' & ', ' | ')::tsquery"
        score = 'ts_rank_cd(c.terms,' + tsquery + ')'
        condition = ' AND c.terms @@ ' + tsquery
        params = (question, SNAPSHOT, list(allowed), question)
    query = 'WITH ranked AS (SELECT ' + columns + ',' + score + ' AS relevance' + scope + condition + ''')
      , pages AS (SELECT * FROM
      (SELECT DISTINCT ON(pncp_id,document_sequence,page) * FROM ranked
       ORDER BY pncp_id,document_sequence,page,relevance DESC,id) distinct_pages),
      balanced AS (SELECT *,row_number() OVER(PARTITION BY pncp_id ORDER BY relevance DESC,id) AS position FROM pages)
      SELECT id,text,pncp_id,document_sequence,page,start_offset,end_offset,url
      FROM balanced WHERE position<=3 ORDER BY relevance DESC,id'''
    with connect() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        if vector is not None:
            register_vector(conn)
        return conn.execute(query, params).fetchall()


def agency_tokens(value):
    normalized = unicodedata.normalize('NFKD', value.lower())
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    generic = {'municipio','municipal','prefeitura','camara','secretaria','estado',
               'fundacao','fundo','departamento','administracao','publica','saude',
               'dos','das','para','com','instituto','federal','brasil'}
    return {t for t in re.findall(r'[a-z0-9]+', normalized) if len(t)>=3 and t not in generic}


def agency_matches(catalog, question):
    """Pistas derivadas do catálogo, sem tabela manual de aliases por caso."""
    tokens = {key: agency_tokens(e.get('agency','')) for key,e in catalog.items()}
    frequencies = Counter(t for words in tokens.values() for t in words)
    query_tokens = agency_tokens(question)
    matches = []
    for key, words in tokens.items():
        distinctive = {t for t in words if frequencies[t]<=2}
        shared = distinctive & query_tokens
        coverage = len(shared)/len(distinctive) if distinctive else 0
        # Nomes pessoais ou compostos podem ser apenas parte do nome oficial.
        # Duas palavras distintivas bastam como pista; homônimos permanecem opções.
        if coverage>=0.5 or len(shared)>=2:
            matches.append((key, coverage))
    return sorted(matches,key=lambda x:(-x[1],x[0]))


def route_discovery(question, catalog, candidates, pncp_id=None):
    """Decide escopo, nunca certifica suporte factual nem probabilidade de acerto."""
    if not candidates:
        return {'status':'no_candidates','reason':'empty_retrieval','pncp_id':None,
                'message':'Não encontrei candidatos. Informe órgão, município ou objeto da compra.'}
    if pncp_id is not None:
        return {'status':'scoped','reason':'user_selected','pncp_id':pncp_id,'message':None}
    normalized = ''.join(c for c in unicodedata.normalize('NFKD',question.lower())
                         if not unicodedata.combining(c))
    if re.search(r'\b(quais|liste|listar|encontre|buscar)\s+(os\s+|as\s+)?(editais|contratacoes)\b',normalized):
        return {'status':'discovery_only','reason':'cross_contract_search','pncp_id':None,
                'message':'Encontrei contratações candidatas. É necessário conferir os trechos '
                          'antes de afirmar quais atendem ao pedido; a lista não é exaustiva.'}
    matches = agency_matches(catalog, question)
    available = {c['pncp_id'] for c in candidates}
    if len(matches)==1 and matches[0][0] in available:
        return {'status':'scoped','reason':'unique_agency_hint','pncp_id':matches[0][0],
                'message':None}
    reason = 'multiple_agency_matches' if len(matches)>1 else 'missing_or_unavailable_agency'
    message = ('Há mais de uma contratação compatível com o órgão informado. Informe o edital '
               'ou acrescente detalhes da compra.' if len(matches)>1 else
               'Para qual órgão ou município? Você pode informar esses detalhes na pergunta '
               'ou escolher um dos editais candidatos.')
    return {'status':'needs_clarification','reason':reason,'pncp_id':None,'message':message}


def rank_contracts(rankings, catalog, question):
    """RRF entre contratações; catálogo acrescenta pistas explícitas de órgão.

    Não consulta respostas esperadas. Cada ramo dá um voto por contratação,
    evitando que PDFs longos obtenham votos extras por páginas semelhantes.
    """
    scores, records = {}, {}
    for rows in rankings.values():
        seen = set()
        for row in rows:
            edital = row[2]
            if edital not in catalog:
                raise ValueError('Resultado fora do escopo permitido')
            if edital in seen:
                continue
            seen.add(edital)
            records.setdefault(edital, row)
            scores[edital] = scores.get(edital, 0) + 1/(60+len(seen))
    matches = [(key,score) for key,score in agency_matches(catalog,question) if key in records]
    for rank,(key,_) in enumerate(matches,1):
        scores[key] += 1/(60+rank)
    return [(records[key],scores[key]) for key in sorted(scores,key=lambda k:(-scores[k],k))]


def discover(question, pncp_id=None):
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        raise ValueError('Pergunta inválida')
    catalog = allowed_editais()
    if pncp_id is not None and (not isinstance(pncp_id, str) or pncp_id not in catalog):
        raise ValueError('Contratação não permitida')
    allowed = [pncp_id] if pncp_id is not None else sorted(catalog)
    started = perf_counter()
    vector = local_embeddings().embed_query(question)
    rankings = {'keyword': search_branch(question, allowed),
                'semantic': search_branch(question, allowed, vector)}
    fused = rank_contracts(rankings, {key:catalog[key] for key in allowed}, question)
    candidates = []
    seen = set()
    for row, score in fused:
        edital = row[2]
        if edital not in catalog or edital not in allowed:
            raise ValueError('Resultado fora do escopo permitido')
        if edital in seen:
            continue
        seen.add(edital)
        candidates.append({'pncp_id': edital, 'agency': catalog[edital].get('agency', ''),
                           'uf': catalog[edital].get('uf', ''), 'score': score,
                           'passage_id': row[0], 'document_sequence': row[3],
                           'page': row[4], 'start': row[5], 'end': row[6], 'url': row[7]})
        if len(candidates) == 5:
            break
    return {'snapshot_id': SNAPSHOT, 'scope': 'selected' if pncp_id else 'development',
            'candidates': candidates, 'exhaustive': False,
            'routing': route_discovery(question,catalog,candidates,pncp_id),
            'latency_ms': (perf_counter() - started) * 1000,
            'interpretation': 'Candidatos de recuperação; relevância e resposta exigem conferência.'}
