"""Avaliação da recuperação com evidências conhecidas; sem julgar geração."""
from statistics import median


def score_case(case, documents, k=5):
    if case['kind'] != 'answerable' or case['review_status'] != 'approved' or not case['evidence']:
        raise ValueError('Somente perguntas factuais aprovadas podem ser pontuadas')
    if not isinstance(k, int) or not 1 <= k <= 100:
        raise ValueError('k inválido')
    selected = documents[:k]
    if any(d.metadata['pncp_id'] != case['pncp_id'] for d in selected):
        raise ValueError('Resultado fora do edital')
    expected = {ev['chunk_id'] for ev in case['evidence']}
    ranks = [i for i,d in enumerate(selected,1) if d.metadata['id'] in expected]
    # Outro trecho sobreposto pode conter a mesma evidência na mesma fonte/página.
    quote_hits = [any(d.metadata['document_sequence'] == ev['document_sequence']
                      and d.metadata['page'] == ev['page']
                      and ev['quote'] in d.page_content for d in selected)
                  for ev in case['evidence']]
    return {'known_chunk_hit_at_k': bool(ranks), 'first_known_rank': min(ranks) if ranks else None,
            'reciprocal_rank_at_k': 1/min(ranks) if ranks else 0.0,
            'all_known_quotes_supported_at_k': all(quote_hits),
            'some_known_quote_supported_at_k': any(quote_hits)}


def summarize(rows):
    if not rows:
        raise ValueError('Avaliação vazia')
    latencies = sorted(row['latency_ms'] for row in rows)
    # Percentil por posto mais próximo, explicitado no relatório.
    from math import ceil
    return {'cases': len(rows), 'known_chunk_hits_at_5': sum(r['known_chunk_hit_at_k'] for r in rows),
            'known_chunk_hit_at_5': sum(r['known_chunk_hit_at_k'] for r in rows)/len(rows),
            'known_chunk_mrr_at_5': sum(r['reciprocal_rank_at_k'] for r in rows)/len(rows),
            'all_known_quotes_supported_at_5': sum(r['all_known_quotes_supported_at_k'] for r in rows)/len(rows),
            'latency_median_ms': median(latencies), 'latency_p95_ms': latencies[ceil(.95*len(rows))-1]}
