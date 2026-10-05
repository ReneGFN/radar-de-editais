"""Relatório público de EXECUÇÃO de uma variante (separado do protocolo congelado).

O protocolo (`generation-protocol-<variante>.json`) descreve o que foi preparado ANTES
de executar e não é reescrito. Este relatório descreve o que aconteceu DEPOIS:
tentativas, falhas, retomadas, estados, consumo e latência. Lê os checkpoints
privados, mas grava somente contagens, ids de caso, estados e números agregados.
"""
import argparse
import hashlib
import json
import statistics
from pathlib import Path
from radar.config import PROJECT, emit_json, private_root

FORBIDDEN = ('answer', 'claims', 'citations', 'quote', 'expected_answer', 'notes_private', 'reviewer')


def _stats(values):
    values = [v for v in values if isinstance(v, (int, float))]
    if not values:
        return {'n': 0, 'median': None, 'total': None}
    return {'n': len(values), 'median': round(statistics.median(values), 1), 'total': round(sum(values), 1)}


def summarize_checkpoint(checkpoint):
    """Agrega um checkpoint de geração sem copiar nenhum texto."""
    answers = checkpoint['answers']
    accepted = {a['case_id'] for a in answers}
    if len(accepted) != len(answers):
        raise ValueError('Caso aceito repetido no checkpoint')
    errors = checkpoint['errors']
    rate_limited = [e['case_id'] for e in errors if e.get('http_status') == 429]
    rejected = sorted({e['case_id'] for e in errors if (e.get('cause_type') or '').startswith('ValueError: ')})
    rejection_causes = {e['case_id']: e['cause_type'] for e in errors if e['case_id'] in rejected}
    other = [e['case_id'] for e in errors if e.get('http_status') != 429 and e['case_id'] not in rejected]
    states = {}
    for a in answers:
        states[a['response']['status']] = states.get(a['response']['status'], 0) + 1
    if rejected:
        states['rejected_by_validator'] = len(rejected)
    usage = [a['response'].get('usage') or {} for a in answers]
    return {
        'cases_completed': len(accepted) + len([c for c in rejected if c not in accepted]),
        'accepted_answers': len(accepted),
        'calls_attempted': len(answers) + len(errors),
        'rate_limited_attempts': len(rate_limited), 'rate_limited_case_ids': rate_limited,
        'rate_limited_then_accepted': sorted(set(rate_limited) & accepted),
        'rejected_by_validator_case_ids': rejected, 'rejection_causes': rejection_causes,
        'other_failures': other,
        'accepted_case_repeated': False,
        'states': dict(sorted(states.items())),
        'citation_integrity_passed': sum(a['response'].get('citation_integrity') == 'passed' for a in answers),
        'input_tokens_accepted': _stats([u.get('input_tokens') for u in usage]),
        'output_tokens_accepted': _stats([u.get('output_tokens') for u in usage]),
        'generation_ms_accepted': _stats([a['response'].get('generation_latency_ms') for a in answers]),
        'total_ms_accepted': _stats([a.get('total_latency_ms') for a in answers]),
        'usage_of_failed_attempts': 'not_recorded_not_confirmed',
        'billing': sorted({a['response'].get('billing') for a in answers} - {None}),
    }


def assert_public(value, path='$'):
    """Falha se algum campo de texto privado entrar no relatório."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN:
                raise ValueError('Campo privado no relatório: ' + path + '.' + key)
            assert_public(item, path + '.' + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_public(item, f'{path}[{index}]')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('variant')
    parser.add_argument('references', nargs='+', type=Path)
    parser.add_argument('--protocol', required=True, help='Relatório de protocolo preservado (reports/)')
    parser.add_argument('--authorization', action='append', default=[], help='Registro textual de cada autorização')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    if not report.is_relative_to((PROJECT / 'reports').resolve()):
        raise SystemExit('Relatório deve ficar em reports/')
    protocol_path = PROJECT / 'reports' / args.protocol
    groups = {}
    for reference in args.references:
        digest = hashlib.sha256(reference.read_bytes()).hexdigest()
        checkpoint_path = private_root() / 'generation' / f'evaluation-{digest[:16]}-{args.variant}.json'
        checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8'))
        if checkpoint.get('reference_sha256') != digest or checkpoint.get('variant') != args.variant:
            raise SystemExit('Checkpoint não corresponde à referência/variante')
        groups[reference.stem] = dict(summarize_checkpoint(checkpoint), reference_sha256=digest,
            snapshot_id=checkpoint.get('snapshot_id'), model=checkpoint.get('model'))
    total = {key: sum(g[key] for g in groups.values())
             for key in ('cases_completed', 'accepted_answers', 'calls_attempted', 'rate_limited_attempts')}
    result = {'schema_version': 'generation-execution-v1', 'variant': args.variant,
        'protocol_report': args.protocol,
        'protocol_report_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        'protocol_preserved_unchanged': True,
        'authorizations': args.authorization, 'totals': total, 'groups': groups,
        'holdout_used': False, 'retrieval_changed_vs_protocol': False,
        'citation_integrity_is_not_semantic_correctness': True,
        'excluded_from_public': list(FORBIDDEN)}
    assert_public({k: v for k, v in result.items() if k != 'excluded_from_public'})
    emit_json(report, result)
    print(json.dumps({'report': report.name, **total}))


if __name__ == '__main__':
    main()
