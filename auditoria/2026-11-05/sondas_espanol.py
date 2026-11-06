"""Pruebas de auditoría del español y del aislamiento de modos.

Las expectativas de Fase 2 se distinguen de las capacidades ya anunciadas.
El JSON conserva cada caso, su entrada, contrato y resultado.
"""
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from minic.grammar import Grammar
from minic.lexer import tokenize
from minic.lexicon_es import LEXICON, TOKENS
from minic.parser import parse

G = Grammar(ROOT / 'gramatica_minic.txt')
RESULTS = []


def record(name, source, expected, scope='actual', inspect_tree=None):
    try:
        tree, errors = parse(source, G, spanish=True)
        actual = inspect_tree(tree) if inspect_tree else not errors
        row = dict(id=name, source=source, expected=expected, actual=actual,
                   scope=scope, ok=actual == expected, errors=errors)
    except Exception as exc:
        row = dict(id=name, source=source, expected=expected, scope=scope,
                   ok=False, exception=type(exc).__name__, message=str(exc))
    RESULTS.append(row)


def command(name, source, flags, expected):
    with tempfile.TemporaryDirectory(prefix='tlp-audit-es-') as directory:
        path = Path(directory) / 'frase.txt'
        path.write_text(source, encoding='utf-8')
        result = subprocess.run(
            [sys.executable, str(ROOT / 'main.py'), str(path), *flags],
            cwd=directory, capture_output=True, encoding='utf-8', errors='replace',
            timeout=30,
        )
    RESULTS.append(dict(id=name, source=source, expected=expected,
                        actual=result.returncode, ok=result.returncode == expected,
                        scope='cli', flags=flags, stdout=result.stdout[:1200],
                        stderr=result.stderr[:1200]))


