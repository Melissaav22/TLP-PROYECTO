"""Sondas de auditoría; no modifican el parser ni sus pruebas originales.

Ejecutar desde cualquier directorio con el Python que tenga requirements.txt:
    .venv/Scripts/python.exe auditoria/verificar_auditoria.py
Las expectativas fallidas documentan brechas, no un fallo del auditor.
"""
import importlib.metadata
import json
import platform
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from minic.grammar import EPS, Grammar, GrammarError
from minic.lexer import tokenize
from minic.parser import parse
from nltk import Tree

RESULTS = []
G = Grammar(ROOT / 'gramatica_minic.txt')


def check(case, expected, operation):
    try:
        actual = operation()
        ok = actual == expected
    except Exception as exc:
        actual = {'exception': type(exc).__name__, 'message': str(exc)[:350]}
        ok = False
    RESULTS.append({'id': case, 'expected': expected, 'actual': actual, 'ok': ok})


def accepts(source):
    return not parse(source, G)[1]


def custom_grammar(text):
    with tempfile.TemporaryDirectory(prefix='minic-audit-') as directory:
        path = Path(directory) / 'grammar.txt'
        path.write_text(text, encoding='utf-8')
        return Grammar(path)


def grammar_failure(text):
    try:
        custom_grammar(text)
    except GrammarError as exc:
        return str(exc)
    return 'ACCEPTED'


def cli(args, source=None, grammar=None, outside=False):
    with tempfile.TemporaryDirectory(prefix='minic-audit-') as directory:
        directory = Path(directory)
        params = list(args)
        if source is not None:
            path = directory / 'source.c'
            path.write_text(source, encoding='utf-8')
            params.insert(0, str(path))
        if grammar is not None:
            path = directory / 'grammar.txt'
            path.write_text(grammar, encoding='utf-8')
            params += ['-g', str(path)]
        result = subprocess.run(
            [sys.executable, str(ROOT / 'main.py'), *params],
            cwd=directory if outside else ROOT,
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20,
        )
        return {'code': result.returncode, 'traceback': 'Traceback' in result.stderr,
                'stdout': result.stdout, 'stderr': result.stderr[:600],
                'stderr_last_line': result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ''}


def cli_contract(**kwargs):
    result = cli(**kwargs)
    return {key: result[key] for key in ('code', 'traceback')}


def precedence_shape():
    expr = next(node for node in parse('int x = 1 + 2 * 3;', G)[0].subtrees()
                if node.label() == 'Expr')
    return {'sum': expr[1][0], 'rhs_term_operator': expr[1][1][1][0],
            'lhs_factor': expr[0][0][0]}


