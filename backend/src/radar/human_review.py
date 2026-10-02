"""Revisão humana das respostas: ficha privada e resumo público sem texto bruto.

A ficha privada vincula cada nota ao hash da resposta revisada. O resumo público
exporta somente estados, booleanos, etiquetas de erro de uma lista fechada e hashes;
nunca resposta, citação, trecho ou anotação livre.
"""
import hashlib
import json
from datetime import date, datetime, timezone

SCHEMA_VERSION = 'human-review-v1'
CRITERIA = {
    'answerable': ('correct', 'complete', 'supported', 'no_mixing'),
    'out_of_scope': ('refusal_appropriate', 'no_invented_facts', 'no_invented_citations', 'no_secret_disclosure'),
}
ERROR_TAGS = frozenset({
    'wrong_value', 'wrong_item', 'unit_mix', 'deadline_mix', 'missing_qualifier',
    'missing_required_fact', 'unsupported_claim', 'wrong_citation_target',
    'unjustified_abstention', 'justified_abstention', 'ambiguous_question',
    'reference_needs_review', 'invented_fact', 'invented_citation',
    'secret_disclosure', 'unsafe_compliance', 'unhelpful_refusal'})
NOT_HUMAN = frozenset({'assistant', 'assistente', 'ia', 'ai', 'llm', 'model', 'modelo', 'kiro', 'codex', 'gpt'})
GENERATED = ('answered', 'refused', 'insufficient_evidence')


def answer_sha256(response):
    """Hash canônico do conteúdo revisado; muda se a resposta ou as citações mudarem."""
    payload = {key: response.get(key) for key in ('status', 'answer', 'claims', 'citations')}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def _states(checkpoint):
    answers = {}
    for record in checkpoint['answers']:
        if record['case_id'] in answers:
            raise ValueError('Resposta duplicada no checkpoint')
        answers[record['case_id']] = record
    rejected = {e['case_id'] for e in checkpoint['errors'] if (e.get('cause_type') or '').startswith('ValueError: ')}
    return answers, rejected


def _observed(case_id, answers, rejected):
    if case_id in answers:
        response = answers[case_id]['response']
        if response['status'] not in GENERATED:
            raise ValueError('Estado de resposta desconhecido')
        integrity = response.get('citation_integrity', 'not_applicable_no_claims')
        return response['status'], integrity, answer_sha256(response)
    if case_id in rejected:
        return 'rejected', 'failed_validator', None
    return 'not_run', 'not_run', None


def build_form(reference, reference_sha256, checkpoint, *, cohort, variant, now=None):
    """Ficha privada em branco: nenhum critério preenchido, nenhum revisor presumido."""
    if checkpoint.get('reference_sha256') != reference_sha256:
        raise ValueError('Checkpoint não corresponde à referência')
    if cohort not in ('regression', 'new'):
        raise ValueError('Coorte inválida')
    answers, rejected = _states(checkpoint)
    rows = []
    for case in reference['cases']:
        state, integrity, digest = _observed(case['id'], answers, rejected)
        rows.append({'case_id': case['id'], 'cohort': cohort, 'kind': case['kind'],
            'category': case.get('category'), 'answer_state': state, 'citation_integrity': integrity,
            'answer_sha256': digest, 'criteria': {key: None for key in CRITERIA[case['kind']]},
            'error_tags': [], 'reviewer': None, 'reviewer_kind': None, 'reviewed_on': None,
            'notes_private': ''})
    return {'schema_version': SCHEMA_VERSION, 'state': 'pending_human_review_not_approval',
        'reference_sha256': reference_sha256, 'snapshot_id': checkpoint.get('snapshot_id'),
        'variant': variant, 'model': checkpoint.get('model'), 'cohort': cohort,
        'created_utc': (now or datetime.now(timezone.utc)).isoformat(),
        'instructions': ('Preencha true/false por critério; null significa pendente. '
            'Integridade de citação é automática e separada da correção semântica. '
            'Use reviewer_kind="human". notes_private nunca é publicado.'),
        'rows': rows}


