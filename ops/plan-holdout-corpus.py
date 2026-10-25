"""Candidatos da amostra de validação futura (holdout); só metadados públicos do PNCP.

Exclui tudo que o projeto já viu (manifestos, candidatos, referências) antes de aceitar
um edital. Não baixa PDFs, não calcula hashes, não grava no banco e não chama a Groq.
Para no primeiro HTTP 429, preservando o que já foi coletado.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx
from radar.config import PROJECT, emit_json
from radar.independence import agency_of, development_exclusions
from radar.ingestion import API, FILES, get, safe_url
from radar.sector import classify_sector

REGIONS = {'AM': 'Norte', 'PA': 'Norte', 'TO': 'Norte', 'RO': 'Norte', 'MA': 'Nordeste', 'PE': 'Nordeste',
           'RN': 'Nordeste', 'PB': 'Nordeste', 'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste', 'MG': 'Sudeste',
           'ES': 'Sudeste', 'RS': 'Sul', 'PR': 'Sul', 'SC': 'Sul', 'SP': 'Sudeste', 'BA': 'Nordeste', 'GO': 'Centro-Oeste'}


def load_exclusions():
    manifests = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((PROJECT / 'datasets/manifests').glob('*.json'))]
    references = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((PROJECT / 'datasets/evaluation').glob('*.json'))]
    listings = [json.loads((PROJECT / 'reports' / name).read_text(encoding='utf-8'))
                for name in ('independent-corpus-candidates-v1.json', 'independent-documents-v1.json')]
    return development_exclusions([m for m in manifests if 'editais' in m], references, listings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--start', default='20260801')
    parser.add_argument('--end', default='20260920')
    parser.add_argument('--target', type=int, default=14)
    args = parser.parse_args()
    exclusions = load_exclusions()
    seen = set(exclusions['pncp_ids'])
    window = [args.start, args.end]
    state = {'candidates': [], 'errors': [], 'dropped_agency_overlap': []}
    if args.report.exists():
        previous = json.loads(args.report.read_text(encoding='utf-8'))
        if previous.get('search_window') == window:
            state = {'candidates': previous['candidates'], 'errors': previous['errors'],
                     'dropped_agency_overlap': previous.get('dropped_agency_overlap', [])}
    if any(c['pncp_id'] in exclusions['pncp_ids'] for c in state['candidates']):
        raise ValueError('Candidato salvo sobrepõe desenvolvimento')
    seen.update(c['pncp_id'] for c in state['candidates'])
    for candidate in [c for c in state['candidates'] if agency_of(c['pncp_id']) in exclusions['agencies']]:
        state['candidates'].remove(candidate)
        state['dropped_agency_overlap'].append({'pncp_id': candidate['pncp_id'], 'uf': candidate['uf']})
    rate_limited = False

    def save(final=False):
        emit_json(args.report, {'state': 'metadata_candidates_not_downloaded' if final else 'collection_in_progress',
            'purpose': 'future_holdout_never_used_for_tuning', 'search_window': window, 'target': args.target,
            'captured_at_utc': datetime.now(timezone.utc).isoformat(),
            'excluded_development': {'pncp_ids': len(exclusions['pncp_ids']),
                'document_sha256': len(exclusions['document_sha256']), 'questions': len(exclusions['questions'])},
            'candidates': state['candidates'], 'errors': state['errors'],
            'dropped_agency_overlap': state['dropped_agency_overlap'], 'rate_limited': rate_limited,
            'pdf_hash_overlap_check': 'pending_download', 'questions': 'not_prepared', 'groq_calls': 0,
            'representative': False})

    headers = {'User-Agent': 'RadarDeEditais/0.1 (portfolio research)'}
    with httpx.Client(timeout=httpx.Timeout(45, connect=15), follow_redirects=False, headers=headers) as client:
        for uf, region in REGIONS.items():
            if len(state['candidates']) >= args.target or rate_limited:
                break
            if any(c['uf'] == uf for c in state['candidates']):
                continue
            selected = None
            for page in range(1, 6):
                try:
                    response = get(client, API, params={'dataInicial': args.start, 'dataFinal': args.end,
                        'codigoModalidadeContratacao': 6, 'uf': uf, 'pagina': page, 'tamanhoPagina': 50})
                except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                    status = getattr(getattr(exc, 'response', None), 'status_code', None)
                    state['errors'].append({'uf': uf, 'page': page, 'stage': 'publication_query',
                                            'error_type': type(exc).__name__, 'http_status': status})
                    rate_limited = status == 429
                    break
                for item in response.get('data', []):
                    identifier = item.get('numeroControlePNCP')
                    if not identifier or identifier in seen or agency_of(identifier) in exclusions['agencies'] \
                            or classify_sector(item.get('objetoCompra', '')) != 'in_scope_candidate':
                        continue
                    cnpj, year, sequence = item['orgaoEntidade']['cnpj'], item['anoCompra'], item['sequencialCompra']
                    try:
                        files = get(client, FILES.format(cnpj=cnpj, year=year, sequence=sequence))
                    except (httpx.HTTPError, ValueError, KeyError) as exc:
                        status = getattr(getattr(exc, 'response', None), 'status_code', None)
                        state['errors'].append({'uf': uf, 'page': page, 'pncp_id': identifier, 'stage': 'file_listing',
                                                'error_type': type(exc).__name__, 'http_status': status})
                        if status == 429:
                            rate_limited = True
                            break
                        continue
                    documents = [{'sequence': f['sequencialDocumento'], 'url': safe_url(f['url']), 'type_id': 2,
                                  'sha256_status': 'pending_download'}
                                 for f in (files if isinstance(files, list) else []) if f.get('tipoDocumentoId') == 2]
                    if not documents or any(d['url'] in exclusions['document_urls'] for d in documents):
                        continue
                    selected = {'pncp_id': identifier, 'uf': uf, 'region': region,
                        'agency': item['orgaoEntidade']['razaoSocial'], 'object': item.get('objetoCompra', '')[:300],
                        'publication_date': item.get('dataPublicacaoPncp'),
                        'official_url': f'https://pncp.gov.br/app/editais/{cnpj}/{year}/{sequence}', 'documents': documents}
                    seen.add(identifier)
                    break
                if rate_limited or selected or page >= response.get('totalPaginas', 0):
                    break
            if selected:
                state['candidates'].append(selected)
            save()
            print(json.dumps({'uf': uf, 'selected': bool(selected), 'total': len(state['candidates']),
                              'rate_limited': rate_limited}), flush=True)
    save(final=True)


if __name__ == '__main__':
    main()
