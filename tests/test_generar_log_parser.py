"""generar_log_parser no debe duplicar registros de una misma corrida."""
import json
from pathlib import Path
import tempfile
import unittest

from experimentos import generar_log_parser as g


class LogParser(unittest.TestCase):
    def setUp(self):
        self.salida = Path(tempfile.mkdtemp()) / 'parser.jsonl'

    def _correr(self, run):
        return g.main(['--output', str(self.salida), '--run', str(run)])

    def _registros(self):
        return [json.loads(l) for l in self.salida.read_text(encoding='utf-8').splitlines()]

    def test_segunda_corrida_con_el_mismo_numero_se_rechaza_y_no_modifica_el_log(self):
        self._correr(1)
        antes = self.salida.read_bytes()
        with self.assertRaises(SystemExit):
            self._correr(1)
        self.assertEqual(self.salida.read_bytes(), antes)

    def test_otra_corrida_se_anade_sin_repetir_llaves(self):
        self._correr(1)
        self._correr(2)
        llaves = [(r['id'], r['tool'], r['variant'], r['criterion'], r['run']) for r in self._registros()]
        self.assertEqual(len(llaves), len(set(llaves)))
        self.assertEqual({r['run'] for r in self._registros()}, {1, 2})


if __name__ == '__main__':
    unittest.main()
