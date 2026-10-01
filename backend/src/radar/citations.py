"""Seleção de fonte pelo modelo; passagem literal escolhida pelo servidor."""
from copy import deepcopy


def source_schema(schema):
    result=deepcopy(schema)
    evidence=result['properties']['claims']['items']['properties']['evidence']['items']
    evidence['properties'].pop('quote')
    evidence['required']=['chunk_id']
    return result


def attach_literal_sources(payload,documents):
    result=deepcopy(payload);sources={d.metadata['id']:d.page_content for d in documents}
    if not isinstance(result,dict) or not isinstance(result.get('claims'),list):
        raise ValueError('Formato de resposta inválido')
    for claim in result['claims']:
        if not isinstance(claim,dict) or not isinstance(claim.get('evidence'),list):
            raise ValueError('Afirmação sem evidência')
        for ev in claim['evidence']:
            if not isinstance(ev,dict) or set(ev)!={'chunk_id'} or ev['chunk_id'] not in sources:
                raise ValueError('Fonte não recuperada')
            ev['quote']=sources[ev['chunk_id']]
    return result


def source_aliases(documents):
    identifiers=[d.metadata['id'] for d in documents]
    if not 1<=len(identifiers)<=5 or any(not isinstance(i,str) or not i for i in identifiers) or len(set(identifiers))!=len(identifiers):
        raise ValueError('Fonte não recuperada')
    return {f'S{i}':identifier for i,identifier in enumerate(identifiers,1)}


def alias_schema(schema,aliases):
    result=source_schema(schema)
    result['properties']['claims']['items']['properties']['evidence']['items']['properties']['chunk_id']['enum']=list(aliases)
    return result


def resolve_aliases(payload,aliases):
    result=deepcopy(payload)
    if not isinstance(result,dict) or not isinstance(result.get('claims'),list):
        raise ValueError('Formato de resposta inválido')
    for claim in result['claims']:
        if not isinstance(claim,dict) or not isinstance(claim.get('evidence'),list):
            raise ValueError('Afirmação sem evidência')
        for ev in claim['evidence']:
            if not isinstance(ev,dict) or set(ev)!={'chunk_id'} or not isinstance(ev['chunk_id'],str) or ev['chunk_id'] not in aliases:
                raise ValueError('Fonte não recuperada')
            ev['chunk_id']=aliases[ev['chunk_id']]
    return result
