"""Regresiones de errores confirmados y contratos nuevos del plan."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from minic.grammar import Grammar, GrammarError
from minic.lexer import tokenize
from minic.parser import parse, parse_detailed
from minic.trees import bracketed, write_svg


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = Grammar(ROOT / 'gramatica_minic.txt')

    def test_positions_and_order(self):
        result = parse_detailed('int = 1;\nint x = @2;', self.g)
        self.assertEqual(result.diagnostics[0].line, 1)
        lexical = next(d for d in result.diagnostics if d.stage == 'lexical')
        self.assertEqual((lexical.line, lexical.column), (2, 9))

    def test_decimal_and_keywords(self):
        for source in ['int return;', 'int float;', 'int do;', 'int switch;',
                       'int x=08;', 'int x=010;', 'int x=١;',
                       'int x=' + '9' * 5000 + ';']:
            with self.subTest(source=source[:30]):
                self.assertTrue(parse(source, self.g)[1])
        self.assertEqual(tokenize('10')[0][0][1], '10')

    def test_spanish_isolation(self):
        for source in ['', '// comentario', 'int x=1;', 'x=1;', 'while(x<2){}']:
            self.assertTrue(parse(source, self.g, True)[1])
        self.assertFalse(parse('El a\u0301rbol es alto', self.g, True)[1])

    def test_svo_tenses_and_agreement(self):
        for source in ['El niño lee el libro', 'Los niños leyeron los libros',
                       'La niña compró la flor', 'Las niñas compran las flores',
                       'La casa fue blanca', 'Las casas fueron blancas']:
            self.assertFalse(parse(source, self.g, True)[1], source)
        for source in ['Los niños leyó el libro', 'La niña compraron la flor',
                       'Las casas fue blanca', 'El niño lee las libro']:
            self.assertTrue(parse(source, self.g, True)[1], source)
        self.assertEqual(tokenize('leyó', True)[0][0][0], 'VERB_PAST_3S')
        tree, _ = parse('El niño lee el libro', self.g, True)
        self.assertTrue(any(n.label() == 'Objeto' and n[0].label() == 'SN' for n in tree.subtrees() if n.label() == 'Objeto'))

    def test_structure(self):
        tree, _ = parse('int x=1+2*3;', self.g)
        expr = next(n for n in tree.subtrees() if n.label() == 'Expr')
        self.assertEqual(expr[1][0], '+')
        self.assertEqual(expr[1][1][1][0], '*')
        nested, errors = parse('La profesora sabe que el niño dice que las niñas cantan', self.g, True)
        self.assertFalse(errors)
        self.assertEqual(sum(n.label() == 'Oracion' for n in nested.subtrees()), 3)
        pp, errors = parse('La mujer vive en la casa de la ciudad', self.g, True)
        self.assertFalse(errors)
        self.assertEqual(sum(n.label() == 'PP' for n in pp.subtrees()), 2)
        self.assertFalse(any(d.label() == 'PP' for n in pp.subtrees() if n.label().startswith('SN') for d in list(n.subtrees())[1:]))

    def test_recovery(self):
        tree, errors = parse('int x=; int y=2;', self.g)
        self.assertTrue(errors)
        self.assertIn('y', tree.leaves())

    def test_grammar_validation_and_oracle(self):
        invalid = ['', 'S -> eps NUM', ' -> ID', 'S -> WHAT',
                   'S -> S', 'S -> ID | ID NUM', 'S -> ID |', 'S ID',
                   'S -> ID\nS -> NUM', '$ -> ID']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'g.txt'
            for text in invalid:
                path.write_text(text, encoding='utf-8')
                with self.subTest(grammar=text), self.assertRaises(GrammarError):
                    Grammar(path)
            path.write_text('S -> A B\nA -> ID | eps\nB -> NUM | eps', encoding='utf-8')
            small = Grammar(path)
            self.assertEqual(small.first['S'], {'ID', 'NUM', 'eps'})
            self.assertEqual(small.follow['A'], {'NUM', '$'})
            self.assertEqual(small.table['S', '$'], ['A', 'B'])

    def test_cli_normal_and_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.txt'
            source.write_text('El niño lee el libro', encoding='utf-8')
            svg = Path(directory) / 'tree.svg'
            command = [sys.executable, str(ROOT / 'main.py')]
            good = subprocess.run(command + [str(source), '--es', '--compacto', '--svg', str(svg)], capture_output=True, timeout=20)
            self.assertEqual(good.returncode, 0)
            self.assertIn('<svg', svg.read_text(encoding='utf-8'))
            for args in [[str(source) + '.missing'], ['--tabla', '-g', str(source) + '.missing']]:
                result = subprocess.run(command + args, capture_output=True, timeout=20)
                self.assertEqual(result.returncode, 1)
                self.assertNotIn(b'Traceback', result.stderr)
            for grammar in ['', 'S -> ID | ID NUM']:
                source.write_text(grammar, encoding='utf-8')
                result = subprocess.run(command + ['--tabla', '-g', str(source)], capture_output=True, timeout=20)
                self.assertEqual(result.returncode, 1)
                self.assertNotIn(b'Traceback', result.stderr)

    def test_long_source_cli(self):
        tree, errors = parse('int x;\n' * 1200, self.g)
        self.assertFalse(errors)
        self.assertIn('(Decl int x', bracketed(tree))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'long.c'
            path.write_text('int x;\n' * 1200, encoding='utf-8')
            for flags in [[], ['--compacto']]:
                result = subprocess.run([sys.executable, str(ROOT / 'main.py'), str(path), *flags], capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0)
                self.assertNotIn(b'Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
