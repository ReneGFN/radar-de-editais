"""Compara alias_items_v2 com alias_items nos mesmos casos de desenvolvimento.

Público (reports/): só ids, estados, contagens, tamanhos, tokens e latências.
Privado (generation/): ficha lado a lado com as duas respostas, para revisão humana.
Não chama a Groq e não lê o holdout.
"""
import hashlib
import json
from statistics import median
from radar.config import PROJECT, emit_json, private_root
from radar.human_review import answer_sha256

REFERENCES = ('pilot-candidate-v1.json', 'independent-bound-v1.json')


def load(digest, variant):
    path = private_root() / 'generation' / f'evaluation-{digest[:16]}-{variant}.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    answers = {a['case_id']: a for a in data['answers']}
    rejected = {e['case_id']: e.get('cause_type') for e in data['errors'] if (e.get('cause_type') or '').startswith('ValueError: ')}
    return answers, rejected


def state(case_id, answers, rejected):
    if case_id in answers:
        return answers[case_id]['response']['status']
    return 'rejected' if case_id in rejected else 'not_run'


def metrics(record):
    if not record:
        return None
    r = record['response']
    usage = r.get('usage', {})
    return {'claims': len(r['claims']), 'answer_chars': len(r['answer']), 'input_tokens': usage.get('input_tokens'),
            'output_tokens': usage.get('output_tokens'), 'generation_ms': round(r.get('generation_latency_ms', 0)),
            'total_ms': round(record.get('total_latency_ms', 0))}


def summary(rows, key):
    values = [r[key] for r in rows if r is not None and r.get(key) is not None]
    return {'n': len(values), 'median': median(values) if values else None, 'total': sum(values) if values else None}


def main():
    public, private = [], []
    for name in REFERENCES:
        raw = (PROJECT / 'datasets/evaluation' / name).read_bytes()
        reference = json.loads(raw)
        digest = hashlib.sha256(raw).hexdigest()
        v1, r1 = load(digest, 'alias_items')
        v2, r2 = load(digest, 'alias_items_v2')
        for case in reference['cases']:
            a, b = v1.get(case['id']), v2.get(case['id'])
            row = {'case_id': case['id'], 'kind': case['kind'], 'category': case.get('category'),
                   'state_v1': state(case['id'], v1, r1), 'state_v2': state(case['id'], v2, r2),
                   'rejection_v2': r2.get(case['id']),
                   'identical_answer': bool(a and b and answer_sha256(a['response']) == answer_sha256(b['response'])),
                   'v1': metrics(a), 'v2': metrics(b)}
            public.append(row)
            private.append({'case_id': case['id'], 'question': case['question'], 'expected': case.get('expected_answer'),
                            'state_v1': row['state_v1'], 'state_v2': row['state_v2'], 'rejection_v2': row['rejection_v2'],
                            'answer_v1': a and a['response']['answer'], 'answer_v2': b and b['response']['answer']})
    changes = [r for r in public if r['state_v1'] != r['state_v2']]
    factual = [r for r in public if r['kind'] == 'answerable']
    report = {
        'schema_version': 'variant-comparison-v1', 'baseline': 'alias_items', 'candidate': 'alias_items_v2',
        'holdout_used': False, 'semantic_correctness': 'not_scored_pending_human_review_of_v2',
        'retrieval_changed': False,
        'state_changes': [{k: r[k] for k in ('case_id', 'kind', 'state_v1', 'state_v2', 'rejection_v2')} for r in changes],
        'factual_answered': {'v1': sum(r['state_v1'] == 'answered' for r in factual), 'v2': sum(r['state_v2'] == 'answered' for r in factual), 'of': len(factual)},
        'identical_answers': sum(r['identical_answer'] for r in public),
        'aggregate': {v: {k: summary([r[v] for r in public], k) for k in ('claims', 'answer_chars', 'input_tokens', 'output_tokens', 'generation_ms', 'total_ms')}
                      for v in ('v1', 'v2')},
        'cases': public}
    emit_json(PROJECT / 'reports/variant-comparison-alias-items-v2.json', report)
    lines = ['# Comparação alias_items x alias_items_v2 (PRIVADO — contém respostas)', '']
    for p in private:
        lines += [f"## {p['case_id']} — v1 `{p['state_v1']}` / v2 `{p['state_v2']}`" + (f" ({p['rejection_v2']})" if p['rejection_v2'] else ''),
                  f"**Pergunta:** {p['question']}", f"**Referência:** {p['expected']}",
                  f"**v1:** {p['answer_v1']}", f"**v2:** {p['answer_v2']}", '']
    (private_root() / 'generation/comparacao-alias-items-v2.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('state_changes', 'factual_answered', 'identical_answers')}, ensure_ascii=False))
    print(json.dumps({v: {k: report['aggregate'][v][k]['median'] for k in report['aggregate'][v]} for v in ('v1', 'v2')}))
    print(json.dumps({v: {k: report['aggregate'][v][k]['total'] for k in ('input_tokens', 'output_tokens')} for v in ('v1', 'v2')}))


if __name__ == '__main__':
    main()
