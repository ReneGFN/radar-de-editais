"""Experimento local: combina posição no ranking e cobertura de termos da pergunta."""
import re
from .query import fold, STOP


def tokens(value):
    return {t for t in re.findall(r'\w+',fold(value)) if t not in STOP}


def rerank_coverage(candidates, query, limit=5):
    # Somente pergunta e trechos recuperados; nenhuma referência ou ID de caso.
    terms=tokens(query)
    scored=[]
    for row,rank_score in candidates:
        coverage=len(terms & tokens(row[1]))/len(terms) if terms else 0
        scored.append((row,rank_score + .02*coverage))
    return sorted(scored,key=lambda pair:(-pair[1],pair[0][0]))[:limit]
