"""Dos adjunciones de la misma frase, verificadas con NLTK ChartParser."""
from nltk import CFG, ChartParser
from minic.grammar import Grammar
from minic.parser import parse_detailed
from minic.trees import bracketed, write_svg
from .common import ROOT, metadata, write_json

TOY = """
S -> NP VP
NP -> DET N | NP PP
VP -> V PP | VP PP
PP -> P NP
DET -> 'La' | 'la'
N -> 'mujer' | 'casa' | 'ciudad'
V -> 'vive'
P -> 'en' | 'de'
"""


def main():
    text = 'La mujer vive en la casa de la ciudad'
    alternatives = list(ChartParser(CFG.fromstring(TOY)).parse(text.split()))
    own = parse_detailed(text, Grammar(ROOT / 'gramatica_minic.txt'), True)
    target = ROOT / 'resultados/ampliacion'
    for index, tree in enumerate(alternatives, 1):
        write_svg(tree, target / f'ambiguedad_{index}.svg')
    write_svg(own.tree, target / 'arbol_propio.svg')
    write_json(target / 'ambiguedad.json', dict(metadata=metadata(ROOT / 'datos/ampliacion_es.json'),
               sentence=text, toy_grammar=TOY, alternatives=len(alternatives),
               trees=[bracketed(tree) for tree in alternatives], own_tree=bracketed(own.tree),
               interpretation='La CFG auxiliar admite adjuncion nominal y verbal; el subconjunto LL(1) selecciona PP verbales sucesivas.'))
    print(f'{len(alternatives)} derivaciones de la CFG auxiliar para la misma frase.')


if __name__ == '__main__':
    main()
