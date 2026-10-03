"""Exporta os dados públicos do painel para `site/data/*.json` (GitHub Pages).

Usa exatamente as mesmas funções e esquemas da API local, então o estático e a API
mostram o mesmo conteúdo. Grava só em `site/data/`, apaga apenas os `.json` que ela
mesma gerou antes e confere cada arquivo com `assert_public`. Não publica nada.
"""
import json
from pathlib import Path

from radar import api, public_data

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site' / 'data'


def payloads():
    yield 'versions.json', api.Versions, public_data.versions()
    for (a, b) in public_data.COMPARISONS:
        for x, y in ((a, b), (b, a)):
            yield f'compare-{x}-{y}.json', api.Comparison, public_data.compare(x, y)
    yield 'cases.json', None, public_data.cases()
    for summary in public_data.cases():
        yield f"case-{summary['id']}.json", api.CaseDetail, public_data.case(summary['id'])
    yield 'quality.json', api.Quality, public_data.quality()
    yield 'corpus.json', api.Corpus, public_data.corpus()


def export(out=OUT):
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.json'):
        old.unlink()
    names = []
    for name, model, data in payloads():
        if model is None:
            data = [api.CaseSummary.model_validate(row).model_dump() for row in data]
        else:
            data = model.model_validate(data).model_dump()
        public_data.assert_public(data)
        (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        names.append(name)
    (out / 'index.json').write_text(json.dumps({'files': sorted(names)}, indent=1) + '\n', encoding='utf-8')
    return names


if __name__ == '__main__':
    print(json.dumps({'files': len(export()), 'directory': 'site/data'}))
