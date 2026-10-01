"""Monta ficha privada de revisão humana, sem exportar respostas ao GitHub."""
import argparse
import hashlib
import json
from pathlib import Path
from radar.config import private_root


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path)
    args=parser.parse_args()
    raw=args.reference.read_bytes();reference=json.loads(raw)
    digest=hashlib.sha256(raw).hexdigest()
    root=private_root()/'generation'
    checkpoint=json.loads((root/f'evaluation-{digest[:16]}.json').read_text(encoding='utf-8'))
    completed={a['case_id']:a for a in checkpoint['answers']}
    errors={}
    for error in checkpoint['errors']:errors.setdefault(error['case_id'],[]).append(error)
    lines=['# Revisão privada das respostas','',
        'Revisão humana pendente. Citação existente não comprova correção/completude.',
        'Critérios sugeridos: resposta correta, completa, apoiada, sem mistura de item/unidade/prazo; recusa apropriada.',
        'Não publicar este arquivo sem revisão de conteúdo e privacidade.','']
    for case in reference['cases']:
        lines.extend(['## '+case['id']+' — '+case['kind'],'',case['question'],'',
            '**Referência aprovada:** '+case['expected_answer'],''])
        if case['id'] in completed:
            value=completed[case['id']]['response']
            lines.extend(['**Estado:** '+value['status'],'','**Resposta:** '+value['answer'],''])
            for citation in value['citations']:
                lines.extend(['- Fonte: arquivo '+str(citation['document_sequence'])+', página '+str(citation['page'])+
                    ' — '+citation['url'],'  Trecho: '+citation['quote'].replace('\n',' '),''])
        else:lines.extend(['**Sem resposta aceita:** rejeitada ou não concluída; consultar erros abaixo.',''])
        for error in errors.get(case['id'],[]):
            lines.append('- Tentativa com erro: '+str(error.get('cause_type') or error['error_type']))
        lines.extend(['','**Conferência de Renê:** pendente.',''])
    path=root/f'revisao-respostas-{digest[:16]}.md'
    path.write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'private_review':str(path),'accepted':len(completed)}))


if __name__=='__main__':main()
