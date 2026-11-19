"""Pruebas del runner de la Fase 2 (sin spaCy ni CESS-ESP: usan una salida cruda de juguete)."""
import json
import tempfile
import unittest
from pathlib import Path

from experimentos import correr_fase2 as r


def _registro(**cambios):
    raw = dict(tokens=[dict(text='Juan', tag='nc0s000'), dict(text='come', tag='vmip3s0')])
    base = dict(id='X-1', tool='nltk_full', criterion='C1', run=1, status='ok', raw_output=raw)
    base.update(cambios)
    from experimentos import criterios
    dec = criterios.decidir(base['tool'], base['criterion'], base['raw_output'])
    base.update(accepted=dec['accepted'], decision=dec)
    return base


def _escribir(ruta, registros):
    ruta.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in registros), encoding='utf-8')


class Verificacion(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / 'registro.jsonl'

    def test_registro_consistente_pasa(self):
        _escribir(self.tmp, [_registro(run=1), _registro(run=2)])
        v = r.verificar(self.tmp)
        self.assertTrue(v['correcta'])
        self.assertEqual(v['registros_verificados'], 2)

    def test_veredicto_alterado_se_detecta(self):
        malo = _registro()
        malo['accepted'] = not malo['accepted']
        _escribir(self.tmp, [malo])
        v = r.verificar(self.tmp)
        self.assertFalse(v['correcta'])
        self.assertEqual(v['veredictos_distintos'], 1)

    def test_salida_cruda_inestable_entre_repeticiones_se_detecta(self):
        otra = dict(tokens=[dict(text='Juan', tag='nc0s000'), dict(text='come', tag='nc0s000')])
        _escribir(self.tmp, [_registro(run=1), _registro(run=2, raw_output=otra)])
        v = r.verificar(self.tmp)
        self.assertEqual(v['pares_con_salida_inestable'], 1)
        self.assertFalse(v['correcta'])

    def test_registro_vacio_no_cuenta_como_correcto(self):
        self.tmp.write_text('', encoding='utf-8')
        self.assertFalse(r.verificar(self.tmp)['correcta'])

    def test_registros_con_error_se_omiten(self):
        err = dict(id='X-2', tool='spacy', criterion='C1', run=1, status='error', error='boom',
                   raw_output=None, accepted=None, decision=None)
        _escribir(self.tmp, [_registro(), err])
        self.assertEqual(r.verificar(self.tmp)['registros_verificados'], 1)


class ComprobacionOficial(unittest.TestCase):
    def test_sin_etiqueta_o_sucio_impide_corrida_oficial(self):
        ok = dict(es_repositorio=True, commit='a', sucio=False, archivos_sucios=[], etiqueta_commit='a')
        self.assertEqual(r.comprobar_oficial(ok), [])
        self.assertEqual(len(r.comprobar_oficial(dict(ok, etiqueta_commit=None))), 1)
        self.assertEqual(len(r.comprobar_oficial(dict(ok, sucio=True, archivos_sucios=[' M x']))), 1)
        self.assertEqual(len(r.comprobar_oficial(dict(es_repositorio=False))), 1)


if __name__ == '__main__':
    unittest.main()
