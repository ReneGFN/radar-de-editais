"""Controles locais explícitos; não constituem detector universal de ataques."""
import re
import unicodedata


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))


def input_reason(question):
    text = normalize(question)
    patterns = (
        r'ignore.{0,40}(?:instrucoes|regras|prompt)',
        r'(?:revele|mostre|imprima|exiba).{0,60}(?:chave.{0,10}api|token secreto|senha|prompt de sistema)',
        r'(?:invente|fabrique|falsifique).{0,60}(?:fonte|citacao|resposta|documento)',
    )
    if any(re.search(p, text, re.S) for p in patterns):
        return 'Não posso ignorar as regras, revelar segredos ou fabricar evidências. Posso consultar exigências dos editais com fontes.'
    return None


def context_is_safe(documents):
    # Só ordens dirigidas ao assistente; termos administrativos como "senha" são permitidos.
    return not any(re.search(r'(?:ignore.{0,40}(?:instrucoes anteriores|system prompt)|(?:assistant|assistente|modelo).{0,30}(?:revele|exfiltre).{0,40}(?:token|senha|chave))', normalize(d.page_content), re.S) for d in documents)


def numeric_mismatches(result):
    """Private diagnostic: unsupported numbers per claim, without changing acceptance."""
    mismatches = []
    if result['status'] != 'answered': return mismatches
    def numbers(text):
        return {m.lstrip('0') or '0' for m in re.findall(r'(?<![\d.,])\d+(?:[.,]\d+)*(?![\d.,])', text)}
    for index, claim in enumerate(result['claims']):
        evidence = ' '.join(e['quote'] for e in claim['evidence'])
        text = claim['text']
        # Validate bibliographic identity against the very sources cited by this claim.
        # This never permits a factual number merely because it occurs in metadata.
        cited_ids = {e['chunk_id'] for e in claim['evidence'] if 'chunk_id' in e}
        allowed = set()
        for source in result.get('citations', []):
            if source.get('id') not in cited_ids: continue
            identifier = re.search(r'-1-(\d+)/(\d{4})$',source.get('pncp_id',''))
            if identifier: allowed.add((int(identifier[1]),int(identifier[2])))
        def bibliographic(match):
            return '' if (int(match[1]),int(match[2])) in allowed else match[0]
        text = re.sub(r'\bedital\s+(?:n[º°.]?\s*)?(\d+)\s*/\s*(\d{4})\b',bibliographic,text,flags=re.I)
        missing = numbers(text) - numbers(evidence)
        if missing: mismatches.append({'claim_index':index,'unsupported_numbers':sorted(missing)})
    return mismatches


def numeric_support(result):
    """Todo número afirmado precisa aparecer nas fontes daquela afirmação.
    Não verifica relações/qualificadores nem equivalência entre unidades.
    """
    if result['status'] != 'answered':
        return result
    if numeric_mismatches(result):
        return dict(result, status='insufficient_evidence', answer='Não consegui verificar todos os números da resposta nas fontes. Reformule a pergunta ou confira o PDF.', claims=[], citations=[])
    return result


def evidence_confidence(status, sources, scope_selected=False):
    if status != 'answered' or not sources:
        return {'level':'unavailable','label':'Sem resposta factual validada', 'reasons':['Não há resposta factual com fontes para conferir.'], 'calibrated':False}
    return {'level':'review_required','label':'Fontes verificadas · interpretação a conferir',
            'reasons':['Cada afirmação possui uma passagem literal e referência de arquivo/página.',
                       'Edital selecionado pelo usuário.' if scope_selected else 'Escopo identificado pela busca; confira o órgão.',
                       'A existência da fonte não comprova a interpretação ou a ausência de conflitos.'], 'calibrated':False}
