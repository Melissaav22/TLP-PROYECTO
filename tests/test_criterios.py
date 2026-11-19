"""Pruebas de criterios.py con datos INVENTADOS. No mezclar con los logs reales de resultados."""
import json
import unittest
from experimentos import criterios as C


def tok(i, text, pos, dep, head, morph=None, sent=0):
    return dict(i=i, text=text, pos=pos, dep=dep, head=head, morph=morph or {}, sent=sent)


MS = {'Gender': 'Masc', 'Number': 'Sing'}
FS = {'Gender': 'Fem', 'Number': 'Sing'}
FP = {'Gender': 'Fem', 'Number': 'Plur'}
VS = {'Number': 'Sing', 'VerbForm': 'Fin'}
VP = {'Number': 'Plur', 'VerbForm': 'Fin'}


def raw(*toks, n_sents=1):
    return dict(n_sents=n_sents, tokens=list(toks))


class SpacyLogica(unittest.TestCase):
    def test_c0_acepta_todo(self):
        self.assertTrue(C.decidir('spacy', 'C0', raw(tok(0, 'gato', 'NOUN', 'ROOT', 0, MS)))['accepted'])

    def test_c1_verbo(self):
        r = raw(tok(0, 'El', 'DET', 'det', 1, MS), tok(1, 'perro', 'NOUN', 'nsubj', 2, MS),
                tok(2, 'duerme', 'VERB', 'ROOT', 2, VS))
        self.assertTrue(C.decidir('spacy', 'C1', r)['accepted'])

    def test_c1_fragmento_nominal(self):
        r = raw(tok(0, 'La', 'DET', 'det', 1, FS), tok(1, 'niña', 'NOUN', 'ROOT', 1, FS),
                tok(2, 'pequeña', 'ADJ', 'amod', 1, FS))
        res = C.decidir('spacy', 'C1', r)
        self.assertFalse(res['accepted'])
        self.assertEqual(res['motivo'], 'raiz_no_verbal_sin_copula')

    def test_c1_copulativa(self):
        r = raw(tok(0, 'La', 'DET', 'det', 1, FS), tok(1, 'mesa', 'NOUN', 'nsubj', 3, FS),
                tok(2, 'es', 'AUX', 'cop', 3, VS), tok(3, 'roja', 'ADJ', 'ROOT', 3, FS))
        self.assertTrue(C.decidir('spacy', 'C1', r)['accepted'])

    def test_c1_sin_sujeto_se_acepta(self):          # decisión del grupo: el sujeto no se exige
        r = raw(tok(0, 'Corre', 'VERB', 'ROOT', 0, VS), tok(1, 'rápidamente', 'ADV', 'advmod', 0))
        self.assertTrue(C.decidir('spacy', 'C1', r)['accepted'])

    def test_c2_viola_atributo(self):
        r = raw(tok(0, 'La', 'DET', 'det', 1, FS), tok(1, 'mesa', 'NOUN', 'nsubj', 3, FS),
                tok(2, 'es', 'AUX', 'cop', 3, VS), tok(3, 'rojo', 'ADJ', 'ROOT', 3, MS))
        res = C.decidir('spacy', 'C2', r)
        self.assertFalse(res['accepted'])
        self.assertEqual(res['motivo'], 'violacion_concordancia')

    def test_c2_viola_sujeto_copula(self):
        r = raw(tok(0, 'Las', 'DET', 'det', 1, FP), tok(1, 'casas', 'NOUN', 'nsubj', 3, FP),
                tok(2, 'es', 'AUX', 'cop', 3, VS), tok(3, 'nuevas', 'ADJ', 'ROOT', 3, FP))
        self.assertFalse(C.decidir('spacy', 'C2', r)['accepted'])

    def test_c2_viola_sujeto_verbo(self):
        r = raw(tok(0, 'Los', 'DET', 'det', 1, dict(Gender='Masc', Number='Plur')),
                tok(1, 'perros', 'NOUN', 'nsubj', 2, dict(Gender='Masc', Number='Plur')),
                tok(2, 'duerme', 'VERB', 'ROOT', 2, VS))
        self.assertFalse(C.decidir('spacy', 'C2', r)['accepted'])

    def test_c2_sin_violaciones(self):
        r = raw(tok(0, 'Las', 'DET', 'det', 1, FP), tok(1, 'niñas', 'NOUN', 'nsubj', 2, FP),
                tok(2, 'cantan', 'VERB', 'ROOT', 2, VP))
        res = C.decidir('spacy', 'C2', r)
        self.assertTrue(res['accepted'])
        self.assertEqual(res['n_indeterminado'], 0)

    def test_c2_genero_comun_no_es_indeterminado(self):
        r = raw(tok(0, 'La', 'DET', 'det', 1, FS), tok(1, 'estudiante', 'NOUN', 'nsubj', 3, {'Number': 'Sing'}),
                tok(2, 'grande', 'ADJ', 'amod', 1, {'Number': 'Sing'}), tok(3, 'corre', 'VERB', 'ROOT', 3, VS))
        res = C.decidir('spacy', 'C2', r)
        self.assertTrue(res['accepted'])
        self.assertEqual(res['n_indeterminado'], 0)
        self.assertGreater(res['n_genero_comun'], 0)

    def test_c2_cabeza_propn_con_determinante_es_indeterminada(self):
        r = raw(tok(0, 'La', 'DET', 'det', 1, FS), tok(1, 'casa', 'PROPN', 'nsubj', 3, {}),
                tok(2, 'blanco', 'ADJ', 'amod', 1, MS), tok(3, 'está', 'AUX', 'ROOT', 3, VS))
        res = C.decidir('spacy', 'C2', r)
        self.assertTrue(res['accepted'])             # sin evidencia de desajuste
        self.assertGreater(res['n_indeterminado'], 0)  # pero queda marcada

    def test_c2_pronombre_relativo_se_omite(self):
        r = raw(tok(0, 'El', 'DET', 'det', 1, MS), tok(1, 'niño', 'NOUN', 'nsubj', 5, MS),
                tok(2, 'que', 'PRON', 'nsubj', 3, {'PronType': 'Int,Rel'}), tok(3, 'corre', 'VERB', 'acl', 1, VS),
                tok(4, 'es', 'AUX', 'cop', 5, VS), tok(5, 'alto', 'ADJ', 'ROOT', 5, MS))
        res = C.decidir('spacy', 'C2', r)
        self.assertTrue(res['accepted'])
        self.assertEqual(res['n_indeterminado'], 0)

    def test_varias_piezas_se_rechaza_si_alguna_falla(self):
        r = raw(tok(0, 'Corre', 'VERB', 'ROOT', 0, VS, 0), tok(1, 'perro', 'NOUN', 'ROOT', 1, MS, 1), n_sents=2)
        for crit in ('C1', 'C2'):
            res = C.decidir('spacy', crit, r)
            self.assertFalse(res['accepted'])
            self.assertEqual(res['motivo'], 'pieza_2_raiz_no_verbal_sin_copula')
            self.assertTrue(res['multi_sent'])
        self.assertTrue(C.decidir('spacy', 'C0', r)['accepted'])

    def test_varias_piezas_se_acepta_si_todas_cumplen(self):
        r = raw(tok(0, 'Corre', 'VERB', 'ROOT', 0, VS, 0), tok(1, 'Canta', 'VERB', 'ROOT', 1, VS, 1), n_sents=2)
        res = C.decidir('spacy', 'C1', r)
        self.assertTrue(res['accepted'])
        self.assertTrue(res['multi_sent'])

    def test_varias_piezas_c2_viola_en_cualquier_pieza(self):
        r = raw(tok(0, 'Corre', 'VERB', 'ROOT', 0, VS, 0),
                tok(1, 'Los', 'DET', 'det', 2, dict(Gender='Masc', Number='Plur'), 1),
                tok(2, 'perros', 'NOUN', 'nsubj', 3, dict(Gender='Masc', Number='Plur'), 1),
                tok(3, 'duerme', 'VERB', 'ROOT', 3, VS, 1), n_sents=2)
        self.assertTrue(C.decidir('spacy', 'C1', r)['accepted'])
        self.assertFalse(C.decidir('spacy', 'C2', r)['accepted'])


