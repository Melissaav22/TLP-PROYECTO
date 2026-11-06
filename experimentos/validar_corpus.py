"""Valida integridad del dataset sin consultar predicciones del parser."""
import argparse
from collections import Counter
import unicodedata
from .common import ROOT, digest, read_json


def validate(corpus, examples=()):
    errors = []
    if len(corpus) < 60:
        errors.append('Se requieren al menos 60 oraciones')
    ids = [row.get('id') for row in corpus]
    if None in ids or len(ids) != len(set(ids)):
        errors.append('IDs ausentes o duplicados')
    texts = [unicodedata.normalize('NFC', row.get('texto', '')).casefold().strip() for row in corpus]
    if '' in texts or len(texts) != len(set(texts)):
        errors.append('Textos ausentes o duplicados')
    levels = Counter(row.get('nivel') for row in corpus)
    if set(levels) != {'simple', 'intermedio', 'complejo'}:
        errors.append('Deben existir exactamente los tres niveles')
    grammar_hash = digest(ROOT / 'gramatica_minic.txt')
    for row in corpus:
        if type(row.get('esperado_cfg')) is not bool:
            errors.append(f'{row.get("id")}: esperado_cfg debe ser booleano')
        if not row.get('fenomenos'):
            errors.append(f'{row.get("id")}: faltan fenomenos')
        if row.get('grammar_version') != grammar_hash:
            errors.append(f'{row.get("id")}: version de gramatica desactualizada')
        if len(row.get('tokens_esperados', [])) != len(row.get('pos_esperado', [])):
            errors.append(f'{row.get("id")}: etiquetas POS desalineadas')
    sample_texts = {unicodedata.normalize('NFC', row['texto']).casefold().strip() for row in examples}
    if set(texts) & sample_texts:
        errors.append('Hay ejemplos few-shot dentro de la evaluacion')
    if set(ids) & {row['id'] for row in examples}:
        errors.append('IDs de ejemplos se superponen a la evaluacion')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', type=str, default=str(ROOT / 'datos/corpus_es.json'))
    args = parser.parse_args()
    corpus = read_json(args.corpus)
    examples = read_json(ROOT / 'datos/ejemplos_few_shot.json')
    errors = validate(corpus, examples)
    for error in errors:
        print(error)
    print(dict(oraciones=len(corpus), niveles=dict(Counter(row['nivel'] for row in corpus)), errores=len(errors)))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
