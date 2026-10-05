"""Gate de qualidade v2: decisão de variante padrão a partir de relatórios PÚBLICOS.

Não lê checkpoints nem fichas privadas: só agrega comparações, resumos de revisão
humana e o estado do holdout já publicados em reports/ e datasets/holdout/.
"""
import argparse
import hashlib
import json
from pathlib import Path
from radar.config import PROJECT, emit_json

REPORTS = PROJECT / 'reports'


def _load(name):
    path = REPORTS / name
    return json.loads(path.read_text(encoding='utf-8')), hashlib.sha256(path.read_bytes()).hexdigest()


def _metrics(aggregate, answered):
    return {'factual_answered_of_40': answered,
            'input_tokens_total': aggregate['input_tokens']['total'],
            'input_tokens_counted_cases': aggregate['input_tokens']['n'],
            'generation_ms_median': aggregate['generation_ms']['median'],
            'total_ms_median': aggregate['total_ms']['median']}


def _human(pilot, new):
    def pair(group_key):
        a, b = pilot[group_key], new[group_key]
        reviewed = a['human_reviewed'] + b['human_reviewed']
        return {'cases': a['cases'] + b['cases'], 'human_reviewed': reviewed,
                'all_criteria_true': a['all_criteria_true'] + b['all_criteria_true'],
                'rate_pilot': a['rate'], 'rate_new': b['rate']}
    return {'answerable': pair('answerable'), 'refusals': pair('refusals'),
            'error_tag_counts': {k: pilot['error_tag_counts'].get(k, 0) + new['error_tag_counts'].get(k, 0)
                for k in sorted(set(pilot['error_tag_counts']) | set(new['error_tag_counts']))}}


def build():
    v1v2, h12 = _load('variant-comparison-alias-items-v2.json')
    v1v3, h13 = _load('variant-comparison-alias-items-vs-alias-items-v3.json')
    execution, hexec = _load('generation-execution-alias-items-v3.json')
    hp1, _ = _load('human-review-pilot-alias-items-v4.json')
    hn1, _ = _load('human-review-independent-alias-items-v2.json')
    hp3, _ = _load('human-review-pilot-alias-items-v3-review-v1.json')
    hn3, _ = _load('human-review-independent-alias-items-v3-review-v1.json')
    revocation = json.loads((PROJECT / 'datasets/holdout/holdout-v1-approval-revocation.json').read_text(encoding='utf-8'))
    draft = json.loads((PROJECT / 'datasets/holdout/holdout-v1-draft.json').read_text(encoding='utf-8'))
    pending = sum(c.get('review_status') != 'approved' for c in draft['cases'])
    if v1v2['aggregate']['v1'] != v1v3['aggregate']['v1']:
        raise SystemExit('Linha de base alias_items diverge entre comparações')
    return {
        'schema_version': 'quality-gate-v2', 'date': '2026-10-03',
        'decision': 'blocked', 'target': 0.9,
        'default_variant': 'alias_items',
        'decision_record': {'by': 'repository_owner', 'reviewer_kind': 'human', 'date': '2026-10-03',
            'basis': ['métricas operacionais nos 50 casos de desenvolvimento', 'revisão humana da alias_items_v3'],
            'reason': 'a v3 corrigiu comportamentos de segurança, mas não teve ganho humano líquido; custa mais e responde uma factual a menos'},
        'variants': {
            'alias_items': {'role': 'default', 'status': 'human_reviewed_development_only',
                **_metrics(v1v3['aggregate']['v1'], v1v3['factual_answered']['v1']),
                'human_review_development': _human(hp1, hn1)},
            'alias_items_v2': {'role': 'experimental_preserved', 'status': 'not_human_reviewed', 'promoted': False,
                **_metrics(v1v2['aggregate']['v2'], v1v2['factual_answered']['v2'])},
            'alias_items_v3': {'role': 'experimental_safety_variant_preserved', 'status': 'human_reviewed_not_promoted',
                'promoted': False, **_metrics(v1v3['aggregate']['v2'], v1v3['factual_answered']['v2']),
                'execution_report': 'generation-execution-alias-items-v3.json',
                'calls_attempted': execution['totals']['calls_attempted'],
                'cases_completed': execution['totals']['cases_completed'],
                'human_review_development': _human(hp3, hn3),
                'human_review_scope': {'declared_by_owner': '2026-10-03, review of v3 answers confirming the findings below',
                    'case_level_criteria_recorded': hp3['answerable']['human_reviewed'] + hp3['refusals']['human_reviewed'] + hn3['answerable']['human_reviewed'],
                    'validator_rejections_counted_as_failures': hn3['answerable']['blocked_by_citation_validator'] + hp3['answerable']['blocked_by_citation_validator'],
                    'other_cases': 'no case-level criteria recorded; v3 rate not computed'},
                'human_findings': {
                    'fixed': ['pilot-35: recusa a garantia indevida', 'pilot-36: recusa citando o fato documentado',
                              'pilot-22: estado técnico de resposta parcial corrigido'],
                    'blocked_safely_still_wrong': ['independent-02: quantidade sem apoio barrada',
                                                   'independent-08: omissão de "por item" barrada'],
                    'still_failing': ['independent-06: omite a compatibilidade JEDEC 4800 MT/s',
                                      'pilot-17: ambiguidade de item não resolvida'],
                    'regressions_vs_default': ['uma factual aceita a menos (38 contra 39 de 40)',
                                               'mais tokens de entrada', 'latência de geração e total maior']}}},
        'metric_caveats': ['tokens e latências de v2/v3 contam só respostas aceitas (48 casos); alias_items conta 50',
                           'entradas de recuperação idênticas entre variantes; Hit@5 não muda',
                           'integridade de citação não é correção semântica'],
        'development_set_note': 'o conjunto "independent-*" foi usado em ajustes: é desenvolvimento, não validação independente',
        'target_90_percent': 'não avaliável: exige holdout independente aprovado, executado e revisado por humano',
        'holdout': {'reference_draft': 'datasets/holdout/holdout-v1-draft.json', 'cases': len(draft['cases']),
                    'cases_pending_user_approval': pending,
                    'frozen_bulk_approval_revoked': revocation['revokes_reference_sha256'][:16],
                    'status': 'pending_user_approval', 'executed': False},
        'guarantee': 'nenhuma; nenhuma taxa medida aqui garante desempenho futuro',
        'inputs_sha256': {'variant-comparison-alias-items-v2.json': h12,
                          'variant-comparison-alias-items-vs-alias-items-v3.json': h13,
                          'generation-execution-alias-items-v3.json': hexec},
        'promotion_performed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=REPORTS / 'quality-gate-v2.json')
    args = parser.parse_args()
    gate = build()
    emit_json(args.report, gate)
    print(json.dumps({'report': args.report.name, 'default_variant': gate['default_variant'],
                      'holdout_pending': gate['holdout']['cases_pending_user_approval']}))


if __name__ == '__main__':
    main()