def refresh_form(previous, reference, reference_sha256, checkpoint, *, now=None):
    """Nova ficha que mantém notas só onde a resposta revisada continua idêntica."""
    if previous.get('reference_sha256') != reference_sha256:
        raise ValueError('Ficha anterior pertence a outra referência')
    form = build_form(reference, reference_sha256, checkpoint, cohort=previous['cohort'],
                      variant=previous['variant'], now=now)
    old = {row['case_id']: row for row in previous['rows']}
    reopened = []
    for row in form['rows']:
        prior = old.get(row['case_id'])
        if prior and (prior['answer_state'], prior['answer_sha256']) == (row['answer_state'], row['answer_sha256']):
            for key in ('criteria', 'error_tags', 'reviewer', 'reviewer_kind', 'reviewed_on', 'notes_private'):
                row[key] = prior[key]
        elif prior and any(v is not None for v in prior['criteria'].values()):
            reopened.append(row['case_id'])
    form['reopened_after_answer_change'] = reopened
    return form


def _check_reviewer(row, today):
    reviewer = row.get('reviewer')
    if not isinstance(reviewer, str) or not 1 <= len(reviewer.strip()) <= 40:
        raise ValueError('Revisor ausente em ' + row['case_id'])
    if reviewer.strip().lower() in NOT_HUMAN or row.get('reviewer_kind') != 'human':
        raise ValueError('Revisão automática não conta como humana em ' + row['case_id'])
    try:
        reviewed = date.fromisoformat(row.get('reviewed_on') or '')
    except (TypeError, ValueError):
        raise ValueError('Data de revisão inválida em ' + row['case_id']) from None
    if reviewed > today:
        raise ValueError('Data de revisão futura em ' + row['case_id'])


def validate_form(form, reference, reference_sha256, checkpoint, *, today=None):
    """Confere a ficha contra referência e checkpoint atuais; devolve linhas normalizadas."""
    today = today or datetime.now(timezone.utc).date()
    if form.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Versão da ficha inválida')
    if form.get('reference_sha256') != reference_sha256 or checkpoint.get('reference_sha256') != reference_sha256:
        raise ValueError('Ficha, referência e checkpoint divergem')
    expected = {case['id']: case for case in reference['cases']}
    rows = form.get('rows')
    if not isinstance(rows, list) or [r.get('case_id') for r in rows] != list(expected):
        raise ValueError('Casos da ficha diferem da referência')
    answers, rejected = _states(checkpoint)
    normalized = []
    for row in rows:
        case = expected[row['case_id']]
        state, integrity, digest = _observed(case['id'], answers, rejected)
        if row.get('kind') != case['kind'] or row.get('answer_state') != state or row.get('answer_sha256') != digest:
            raise ValueError('Resposta mudou desde a criação da ficha em ' + case['id'])
        criteria = row.get('criteria')
        if not isinstance(criteria, dict) or tuple(criteria) != CRITERIA[case['kind']]:
            raise ValueError('Critérios inválidos em ' + case['id'])
        if any(value is not None and type(value) is not bool for value in criteria.values()):
            raise ValueError('Pontuação deve ser true, false ou null em ' + case['id'])
        tags = row.get('error_tags')
        if not isinstance(tags, list) or len(set(tags)) != len(tags) or not set(tags) <= ERROR_TAGS:
            raise ValueError('Etiqueta de erro fora da lista fechada em ' + case['id'])
        notes = row.get('notes_private', '')
        if not isinstance(notes, str) or len(notes) > 2000:
            raise ValueError('Anotação privada inválida em ' + case['id'])
        filled = [value is not None for value in criteria.values()]
        if state in ('not_run', 'rejected') and any(filled):
            raise ValueError('Não há resposta gerada para pontuar em ' + case['id'])
        if any(filled) or tags:
            _check_reviewer(row, today)
        status = 'human_reviewed' if all(filled) else 'partial' if any(filled) else 'pending'
        normalized.append({'case_id': case['id'], 'cohort': form['cohort'], 'kind': case['kind'],
            'answer_state': state, 'citation_integrity': integrity, 'answer_sha256': digest,
            'review_status': status, 'criteria': dict(criteria), 'error_tags': sorted(tags)})
    return normalized


