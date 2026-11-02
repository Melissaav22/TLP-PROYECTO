"""Interfaz de linea de comandos del parser MiniC.

Uso:
    python main.py programa.c            # analiza y muestra el arbol
    python main.py programa.c --compacto # arbol en una sola linea
    python main.py --tabla               # muestra FIRST, FOLLOW y la tabla
"""
import argparse
import os
import sys

from minic.grammar import Grammar, GrammarError
from minic.parser import parse

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser(description='Parser LL(1) para MiniC')
    ap.add_argument('archivo', nargs='?', help='programa fuente a analizar')
    ap.add_argument('-g', '--gramatica',
                    default=os.path.join(AQUI, 'gramatica_minic.txt'))
    ap.add_argument('--tabla', action='store_true',
                    help='mostrar FIRST, FOLLOW y la tabla LL(1)')
    ap.add_argument('--compacto', action='store_true',
                    help='imprimir el arbol en formato de corchetes')
    args = ap.parse_args()

    try:
        g = Grammar(args.gramatica)
    except GrammarError as e:
        print(f'Error en la gramatica: {e}', file=sys.stderr)
        return 2
    if args.tabla:
        g.show()
    if not args.archivo:
        return 0

    with open(args.archivo, encoding='utf-8') as f:
        tree, errors = parse(f.read(), g)
    if errors:
        print(f'{len(errors)} error(es):')
        for e in errors:
            print('  ', e)
        return 1
    if args.compacto:
        print(tree)
    else:
        tree.pretty_print()
    print('Analisis exitoso.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