def main():
    for name, source in {
        'declaration_plain': 'int x;',
        'declaration_initialized': 'int x = 1;',
        'assignment': 'x = 3;',
        'arithmetic': 'int x = (1 + 2) * (3 - 4) / 5;',
        'if': 'if (x < 2) { x = 3; }',
        'else_if_else': 'if (x < 2) {} else if (x == 2) {} else {}',
        'while': 'while (x > 0) { x = x - 1; }',
        'for_full': 'for (int i = 0; i < 3; i = i + 1) {}',
        'for_assignment_init': 'for (i = 0; i < 3; i = i + 1) {}',
        'for_empty_init_step': 'for (; i != 3; ) {}',
        'nested': 'while (x > 0) { if (x < 2) {} else { for (; x < 3;) {} } }',
        'empty': '',
        'comments': '// only comment\n',
        'comment_between_statements': 'int x; // comment\nx = 1;',
        'keyword_prefix_ids': 'int integer; int iffy; int elsewhere; int format;',
        'no_semantic_check': 'undeclared = 1;',
    }.items():
        check('accept_' + name, True, lambda source=source: accepts(source))

    for operator in ['<', '>', '==', '<=', '>=', '!=']:
        check('relop_' + operator, True, lambda operator=operator: accepts(f'if (x {operator} 1) {{}}'))

    for name, source in {
        'missing_semi': 'int x = 1',
        'missing_paren': 'x = (1 + 2;',
        'if_no_braces': 'if (x < 2) x = 3;',
        'else_no_braces': 'if (x < 2) {} else x = 3;',
        'while_no_braces': 'while (x < 2) x = 3;',
        'for_no_braces': 'for (; x < 2;) x = 3;',
        'condition_no_relation': 'while (x) {}',
        'multiple_variables': 'int x, y;',
        'other_type': 'float x;',
        'chained_assignment': 'a = b = 3;',
        'assignment_in_condition': 'if (a = 3) {}',
        'function': 'int main() {}',
        'return_statement': 'return 1;',
        'do_while': 'do {} while (x < 2);',
        'logical_and': 'if (x < 2 && y > 0) {}',
        'logical_or': 'if (x < 2 || y > 0) {}',
        'block_comment': '/* comment */ int x;',
        'extra_brace': 'int x; }',
        'reserved_minic_id': 'int while;',
        'invalid_character': 'int x = @1;',
    }.items():
        check('reject_' + name, False, lambda source=source: accepts(source))

    check('tree_type', True, lambda: isinstance(parse('int x;', G)[0], Tree))
    check('tree_root', 'Program', lambda: parse('int x;', G)[0].label())
    check('tree_precedence', {'sum': '+', 'rhs_term_operator': '*', 'lhs_factor': '1'}, precedence_shape)
    check('tree_multiplication_inside_term', True, lambda: any(
        node.label() == 'TermP' and node and node[0] == '*'
        for node in parse('int x = 1 + 2 * 3;', G)[0].subtrees()
    ))
    check('tree_right_recursive_subtraction', True, lambda: any(
        node.label() == 'ExprP' and node[0] == '-' and
        isinstance(node[-1], Tree) and node[-1].label() == 'ExprP' and node[-1][0] == '-'
        for node in parse('int x = 10 - 4 - 3;', G)[0].subtrees()
        if len(node) >= 3
    ))

    tokens, errors = tokenize('int\tx = 1;\r\n  x <= 2; // hi\n')
    check('lexer_positions', ['ID', 'x', 2, 3], lambda: list(tokens[5]))
    check('lexer_longest_relop', 'LE', lambda: tokens[6][0])
    check('lexer_eof', ['$', '$', 3, 1], lambda: list(tokens[-1]))
    check('lexer_reset_between_calls', 1, lambda: tokenize('int z;')[0][0][2])
    check('lexical_error_has_column', True, lambda: bool(re.search(
        r'Linea 1, col 9:', parse('int x = @1;', G)[1][0])))
    check('syntax_error_has_position', True, lambda: bool(re.search(
        r'Linea 2, col 1:', parse('int x = 1\nx = 2;', G)[1][0])))
    check('first_error_source_order', 1, lambda: int(re.search(
        r'Linea (\d+)', parse('int = 1;\nint x = @2;', G)[1][0]).group(1)))
    check('panic_recovers_following_statement', True, lambda: 'y' in parse(
        'int x = ; int y = 2;', G)[0].leaves())

    small = custom_grammar('S -> A B\nA -> ID | eps\nB -> NUM | eps\n')
    check('first_oracle', {'ID', 'NUM', EPS}, lambda: small.first['S'])
    check('follow_oracle_a', {'NUM', '$'}, lambda: small.follow['A'])
    check('follow_oracle_b', {'$'}, lambda: small.follow['B'])
    check('nullable_table_oracle', ['A', 'B'], lambda: small.table[('S', '$')])
    check('custom_grammar_same_tokens', True, lambda: not parse('abc 1', small)[1])
    check('custom_grammar_empty_source', True, lambda: not parse('', small)[1])
    check('conflict_first_first', True, lambda: 'M[S,ID]' in grammar_failure(
        'S -> ID | ID NUM\n'))
    check('conflict_first_follow', True, lambda: 'M[A,ID]' in grammar_failure(
        'S -> A ID\nA -> ID | eps\n'))
    check('grammar_unknown_symbol', True, lambda: 'Simbolo desconocido' in grammar_failure('S -> WHAT\n'))
    check('grammar_missing_arrow', True, lambda: 'falta "->"' in grammar_failure('S ID\n'))
    check('grammar_empty_alt', True, lambda: 'alternativa vacia' in grammar_failure('S -> ID |\n'))
    check('grammar_duplicate_lhs', True, lambda: 'repetido' in grammar_failure('S -> ID\nS -> NUM\n'))
    check('grammar_empty_controlled', True, lambda: grammar_failure('') != 'ACCEPTED')
    check('grammar_mixed_eps_rejected', True, lambda: grammar_failure('S -> eps NUM\n') != 'ACCEPTED')
    check('grammar_empty_lhs_rejected', True, lambda: grammar_failure(' -> ID\n') != 'ACCEPTED')

    for keyword in ['return', 'float', 'do', 'switch']:
        check('c_keyword_' + keyword, False, lambda keyword=keyword: accepts(f'int {keyword};'))
    check('c_invalid_octal_rejected', False, lambda: accepts('int x = 08;'))
    check('c_unicode_digit_rejected', False, lambda: accepts('int x = \u0661;'))
    check('number_lexeme_preserved', '010', lambda: tokenize('int x = 010;')[0][3][1])

    check('cli_pretty_valid', {'code': 0, 'traceback': False}, lambda: cli_contract(args=[], source='int x;'))
    check('cli_compact_valid', {'code': 0, 'traceback': False}, lambda: cli_contract(args=['--compacto'], source='int x;'))
    check('cli_invalid', {'code': 1, 'traceback': False}, lambda: cli_contract(args=['--compacto'], source='int = 1;'))
    table_output = cli(['--tabla'])
    check('cli_table', True, lambda: table_output['code'] == 0 and all(
        text in table_output['stdout'] for text in ['FIRST:', 'FOLLOW:', 'TABLA:']))
    check('cli_outside_repo', {'code': 0, 'traceback': False}, lambda: cli_contract(args=['--compacto'], source='int x;', outside=True))
    check('cli_custom_grammar', {'code': 0, 'traceback': False}, lambda: cli_contract(args=['--compacto'], source='abc', grammar='S -> ID\n'))
    check('cli_grammar_error_contract', {'code': 1, 'traceback': False}, lambda: cli_contract(args=['--tabla'], grammar='S -> ID | ID NUM\n'))
    check('cli_missing_file_controlled', {'code': 1, 'traceback': False}, lambda: cli_contract(args=[str(ROOT / 'not-present-audit.c')]))
    check('cli_missing_grammar_controlled', {'code': 1, 'traceback': False}, lambda: cli_contract(args=['--tabla', '-g', str(ROOT / 'not-present-audit.txt')]))
    check('cli_empty_grammar_controlled', {'code': 1, 'traceback': False}, lambda: cli_contract(args=['--tabla'], grammar=''))
    check('large_number_controlled', {'code': 1, 'traceback': False}, lambda: cli_contract(args=['--compacto'], source='int x = ' + '9' * 5000 + ';'))
    check('long_valid_source_compact', {'code': 0, 'traceback': False}, lambda: cli_contract(args=['--compacto'], source='int x;\n' * 1200))
    check('long_valid_source_pretty', {'code': 0, 'traceback': False}, lambda: cli_contract(args=[], source='int x;\n' * 1200))

    # Caracterizaciones de alcance, sin considerarlas requisitos adicionales.
    observations = {
        'for_empty_condition_accepted': accepts('for (;;) {}'),
        'unary_minus_accepted': accepts('int x = -1;'),
        'standalone_block_accepted': accepts('{ int x; }'),
        'grammar_nonproductive_accepted': grammar_failure('S -> S\n') == 'ACCEPTED',
        'lexical_then_syntactic_errors': parse('int = 1;\nint x = @2;', G)[1],
        'long_source_parse_without_render': accepts('int x;\n' * 1200),
        'example_octal_tokens': tokenize('int x = 010;')[0],
        'large_number_cli_exception': cli(['--compacto'], source='int x = ' + '9' * 5000 + ';')['stderr_last_line'],
        'long_source_cli_exception': cli(['--compacto'], source='int x;\n' * 1200)['stderr_last_line'],
    }
    serializable = lambda value: sorted(value) if isinstance(value, set) else str(value)
    payload = {
        'python': platform.python_version(),
        'dependencies': {name: importlib.metadata.version(name) for name in ['ply', 'nltk']},
        'grammar': {'nonterminals': len(G.rules), 'productions': sum(map(len, G.rules.values())), 'table_cells': len(G.table)},
        'total': len(RESULTS), 'passed': sum(row['ok'] for row in RESULTS),
        'failed': sum(not row['ok'] for row in RESULTS),
        'results': RESULTS, 'observations': observations,
    }
    target = Path(__file__).with_name('resultados_sondas.json')
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=serializable) + '\n', encoding='utf-8')
    print(f"{payload['passed']}/{payload['total']} expectativas satisfechas; {payload['failed']} brechas reproducidas.")
    for row in RESULTS:
        if not row['ok']:
            print(row['id'] + ': ' + json.dumps(row['actual'], ensure_ascii=True, default=serializable))
    print('Observaciones: ' + json.dumps(observations, ensure_ascii=True, default=serializable))
    return 0


if __name__ == '__main__':
    sys.exit(main())
