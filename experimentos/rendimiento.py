"""Mediciones locales de parsing repetido con gramática ya cargada."""
from statistics import mean, pstdev
from time import perf_counter
import platform
from minic.grammar import Grammar
from minic.parser import parse_detailed
from .common import ROOT, metadata, write_json


def main():
    grammar = Grammar(ROOT / 'gramatica_minic.txt')
    measurements = []
    for language, sizes in [('minic', [10, 100, 500, 1200]), ('espanol', [1, 5, 10, 25])]:
        for size in sizes:
            source = 'int x;\n' * size if language == 'minic' else 'El niño dice que ' * size + 'la niña canta'
            seconds = []
            accepted = []
            for _ in range(5):
                start = perf_counter()
                result = parse_detailed(source, grammar, language == 'espanol')
                seconds.append(perf_counter() - start)
                accepted.append(result.accepted)
            measurements.append(dict(language=language, size=size, characters=len(source),
                                     repeats=5, accepted=all(accepted),
                                     mean_seconds=mean(seconds), std_seconds=pstdev(seconds)))
    write_json(ROOT / 'resultados/metricas/rendimiento.json', dict(
        metadata=metadata(ROOT / 'datos/corpus_es.json'), python=platform.python_version(),
        platform=platform.platform(), machine=platform.machine(), measurements=measurements))
    print(f'{len(measurements)} tamaños medidos con cinco repeticiones.')


if __name__ == '__main__':
    main()
