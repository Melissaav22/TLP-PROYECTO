"""Criterios de aceptación/rechazo para spaCy y NLTK (versión criterios-v1).

spaCy y NLTK no aceptan ni rechazan oraciones por sí solos. Este módulo convierte la
SALIDA CRUDA de cada herramienta en un veredicto, con una sola función compartida:

    decidir(herramienta, criterio, salida_cruda) -> dict

Herramientas: 'spacy', 'nltk' (etiquetas gruesas de la Fase 1: solo C0 y C1) y
'nltk_full' (etiquetas EAGLES completas de CESS-ESP).
Criterios: 'C0' (acepta todo), 'C1' (estructura mínima), 'C2' (C1 + concordancia).

El veredicto mide si la herramienta muestra la evidencia mínima de oración bien formada;
si ese veredicto es correcto lo decide la etiqueta gold del corpus, no este módulo.
"""
import hashlib
from pathlib import Path

CRITERIOS_VERSION = 'criterios-v1'
CLASES_CON_RASGOS = {'DET', 'NOUN', 'ADJ', 'VERB', 'AUX'}


def hash_criterios():
    """SHA-256 de este archivo, para guardarlo en cada registro de resultados."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# ---------------------------------------------------------------- salida cruda
def spacy_raw(doc):
    """Salida cruda de spaCy (JSON-serializable) a partir de un Doc."""
    sent_of = {}
    for k, sent in enumerate(doc.sents):
        for t in sent:
            sent_of[t.i] = k
    return dict(n_sents=max(sent_of.values()) + 1 if sent_of else 0,
                tokens=[dict(i=t.i, text=t.text, pos=t.pos_, dep=t.dep_, head=t.head.i,
                             morph=t.morph.to_dict(), sent=sent_of.get(t.i, 0)) for t in doc])


def nltk_raw(words, tags):
    """Salida cruda de NLTK: palabras y etiquetas tal como las devuelve el etiquetador."""
    return dict(tokens=[dict(text=w, tag=t) for w, t in zip(words, tags)])


# ----------------------------------------------------------------- utilidades
def _resultado(accepted, motivo, comparaciones=None, n_indeterminado=0, n_genero_comun=0,
               multi_sent=False, aplicable=True):
    return dict(version=CRITERIOS_VERSION, aplicable=aplicable, accepted=accepted, motivo=motivo,
                n_indeterminado=n_indeterminado, n_genero_comun=n_genero_comun,
                multi_sent=multi_sent, comparaciones=comparaciones or [])


# ----------------------------------------------------------------------- spaCy
def _spacy_c1(toks):
    if not toks:
        return False, 'sin_tokens'
    raices = [t for t in toks if t['dep'] == 'ROOT']
    if not raices:
        return False, 'sin_raiz'
    raiz = raices[0]
    if raiz['pos'] in ('VERB', 'AUX'):
        return True, 'raiz_verbal'
    if any(t['head'] == raiz['i'] and t['dep'] == 'cop' for t in toks):
        return True, 'raiz_con_copula'
    return False, 'raiz_no_verbal_sin_copula'


def _comparar_spacy(dep, cab, rasgos, relacion):
    """Compara los rasgos de dos palabras. Devuelve (lista de registros)."""
    if dep['pos'] not in CLASES_CON_RASGOS:
        return []                                   # silencio legítimo (nombres, pronombres...)
    cab_como_sust = cab['pos'] == 'PROPN' and dep['pos'] in ('DET', 'ADJ')
    if cab['pos'] not in CLASES_CON_RASGOS and not cab_como_sust:
        return []                                   # silencio legítimo
    out = []
    for r in rasgos:
        a, b = dep['morph'].get(r), cab['morph'].get(r)
        if a and b:
            res = 'concuerda' if a == b else 'viola'
        else:
            faltante = dep if not a else cab
            if r == 'Gender' and faltante['pos'] in ('NOUN', 'ADJ'):
                res = 'genero_comun'               # spaCy omite Gender en palabras de género común
            else:
                res = 'indeterminado'
        out.append(dict(relacion=relacion, palabra=dep['text'], cabeza=cab['text'], rasgo=r,
                        valores=[a, b], resultado=res))
    return out


def _spacy_c2(toks):
    por_i = {t['i']: t for t in toks}
    comps = []
    for t in toks:
        h = por_i.get(t['head'])
        if h is None or h is t:
            continue
        if t['dep'] in ('det', 'amod'):
            comps += _comparar_spacy(t, h, ('Gender', 'Number'), t['dep'] + '->' + 'sustantivo')
        elif t['dep'] in ('nsubj', 'nsubj:pass'):
            if h['pos'] == 'ADJ':
                comps += _comparar_spacy(t, h, ('Gender', 'Number'), 'sujeto->atributo')
            elif h['pos'] in ('VERB', 'AUX', 'NOUN'):
                comps += _comparar_spacy(t, h, ('Number',), 'sujeto->verbo')
            for c in toks:
                if c['head'] == h['i'] and c['dep'] == 'cop':
                    comps += _comparar_spacy(t, c, ('Number',), 'sujeto->copula')
    return comps


def _piezas(raw):
    """Agrupa los tokens por oración detectada por spaCy, en orden."""
    grupos = {}
    for t in raw['tokens']:
        grupos.setdefault(t.get('sent', 0), []).append(t)
    return [grupos[k] for k in sorted(grupos)]


def _decidir_spacy(criterio, raw):
    piezas = _piezas(raw)
    multi = len(piezas) > 1
    if criterio == 'C0':
        return _resultado(True, 'acepta_todo', multi_sent=multi)
    if not piezas:
        return _resultado(False, 'sin_tokens', multi_sent=False)
    # Si spaCy parte el elemento en varias oraciones, TODAS las piezas deben cumplir C1.
    for k, toks in enumerate(piezas, 1):
        ok, motivo = _spacy_c1(toks)
        if not ok:
            return _resultado(False, f'pieza_{k}_{motivo}' if multi else motivo, multi_sent=multi)
    motivo_c1 = 'todas_las_piezas_cumplen_c1' if multi else _spacy_c1(piezas[0])[1]
    if criterio == 'C1':
        return _resultado(True, motivo_c1, multi_sent=multi)
    comps = [c for toks in piezas for c in _spacy_c2(toks)]
    viol = [c for c in comps if c['resultado'] == 'viola']
    return _resultado(not viol, 'violacion_concordancia' if viol else 'sin_violaciones', comps,
                      sum(c['resultado'] == 'indeterminado' for c in comps),
                      sum(c['resultado'] == 'genero_comun' for c in comps), multi)


# ----------------------------------------------------------------------- NLTK
# Posiciones (base 0) de género y número en etiquetas EAGLES de CESS-ESP, verificadas con
# ejemplos reales: da0ms0, ncfs000, aq0fs0. 'c' (género común) y 'n' (invariable) concuerdan
# con cualquier valor; '0' o ausencia = sin rasgo.
_EAGLES = {'n': dict(genero=2, numero=3), 'd': dict(genero=3, numero=4), 'a': dict(genero=3, numero=4)}


def _valor_eagles(tag, clase, rasgo):
    i = _EAGLES[clase][rasgo]
    return tag[i].lower() if len(tag) > i else '0'


def _comparar_eagles(w1, t1, c1, w2, t2, c2, relacion):
    out = []
    for rasgo, comodin in (('genero', 'c'), ('numero', 'n')):
        a, b = _valor_eagles(t1, c1, rasgo), _valor_eagles(t2, c2, rasgo)
        if a == '0' or b == '0':
            res = 'indeterminado'
        elif a == comodin or b == comodin:
            res = 'genero_comun' if rasgo == 'genero' else 'concuerda'
        else:
            res = 'concuerda' if a == b else 'viola'
        out.append(dict(relacion=relacion, palabra=w1, cabeza=w2, rasgo=rasgo, valores=[a, b], resultado=res))
    return out


def _decidir_nltk(herramienta, criterio, raw):
    toks = raw['tokens']
    if criterio == 'C0':
        return _resultado(True, 'acepta_todo')
    tags = [t['tag'] for t in toks]
    if herramienta == 'nltk':                        # etiquetas gruesas de la Fase 1
        tiene_n, tiene_v = 'NOUN' in tags, 'VERB' in tags
    else:
        tiene_n = any(t[:1].lower() == 'n' for t in tags)
        tiene_v = any(t[:1].lower() == 'v' for t in tags)
    if criterio == 'C1' or not (tiene_n and tiene_v):
        motivo = 'sustantivo_y_verbo' if (tiene_n and tiene_v) else (
            'sin_verbo' if tiene_n else 'sin_sustantivo' if tiene_v else 'sin_sustantivo_ni_verbo')
        return _resultado(tiene_n and tiene_v, motivo)
    if herramienta == 'nltk':
        return _resultado(None, 'c2_no_aplicable_sin_rasgos', aplicable=False)
    comps = []
    for a, b in zip(toks, toks[1:]):
        ta, tb = a['tag'], b['tag']
        ca, cb = ta[:1].lower(), tb[:1].lower()
        if ta[:2].lower() == 'np' or tb[:2].lower() == 'np':
            continue                                 # nombres propios: silencio legítimo
        if ca == 'd' and cb == 'n':
            comps += _comparar_eagles(a['text'], ta, 'd', b['text'], tb, 'n', 'determinante->sustantivo')
        elif ca == 'n' and cb == 'a':
            comps += _comparar_eagles(b['text'], tb, 'a', a['text'], ta, 'n', 'adjetivo->sustantivo')
    viol = [c for c in comps if c['resultado'] == 'viola']
    return _resultado(not viol, 'violacion_concordancia' if viol else 'sin_violaciones', comps,
                      sum(c['resultado'] == 'indeterminado' for c in comps),
                      sum(c['resultado'] == 'genero_comun' for c in comps))


# --------------------------------------------------------------------- entrada
def decidir(herramienta, criterio, raw):
    """Veredicto de una herramienta con un criterio, a partir de su salida cruda."""
    if criterio not in ('C0', 'C1', 'C2'):
        raise ValueError(f'criterio desconocido: {criterio}')
    if herramienta == 'spacy':
        return _decidir_spacy(criterio, raw)
    if herramienta in ('nltk', 'nltk_full'):
        return _decidir_nltk(herramienta, criterio, raw)
    raise ValueError(f'herramienta desconocida: {herramienta}')