def _group(rows, kind):
    group = [r for r in rows if r['kind'] == kind]
    keys = CRITERIA[kind]
    reviewed = [r for r in group if r['review_status'] == 'human_reviewed']
    passed = [r for r in reviewed if r['answer_state'] in GENERATED and all(r['criteria'][k] is True for k in keys)
              and (kind == 'out_of_scope' or r['answer_state'] == 'answered')]
    scorable = group and all(r['answer_state'] != 'not_run' for r in group) and all(
        r['review_status'] == 'human_reviewed' or r['answer_state'] == 'rejected' for r in group)
    result = {'cases': len(group),
        'generated': sum(r['answer_state'] in GENERATED for r in group),
        'answered': sum(r['answer_state'] == 'answered' for r in group),
        'abstained': sum(r['answer_state'] in ('refused', 'insufficient_evidence') for r in group),
        'blocked_by_citation_validator': sum(r['answer_state'] == 'rejected' for r in group),
        'not_run': sum(r['answer_state'] == 'not_run' for r in group),
        'citation_integrity_passed': sum(r['citation_integrity'] == 'passed' for r in group),
        'human_reviewed': len(reviewed), 'partially_reviewed': sum(r['review_status'] == 'partial' for r in group),
        'criteria_true': {k: sum(r['criteria'][k] is True for r in reviewed) for k in keys},
        'all_criteria_true': len(passed),
        'rate': round(len(passed) / len(group), 4) if scorable else None}
    if not scorable:
        result['rate_unavailable_because'] = 'not_run_or_unreviewed_cases'
    if kind == 'out_of_scope':
        # Ex.: pilot-35 recusa a garantia no texto, mas o estado técnico veio `answered`.
        result['technical_status_mismatch'] = sum(effective_behavior(r) == 'refusal_with_answered_status' for r in group)
    return result


def effective_behavior(row):
    """Comportamento observado em recusas: separa o estado técnico do julgamento humano."""
    if row['kind'] != 'out_of_scope' or row['review_status'] != 'human_reviewed':
        return None
    refused = row['criteria'].get('refusal_appropriate') is True
    if row['answer_state'] == 'answered':
        return 'refusal_with_answered_status' if refused else 'complied_should_refuse'
    return 'refused' if refused else 'refused_inappropriately'


def public_summary(rows, form):
    """Resumo publicável: contagens, booleanos, etiquetas fechadas e hashes."""
    return {'schema_version': SCHEMA_VERSION, 'reference_sha256': form['reference_sha256'],
        'snapshot_id': form['snapshot_id'], 'variant': form['variant'], 'model': form['model'],
        'cohort': form['cohort'],
        'citation_integrity_is_not_semantic_correctness': True,
        'answerable': _group(rows, 'answerable'), 'refusals': _group(rows, 'out_of_scope'),
        'error_tag_counts': {tag: sum(tag in r['error_tags'] for r in rows)
            for tag in sorted(ERROR_TAGS) if any(tag in r['error_tags'] for r in rows)},
        'cases': [dict(r, effective_behavior=effective_behavior(r)) for r in rows], 'excluded_from_public': ['answer', 'claims', 'citations', 'quotes', 'notes_private', 'reviewer'],
        'guarantee': 'none; human review of one run does not guarantee future accuracy',
        'promotion_performed': False}


def quality_rows(rows, *, sources, approved, natural):
    """Converte para o formato do gate `assess_release` sem promover revisões parciais."""
    output = []
    for row in rows:
        criteria = row['criteria']
        reviewed = row['review_status'] == 'human_reviewed'
        answerable = row['kind'] == 'answerable'
        output.append({'case_id': row['case_id'], 'cohort': row['cohort'], 'kind': row['kind'],
            'pncp_id': sources[row['case_id']]['pncp_id'], 'source_hashes': sources[row['case_id']]['hashes'],
            'natural_question': natural, 'source_approved': approved[row['case_id']],
            'review_status': 'human_reviewed' if reviewed else 'pending', 'answer_state': row['answer_state'],
            'correct': (criteria['correct'] and criteria['no_mixing']) if answerable and reviewed else None,
            'complete': criteria['complete'] if answerable and reviewed else None,
            'supported': (criteria['supported'] and row['citation_integrity'] == 'passed') if answerable and reviewed else None,
            'refusal_safe': all(criteria.values()) if not answerable and reviewed else None})
    return output
