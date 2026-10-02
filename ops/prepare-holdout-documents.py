"""Baixa os PDFs do holdout para o diretório privado e grava só metadados públicos.

- PDFs vão para <privado>/raw/<sha256>.pdf; o texto por página fica em
  <privado>/holdout/pages-<hash dos candidatos>.json (nunca no repositório).
- Antes de aceitar um PDF, compara hash e URL com TODO o desenvolvimento
  (manifestos, referências e listas de candidatos) e com a própria amostra.
- Não indexa, não grava no banco, não chama a Groq. Para no primeiro HTTP 429 e
  retoma do checkpoint na próxima execução, sem baixar de novo o que já tem.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
import httpx
from pypdf import PdfReader
from radar.config import PROJECT, emit_json, private_root
from radar.independence import development_exclusions
from radar.ingestion import get

MIN_TEXT = 80


def load_exclusions():
    """Mesmo critério do coletor: tudo em manifests/, evaluation/ e listas antigas é desenvolvimento."""
    manifests = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((PROJECT / 'datasets/manifests').glob('*.json'))]
    references = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((PROJECT / 'datasets/evaluation').glob('*.json'))]
    listings = [json.loads((PROJECT / 'reports' / name).read_text(encoding='utf-8'))
                for name in ('independent-corpus-candidates-v1.json', 'independent-documents-v1.json')]
    return development_exclusions([m for m in manifests if 'editais' in m], references, listings)


def public_document(d):
    keys = ('pncp_id', 'uf', 'region', 'agency', 'document_sequence', 'sha256', 'url', 'bytes',
            'page_count', 'low_text_pages', 'overlap_development', 'overlap_in_sample')
    return {k: d[k] for k in keys}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidates', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    raw = args.candidates.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    selection = json.loads(raw)
    exclusions = load_exclusions()
    for path in (args.report, args.manifest):
        if path.resolve().is_relative_to((PROJECT / 'datasets/manifests').resolve()) or \
                path.resolve().is_relative_to((PROJECT / 'datasets/evaluation').resolve()):
            raise SystemExit('Holdout não pode ficar em datasets/manifests ou datasets/evaluation (viraria desenvolvimento)')
    root = private_root()
    checkpoint = root / 'holdout' / f'pages-{digest[:16]}.json'
    prepared = json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else \
        {'candidate_sha256': digest, 'documents': [], 'errors': []}
    if prepared['candidate_sha256'] != digest:
        raise ValueError('Checkpoint diverge da lista de candidatos')
    done = {(d['pncp_id'], d['document_sequence']) for d in prepared['documents']}
    state = {'rate_limited': False}

    def save():
        emit_json(checkpoint, prepared)
        docs = [public_document(d) for d in prepared['documents']]
        emit_json(args.report, {
            'captured_at_utc': datetime.now(timezone.utc).isoformat(), 'candidate_sha256': digest,
            'purpose': 'future_holdout_never_used_for_tuning', 'state': 'downloaded_extracted_not_indexed',
            'documents': docs, 'errors': prepared['errors'], 'rate_limited': state['rate_limited'],
            'overlap_development': sum(d['overlap_development'] for d in docs),
            'overlap_in_sample': sum(d['overlap_in_sample'] for d in docs),
            'extractor': {'package': 'pypdf', 'version': version('pypdf'), 'low_text_threshold_chars': MIN_TEXT},
            'database_changes': 0, 'groq_calls': 0, 'system_outputs_seen_for_these_documents': 0})
        editais = {}
        for d in prepared['documents']:
            if d['overlap_development']:
                continue
            editais.setdefault(d['pncp_id'], {'pncp_id': d['pncp_id'], 'uf': d['uf'], 'agency': d['agency'], 'documents': []})
            editais[d['pncp_id']]['documents'].append({'sequence': d['document_sequence'], 'sha256': d['sha256'],
                'url': d['url'], 'bytes': d['bytes'], 'page_count': d['page_count']})
        emit_json(args.manifest, {'role': 'holdout_draft_not_indexed', 'candidate_sha256': digest,
                                  'editais': list(editais.values())})

    headers = {'User-Agent': 'RadarDeEditais/0.1 (portfolio research)'}
    with httpx.Client(timeout=httpx.Timeout(60, connect=15), follow_redirects=False, headers=headers) as client:
        for edital in selection['candidates']:
            if edital['pncp_id'] in exclusions['pncp_ids']:
                raise ValueError('Candidato sobrepõe desenvolvimento: ' + edital['pncp_id'])
            for doc in edital['documents']:
                if (edital['pncp_id'], doc['sequence']) in done:
                    continue
                try:
                    if doc['url'] in exclusions['document_urls']:
                        raise ValueError('URL já vista no desenvolvimento')
                    content = get(client, doc['url'], binary=True)
                    if not content.startswith(b'%PDF-'):
                        raise ValueError('Documento não é PDF')
                    sha = hashlib.sha256(content).hexdigest()
                    in_sample = any(d['sha256'] == sha and d['pncp_id'] != edital['pncp_id'] for d in prepared['documents'])
                    pdf = root / 'raw' / f'{sha}.pdf'
                    pdf.parent.mkdir(parents=True, exist_ok=True)
                    if not pdf.exists():
                        pdf.write_bytes(content)
                    pages = []
                    for index, page in enumerate(PdfReader(BytesIO(content)).pages, 1):
                        text = page.extract_text() or ''
                        pages.append({'page': index, 'text': text,
                                      'quality': 'text' if len(text.strip()) >= MIN_TEXT else 'needs_review'})
                    prepared['documents'].append({'pncp_id': edital['pncp_id'], 'uf': edital['uf'],
                        'region': edital['region'], 'agency': edital['agency'], 'document_sequence': doc['sequence'],
                        'sha256': sha, 'url': doc['url'], 'bytes': len(content), 'page_count': len(pages),
                        'low_text_pages': sum(p['quality'] != 'text' for p in pages),
                        'overlap_development': sha in exclusions['document_sha256'], 'overlap_in_sample': in_sample,
                        'pages': pages})
                    done.add((edital['pncp_id'], doc['sequence']))
                    print(json.dumps({'prepared': len(done), 'pncp_id': edital['pncp_id'], 'sequence': doc['sequence'],
                                      'pages': len(pages), 'overlap_development': sha in exclusions['document_sha256']}),
                          flush=True)
                except Exception as exc:  # registra e segue; 429 encerra
                    status = getattr(getattr(exc, 'response', None), 'status_code', None)
                    prepared['errors'].append({'pncp_id': edital['pncp_id'], 'document_sequence': doc['sequence'],
                                               'error_type': type(exc).__name__, 'http_status': status,
                                               'date_utc': datetime.now(timezone.utc).isoformat()})
                    print(json.dumps({'pncp_id': edital['pncp_id'], 'error_type': type(exc).__name__,
                                      'http_status': status}), flush=True)
                    if status == 429:
                        state['rate_limited'] = True
                save()
                if state['rate_limited']:
                    return
    save()


if __name__ == '__main__':
    main()
