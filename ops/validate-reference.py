"""Confere referências contra o corpus privado; não aprova interpretação humana."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from radar.config import private_root, emit_json


def validate(reference, prepared, manifest):
    if reference['snapshot_id'] != prepared['snapshot_id'] or reference['snapshot_id'] != manifest['snapshot_id']:
        raise ValueError('Snapshot divergente')
    chunks = {c['id']: c for c in prepared['chunks']}
    page_offsets=reference.get('evidence_format')=='page_offsets_v1'
    pages={(d['pncp_id'],d['document_sequence'],p['page']):p['text']
           for d in prepared.get('documents',[]) for p in d['pages']}
    sources = {(e['pncp_id'], d['sequence']): d for e in manifest['editais'] for d in e['documents']}
    seen = set()
    counts = Counter()
    editais = {e['pncp_id']: e for e in manifest['editais']}
    documents = set()
    covered = set()
    for case in reference['cases']:
        if not isinstance(case['id'], str) or not case['id'] or case['id'] in seen or not isinstance(case['question'], str) or not case['question'].strip() or not 1 <= len(case['question']) <= 1000:
            raise ValueError('ID duplicado ou pergunta inválida')
        seen.add(case['id'])
        if case['review_status'] not in ('draft', 'approved') or case['kind'] not in ('answerable', 'out_of_scope'):
            raise ValueError('Classificação inválida')
        if not isinstance(case['expected_answer'], str) or not case['expected_answer'].strip():
            raise ValueError('Resposta esperada vazia')
        if case['review_status'] == 'approved' and not case.get('review_record', {}).get('basis'):
            raise ValueError('Aprovação sem registro')
        if case['pncp_id'] not in editais:
            raise ValueError('Edital inexistente')
        counts[case['kind']] += 1
        if (case['kind'] == 'answerable') != bool(case['evidence']):
            raise ValueError('Evidência incompatível com tipo de caso')
        for ev in case['evidence']:
            c = chunks[ev['chunk_id']]
            source = sources[(case['pncp_id'], ev['document_sequence'])]
            if c['pncp_id'] != case['pncp_id'] or c['document_sequence'] != ev['document_sequence'] or c['page'] != ev['page']:
                raise ValueError('Escopo de citação divergente')
            if page_offsets:
                page=pages[(case['pncp_id'],ev['document_sequence'],ev['page'])]
                if any(type(ev[k]) is not int for k in ('start','end')) or not 0<=ev['start']<ev['end']<=len(page):
                    raise ValueError('Offsets inválidos')
                if page[ev['start']:ev['end']]!=ev['quote'] or max(c['start'],ev['start'])>=min(c['end'],ev['end']):
                    raise ValueError('Citação ou âncora não encontrada na página')
            elif ev['quote'] not in c['text'] or not ev['quote'].strip():
                raise ValueError('Citação não encontrada')
            if ev['document_sha256'] != c['document_sha'] or ev['document_sha256'] != source['sha256'] or ev['url'] != source['url']:
                raise ValueError('Origem divergente')
            covered.add(case['pncp_id'])
            documents.add((case['pncp_id'], ev['document_sequence']))
    if reference.get('target_counts') and dict(counts) != reference['target_counts']:
        raise ValueError('Quantidade de casos divergente da meta')
    return {'cases': len(seen), 'approved': sum(c['review_status'] == 'approved' for c in reference['cases']),
            'counts_by_kind': dict(counts), 'draft': sum(c['review_status'] == 'draft' for c in reference['cases']),
            'answerable_editais': len(covered), 'evidence_documents': len(documents),
            'answerable_states': sorted({editais[e]['uf'] for e in covered}),
            'coverage_note': 'known_evidence_not_exhaustive_relevance_labels',
            'evidence_integrity': 'passed', 'human_review': 'not_performed_by_validator',
            'quality_metrics': 'not_computed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.reference.read_bytes()
    ref = json.loads(raw)
    # Nome de snapshot restrito: impede resolução de caminhos arbitrários no diretório privado.
    if len(ref['snapshot_id']) != 16 or any(c not in '0123456789abcdef' for c in ref['snapshot_id']):
        raise ValueError('Snapshot inválido')
    prepared = json.loads((private_root() / 'prepared' / (ref['snapshot_id'] + '.json')).read_text(encoding='utf-8'))
    result = validate(ref, prepared, json.loads(args.manifest.read_text(encoding='utf-8')))
    result.update(snapshot_id=ref['snapshot_id'], reference_sha256=hashlib.sha256(raw).hexdigest())
    emit_json(args.report, result)
    print(json.dumps(result))
