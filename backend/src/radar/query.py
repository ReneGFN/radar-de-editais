"""Planejamento determinístico usando somente pergunta e metadados de escopo."""
import re
import unicodedata


def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if not unicodedata.combining(c))


STOP = set('''a as ao aos o os de da das do dos e em na nas no nos para por pelo pela pelos pelas
um uma uns umas qual quais que qualis sao e ser se como como quando onde com sem sobre sua seu
suas seus esse essa este esta estes estas isso isto ha tem ter ela ele eles elas ou partir
especificacao especificacoes especificado especificada especificados especificadas exigido exigida
exigidos exigidas descrito descrita descritos descritas descricao indicado indicada indicados indicadas
previsto prevista previstos previstas consta constam constar estabelecido estabelecida estabelecidos
pagina paginas lista planilha trecho trechos arquivo arquivos edital editais contratacao contratacoes
camara municipal municipio fundacao estado sequencia clausula secao item itens lote lotes qual
quantos quantas quantidades quais delas deles daqueles daquelas diferenciando diferencia tratar
aparecem aparece apresentada apresentado referente respectivos respectiva respectivo respectivas
'''.split())


def plan(query, agency='', structured=False):
    page = re.search(r'\bp[aá]gina\s+(\d+)\b',query,re.I)
    document = re.search(r'\barquivo\s+(\d+)\b',query,re.I)
    clause = re.search(r'\b(?:cl[aá]usula|item)\s+(\d+(?:\.\d+)+)\b',query,re.I)
    clean = re.sub(r'\b(?:p[aá]gina|arquivo|sequ[eê]ncia)\s+\d+\b',' ',query,flags=re.I)
    clean = re.sub(r'\b(?:cl[aá]usula|item)\s+\d+(?:\.\d+)+\b',' ',clean,flags=re.I)
    identity = set(re.findall(r'[\w]+',fold(agency)))
    tokens = re.findall(r'\w+(?:[.,]\d+)?',clean,flags=re.UNICODE)
    selected = [t for t in tokens if fold(t) not in STOP and fold(t) not in identity]
    focused = ' '.join(selected).strip() or query
    filters = {}
    if structured:
        if page: filters['page'] = int(page.group(1))
        if document: filters['document_sequence'] = int(document.group(1))
        if clause: filters['clause'] = clause.group(1)
    return {'query':focused,'filters':filters}
