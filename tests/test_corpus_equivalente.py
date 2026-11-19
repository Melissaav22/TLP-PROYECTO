"""El corpus congelado (CSV) y la copia convertida que lee el benchmark del LLM (JSON) coinciden.

datos/corpus_fase2.csv         corpus congelado con la etiqueta criterios-v1 (spaCy y NLTK)
datos/corpus_ordenado.json     copia convertida que usan llm.py, resumir_llm.py y validar_corpus.py

La conversión solo cambia la forma de escribir los valores:
  nivel            1 / 2 / 3            <->  simple / intermedio / complejo
  en_vocabulario   si / no              <->  True / False
  esperado_*       aceptada / rechazada <->  True / False
La columna «nota» es texto libre y no entra en la comparación (el benchmark no la usa).
Solo usa la biblioteca estándar.
"""
import csv
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'datos/corpus_fase2.csv'
JSON = ROOT / 'datos/corpus_ordenado.json'

NIVEL = {'1': 'simple', '2': 'intermedio', '3': 'complejo'}
BOOL_ETIQUETA = {'aceptada': True, 'rechazada': False}
BOOL_SI_NO = {'si': True, 'no': False}
# columna del CSV -> (columna del JSON, función que convierte el valor del CSV al del JSON)
CAMPOS = {
    'texto': ('texto', lambda v: v),
    'nivel': ('nivel', NIVEL.get),
    'esperado_espanol': ('gramatical_espanol', BOOL_ETIQUETA.get),
    'esperado_gramatica': ('esperado_cfg', BOOL_ETIQUETA.get),
    'en_vocabulario': ('en_vocabulario', BOOL_SI_NO.get),
    'categoria_error': ('categoria_error', lambda v: v),
    'motivo_rechazo_esperado': ('motivo_rechazo_esperado', lambda v: v),
    'par_minimo_de': ('par_minimo_de', lambda v: v),
    'estructura_esperada': ('estructura_esperada', lambda v: v),
}


def leer_csv(ruta=CSV):
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def leer_json(ruta=JSON):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


def diferencias(filas_csv, filas_json):
    """Lista de textos que describen cada diferencia (vacía si el corpus es equivalente)."""
    problemas = []
    ids_csv = [r['id'] for r in filas_csv]
    ids_json = [r['id'] for r in filas_json]
    if ids_csv != ids_json:
        problemas.append(f'los ids o su orden difieren ({len(ids_csv)} vs {len(ids_json)} filas)')
        return problemas
    for a, b in zip(filas_csv, filas_json):
        for col_csv, (col_json, convertir) in CAMPOS.items():
            esperado = convertir(a[col_csv])
            real = b.get(col_json)
            if real is None:
                real = ''
            if esperado != real:
                problemas.append(f"{a['id']} {col_csv}: csv={a[col_csv]!r} json={b.get(col_json)!r}")
    return problemas


class CorpusEquivalente(unittest.TestCase):
    def test_csv_y_json_describen_el_mismo_corpus(self):
        self.assertEqual(diferencias(leer_csv(), leer_json()), [])

    def test_el_csv_congelado_no_tiene_bom_ni_cr(self):
        datos = CSV.read_bytes()
        self.assertFalse(datos.startswith(b'\xef\xbb\xbf'), 'el CSV congelado no debe llevar BOM')
        self.assertNotIn(b'\r', datos, 'el CSV congelado debe usar saltos LF')

    def test_detecta_un_texto_cambiado(self):
        filas = leer_json()
        filas[3] = dict(filas[3], texto=filas[3]['texto'] + 'X')
        self.assertTrue(any('texto' in p for p in diferencias(leer_csv(), filas)))

    def test_detecta_una_etiqueta_cambiada(self):
        filas = leer_json()
        filas[5] = dict(filas[5], gramatical_espanol=not filas[5]['gramatical_espanol'])
        self.assertTrue(any('esperado_espanol' in p for p in diferencias(leer_csv(), filas)))

    def test_detecta_una_fila_faltante(self):
        self.assertEqual(len(diferencias(leer_csv(), leer_json()[:-1])), 1)


if __name__ == '__main__':
    unittest.main()
