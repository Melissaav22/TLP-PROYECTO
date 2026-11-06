"""Ejecuta el mismo conjunto con parser propio, NLTK y spaCy."""
import argparse
from time import perf_counter
from .adaptadores import ADAPTERS, create
from .common import ROOT, metadata, read_json, write_json


def run(corpus_path, names):
    corpus = read_json(corpus_path)
    payload = dict(metadata=metadata(corpus_path), tools={}, results=[])
    for name in names:
        adapter = create(name)
        payload['tools'][name] = adapter.info
        for row in corpus:
            start = perf_counter()
            result = dict(id=row['id'], tool=name, text=row['texto'], level=row['nivel'])
            try:
                result.update(adapter.analyze(row['texto']))
                result['execution_error'] = None
            except Exception as exc:
                result['execution_error'] = f'{type(exc).__name__}: {exc}'
            result['seconds'] = perf_counter() - start
            payload['results'].append(result)
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', default=str(ROOT / 'datos/corpus_es.json'))
    parser.add_argument('--tools', nargs='+', choices=list(ADAPTERS), default=list(ADAPTERS))
    parser.add_argument('--output', default=str(ROOT / 'resultados/nlp/comparacion.json'))
    args = parser.parse_args(argv)
    try:
        results = run(args.corpus, args.tools)
    except (ImportError, LookupError, OSError) as exc:
        print(f'Error de preparacion: {exc}')
        return 1
    write_json(args.output, results)
    failures = sum(bool(row['execution_error']) for row in results['results'])
    print(f'{len(results["results"])} analisis guardados; {failures} errores de ejecucion.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
