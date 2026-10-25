"""Fluxo do holdout em etapas, cada uma bloqueada até a aprovação humana dos casos.

Nenhuma etapa roda enquanto houver caso sem `review_status: approved` com registro de
revisão humana, ou se o hash da referência estiver revogado. Ordem obrigatória:

  precheck   só leitura: aprovação, independência (PNCP, URL, hash de PDF, perguntas),
             URLs HTTPS do PNCP, hashes dos PDFs privados, página e offsets dos trechos.
  freeze     grava o protocolo público (hashes de código, referência, manifesto,
             configuração, modelo, prompt e snapshot planejado). Nunca sobrescreve.
  index      cria o snapshot EXCLUSIVO do holdout (manifesto em datasets/holdout/,
             nunca em datasets/manifests/, que é desenvolvimento). Exige --confirm-index.
  preview    prévia privada dos prompts (sem chave, sem gabarito). Leitura no banco.
  generate   chamadas à Groq com checkpoint privado; exige --confirm-free-plan e
             --max-calls; para no primeiro HTTP 429 e nunca repete caso aceito.
  report     relatório público só com estados, hashes e agregados.

Este arquivo foi preparado sem executar nenhuma etapa além de `precheck`.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from radar.config import PROJECT, emit_json, private_root

DEVELOPMENT_SNAPSHOT = '1446c44aca18011a'
HOLDOUT_DIR = PROJECT / 'datasets/holdout'
PNCP_URL = re.compile(r'https://pncp\.gov\.br/[A-Za-z0-9/._~%-]+')
SHA256 = re.compile(r'[0-9a-f]{64}')
PROFILES = {  # mesma configuração do desenvolvimento, por variante
    'alias_items': {'context_profile': 'item_structure', 'citation_mode': 'source_alias', 'prompt_version': 'v1'},
    'alias_items_v3': {'context_profile': 'item_structure', 'citation_mode': 'source_alias', 'prompt_version': 'v3'},
}
CODE = ('backend/src/radar/generation.py', 'backend/src/radar/retrieval.py', 'backend/src/radar/item_structure.py',
        'backend/src/radar/citations.py', 'backend/src/radar/ingestion.py', 'backend/src/radar/storage.py',
        'backend/src/radar/independence.py', 'ops/holdout-pipeline.py', 'ops/check-holdout.py')
MAX_PASSAGES = 5
ITEM_KEYS = ('item_number', 'item_header_page', 'item_header_start', 'item_recognition', 'item_continuation', 'quantity_candidates')


def _module(name, file):
    spec = importlib.util.spec_from_file_location(name, PROJECT / 'ops' / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def approval_blockers(reference, digest, revoked):
    """Motivos que impedem qualquer etapa; lista vazia significa aprovado."""
    blockers = []
    if digest in revoked:
        blockers.append('reference_approval_revoked')
    if 'pending' in str(reference.get('status', '')) or 'draft' in str(reference.get('status', '')):
        blockers.append('reference_status_not_approved')
    for case in reference['cases']:
        record = case.get('review_record') or {}
        if case.get('review_status') != 'approved':
            blockers.append('case_not_approved:' + case['id'])
        elif record.get('reviewer_kind') != 'human' or not record.get('reviewed_on'):
            blockers.append('case_without_human_review_record:' + case['id'])
    return blockers


def source_blockers(manifest, raw_dir=None):
    """URLs só HTTPS do PNCP; hash bem formado; PDF privado presente e íntegro."""
    blockers = []
    for edital in manifest['editais']:
        for doc in edital['documents']:
            if not PNCP_URL.fullmatch(doc.get('url', '')):
                blockers.append('source_url_not_https_pncp:' + edital['pncp_id'])
            if not SHA256.fullmatch(doc.get('sha256', '')):
                blockers.append('invalid_document_hash:' + edital['pncp_id'])
                continue
            if raw_dir is not None:
                pdf = Path(raw_dir) / f"{doc['sha256']}.pdf"
                if not pdf.exists():
                    blockers.append('private_pdf_missing:' + doc['sha256'][:16])
                elif sha256_file(pdf) != doc['sha256']:
                    blockers.append('private_pdf_hash_mismatch:' + doc['sha256'][:16])
    return blockers


def evidence_blockers(reference, manifest):
    """Cada evidência aponta para um documento do manifesto, com URL e página válidas."""
    documents = {d['sha256']: d for e in manifest['editais'] for d in e['documents']}
    blockers = []
    for case in reference['cases']:
        for ev in case.get('evidence', []):
            doc = documents.get(ev.get('document_sha256'))
            if doc is None:
                blockers.append('evidence_document_not_in_manifest:' + case['id'])
                continue
            if ev.get('url') not in (doc['url'], f"{doc['url']}#page={ev.get('page')}"):
                blockers.append('evidence_url_differs_from_manifest:' + case['id'])
            page_count = doc.get('page_count')
            if not isinstance(ev.get('page'), int) or ev['page'] < 1 or (page_count and ev['page'] > page_count):
                blockers.append('evidence_page_out_of_range:' + case['id'])
            if not (isinstance(ev.get('char_start'), int) and isinstance(ev.get('char_end'), int)
                    and 0 <= ev['char_start'] < ev['char_end']):
                blockers.append('evidence_offsets_invalid:' + case['id'])
    return blockers


def planned_snapshot_id(manifest):
    """Id determinístico do snapshot exclusivo do holdout; nunca o de desenvolvimento."""
    identity = {'role': 'holdout', 'editais': [{'pncp_id': e['pncp_id'], 'documents': [
        {k: d[k] for k in ('sequence', 'sha256', 'url')} for d in e['documents']]} for e in manifest['editais']]}
    snapshot = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:16]
    if snapshot == DEVELOPMENT_SNAPSHOT:
        raise ValueError('Snapshot do holdout colidiu com o de desenvolvimento')
    return snapshot


def precheck(manifest_path, reference_path, *, check_private=True):
    checker = _module('check_holdout_cli', 'check-holdout.py')
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    raw = Path(reference_path).read_bytes()
    reference = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    if HOLDOUT_DIR.resolve() not in Path(reference_path).resolve().parents:
        raise SystemExit('Referência do holdout deve ficar em datasets/holdout/')
    result = checker.check_holdout(manifest, reference, checker.load_exclusions())
    blockers = approval_blockers(reference, digest, checker.revoked_hashes(HOLDOUT_DIR))
    blockers += ['independence:' + v['type'] for v in result['violations']]
    blockers += source_blockers(manifest, private_root() / 'raw' if check_private else None)
    blockers += evidence_blockers(reference, manifest)
    if check_private:
        pages = private_root() / 'holdout' / f"pages-{manifest['candidate_sha256'][:16]}.json"
        blockers += ['quote:' + q['type'] + ':' + q['value'] for q in checker.quote_checks(reference, pages)]
    return {'reference_sha256': digest, 'manifest_sha256': sha256_file(manifest_path),
            'planned_snapshot_id': planned_snapshot_id(manifest), 'independent': result['independent'],
            'warnings': result['warnings'], 'blockers': blockers, 'ready': not blockers}, manifest, reference


def build_protocol(check, *, variant, system_prompt_sha256, model):
    if variant not in PROFILES:
        raise SystemExit('Variante sem perfil para o holdout: ' + variant)
    return {'schema_version': 'holdout-protocol-v1', 'state': 'frozen_before_indexing',
        'reference_sha256': check['reference_sha256'], 'manifest_sha256': check['manifest_sha256'],
        'planned_snapshot_id': check['planned_snapshot_id'], 'development_snapshot_untouched': DEVELOPMENT_SNAPSHOT,
        'variant': variant, 'retrieval': dict(PROFILES[variant], mode='hybrid', max_passages=MAX_PASSAGES),
        'model': model, 'system_prompt_sha256': system_prompt_sha256,
        'code_sha256': {f: sha256_file(PROJECT / f) for f in CODE},
        'single_attempt_per_case': True, 'stop_on_http_429': True, 'gold_in_prompt': False, 'key_in_prompt': False}


def protocol_path(reference_sha256):
    return PROJECT / 'reports' / f'holdout-protocol-{reference_sha256[:16]}.json'


def assert_protocol(protocol, check, current_code=None):
    """Recusa executar se código, referência, manifesto ou snapshot mudaram desde o congelamento."""
    current_code = current_code or {f: sha256_file(PROJECT / f) for f in protocol['code_sha256']}
    for key in ('reference_sha256', 'manifest_sha256', 'planned_snapshot_id'):
        if protocol[key] != check[key]:
            raise SystemExit('Protocolo divergente em ' + key)
    drift = sorted(f for f, h in protocol['code_sha256'].items() if current_code.get(f) != h)
    if drift:
        raise SystemExit('Código mudou desde o congelamento: ' + ', '.join(drift))


def run_cases(cases, checkpoint, answer_fn, *, max_calls, interval, sleep=time.sleep, now=None):
    """Executa casos pendentes; não repete aceitos nem rejeitados; para no primeiro 429."""
    now = now or (lambda: datetime.now(timezone.utc).isoformat())
    accepted = {a['case_id'] for a in checkpoint['answers']}
    rejected = {e['case_id'] for e in checkpoint['errors'] if (e.get('cause_type') or '').startswith('ValueError: ')}
    pending = [c for c in cases if c['id'] not in accepted | rejected]
    calls = 0
    for case in pending:
        if calls >= max_calls:
            return 'call_budget_reached'
        if calls:
            sleep(interval)
        calls += 1
        start = time.perf_counter()
        try:
            value = answer_fn(case)
        except Exception as exc:  # o tipo e o status bastam; nenhuma mensagem do provedor é guardada
            kind = getattr(exc, 'kind', None) or ''
            checkpoint['errors'].append({'case_id': case['id'], 'error_type': type(exc).__name__,
                'cause_type': kind or None, 'http_status': getattr(exc, 'status_code', None), 'date_utc': now()})
            if kind.startswith('ValueError: '):
                continue
            return 'stopped_on_error'
        checkpoint['answers'].append({'case_id': case['id'], 'kind': case['kind'], 'response': value,
            'total_latency_ms': (time.perf_counter() - start) * 1000, 'human_review': 'pending', 'date_utc': now()})
    return 'completed'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('stage', choices=('precheck', 'freeze', 'index', 'preview', 'generate', 'report'))
    parser.add_argument('reference', type=Path)
    parser.add_argument('--manifest', type=Path, default=HOLDOUT_DIR / 'manifest-v1.json')
    parser.add_argument('--variant', default='alias_items')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--confirm-index', action='store_true')
    parser.add_argument('--confirm-free-plan', action='store_true')
    parser.add_argument('--max-calls', type=int, default=0)
    parser.add_argument('--interval', type=float, default=35)
    args = parser.parse_args()
    check, manifest, reference = precheck(args.manifest, args.reference)
    if args.stage == 'precheck':
        summary = {k: check[k] for k in ('ready', 'independent', 'planned_snapshot_id')} | {
            'blocker_count': len(check['blockers']), 'blocker_kinds': sorted({b.split(':')[0] for b in check['blockers']})}
        if args.report:
            emit_json(args.report, dict(check, checked_at_utc=datetime.now(timezone.utc).isoformat(),
                                        groq_calls=0, database_changes=0, retrieval_calls=0))
        print(json.dumps(summary, ensure_ascii=False))
        raise SystemExit(0 if check['ready'] else 2)
    if not check['ready']:
        raise SystemExit('Bloqueado: ' + '; '.join(check['blockers'][:10]))
    from radar.generation import MODEL, system_prompt
    path = protocol_path(check['reference_sha256'])
    if args.stage == 'freeze':
        prompt = system_prompt(PROFILES[args.variant]['citation_mode'], PROFILES[args.variant]['prompt_version'])
        protocol = build_protocol(check, variant=args.variant, model=MODEL,
                                  system_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
        if path.exists():
            raise SystemExit('Protocolo já congelado; não sobrescrevo: ' + path.name)
        emit_json(path, dict(protocol, frozen_at_utc=datetime.now(timezone.utc).isoformat()))
        print(json.dumps({'protocol': path.name, 'planned_snapshot_id': protocol['planned_snapshot_id']}))
        return
    protocol = json.loads(path.read_text(encoding='utf-8'))
    assert_protocol(protocol, check)
    snapshot = protocol['planned_snapshot_id']
    root = private_root() / 'holdout'
    if args.stage == 'index':
        if not args.confirm_index:
            raise SystemExit('Indexação exige --confirm-index após aprovação explícita')
        from radar.ingestion import prepare
        from radar.storage import load_corpus
        snap_manifest = dict(manifest, snapshot_id=snapshot, sector='informatica', uf='MULTI',
                             role='holdout_snapshot_isolated', parent_snapshot=None,
                             captured_at=manifest.get('captured_at') or protocol['frozen_at_utc'])
        snap_path = HOLDOUT_DIR / f'snapshot-{snapshot}.json'
        if snap_path.exists() and json.loads(snap_path.read_text(encoding='utf-8')) != snap_manifest:
            raise SystemExit('Manifesto do snapshot do holdout é imutável e diverge')
        emit_json(snap_path, snap_manifest)
        prepared = prepare(snap_path, PROJECT / f'reports/holdout-preparation-{snapshot}.json')
        loaded = load_corpus(snap_path, PROJECT / f'reports/holdout-load-{snapshot}.json')
        print(json.dumps({'snapshot_id': snapshot, 'prepared': bool(prepared), 'load_status': loaded.get('status')}))
        return
    cases = [dict(c, pncp_id=c['pncp_id']) for c in reference['cases']]
    profile = protocol['retrieval']
    if args.stage == 'preview':
        from radar.citations import alias_schema, source_aliases
        from radar.generation import SCHEMA
        from radar.retrieval import retrieve_with_trace
        requests = []
        for case in cases:
            docs, _ = retrieve_with_trace(case['question'], snapshot, case['pncp_id'], context_profile=profile['context_profile'])
            aliases = source_aliases(docs)
            reverse = {v: k for k, v in aliases.items()}
            # Mesmo contexto que radar.generation.answer monta: só pergunta e trechos recuperados.
            documents = [{'chunk_id': reverse[d.metadata['id']], 'page': d.metadata['page'],
                          'document_sequence': d.metadata['document_sequence'], 'content': d.page_content,
                          'item_context': {k: d.metadata[k] for k in ITEM_KEYS if k in d.metadata}} for d in docs]
            user = {'question': case['question'], 'documents': documents}
            if len(json.dumps(user, ensure_ascii=False)) > 16000:
                raise SystemExit('Contexto excede o limite de consulta em ' + case['id'])
            requests.append({'case_id': case['id'], 'user': user, 'schema': alias_schema(SCHEMA, aliases)})
        golds = [json.dumps(c['expected_answer'], ensure_ascii=False) for c in cases if c.get('expected_answer')]
        if any(g in json.dumps(r['user'], ensure_ascii=False) for r in requests for g in golds if len(g) > 20):
            raise SystemExit('Gabarito apareceu no prompt')
        preview = root / f"preview-{check['reference_sha256'][:16]}-{protocol['variant']}.json"
        emit_json(preview, {'model': protocol['model'], 'requests': requests, 'groq_calls': 0, 'key_included': False})
        emit_json(PROJECT / f"reports/holdout-preview-{check['reference_sha256'][:16]}.json", {
            'cases': len(requests), 'preview_sha256': sha256_file(preview), 'protocol': path.name,
            'groq_calls': 0, 'key_in_prompt': False, 'gold_in_prompt': False})
        print(json.dumps({'requests_prepared': len(requests), 'groq_calls': 0}))
        return
    checkpoint_path = root / f"evaluation-{check['reference_sha256'][:16]}-{protocol['variant']}.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8')) if checkpoint_path.exists() else {
        'variant': protocol['variant'], 'model': protocol['model'], 'reference_sha256': check['reference_sha256'],
        'snapshot_id': snapshot, 'answers': [], 'errors': [], 'semantic_review': 'pending'}
    if (checkpoint['reference_sha256'], checkpoint['variant'], checkpoint['snapshot_id']) != (
            check['reference_sha256'], protocol['variant'], snapshot):
        raise SystemExit('Checkpoint incompatível com o protocolo')
    if args.stage == 'generate':
        if not args.confirm_free_plan or not 1 <= args.max_calls <= len(cases) or args.interval < 30:
            raise SystemExit('Exige --confirm-free-plan, 1 <= --max-calls <= casos e intervalo >= 30 s')
        from radar.generation import answer

        def call(case):
            return answer(case['question'], snapshot, case['pncp_id'], free_plan_confirmed=True,
                          context_profile=profile['context_profile'], citation_mode=profile['citation_mode'],
                          prompt_version=profile['prompt_version'])
        outcome = run_cases(cases, checkpoint, call, max_calls=args.max_calls, interval=args.interval)
        emit_json(checkpoint_path, checkpoint)
        print(json.dumps({'outcome': outcome, 'accepted': len(checkpoint['answers']), 'errors': len(checkpoint['errors'])}))
        return
    execution = _module('generation_execution', 'report-generation-execution.py')
    summary = dict(execution.summarize_checkpoint(checkpoint), reference_sha256=check['reference_sha256'],
                   snapshot_id=snapshot, variant=protocol['variant'], protocol=path.name,
                   citation_integrity_is_not_semantic_correctness=True, human_accuracy='pending_human_review')
    execution.assert_public(summary)
    emit_json(args.report or PROJECT / f"reports/holdout-execution-{check['reference_sha256'][:16]}.json", summary)
    print(json.dumps({k: summary[k] for k in ('cases_completed', 'accepted_answers', 'calls_attempted')}))


if __name__ == '__main__':
    main()
