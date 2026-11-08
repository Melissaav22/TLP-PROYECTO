"""Demo comparativa de las mismas oraciones con tres sistemas."""
from .comparar_nlp import main
from .common import ROOT

if __name__ == '__main__':
    raise SystemExit(main(['--corpus', str(ROOT / 'datos/fase1.json'),
                          '--output', str(ROOT / 'resultados/fase1/comparacion.json')]))
