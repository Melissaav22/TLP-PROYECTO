"""Exporta una comparación de variantes y el detalle auditable por oración."""
import csv


SCORES = (
    ('precision_pct', 'Precisión'),
    ('recall_pct', 'Recall'),
    ('rechazo_correcto_pct', 'Rechazo\ncorrecto'),
    ('adherencia_cfg_pct', 'Adherencia\na la CFG'),
)


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export_report(folder, summaries, results, gold):
    comparison = []
    for summary in summaries:
        cfg = summary['cfg']
        denominator = summary['adherence_denominator']
        percentages = [
            cfg['precision'], cfg['recall'], cfg['correct_rejection'],
            summary['formal_adherence'] / denominator if denominator else None,
        ]
        comparison.append(dict(
            variante=summary['variant'], oraciones_corpus=len(gold), evaluables=cfg['n'],
            errores_ejecucion=summary['execution_errors'], sin_registro=len(gold)-summary['completed'],
            verdaderos_positivos=cfg['tp'], falsos_positivos=cfg['fp'],
            verdaderos_negativos=cfg['tn'], falsos_negativos=cfg['fn'],
            **{field: round(value * 100, 2) if value is not None else None
               for (field, _), value in zip(SCORES, percentages)},
        ))
    write_csv(folder / 'comparacion_llm.csv', list(comparison[0]), comparison)

    by_pair = {(row['variant'], row['id']): row for row in results}
    detail = []
    for summary in summaries:
        variant = summary['variant']
        for case_id, reference in gold.items():
            row = by_pair.get((variant, case_id))
            expected = reference['esperado_cfg']
            predicted, valid, reason, execution_error = None, None, None, None
            if row is None:
                classification = 'sin_registro'
            elif row.get('execution_error'):
                classification = 'error_ejecucion'
                execution_error = row['execution_error']
            else:
                predicted = row['accepted']
                classification = {(True, True): 'verdadero_positivo', (True, False): 'falso_negativo',
                                  (False, True): 'falso_positivo', (False, False): 'verdadero_negativo'}[
                                      (expected, predicted)]
                valid = row['adherence']['valid']
                reason = row['adherence']['reason']
            detail.append(dict(
                variante=variant, id=case_id, nivel=reference['nivel'], texto=reference['texto'],
                esperado_cfg=expected, aceptado_llm=predicted, clasificacion=classification,
                adherencia_valida=valid, motivo_adherencia=reason, error_ejecucion=execution_error,
                timestamp_utc=row.get('timestamp_utc') if row else None,
                request_sha256=row.get('request_sha256') if row else None,
            ))
    write_csv(folder / 'detalle_llm.csv', list(detail[0]), detail)
    plot_comparison(folder / 'comparacion_llm.png', comparison)


def plot_comparison(path, comparison):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(8.6, 4.8), layout='constrained')
    FigureCanvasAgg(figure)
    ax = figure.subplots()
    width = 0.34
    for index, (row, color) in enumerate(zip(comparison, ('#1b5680', '#b75629'))):
        positions = [n + (index - 0.5) * width for n in range(len(SCORES))]
        values = [row[field] for field, _ in SCORES]
        name = row['variante'].replace('_', '-').capitalize()
        label = f'{name} ({row["evaluables"]}/{row["oraciones_corpus"]} evaluables)'
        bars = ax.bar(positions, [value if value is not None else 0 for value in values],
                      width, label=label, color=color)
        ax.bar_label(bars, labels=[f'{value:.1f} %' if value is not None else 'N/D' for value in values],
                     padding=4, fontsize=9)
    figure.suptitle('Comparación de las variantes del LLM', fontsize=15, fontweight='bold')
    ax.set_xticks(range(len(SCORES)), [label for _, label in SCORES])
    ax.set(ylim=(0, 108), ylabel='Porcentaje', yticks=range(0, 101, 20))
    ax.grid(axis='y', alpha=0.2)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    figure.savefig(path, dpi=180)
