import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from radar import api, public_data

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(api.app)
ROUTES = ['/api/versions', '/api/versions/alias_items/compare/alias_items_v3',
          '/api/versions/alias_items_v3/compare/alias_items', '/api/versions/alias_items/compare/alias_items_v2',
          '/api/versions/alias_items_v2/compare/alias_items_v3', '/api/cases', '/api/cases/pilot-17',
          '/api/cases/independent-06', '/api/quality', '/api/corpus']
FORBIDDEN = {'answer', 'quote', 'quotes', 'claims', 'citations', 'notes_private', 'reviewer', 'text',
             'password', 'senha', 'token', 'api_key', 'key', 'secret', 'review_record', 'review_notes'}


def _walk(value, keys, strings):
    if isinstance(value, dict):
        for k, v in value.items():
            keys.add(k)
            _walk(v, keys, strings)
    elif isinstance(value, list):
        for v in value:
            _walk(v, keys, strings)
    elif isinstance(value, str):
        strings.append(value)


@pytest.mark.parametrize('route', ROUTES)
def test_route_has_no_private_field_or_value(route):
    response = client.get(route)
    assert response.status_code == 200
    keys, strings = set(), []
    _walk(response.json(), keys, strings)
    assert not keys & FORBIDDEN
    blob = '\n'.join(strings)
    assert not re.search(r'gsk_|AppData|LocalCache|[A-Za-z]:\\|@[\w-]+\.(gov|com)|\d{3}\.\d{3}\.\d{3}-\d{2}', blob)
    assert 'Renê' not in blob and 'Rene' not in blob


def test_every_url_is_https_pncp():
    urls = []
    for route in ROUTES:
        _walk(client.get(route).json(), set(), urls)
    links = [u for u in urls if '://' in u]
    assert links and all(re.fullmatch(r'https://pncp\.gov\.br/\S+', u) for u in links)


def test_quotes_from_public_references_are_not_exposed():
    reference = json.loads((ROOT / 'datasets/evaluation/pilot-candidate-v1.json').read_text(encoding='utf-8'))
    quote = next(e['quote'] for c in reference['cases'] for e in c['evidence'] if len(e.get('quote', '')) > 30)
    assert quote not in client.get('/api/cases/pilot-01').text
    assert quote not in json.dumps([client.get(r).json() for r in ROUTES], ensure_ascii=False)


def test_case_detail_shows_not_evaluated_and_human_criteria():
    detail = client.get('/api/cases/pilot-17').json()
    assert detail['variants']['alias_items_v2']['human_status'] == 'not_evaluated'
    assert detail['variants']['alias_items']['criteria'] == {'correct': False, 'complete': True,
                                                            'supported': True, 'no_mixing': False}
    assert detail['variants']['alias_items']['human_pass'] is False
    assert detail['variants']['alias_items_v3']['error_tags'] == ['ambiguous_question']
    assert detail['sources'][0]['page'] == 54


def test_comparison_highlights_regressions_not_only_averages():
    data = client.get('/api/versions/alias_items/compare/alias_items_v3').json()
    assert 'independent-08' in data['regressions']
    assert 'pilot-35' in data['improvements']
    assert data['factual_answered'] == {'alias_items': 39, 'alias_items_v3': 38, 'of': 40}


def test_versions_and_quality_state_decision_and_blockers():
    versions = client.get('/api/versions').json()
    assert versions['default_variant'] == 'alias_items'
    by_id = {v['id']: v for v in versions['versions']}
    assert by_id['alias_items']['is_default'] and not by_id['alias_items_v3']['promoted']
    assert by_id['alias_items_v2']['human'] is None
    quality = client.get('/api/quality').json()
    assert quality['decision'] == 'blocked' and quality['holdout']['executed'] is False
    assert quality['holdout']['cases_pending_user_approval'] == 46


@pytest.mark.parametrize('route,status', [('/api/cases/pilot-99', 404), ('/api/cases/..%2Fsecrets', 404),
                                          ('/api/cases/x' * 1, 422), ('/api/versions/alias_items/compare/alias_items', 404),
                                          ('/api/versions/evil/compare/alias_items', 422)])
def test_invalid_inputs_are_rejected(route, status):
    assert client.get(route).status_code == status


@pytest.mark.parametrize('method', ['post', 'put', 'delete', 'patch'])
def test_only_reads_are_allowed(method):
    assert getattr(client, method)('/api/cases').status_code == 405


def test_no_cors_and_security_headers():
    response = client.get('/api/versions', headers={'Origin': 'https://evil.example'})
    assert 'access-control-allow-origin' not in response.headers
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert "default-src 'none'" in response.headers['content-security-policy']
    preflight = client.options('/api/versions', headers={'Origin': 'https://evil.example',
                                                         'Access-Control-Request-Method': 'GET'})
    assert 'access-control-allow-origin' not in preflight.headers
    assert client.get('/docs').status_code == 404 and client.get('/openapi.json').status_code == 404


def test_injected_private_field_fails_closed(monkeypatch):
    original = public_data.quality

    def leaky():
        data = original()
        data['blockers'] = data['blockers'] + [{'answer': 'resposta bruta'}]
        return public_data.assert_public(data)
    monkeypatch.setattr(public_data, 'quality', leaky)
    with pytest.raises(ValueError, match='Campo privado'):
        client.get('/api/quality')


@pytest.mark.parametrize('value', ['gsk_abcdefghijklmnop', r'C:\Users\x', 'fulano@orgao.gov.br', '123.456.789-00'])
def test_private_values_are_refused(value):
    with pytest.raises(ValueError, match='Valor privado'):
        public_data.assert_public({'x': [value]})


@pytest.mark.parametrize('url', ['http://pncp.gov.br/a', 'https://pncp.gov.br.evil.com/a', 'javascript:alert(1)'])
def test_non_pncp_urls_are_refused(url):
    with pytest.raises(ValueError):
        public_data.safe_url(url)


def test_api_does_not_import_database_groq_or_private_paths():
    code = ('import sys; import radar.api; '
            "bad=[m for m in ('radar.config','radar.storage','radar.generation','radar.embeddings','psycopg','langchain_groq') if m in sys.modules];"
            'print(bad)')
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == '[]'
    source = (ROOT / 'backend/src/radar/api.py').read_text(encoding='utf-8') + \
        (ROOT / 'backend/src/radar/public_data.py').read_text(encoding='utf-8')
    assert 'private_root(' not in source and 'import private_root' not in source and 'connect(' not in source


def test_static_export_matches_api_and_is_public(tmp_path):
    spec = importlib.util.spec_from_file_location('export_site', ROOT / 'ops/export-site-data.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = module.export(tmp_path)
    assert {'versions.json', 'quality.json', 'corpus.json', 'cases.json', 'case-pilot-17.json'} <= set(names)
    assert all(p.suffix == '.json' for p in tmp_path.iterdir())
    assert json.loads((tmp_path / 'quality.json').read_text(encoding='utf-8')) == client.get('/api/quality').json()
    keys = set()
    for path in tmp_path.glob('*.json'):
        _walk(json.loads(path.read_text(encoding='utf-8')), keys, [])
    assert not keys & FORBIDDEN