def main():
    forms = [
        ('el', 'niño', 'alto', 'corre'),
        ('la', 'niña', 'alta', 'corre'),
        ('los', 'niños', 'altos', 'corren'),
        ('las', 'niñas', 'altas', 'corren'),
    ]
    for di, det in enumerate(forms):
        for ni, noun in enumerate(forms):
            for ai, adj in enumerate(forms):
                for vi, verb in enumerate(['corre', 'corren']):
                    record(f'concordancia_{di}_{ni}_{ai}_{vi}',
                           f'{det[0]} {noun[1]} {adj[2]} {verb}',
                           di == ni == ai and vi == (di // 2))
    for si, form in enumerate(forms):
        for ai, adj in enumerate(forms):
            for ci, copula in enumerate(['es', 'son']):
                record(f'atributo_{si}_{ai}_{ci}', f'{form[0]} {form[1]} {copula} {adj[2]}',
                       si == ai and ci == (si // 2))

    cases = [
        ('svo', 'El niño lee el libro', True, 'fase2'),
        ('svo_plural', 'Las niñas compran las flores', True, 'fase2'),
        ('preterito', 'El niño corrió', True, 'fase2'),
        ('preterito_plural', 'Los niños corrieron', True, 'fase2'),
        ('imperfecto', 'La niña cantaba', True, 'fase2'),
        ('presente', 'La niña canta', True, 'actual'),
        ('subordinada_doble', 'La profesora sabe que el niño dice que las niñas cantan', True, 'actual'),
        ('subordinada_sujeto_plural', 'Los profesores dicen que la niña canta', True, 'actual'),
        ('subordinada_verbo_inconcordante', 'Los profesores dice que la niña canta', False, 'actual'),
        ('subordinada_adjetivo_inconcordante', 'El niño dice que la casa es blancos', False, 'actual'),
        ('adverbio_y_pp', 'El niño corre rápidamente en el parque', True, 'actual'),
        ('pp_y_adverbio', 'La niña camina en la ciudad despacio', True, 'actual'),
        ('pp_encadenadas', 'La mujer vive en la casa de la ciudad', True, 'actual'),
        ('sin_determinante', 'Niño corre', False, 'alcance_documentado'),
        ('oov', 'El astronauta corre', False, 'alcance_documentado'),
        ('punto_final', 'El niño corre.', False, 'alcance_documentado'),
        ('mayusculas', 'EL NIÑO CORRE', True, 'actual'),
        ('acento_nfc', 'El árbol es alto', True, 'actual'),
        ('acento_nfd', 'El a\u0301rbol es alto', True, 'robustez'),
        ('dos_oraciones', 'El niño corre\nLa niña canta', False, 'actual'),
        ('modo_es_vacio', '', False, 'aislamiento_oraciones'),
        ('modo_es_comentario', '// sin oracion', False, 'aislamiento_oraciones'),
        ('modo_es_declaracion_c', 'int x = 1;', False, 'aislamiento_oraciones'),
        ('modo_es_asignacion_c', 'x = 1;', False, 'aislamiento_oraciones'),
        ('modo_es_if_c', 'if (x < 2) {}', False, 'aislamiento_oraciones'),
        ('modo_es_while_c', 'while (x < 2) {}', False, 'aislamiento_oraciones'),
        ('modo_es_for_c', 'for (; x < 2;) {}', False, 'aislamiento_oraciones'),
    ]
    for name, source, expected, scope in cases:
        record(name, source, expected, scope)

    # Capacidad de análisis y estructura se inspeccionan de forma independiente.
    record('arbol_tiene_oracion', 'El niño corre', True,
           inspect_tree=lambda tree: any(node.label() == 'Oracion' for node in tree.subtrees()))
    record('pp_anidada_en_sn', 'La mujer vive en la casa de la ciudad', True,
           scope='interpretacion_estructural', inspect_tree=lambda tree: any(
               node.label().startswith('SN') and any(desc.label() == 'PP' for desc in list(node.subtrees())[1:])
               for node in tree.subtrees()))
    record('subordinada_doble_en_arbol', 'La profesora sabe que el niño dice que las niñas cantan', 3,
           inspect_tree=lambda tree: sum(node.label() == 'Oracion' for node in tree.subtrees()))

    for source in ['El niño es', 'La casa está', 'El niño compra', 'El niño corre que la niña canta']:
        record('caracterizacion_' + source, source, True, 'caracterizacion')

    command('cli_es_compacto', 'El niño corre', ['--es', '--compacto'], 0)
    command('cli_es_visual', 'El niño corre', ['--es'], 0)
    command('cli_es_error', 'El niño corren', ['--es', '--compacto'], 1)
    command('cli_sin_es', 'El niño corre', ['--compacto'], 1)
    command('cli_es_modo_no_filtra_c', 'int x = 1;', ['--es', '--compacto'], 1)

    # Verificar que el clon del lexer no hereda el modo de la llamada anterior.
    modes = [tokenize('el')[0][0][0], tokenize('el', True)[0][0][0], tokenize('el')[0][0][0]]
    groups = {}
    for row in RESULTS:
        group = groups.setdefault(row['scope'], dict(total=0, passed=0, failed=0))
        group['total'] += 1
        group['passed' if row['ok'] else 'failed'] += 1
    corpus = list((ROOT / 'tests/es').rglob('*.txt'))
    payload = dict(python=platform.python_version(), grammar=dict(
        nonterminals=len(G.rules), productions=sum(map(len, G.rules.values())),
        table_cells=len(G.table)), lexicon_words=len(LEXICON), lexical_categories=len(TOKENS),
        corpus_size=len(corpus), mode_sequence=modes,
        total=len(RESULTS), passed=sum(row['ok'] for row in RESULTS),
        failed=sum(not row['ok'] for row in RESULTS), groups=groups, results=RESULTS)
    Path(__file__).with_name('resultados_espanol.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"{payload['passed']}/{payload['total']} expectativas satisfechas; {payload['failed']} diferencias.")
    print('Grupos: ' + json.dumps(groups, ensure_ascii=True))
    print('Gramatica: ' + json.dumps(payload['grammar']))
    print('Lexico:', len(LEXICON), 'palabras;', len(TOKENS), 'categorias; corpus:', len(corpus))
    for row in RESULTS:
        if not row['ok']:
            print(json.dumps({
                'id': row['id'], 'actual': row.get('actual', row.get('exception')),
                'first_error': row.get('errors', [])[:1],
            }, ensure_ascii=True))


if __name__ == '__main__':
    main()
