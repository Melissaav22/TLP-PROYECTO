"""Resume respuestas reales de API y mantiene separados errores de ejecución."""
import argparse
from collections import Counter
from .common import ROOT, digest, read_json, write_json
from .metricas import binary_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=str(ROOT / 'resultados/llm/resultados.json'))
    args = parser.parse_args()
    path = ROOT / 'datos/corpus_es.json'
    data = read_json(args.input)
    if data['metadata']['corpus_sha256'] != digest(path):
        raise ValueError('Las respuestas corresponden a otro corpus')
    gold = {row['id']: row for row in read_json(path)}
    summaries = []
    for variant in ['zero_shot', 'few_shot']:
        rows = [row for row in data['results'] if row['variant'] == variant]
        successful = [row for row in rows if not row.get('execution_error')]
        metrics = binary_metrics([gold[row['id']]['esperado_cfg'] for row in successful],
                                 [row['accepted'] for row in successful])
        summaries.append(dict(variant=variant, completed=len(rows),
                              execution_errors=len(rows)-len(successful), cfg=metrics,
                              formal_adherence=sum(row['adherence']['valid'] for row in successful),
                              adherence_denominator=len(successful),
                              deviations=dict(Counter(row['adherence']['reason'] for row in successful
                                                      if not row['adherence']['valid'])),
                              estimated_usd=sum(row.get('estimated_usd', 0) for row in rows)
                              if all('estimated_usd' in row for row in rows) and rows else None))
    write_json(ROOT / 'resultados/llm/resumen.json', dict(metadata=data['metadata'], summaries=summaries))


if __name__ == '__main__':
    main()
