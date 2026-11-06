"""Contratos de la demostración NLP de la fase 1."""
from pathlib import Path
import tempfile
import unittest

from experimentos.common import ROOT, digest, read_json
from experimentos.metricas import binary_metrics
from minic.grammar import Grammar
from minic.parser import parse_detailed


class PhaseOneExperiments(unittest.TestCase):
    def test_text_hash_is_portable(self):
        with tempfile.TemporaryDirectory() as directory:
            lf = Path(directory) / 'unix.json'
            crlf = Path(directory) / 'windows.json'
            lf.write_bytes(b'{"a":1}\n')
            crlf.write_bytes(b'{"a":1}\r\n')
            self.assertEqual(digest(lf), digest(crlf))

    def test_demo_reference_matches_grammar(self):
        grammar = Grammar(ROOT / 'gramatica_minic.txt')
        rows = read_json(ROOT / 'datos/fase1.json')
        self.assertEqual(len(rows), 13)
        self.assertEqual(len({row['id'] for row in rows}), 13)
        for row in rows:
            with self.subTest(id=row['id']):
                self.assertEqual(row['grammar_version'], digest(ROOT / 'gramatica_minic.txt'))
                self.assertEqual(parse_detailed(row['texto'], grammar, True).accepted, row['esperado_cfg'])

    def test_confusion_matrix(self):
        result = binary_metrics([True, True, False, False], [True, False, True, False])
        self.assertEqual([result[key] for key in ['tp', 'fp', 'tn', 'fn']], [1, 1, 1, 1])
        self.assertEqual(result['precision'], .5)
        self.assertIsNone(binary_metrics([], [])['precision'])
        with self.assertRaises(ValueError):
            binary_metrics([True], [])


if __name__ == '__main__':
    unittest.main()
