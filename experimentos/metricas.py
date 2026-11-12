"""Indicadores definidos por tarea y denominadores auditables."""
import argparse
from collections import defaultdict
from .common import ROOT, digest, read_json, write_json


def binary_metrics(expected, predicted):
    if len(expected) != len(predicted):
        raise ValueError('Listas de decisiones desalineadas')
    if any(type(x) is not bool for x in [*expected, *predicted]):
        raise ValueError('Las decisiones binarias deben ser booleanas')
    tp = sum(e and p for e, p in zip(expected, predicted))
    fp = sum(not e and p for e, p in zip(expected, predicted))
    tn = sum(not e and not p for e, p in zip(expected, predicted))
    fn = sum(e and not p for e, p in zip(expected, predicted))
    ratio = lambda a, b: a / b if b else None
    return dict(n=len(expected), tp=tp, fp=fp, tn=tn, fn=fn,
                precision=ratio(tp, tp + fp), recall=ratio(tp, tp + fn),
                correct_rejection=ratio(tn, tn + fp), accuracy=ratio(tp + tn, len(expected)))


def summarize(data, corpus):
    gold = {row['id']: row for row in corpus}
    groups = defaultdict(list)
    errors = []
    for row in data['results']:
        if row['id'] not in gold:
            raise ValueError(f'ID sin oro: {row["id"]}')
        groups[(row['tool'], 'todos')].append(row)
        groups[(row['tool'], gold[row['id']]['nivel'])].append(row)
    reports = []
    for (tool, level), rows in sorted(groups.items()):
        good = [row for row in rows if not row.get('execution_error')]
        decisions = [row for row in good if type(row.get('accepted')) is bool]
        expected = [gold[row['id']]['esperado_cfg'] for row in decisions]
        predicted = [row['accepted'] for row in decisions]
        noun_gold, noun_pred = [], []
        tag_correct = 0
        alignment_errors = 0
        for row in good:
            reference = gold[row['id']]
            if row['tokens'] != reference['tokens_esperados'] or len(row['pos']) != len(reference['pos_esperado']):
                alignment_errors += 1
                if level == 'todos':
                    errors.append(dict(id=row['id'], tool=tool, type='token_alignment'))
                continue
            for word, e, p in zip(row['tokens'], reference['pos_esperado'], row['pos']):
                noun_gold.append(e == 'NOUN')
                noun_pred.append(p == 'NOUN')
                tag_correct += e == p
                if e != p and level == 'todos':
                    errors.append(dict(id=row['id'], tool=tool, type='tagging_error', word=word, expected=e, predicted=p))
        if level == 'todos':
            for row in rows:
                if row.get('execution_error'):
                    errors.append(dict(id=row['id'], tool=tool, type='execution_error', error=row['execution_error']))
            for row in decisions:
                e = gold[row['id']]['esperado_cfg']
                if e != row['accepted']:
                    errors.append(dict(id=row['id'], tool=tool,
                                       type='false_positive' if row['accepted'] else 'false_negative'))
        reports.append(dict(tool=tool, level=level, sentences=len(rows),
                            execution_errors=len(rows) - len(good), alignment_errors=alignment_errors,
                            cfg=binary_metrics(expected, predicted) if decisions else None,
                            noun_detection=binary_metrics(noun_gold, noun_pred),
                            pos_accuracy=tag_correct / len(noun_gold) if noun_gold else None,
                            mean_seconds=sum(row['seconds'] for row in good) / len(good) if good else None))
    return dict(evaluation_tasks=dict(
        cfg='Pertenencia a la CFG controlada, solo sistemas que emiten esa decisión.',
        noun_detection='Clasificación binaria por token: NOUN frente al resto, POS común.',
        pos='Exactitud de etiquetas gruesas, AUX/VERB y PROPN/NOUN unificados.'),
        reports=reports, errors=errors)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=str(ROOT / 'resultados/ampliacion/comparacion.json'))
    parser.add_argument('--corpus', default=str(ROOT / 'datos/ampliacion_es.json'))
    parser.add_argument('--output', default=str(ROOT / 'resultados/ampliacion/resumen.json'))
    args = parser.parse_args()
    data = read_json(args.input)
    if data['metadata']['corpus_sha256'] != digest(args.corpus):
        raise ValueError('El corpus cambió desde la ejecución')
    result = summarize(data, read_json(args.corpus))
    result['source_metadata'] = data['metadata']
    result['input_sha256'] = digest(args.input)
    write_json(args.output, result)
    for row in result['reports']:
        if row['level'] == 'todos':
            print(row['tool'], 'POS=', round(row['pos_accuracy'], 4), 'CFG=', row['cfg'])


if __name__ == '__main__':
    main()
