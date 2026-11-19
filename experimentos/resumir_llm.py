"""Resume respuestas reales de API y mantiene separados errores de ejecución."""
import argparse
from collections import Counter
from pathlib import Path
from .common import CURRENT_CORPUS, digest, read_json, write_json
from .llm_config import load_profile, output_directory
from .metricas import binary_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', help='perfil a usar en lugar de LLM_PROVIDER en .env')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--corpus', type=Path, default=CURRENT_CORPUS,
                        help='mismo JSON etiquetado utilizado para generar los resultados')
    args = parser.parse_args()
    if args.input is None:
        try:
            profile, prefix, _, env = load_profile(args.provider)
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
        args.input = output_directory(profile, prefix, env) / 'resultados.json'
    path = args.corpus
    data = read_json(args.input)
    if data['metadata']['corpus_sha256'] != digest(path):
        raise ValueError('Las respuestas corresponden a otro corpus')
    gold = {row['id']: row for row in read_json(path)}
    summaries = []
    for variant in ['zero_shot', 'few_shot']:
        rows = [row for row in data['results'] if row['variant'] == variant]
        cost_rows = [row for row in data.get('calls', data['results']) if row['variant'] == variant]
        successful = [row for row in rows if not row.get('execution_error')]
        metrics = binary_metrics([gold[row['id']]['esperado_cfg'] for row in successful],
                                 [row['accepted'] for row in successful])
        summaries.append(dict(variant=variant, completed=len(rows),
                              execution_errors=len(rows)-len(successful), cfg=metrics,
                              formal_adherence=sum(row['adherence']['valid'] for row in successful),
                              adherence_denominator=len(successful),
                              deviations=dict(Counter(row['adherence']['reason'] for row in successful
                                                      if not row['adherence']['valid'])),
                              estimated_usd=sum(row['estimated_usd'] for row in cost_rows)
                              if cost_rows and all(row.get('estimated_usd') is not None for row in cost_rows)
                              else None))
    write_json(args.input.with_name('resumen.json'), dict(metadata=data['metadata'], summaries=summaries))


if __name__ == '__main__':
    main()
