"""Corre todos los casos de prueba y muestra una tabla de resultados.

- tests/validos/*.c    -> el parser debe aceptarlos (0 errores).
- tests/invalidos/*.c  -> el parser debe rechazarlos; la primera linea del
  archivo indica donde se espera el primer error:
      // ESPERA: error en linea N

Con --es corre los casos de tests/es usando el lexico del espanol.
Ambos suites usan la misma gramatica unificada (gramatica_minic.txt).

Uso (desde la raiz del proyecto):  python tests/run_tests.py [--es]
"""
import glob
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)

from minic.grammar import Grammar          # noqa: E402
from minic.parser import parse             # noqa: E402


def primera_linea_de_error(errores):
    m = re.search(r'[Ll]inea (\d+)', errores[0])
    return int(m.group(1)) if m else None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    desconocidos = [a for a in argv if a != '--es']
    if desconocidos:
        print(f'Argumento no reconocido: {desconocidos[0]}')
        print('Uso: python tests/run_tests.py [--es]')
        return 2

    es = '--es' in argv
    ruta_gramatica = os.path.join(RAIZ, 'gramatica_minic.txt')
    if es:
        base = os.path.join(AQUI, 'es')
        patron = '*.txt'
    else:
        base = AQUI
        patron = '*.c'

    g = Grammar(ruta_gramatica)
    filas = []

    for ruta in sorted(glob.glob(os.path.join(base, 'validos', patron))):
        with open(ruta, encoding='utf-8') as f:
            _, errores = parse(f.read(), g, spanish=es)
        ok = not errores
        filas.append((os.path.basename(ruta), 'aceptar',
                      'aceptado' if ok else f'rechazado ({errores[0]})', ok))

    for ruta in sorted(glob.glob(os.path.join(base, 'invalidos', patron))):
        with open(ruta, encoding='utf-8') as f:
            texto = f.read()
        m = re.search(r'ESPERA: error en linea (\d+)', texto.splitlines()[0])
        esperada = int(m.group(1)) if m else None
        _, errores = parse(texto, g, spanish=es)
        if not errores:
            filas.append((os.path.basename(ruta),
                          f'rechazar (linea {esperada})', 'aceptado', False))
        else:
            obtenida = primera_linea_de_error(errores)
            filas.append((os.path.basename(ruta),
                          f'rechazar (linea {esperada})',
                          f'rechazado (linea {obtenida})',
                          obtenida == esperada))

    ancho = max(len(f[0]) for f in filas)
    print(f'{"caso":{ancho}s} | {"esperado":22s} | {"obtenido":30s} | resultado')
    print('-' * (ancho + 70))
    for nombre, esp, obt, ok in filas:
        obt_corto = obt if len(obt) <= 30 else obt[:27] + '...'
        print(f'{nombre:{ancho}s} | {esp:22s} | {obt_corto:30s} | '
              f'{"OK" if ok else "FALLA"}')
    pasan = sum(1 for f in filas if f[3])
    print(f'\n{pasan}/{len(filas)} casos pasan.')
    return 0 if pasan == len(filas) else 1


if __name__ == '__main__':
    sys.exit(main())