def nl(*pares):
    return C.nltk_raw([p for p, _ in pares], [t for _, t in pares])


class NltkLogica(unittest.TestCase):
    def test_c1_sustantivo_y_verbo(self):
        r = nl(('el', 'da0ms0'), ('niño', 'ncms000'), ('corre', 'vmip3s0'))
        self.assertTrue(C.decidir('nltk_full', 'C1', r)['accepted'])

    def test_c1_sin_verbo(self):
        r = nl(('la', 'da0fs0'), ('niña', 'ncfs000'), ('pequeña', 'aq0fs0'))
        res = C.decidir('nltk_full', 'C1', r)
        self.assertFalse(res['accepted'])
        self.assertEqual(res['motivo'], 'sin_verbo')

    def test_c2_viola_genero_sust_adj(self):
        r = nl(('la', 'da0fs0'), ('casa', 'ncfs000'), ('blanco', 'aq0ms0'), ('está', 'vmip3s0'))
        self.assertFalse(C.decidir('nltk_full', 'C2', r)['accepted'])

    def test_c2_viola_numero_det_sust(self):
        r = nl(('los', 'da0mp0'), ('niño', 'ncms000'), ('corre', 'vmip3s0'))
        self.assertFalse(C.decidir('nltk_full', 'C2', r)['accepted'])

    def test_c2_concuerda(self):
        r = nl(('la', 'da0fs0'), ('casa', 'ncfs000'), ('blanca', 'aq0fs0'), ('está', 'vmip3s0'))
        res = C.decidir('nltk_full', 'C2', r)
        self.assertTrue(res['accepted'])
        self.assertEqual(res['n_indeterminado'], 0)

    def test_c2_genero_comun(self):
        r = nl(('la', 'da0fs0'), ('empresa', 'ncfs000'), ('estatal', 'aq0cs0'), ('crece', 'vmip3s0'))
        res = C.decidir('nltk_full', 'C2', r)
        self.assertTrue(res['accepted'])
        self.assertGreater(res['n_genero_comun'], 0)

    def test_c2_palabra_desconocida_es_indeterminada(self):
        r = nl(('la', 'da0fs0'), ('zzzcasa', 'nc00000'), ('corre', 'vmip3s0'))
        res = C.decidir('nltk_full', 'C2', r)
        self.assertTrue(res['accepted'])
        self.assertGreater(res['n_indeterminado'], 0)

    def test_c2_nombre_propio_se_omite(self):
        r = nl(('pedro', 'np00000'), ('corre', 'vmip3s0'), ('el', 'da0ms0'), ('niño', 'ncms000'))
        self.assertEqual(C.decidir('nltk_full', 'C2', r)['comparaciones'][0]['palabra'], 'el')

    def test_nltk_grueso_c2_no_aplicable(self):
        r = nl(('el', 'DET'), ('niño', 'NOUN'), ('corre', 'VERB'))
        res = C.decidir('nltk', 'C2', r)
        self.assertFalse(res['aplicable'])
        self.assertIsNone(res['accepted'])
        self.assertTrue(C.decidir('nltk', 'C1', r)['accepted'])

    def test_errores_de_uso(self):
        with self.assertRaises(ValueError):
            C.decidir('spacy', 'C9', raw())
        with self.assertRaises(ValueError):
            C.decidir('otra', 'C1', raw())


