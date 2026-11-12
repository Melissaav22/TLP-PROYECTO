"""Las 13 frases históricas evaluadas con la gramática de la variante.

La referencia original permanece en datos/fase1.json y resultados/fase1/.
"""
from .comparar_nlp import main
from .common import ROOT

if __name__ == '__main__':
    raise SystemExit(main(['--corpus', str(ROOT / 'datos/comparacion_fase1_ampliada.json'),
                          '--output', str(ROOT / 'resultados/ampliacion/comparacion_fase1.json')]))
