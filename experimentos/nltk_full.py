"""Segundo etiquetador de NLTK, con etiquetas EAGLES completas (variante 'nltk_full').

El etiquetador de la Fase 1 (adaptadores.NltkSpanish) reduce las etiquetas a categorías
gruesas y NO se modifica. Este conserva género y número para poder medir concordancia.
Las palabras desconocidas reciben 'nc00000' (sustantivo sin género ni número), no un rasgo
inventado: el criterio C2 las cuenta como indeterminadas.
"""
import re
import unicodedata
from pathlib import Path
from .common import ROOT, digest

ETIQUETA_DESCONOCIDA = 'nc00000'


def entrenar(oraciones):
    """oraciones: lista de listas (palabra, etiqueta EAGLES). Devuelve el etiquetador."""
    import nltk
    datos = [[(unicodedata.normalize('NFC', p).lower(), t) for p, t in o] for o in oraciones]
    respaldo = nltk.DefaultTagger(ETIQUETA_DESCONOCIDA)
    sufijos = nltk.AffixTagger(datos, affix_length=-3, backoff=respaldo)
    return nltk.UnigramTagger(datos, backoff=sufijos), datos


def ruta_cess_esp():
    """Ruta real del zip de CESS-ESP que NLTK está usando (puede no estar en .models), o None.
    Se recorre nltk.data.path en orden, el mismo en que NLTK busca los recursos."""
    import nltk
    for base in nltk.data.path:
        ruta = Path(base) / 'corpora' / 'cess_esp.zip'
        if ruta.is_file():
            return ruta
    return None


class NltkSpanishFull:
    def __init__(self):
        import nltk
        from nltk.corpus import cess_esp
        nltk.data.path.insert(0, str(ROOT / '.models/nltk'))
        self.tagger, datos = entrenar(cess_esp.tagged_sents())
        zip_usado = ruta_cess_esp()
        self.info = dict(tool='nltk_full', version=nltk.__version__,
                         model='CESS-ESP unigram + sufijos -3 + nc00000 (etiquetas EAGLES completas)',
                         training_sentences=len(datos), training_tokens=sum(map(len, datos)),
                         training_source=str(zip_usado) if zip_usado else None,
                         training_sha256=digest(zip_usado) if zip_usado else None)

    def analyze(self, text):
        palabras = re.findall(r'[^\W\d_]+|[^\w\s]', unicodedata.normalize('NFC', text), re.UNICODE)
        etiquetadas = self.tagger.tag([p.lower() for p in palabras])
        return dict(tokens=palabras, tags=[t for _, t in etiquetadas], accepted=None)
