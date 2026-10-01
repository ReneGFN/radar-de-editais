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
