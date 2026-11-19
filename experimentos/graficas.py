"""Tablas CSV y gráficas regeneradas desde las métricas guardadas."""
import csv
from .common import ROOT, read_json


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data = read_json(ROOT / 'resultados/metricas/resumen.json')
    target = ROOT / 'resultados/metricas'
    with (target / 'tabla.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['sistema', 'nivel', 'exactitud_pos', 'precision_noun', 'recall_noun',
                         'rechazo_correcto_noun', 'tiempo_medio_s', 'errores_ejecucion'])
        for row in data['reports']:
            m = row['noun_detection']
            writer.writerow([row['tool'], row['level'], row['pos_accuracy'], m['precision'],
                             m['recall'], m['correct_rejection'], row['mean_seconds'], row['execution_errors']])
    rows = [row for row in data['reports'] if row['level'] == 'todos']
    fig, ax = plt.subplots(figsize=(8, 4.4), layout='constrained')
    bars = ax.bar([r['tool'] for r in rows], [r['pos_accuracy'] for r in rows],
                  color=['#17365d', '#2a7f8e', '#b27735'])
    ax.set(ylim=(0, 1.09), ylabel='Exactitud de POS', title='Etiquetado sobre el mismo corpus de 60 oraciones')
    ax.bar_label(bars, labels=[f'{r["pos_accuracy"]:.1%}' for r in rows], padding=5)
    ax.spines[['top', 'right']].set_visible(False)
    fig.savefig(target / 'exactitud_pos.png', dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.4), layout='constrained')
    ax.bar([r['tool'] for r in rows], [r['mean_seconds'] * 1000 for r in rows],
           color=['#17365d', '#2a7f8e', '#b27735'])
    ax.set(ylabel='Milisegundos por oración', title='Tiempo de inferencia con modelos ya cargados')
    ax.spines[['top', 'right']].set_visible(False)
    fig.savefig(target / 'tiempos.png', dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
