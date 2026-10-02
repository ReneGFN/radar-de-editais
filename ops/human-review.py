"""Ficha privada de revisão humana e resumo público sem respostas brutas.

init       cria a ficha em branco no diretório privado (nunca sobrescreve uma ficha existente).
refresh    regenera a ficha após novas respostas; mantém notas de respostas idênticas e guarda a anterior.
summarize  valida a ficha preenchida contra referência/checkpoint atuais e grava só agregados.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from radar.config import PROJECT, emit_json, private_root
from radar.human_review import build_form, public_summary, quality_rows, refresh_form, validate_form

VARIANTS = ('baseline', 'source_window', 'alias_window', 'alias_items')


def paths(reference_path, variant):
    raw = reference_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    suffix = '' if variant == 'baseline' else '-' + variant
    root = private_root() / 'generation'
    return json.loads(raw), digest, root / f'evaluation-{digest[:16]}{suffix}.json', root / f'human-review-{digest[:16]}{suffix}.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=('init', 'refresh', 'summarize'))
    parser.add_argument('reference', type=Path)
    parser.add_argument('--cohort', choices=('regression', 'new'), required=True)
    parser.add_argument('--variant', choices=VARIANTS, default='alias_items')
    parser.add_argument('--report', type=Path, help='Resumo público (somente summarize)')
    args = parser.parse_args()
    reference, digest, checkpoint_path, form_path = paths(args.reference, args.variant)
    checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8'))
    if args.action == 'init':
        if form_path.exists():
            raise SystemExit('Ficha já existe; use refresh: ' + form_path.name)
        form = build_form(reference, digest, checkpoint, cohort=args.cohort, variant=args.variant)
        emit_json(form_path, form)
        print(json.dumps({'private_form': form_path.name, 'cases': len(form['rows']),
                          'scored': 0, 'state': form['state']}))
        return
    if args.action == 'refresh':
        previous_text = form_path.read_text(encoding='utf-8')
        form = refresh_form(json.loads(previous_text), reference, digest, checkpoint)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup = form_path.with_name(form_path.stem + '.previous-' + stamp + '.json')
        backup.write_text(previous_text, encoding='utf-8')
        emit_json(form_path, form)
        print(json.dumps({'private_form': form_path.name, 'previous_kept': backup.name,
                          'reopened': form['reopened_after_answer_change']}))
        return
    if not args.report:
        parser.error('--report é obrigatório em summarize')
    report = args.report.resolve()
    if not report.is_relative_to((PROJECT / 'reports').resolve()):
        raise SystemExit('Resumo público deve ficar em reports/')
    form = json.loads(form_path.read_text(encoding='utf-8'))
    if form.get('cohort') != args.cohort or form.get('variant') != args.variant:
        raise SystemExit('Coorte ou variante divergem da ficha')
    rows = validate_form(form, reference, digest, checkpoint)
    summary = public_summary(rows, form)
    manifest = json.loads((PROJECT / 'datasets/manifests' / f"{form['snapshot_id']}.json").read_text(encoding='utf-8'))
    documents = {e['pncp_id']: [d['sha256'] for d in e['documents']] for e in manifest['editais']}
    sources = {c['id']: {'pncp_id': c['pncp_id'],
        'hashes': sorted({e['document_sha256'] for e in c['evidence']}) or documents[c['pncp_id']]}
        for c in reference['cases']}
    summary['quality_rows'] = quality_rows(rows, sources=sources,
        approved={c['id']: c['review_status'] == 'approved' for c in reference['cases']},
        natural=args.cohort == 'new')
    emit_json(report, summary)
    print(json.dumps({'report': report.name, 'answerable_rate': summary['answerable']['rate'],
                      'refusal_rate': summary['refusals']['rate'],
                      'human_reviewed': summary['answerable']['human_reviewed'] + summary['refusals']['human_reviewed']}))


if __name__ == '__main__':
    main()
