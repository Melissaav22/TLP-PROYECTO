"""Concordancia, estructura y evaluación de la variante de español."""
import itertools
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experimentos.adaptadores import OwnParser, token_pos
from experimentos.common import digest, read_json
from minic.grammar import Grammar
from minic.parser import parse_detailed


class SpanishExpansion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grammar = Grammar(ROOT / 'gramatica_minic.txt')

    def assert_sentence(self, text, expected):
        result = parse_detailed(text, self.grammar, spanish=True)
        self.assertEqual(result.accepted, expected,
                         f'{text}: {[str(d) for d in result.diagnostics]}')
        return result

    def test_both_start_symbols_are_ll1(self):
        for start in ['Program', 'Oracion']:
            grammar = Grammar(ROOT / 'gramatica_minic.txt', start=start)
            self.assertIn('$', grammar.follow[start])
            self.assertTrue(grammar.table)

    def test_corpus_integrity_and_decisions(self):
        rows = read_json(ROOT / 'datos/ampliacion_es.json')
        self.assertEqual(len(rows), 65)
        self.assertEqual(len({r['id'] for r in rows}), len(rows))
        self.assertEqual(len({r['texto'] for r in rows}), len(rows))
        for row in rows:
            with self.subTest(id=row['id']):
                self.assertEqual(row['grammar_version'], digest(ROOT / 'gramatica_minic.txt'))
                self.assertEqual(len(row['tokens_esperados']), len(row['pos_esperado']))
                self.assertIs(type(row['esperado_cfg']), bool)
                self.assert_sentence(row['texto'], row['esperado_cfg'])

    def test_comparable_reference_preserves_pos(self):
        original = read_json(ROOT / 'datos/fase1.json')
        revised = read_json(ROOT / 'datos/comparacion_fase1_ampliada.json')
        self.assertEqual(len(revised), 13)
        changed = set()
        for before, after in zip(original, revised):
            for key in ['id', 'texto', 'tokens_esperados', 'pos_esperado', 'gramatical_espanol']:
                self.assertEqual(before[key], after[key])
            self.assertEqual(after['esperado_cfg_fase1'], before['esperado_cfg'])
            self.assertEqual(after['grammar_version'], digest(ROOT / 'gramatica_minic.txt'))
            if before['esperado_cfg'] != after['esperado_cfg']:
                changed.add(after['id'])
            self.assert_sentence(after['texto'], after['esperado_cfg'])
        self.assertEqual(changed, {'ES-005', 'ES-041', 'ES-053'})

    def test_coordination_number_and_gender(self):
        members = [('El niño', 'M'), ('La niña', 'F'),
                   ('Los niños', 'M'), ('Las niñas', 'F')]
        for size in [2, 3]:
            for group in itertools.product(members, repeat=size):
                subject = ' y '.join(word for word, _ in group)
                all_female = all(gender == 'F' for _, gender in group)
                attribute = 'altas' if all_female else 'altos'
                wrong = 'altos' if all_female else 'altas'
                with self.subTest(subject=subject):
                    self.assert_sentence(subject + ' comen fruta', True)
                    self.assert_sentence(subject + ' come fruta', False)
                    self.assert_sentence(subject + ' son ' + attribute, True)
                    self.assert_sentence(subject + ' son ' + wrong, False)

    def test_member_agreement_and_incomplete_coordination(self):
        for text in ['La niño y el niño comen fruta',
                     'La niña pequeña y los niño comen fruta',
                     'La niña pequeños y el niño comen fruta',
                     'La niña y comen fruta', 'La niña y y el niño comen fruta',
                     'La niña y el niño y', 'Y la niña come fruta']:
            with self.subTest(text=text):
                self.assert_sentence(text, False)

    def test_mass_and_nominal_objects(self):
        for text in ['La niña come fruta', 'La niña come la fruta',
                     'La niña come fruta nueva', 'La niña compra las frutas',
                     'La fruta es nueva', 'Las frutas son nuevas',
                     'Las niñas compran el libro', 'El niño mira la casa blanca']:
            with self.subTest(text=text):
                self.assert_sentence(text, True)
        for text in ['La niña come fruta nuevo', 'La niña come el fruta',
                     'La niña come las fruta', 'La niña compra frutas',
                     'El niño lee libro', 'Fruta es nueva',
                     'La niña come fruta el libro', 'La niña come la fruta y el libro']:
            with self.subTest(text=text):
                self.assert_sentence(text, False)

    def test_inversion_and_limits(self):
        for text in ['Come la niña pequeña', 'Comen las niñas pequeñas',
                     'Comió el niño', 'Comieron los niños',
                     'Come la niña despacio en la casa']:
            with self.subTest(text=text):
                self.assert_sentence(text, True)
        for text in ['Come las niñas pequeñas', 'Comen la niña pequeña',
                     'Comió los niños', 'Comieron el niño',
                     'Lee la niña el libro', 'Comen la niña y el niño',
                     'Es la niña alta', 'Come']:
            with self.subTest(text=text):
                self.assert_sentence(text, False)

    def test_past_and_subordination(self):
        for text in ['La niña y el niño comieron fruta',
                     'El niño leyó el libro', 'La niña fue alta',
                     'La niña y la mujer estuvieron altas',
                     'La profesora dijo que el niño y la niña comieron fruta',
                     'La profesora sabe que el niño dice que la niña y la mujer comen fruta']:
            with self.subTest(text=text):
                self.assert_sentence(text, True)
        for text in ['La niña y el niño comió fruta', 'Las niñas leyó el libro',
                     'La niña y la mujer estuvo alta', 'La niña cantaba',
                     'El profesor dijo que las niñas comió fruta']:
            with self.subTest(text=text):
                self.assert_sentence(text, False)

    def test_tree_separates_members_and_object(self):
        result = self.assert_sentence('La niña y el niño comen fruta', True)
        objects = [n for n in result.tree.subtrees() if n.label() == 'Objeto']
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].leaves(), ['fruta', 'eps'])
        members = [n for n in result.tree.subtrees() if n.label() in {'SN_MS', 'SN_FS'}]
        self.assertEqual([n.leaves()[:2] for n in members], [['La', 'niña'], ['el', 'niño']])
        self.assertTrue(any(n.label() == 'CoordinadoF' for n in result.tree.subtrees()))
        self.assertTrue(any(n.label() == 'SV_MP' for n in result.tree.subtrees()))
        self.assertNotIn('y', objects[0].leaves())

    def test_new_tokens_and_positions(self):
        text = 'La niña y el niño comieron fruta'
        result = self.assert_sentence(text, True)
        conjunction = next(t for t in result.tokens if t[1] == 'y')
        self.assertEqual(conjunction, ('CONJ_Y', 'y', 1, 9))
        self.assertEqual(next(t[0] for t in result.tokens if t[1] == 'comieron'), 'VERB_PAST_3P')
        self.assertEqual(next(t[0] for t in result.tokens if t[1] == 'fruta'), 'SUST_MASA_FS')
        analysis = OwnParser().analyze(text)
        self.assertEqual(analysis['pos'], ['DET', 'NOUN', 'CCONJ', 'DET', 'NOUN', 'VERB', 'NOUN'])
        self.assertEqual(token_pos('COP_PAST_3P'), 'VERB')
        self.assert_sentence('LA NIÑA Y EL NIÑO COMEN FRUTA', True)
        self.assert_sentence('El a\u0301rbol y la niña son altos', True)

    def test_minic_isolation_and_unsupported_spanish(self):
        source = 'int y=1; int fruta=y; int comieron=fruta;'
        self.assertTrue(parse_detailed(source, self.grammar).accepted)
        self.assert_sentence(source, False)
        for text in ['La niña come fruta.', 'La niña come piedra',
                     'La niña no come fruta', 'Ella come fruta']:
            with self.subTest(text=text):
                self.assert_sentence(text, False)

    def test_cli_and_evaluation_pipeline(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source, svg = folder / 'manual.txt', folder / 'tree.svg'
            source.write_text('La niña y el niño comen fruta', encoding='utf-8')
            command = [sys.executable, str(ROOT / 'main.py'), str(source), '--es', '--compacto', '--svg', str(svg)]
            good = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=20)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertIn('<svg', svg.read_text(encoding='utf-8'))
            source.write_text('La niña y el niño come fruta', encoding='utf-8')
            bad = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=20)
            self.assertEqual(bad.returncode, 1)
            self.assertNotIn(b'Traceback', bad.stderr)
            comparison, summary = folder / 'comparison.json', folder / 'summary.json'
            for args in [
                ['experimentos.comparar_nlp', '--tools', 'parser', '--output', str(comparison)],
                ['experimentos.metricas', '--input', str(comparison), '--output', str(summary)],
            ]:
                done = subprocess.run([sys.executable, '-m', *args], cwd=ROOT, capture_output=True, timeout=30)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            report = next(r for r in read_json(summary)['reports'] if r['level'] == 'todos')
            self.assertEqual(report['cfg']['n'], 65)
            self.assertEqual(report['cfg']['accuracy'], 1.0)
            self.assertEqual(report['execution_errors'], 0)


if __name__ == '__main__':
    unittest.main()
