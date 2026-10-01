"""Triagem de domínio; compatibilidade por palavra não equivale a revisão do PDF."""
import re
import unicodedata


def classify_sector(text):
    if not isinstance(text,str) or not text.strip() or len(text)>10000:
        return 'review_required'
    text=''.join(c for c in unicodedata.normalize('NFD',text.lower()) if not unicodedata.combining(c))
    medical=bool(re.search(r'glicemi|glicose|sinais vitais|multiparametric|cardiac|hospitalar|odontolog|fisioterapeut|equipamentos medicos',text))
    explicit=bool(re.search(r'\b(computadores?|microcomputadores?|notebooks?|workstations?|ssd|roteadores?|switch|teclados?|mouses?)\b',text))
    category='informatica' in text and bool(re.search(r'equipamento|periferic|computador|notebook|monitor|switch|rack|workstation|materiais (?:de|para) informatica',text))
    display=bool(re.search(r'monitores?.{0,20}\b(video|lcd|led|lfd|tela)\b',text))
    if explicit or category:
        return 'mixed_requires_item_review' if medical else 'in_scope_candidate'
    if medical or 'monitoramento ambiental' in text:return 'out_of_scope'
    if display:return 'in_scope_candidate'
    if re.search(r'\bmonitores?\b',text):return 'review_required'
    return 'out_of_scope'
