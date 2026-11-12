"""Exporta tokens, producciones, fenómeno y punto de fallo por oración."""
from minic.grammar import Grammar
from minic.parser import parse_detailed
from .common import ROOT, metadata, read_json, write_json


def main():
    path = ROOT / 'datos/ampliacion_es.json'
    grammar = Grammar(ROOT / 'gramatica_minic.txt')
    records = []
    for row in read_json(path):
        result = parse_detailed(row['texto'], grammar, True)
        lexical = any(d.code == 'unknown_word' for d in result.diagnostics)
        classification = 'vocabulario' if lexical else ('sintaxis_del_subconjunto' if result.diagnostics else 'aceptada')
        records.append(dict(id=row['id'], text=row['texto'], phenomena=row['fenomenos'],
                            expected=row['esperado_cfg'], accepted=result.accepted,
                            classification=classification, tokens=result.tokens,
                            productions=result.productions,
                            diagnostics=[d.to_dict() for d in result.diagnostics]))
    write_json(ROOT / 'resultados/ampliacion/fallos.json', dict(metadata=metadata(path), cases=records))
    print(f'{len(records)} casos con trazas guardados.')


if __name__ == '__main__':
    main()
