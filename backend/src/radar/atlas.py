"""Catálogo público do atlas; somente manifesto de desenvolvimento, sem banco ou Groq."""
import json
import re
from pathlib import Path


def explore_catalog():
    root=Path(__file__).resolve().parents[3]
    manifest=json.loads((root/'datasets/manifests/1446c44aca18011a.json').read_text(encoding='utf-8'))
    result=[]
    for e in sorted(manifest['editais'],key=lambda e:e['pncp_id']):
        m=re.fullmatch(r'(\d{14})-1-(\d{6})/(\d{4})',e['pncp_id'])
        if not m:raise ValueError('Identificador inválido')
        cnpj,sequence,year=m.groups()
        documents=[]
        for d in e['documents']:
            if not isinstance(d['sequence'],int) or d['sequence']<1:raise ValueError('Arquivo inválido')
            documents.append({'sequence':d['sequence'],'url':f'https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{year}/{int(sequence)}/arquivos/{d["sequence"]}'})
        result.append({'pncp_id':e['pncp_id'],'agency':e['agency'],'uf':e.get('uf'),'object':e.get('object',''),'documents':documents})
    return result
