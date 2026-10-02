"""Prévia privada da variante alias_items_v3 (prompt v3) nos dois conjuntos de desenvolvimento.

Não lê chave, não chama Groq e não toca no holdout. Recupera os trechos (leitura no
banco, transação somente leitura), monta exatamente o prompt que seria enviado e grava:
- prévia privada: generation/alias-items-v3-request-preview.json (perguntas e trechos);
- protocolo público: reports/generation-protocol-alias-items-v3.json (só hashes e contagens).
"""
import hashlib
import json
from radar.citations import alias_schema, source_aliases
from radar.config import PROJECT, emit_json, private_root
from radar.generation import MODEL, SCHEMA, system_prompt
from radar.retrieval import retrieve_with_trace

REFERENCES = ('pilot-candidate-v1.json', 'independent-bound-v1.json')
CODE = ('backend/src/radar/generation.py', 'backend/src/radar/retrieval.py', 'backend/src/radar/item_structure.py',
        'backend/src/radar/citations.py', 'ops/evaluate-generation.py', 'ops/preview-generation-v3.py')
ITEM_KEYS = ('item_number', 'item_header_page', 'item_header_start', 'item_recognition', 'item_continuation', 'quantity_candidates')


def main():
    system = system_prompt('source_alias', 'v3')
    requests, hashes = [], {}
    for name in REFERENCES:
        raw = (PROJECT / 'datasets/evaluation' / name).read_bytes()
        reference = json.loads(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
        for case in reference['cases']:
            docs, _ = retrieve_with_trace(case['question'], reference['snapshot_id'], case['pncp_id'], context_profile='item_structure')
            aliases = source_aliases(docs)
            reverse = {v: k for k, v in aliases.items()}
            context = [{'chunk_id': reverse[d.metadata['id']], 'page': d.metadata['page'],
                        'document_sequence': d.metadata['document_sequence'], 'content': d.page_content,
                        'item_context': {k: d.metadata[k] for k in ITEM_KEYS if k in d.metadata}} for d in docs]
            # Só pergunta e trechos recuperados: o gabarito nunca entra no prompt.
            user = {'question': case['question'], 'documents': context}
            if len(json.dumps(user, ensure_ascii=False)) > 16000:
                raise ValueError('Contexto excede o limite de consulta')
            requests.append({'case_id': case['id'], 'user': user, 'schema': alias_schema(SCHEMA, aliases),
                             'source_alias_map': aliases})
    gold = {json.dumps(c.get('expected_answer'), ensure_ascii=False) for n in REFERENCES
            for c in json.loads((PROJECT / 'datasets/evaluation' / n).read_bytes())['cases'] if c.get('expected_answer')}
    if any(g in json.dumps(r['user'], ensure_ascii=False) for r in requests for g in gold if len(g) > 20):
        raise ValueError('Gabarito apareceu no prompt')
    preview = private_root() / 'generation/alias-items-v3-request-preview.json'
    emit_json(preview, {'model': MODEL, 'system': system, 'requests': requests, 'groq_calls': 0, 'key_included': False})
    emit_json(PROJECT / 'reports/generation-protocol-alias-items-v3.json', {
        'state': 'prepared_before_execution_awaiting_user_authorization', 'variant': 'alias_items_v3',
        'baseline_variant_preserved': 'alias_items', 'previous_candidate': 'alias_items_v2', 'model': MODEL,
        'endpoint': 'https://api.groq.com/openai/v1/chat/completions', 'cases': len(requests), 'max_passages': 5,
        'reference_sha256': hashes, 'system_prompt_sha256': hashlib.sha256(system.encode()).hexdigest(),
        'preview_sha256': hashlib.sha256(preview.read_bytes()).hexdigest(),
        'code_sha256': {f: hashlib.sha256((PROJECT / f).read_bytes()).hexdigest() for f in CODE},
        'holdout_used': False, 'key_in_prompt': False, 'gold_in_prompt': False, 'groq_calls': 0, 'human_accuracy': None})
    print(json.dumps({'requests_prepared': len(requests), 'groq_calls': 0}))


if __name__ == '__main__':
    main()
