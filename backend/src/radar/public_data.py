"""Dados públicos do painel: lidos SOMENTE de relatórios e referências já publicáveis.

Este módulo não importa banco, Groq, embeddings nem `private_root`. Cada saída é
montada por lista de campos permitidos (nunca copiando objetos inteiros) e depois
conferida por `assert_public`, que recusa chaves e valores privados. A mesma função
alimenta a API local e a exportação estática, para que as duas mostrem o mesmo.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / 'reports'
DEVELOPMENT_SNAPSHOT = '1446c44aca18011a'
VARIANTS = ('alias_items', 'alias_items_v2', 'alias_items_v3')
LABELS = {'alias_items': 'alias_items (v1, padrão)', 'alias_items_v2': 'alias_items_v2 (experimental)',
          'alias_items_v3': 'alias_items_v3 (experimental de segurança)'}
COMPARISONS = {  # (base, candidata) -> relatório público já publicado
    ('alias_items', 'alias_items_v2'): 'variant-comparison-alias-items-v2.json',
    ('alias_items', 'alias_items_v3'): 'variant-comparison-alias-items-vs-alias-items-v3.json',
    ('alias_items_v2', 'alias_items_v3'): 'variant-comparison-alias-items-v2-vs-alias-items-v3.json',
}
HUMAN_REVIEWS = {
    'alias_items': ('human-review-pilot-alias-items-v4.json', 'human-review-independent-alias-items-v2.json'),
    'alias_items_v3': ('human-review-pilot-alias-items-v3-review-v1.json', 'human-review-independent-alias-items-v3-review-v1.json'),
}
REFERENCES = {'pilot-candidate-v1.json': 'desenvolvimento (piloto histórico)',
              'independent-bound-v1.json': 'desenvolvimento (lote novo usado em ajustes)'}
REGIONS = {'Norte': 'AC AM AP PA RO RR TO', 'Nordeste': 'AL BA CE MA PB PE PI RN SE',
           'Centro-Oeste': 'DF GO MS MT', 'Sudeste': 'ES MG RJ SP', 'Sul': 'PR RS SC'}
REGION_OF = {uf: region for region, ufs in REGIONS.items() for uf in ufs.split()}

FORBIDDEN_KEYS = frozenset({'answer', 'quote', 'quotes', 'claims', 'citations', 'notes_private', 'reviewer',
    'text', 'content', 'password', 'senha', 'token', 'api_key', 'key', 'secret', 'expected_answer_private',
    'review_notes', 'notes', 'drafting_record', 'review_record', 'embedding', 'vectors'})
PRIVATE_VALUE = re.compile(
    r'gsk_[A-Za-z0-9]{8,}|[A-Za-z]:\\|AppData|LocalCache|/home/|/Users/|RADAR_PRIVATE_ROOT'
    r'|[\w.+-]+@[\w-]+\.[\w.]+|\d{3}\.\d{3}\.\d{3}-\d{2}|BEGIN [A-Z ]*PRIVATE KEY|Bearer\s', re.I)
PNCP_URL = re.compile(r'https://pncp\.gov\.br/[A-Za-z0-9/._~%#=-]+')
CASE_ID = re.compile(r'(pilot|independent)-\d{2}')


def assert_public(value, path='$'):
    """Recusa qualquer chave privada ou valor com cara de segredo, caminho local ou dado pessoal."""
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise ValueError(f'Campo privado {path}.{key}')
            assert_public(item, f'{path}.{key}')
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_public(item, f'{path}[{index}]')
    elif isinstance(value, str) and PRIVATE_VALUE.search(value):
        raise ValueError(f'Valor privado em {path}')
    return value


def safe_url(url):
    """Só links HTTPS do PNCP saem para o painel; qualquer outro valor é recusado."""
    if not isinstance(url, str) or not PNCP_URL.fullmatch(url):
        raise ValueError('URL de fonte fora de https://pncp.gov.br')
    return url


@lru_cache(maxsize=None)
def _read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def _report(name):
    return _read('reports/' + name)


def gate():
    return _report('quality-gate-v2.json')


def _human_cases(variant):
    rows = {}
    for name in HUMAN_REVIEWS.get(variant, ()):
        for row in _report(name)['cases']:
            rows[row['case_id']] = {'review_status': row['review_status'], 'criteria': dict(row['criteria']),
                                    'error_tags': list(row['error_tags']), 'answer_state': row['answer_state'],
                                    'citation_integrity': row['citation_integrity']}
    return rows


def _technical_states():
    states = {}
    for (base, candidate), name in COMPARISONS.items():
        for case in _report(name)['cases']:
            entry = states.setdefault(case['case_id'], {})
            entry[base] = case['state_v1']
            entry[candidate] = case['state_v2'] if not case.get('rejection_v2') else 'rejected'
    return states


def versions():
    current = gate()
    output = []
    for variant in VARIANTS:
        data = current['variants'][variant]
        human = data.get('human_review_development')
        output.append({'id': variant, 'label': LABELS[variant], 'role': data['role'], 'status': data['status'],
            'is_default': variant == current['default_variant'], 'promoted': variant == current['default_variant'],
            'factual_answered_of_40': data['factual_answered_of_40'],
            'input_tokens_total': data['input_tokens_total'], 'input_tokens_counted_cases': data['input_tokens_counted_cases'],
            'generation_ms_median': data['generation_ms_median'], 'total_ms_median': data['total_ms_median'],
            'human': None if human is None else {
                'answerable_reviewed': human['answerable']['human_reviewed'], 'answerable_cases': human['answerable']['cases'],
                'answerable_all_criteria_true': human['answerable']['all_criteria_true'],
                'refusals_reviewed': human['refusals']['human_reviewed'], 'refusals_cases': human['refusals']['cases'],
                'refusals_all_criteria_true': human['refusals']['all_criteria_true'],
                'rate_available': human['answerable']['human_reviewed'] == human['answerable']['cases']
                                  and human['refusals']['human_reviewed'] == human['refusals']['cases'],
                'error_tag_counts': dict(human['error_tag_counts'])},
            'findings': data.get('human_findings')})
    return assert_public({'default_variant': current['default_variant'], 'decision_record': {
        k: current['decision_record'][k] for k in ('date', 'basis', 'reason')}, 'metric_caveats': current['metric_caveats'],
        'versions': output})


def _change(kind, before, after):
    """Classifica a mudança técnica de estado; humano decide a correção semântica."""
    good_answerable = before == 'answered'
    if kind == 'answerable':
        if before == after:
            return 'unchanged'
        return 'regression' if good_answerable else 'improvement' if after == 'answered' else 'changed'
    abstain = ('refused', 'insufficient_evidence')
    if before == after:
        return 'unchanged'
    if before in abstain and after == 'answered':
        return 'regression'
    if before == 'answered' and after in abstain:
        return 'improvement'
    return 'changed'


def compare(a, b):
    if (a, b) in COMPARISONS:
        report, flip = _report(COMPARISONS[(a, b)]), False
    elif (b, a) in COMPARISONS:
        report, flip = _report(COMPARISONS[(b, a)]), True
    else:
        raise KeyError('Comparação inexistente')
    side_a, side_b = ('v2', 'v1') if flip else ('v1', 'v2')
    human_a, human_b = _human_cases(a), _human_cases(b)
    cases = []
    for case in report['cases']:
        state = {'v1': case['state_v1'], 'v2': case['state_v2'] if not case.get('rejection_v2') else 'rejected'}
        before, after = state[side_a], state[side_b]
        metrics = {side: {k: case[side].get(k) for k in ('input_tokens', 'output_tokens', 'generation_ms', 'total_ms')}
                   if case.get(side) else None for side in ('v1', 'v2')}
        ha, hb = human_a.get(case['case_id']), human_b.get(case['case_id'])
        cases.append({'case_id': case['case_id'], 'kind': case['kind'], 'category': case.get('category'),
            'state_a': before, 'state_b': after, 'technical_change': _change(case['kind'], before, after),
            'human_a': ha['review_status'] if ha else 'not_evaluated',
            'human_b': hb['review_status'] if hb else 'not_evaluated',
            'human_pass_a': _passed(ha), 'human_pass_b': _passed(hb),
            'metrics_a': metrics[side_a], 'metrics_b': metrics[side_b]})
    for case in cases:
        if case['human_pass_a'] is True and case['human_pass_b'] is False:
            case['human_change'] = 'regression'
        elif case['human_pass_a'] is False and case['human_pass_b'] is True:
            case['human_change'] = 'improvement'
        else:
            case['human_change'] = 'not_comparable' if None in (case['human_pass_a'], case['human_pass_b']) else 'unchanged'
    agg = {side: {k: report['aggregate'][side][k] for k in ('input_tokens', 'output_tokens', 'generation_ms', 'total_ms')}
           for side in ('v1', 'v2')}
    return assert_public({'a': a, 'b': b, 'retrieval_changed': report['retrieval_changed'],
        'holdout_used': report['holdout_used'],
        'factual_answered': {a: report['factual_answered'][side_a], b: report['factual_answered'][side_b],
                             'of': report['factual_answered']['of']},
        'aggregate': {a: agg[side_a], b: agg[side_b]},
        'regressions': [c['case_id'] for c in cases if 'regression' in (c['technical_change'], c['human_change'])],
        'improvements': [c['case_id'] for c in cases if 'improvement' in (c['technical_change'], c['human_change'])],
        'cases': cases,
        'note': 'mudança técnica de estado não é correção semântica; "not_evaluated" significa sem revisão humana'})


def _passed(human):
    if not human or human['review_status'] != 'human_reviewed':
        return None
    if human['answer_state'] == 'rejected':
        return False
    return all(v is True for v in human['criteria'].values())


def _source(evidence):
    return {'document_sha256': evidence['document_sha256'], 'document_sequence': evidence.get('document_sequence'),
            'page': evidence['page'], 'url': safe_url(evidence['url'])}


@lru_cache(maxsize=None)
def _case_index():
    states = _technical_states()
    humans = {variant: _human_cases(variant) for variant in VARIANTS}
    index = {}
    for name, role in REFERENCES.items():
        reference = _read('datasets/evaluation/' + name)
        if reference.get('status') not in ('approved', 'approved_bound_reference'):
            raise ValueError('Referência não aprovada não entra no painel: ' + name)
        for case in reference['cases']:
            if case.get('review_status') != 'approved' or not CASE_ID.fullmatch(case['id']):
                continue
            per_variant = {}
            for variant in VARIANTS:
                human = humans[variant].get(case['id'])
                per_variant[variant] = {'technical_state': states.get(case['id'], {}).get(variant, 'not_run'),
                    'human_status': human['review_status'] if human else 'not_evaluated',
                    'human_pass': _passed(human),
                    'criteria': human['criteria'] if human and human['review_status'] != 'pending' else None,
                    'error_tags': human['error_tags'] if human else []}
            index[case['id']] = {'id': case['id'], 'set': role, 'kind': case['kind'], 'category': case.get('category'),
                'pncp_id': case['pncp_id'], 'question': case['question'], 'expected_answer': case.get('expected_answer'),
                'sources': [_source(e) for e in case.get('evidence', [])], 'variants': per_variant}
    return index


def cases():
    return assert_public([{k: c[k] for k in ('id', 'set', 'kind', 'category', 'pncp_id')} | {
        'states': {v: c['variants'][v]['technical_state'] for v in VARIANTS},
        'human': {v: c['variants'][v]['human_status'] for v in VARIANTS},
        'human_pass': {v: c['variants'][v]['human_pass'] for v in VARIANTS}} for c in _case_index().values()])


def case(case_id):
    if not CASE_ID.fullmatch(case_id or ''):
        raise KeyError('Caso inválido')
    return assert_public(_case_index()[case_id])


def quality():
    current, release = gate(), _report('quality-release-v1.json')
    holdout = current['holdout']
    default = current['variants'][current['default_variant']]['human_review_development']
    met = [f"Revisão humana do desenvolvimento em {current['default_variant']}: "
           f"{default['answerable']['all_criteria_true']}/{default['answerable']['cases']} factuais e "
           f"{default['refusals']['all_criteria_true']}/{default['refusals']['cases']} recusas",
           'Integridade de citação verificada automaticamente (separada da correção)',
           'Independência do holdout verificada: sem sobreposição de edital, PDF, URL ou pergunta']
    blockers = [f"Holdout com {holdout['cases_pending_user_approval']} de {holdout['cases']} casos pendentes de aprovação",
                'Holdout não executado', 'Respostas do holdout sem revisão humana',
                'Conjunto novo anterior é desenvolvimento, não validação independente']
    return assert_public({'decision': current['decision'], 'target': current['target'],
        'target_status': current['target_90_percent'], 'default_variant': current['default_variant'],
        'criteria_met': met, 'blockers': blockers, 'previous_gate_reasons': list(release['reasons']),
        'holdout': {k: holdout[k] for k in ('cases', 'cases_pending_user_approval', 'status', 'executed')},
        'holdout_requirements': ['aprovação humana explícita dos 46 casos', 'protocolo congelado com hashes',
            'snapshot exclusivo, separado de ' + DEVELOPMENT_SNAPSHOT, 'execução única autorizada',
            'revisão humana das respostas', 'mínimo de 30 factuais, 10 recusas e 10 contratações'],
        'development_set_note': current['development_set_note'], 'guarantee': current['guarantee']})


def _editais(manifest, role, page_counts=None):
    rows = []
    for edital in manifest['editais']:
        uf = edital.get('uf')
        rows.append({'pncp_id': edital['pncp_id'], 'uf': uf, 'region': REGION_OF.get(uf, 'não informado'),
            'role': role, 'documents': len(edital['documents']),
            'pages': sum(d['page_count'] for d in edital['documents']) if all('page_count' in d for d in edital['documents']) else None,
            'official_url': safe_url(edital['official_url']) if edital.get('official_url') else None,
            'document_urls': [safe_url(d['url']) for d in edital['documents']]})
    return rows


def corpus():
    dev = _read(f'datasets/manifests/{DEVELOPMENT_SNAPSHOT}.json')
    prep = _report('independent-preparation-v1.json')
    holdout = _read('datasets/holdout/manifest-v1.json')
    rows = _editais(dev, 'development') + _editais(holdout, 'holdout_pending')
    summary = {}
    for row in rows:
        key = (row['role'], row['region'], row['uf'])
        entry = summary.setdefault(key, {'role': row['role'], 'region': row['region'], 'uf': row['uf'],
                                         'editais': 0, 'documents': 0, 'pages': 0, 'pages_known': True})
        entry['editais'] += 1
        entry['documents'] += row['documents']
        if row['pages'] is None:
            entry['pages_known'] = False
        else:
            entry['pages'] += row['pages']
    for entry in summary.values():
        if not entry['pages_known']:
            entry['pages'] = None
    return assert_public({'development': {'snapshot_id': DEVELOPMENT_SNAPSHOT, 'editais': prep['editais'],
            'documents': prep['documents'], 'pages': prep['pages'], 'chunks': prep['chunks']},
        'holdout': {'snapshot_id': None, 'status': 'pending_user_approval_not_indexed', 'editais': len(holdout['editais']),
            'documents': sum(len(e['documents']) for e in holdout['editais']),
            'pages': sum(d['page_count'] for e in holdout['editais'] for d in e['documents'])},
        'by_uf': sorted(summary.values(), key=lambda e: (e['role'], e['region'], e['uf'] or '')),
        'editais': rows, 'note': 'páginas por UF de desenvolvimento não constam do manifesto público (null)'})