class EntrenarEtiquetador(unittest.TestCase):
    def test_conserva_etiqueta_completa_y_no_inventa_rasgos(self):
        try:
            from experimentos.nltk_full import entrenar, ETIQUETA_DESCONOCIDA
        except ImportError as e:                      # nltk o .common no disponibles
            self.skipTest(str(e))
        tagger, _ = entrenar([[('El', 'da0ms0'), ('niño', 'ncms000'), ('corre', 'vmip3s0')]])
        etq = dict(tagger.tag(['el', 'niño', 'xyzwq']))
        self.assertEqual(etq['el'], 'da0ms0')
        self.assertEqual(etq['niño'], 'ncms000')
        self.assertEqual(etq['xyzwq'], ETIQUETA_DESCONOCIDA)


class RutaCess(unittest.TestCase):
    def test_encuentra_el_zip_donde_este(self):
        import tempfile
        from pathlib import Path
        try:
            import nltk
            from experimentos.nltk_full import ruta_cess_esp
        except ImportError as e:
            self.skipTest(str(e))
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'corpora').mkdir()
            (Path(d) / 'corpora' / 'cess_esp.zip').write_bytes(b'x')
            anterior = list(nltk.data.path)
            nltk.data.path[:] = [d]
            try:
                self.assertEqual(ruta_cess_esp().name, 'cess_esp.zip')
            finally:
                nltk.data.path[:] = anterior


class SpacyEnVivo(unittest.TestCase):
    """Prueba de humo con el modelo real: el contrato de la salida cruda, no la calidad del análisis."""
    @classmethod
    def setUpClass(cls):
        try:
            import spacy
            cls.nlp = spacy.load('es_core_news_sm')
        except Exception as e:
            raise unittest.SkipTest(f'spaCy o es_core_news_sm no disponible: {e}')

    def test_contrato_y_serializacion(self):
        for texto in ['El perro duerme', 'La mesa es roja', 'Los gatos que miran corren', 'La niña pequeña']:
            r = C.spacy_raw(self.nlp(texto))
            json.dumps(r)
            for crit in ('C0', 'C1', 'C2'):
                res = C.decidir('spacy', crit, r)
                self.assertIsInstance(res['accepted'], bool)

    def test_hash_estable(self):
        self.assertEqual(C.hash_criterios(), C.hash_criterios())
        self.assertEqual(len(C.hash_criterios()), 64)


if __name__ == '__main__':
    unittest.main()
