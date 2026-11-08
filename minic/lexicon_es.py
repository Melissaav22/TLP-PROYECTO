"""Lexico del espanol para la gramatica unificada gramatica_minic.txt.

Cada entrada asocia una palabra (en minusculas) con un token que ya codifica
sus rasgos morfologicos: numero y genero para sustantivos, adjetivos y
determinantes, y numero para los verbos en tercera persona.

El lexer consulta este diccionario antes de emitir un ID; asi la concordancia
se decide en la gramatica, no en un chequeo posterior.
"""

DET_MS = 'DET_MS'
DET_FS = 'DET_FS'
DET_MP = 'DET_MP'
DET_FP = 'DET_FP'

SUST_MS = 'SUST_MS'
SUST_FS = 'SUST_FS'
SUST_MP = 'SUST_MP'
SUST_FP = 'SUST_FP'

ADJ_MS = 'ADJ_MS'
ADJ_FS = 'ADJ_FS'
ADJ_MP = 'ADJ_MP'
ADJ_FP = 'ADJ_FP'

VERB_3S = 'VERB_3S'
VERB_3P = 'VERB_3P'
COP_3S = 'COP_3S'
COP_3P = 'COP_3P'

ADV = 'ADV'
PREP = 'PREP'
QUE = 'QUE'

TOKENS = [
    DET_MS, DET_FS, DET_MP, DET_FP,
    SUST_MS, SUST_FS, SUST_MP, SUST_FP,
    ADJ_MS, ADJ_FS, ADJ_MP, ADJ_FP,
    VERB_3S, VERB_3P, COP_3S, COP_3P,
    ADV, PREP, QUE,
]

LEXICON = {
    # determinantes
    'el': DET_MS, 'la': DET_FS, 'los': DET_MP, 'las': DET_FP,
    'un': DET_MS, 'una': DET_FS, 'unos': DET_MP, 'unas': DET_FP,

    # sustantivos masculinos
    'niño': SUST_MS, 'niños': SUST_MP,
    'hombre': SUST_MS, 'hombres': SUST_MP,
    'perro': SUST_MS, 'perros': SUST_MP,
    'gato': SUST_MS, 'gatos': SUST_MP,
    'libro': SUST_MS, 'libros': SUST_MP,
    'parque': SUST_MS, 'parques': SUST_MP,
    'profesor': SUST_MS, 'profesores': SUST_MP,
    'profesora': SUST_FS, 'profesoras': SUST_FP,
    'hermano': SUST_MS, 'hermanos': SUST_MP,
    'árbol': SUST_MS, 'árboles': SUST_MP,
    'coche': SUST_MS, 'coches': SUST_MP,

    # sustantivos femeninos
    'casa': SUST_FS, 'casas': SUST_FP,
    'mujer': SUST_FS, 'mujeres': SUST_FP,
    'flor': SUST_FS, 'flores': SUST_FP,
    'ciudad': SUST_FS, 'ciudades': SUST_FP,
    'mesa': SUST_FS, 'mesas': SUST_FP,
    'niña': SUST_FS, 'niñas': SUST_FP,
    'escuela': SUST_FS, 'escuelas': SUST_FP,
    'hermana': SUST_FS, 'hermanas': SUST_FP,
    'silla': SUST_FS, 'sillas': SUST_FP,
    'ventana': SUST_FS, 'ventanas': SUST_FP,

    # adjetivos (las cuatro formas)
    'alto': ADJ_MS, 'alta': ADJ_FS, 'altos': ADJ_MP, 'altas': ADJ_FP,
    'bajo': ADJ_MS, 'baja': ADJ_FS, 'bajos': ADJ_MP, 'bajas': ADJ_FP,
    'blanco': ADJ_MS, 'blanca': ADJ_FS, 'blancos': ADJ_MP, 'blancas': ADJ_FP,
    'negro': ADJ_MS, 'negra': ADJ_FS, 'negros': ADJ_MP, 'negras': ADJ_FP,
    'rojo': ADJ_MS, 'roja': ADJ_FS, 'rojos': ADJ_MP, 'rojas': ADJ_FP,
    'nuevo': ADJ_MS, 'nueva': ADJ_FS, 'nuevos': ADJ_MP, 'nuevas': ADJ_FP,
    'viejo': ADJ_MS, 'vieja': ADJ_FS, 'viejos': ADJ_MP, 'viejas': ADJ_FP,
    'pequeño': ADJ_MS, 'pequeña': ADJ_FS, 'pequeños': ADJ_MP, 'pequeñas': ADJ_FP,
    'caro': ADJ_MS, 'cara': ADJ_FS, 'caros': ADJ_MP, 'caras': ADJ_FP,
    'bueno': ADJ_MS, 'buena': ADJ_FS, 'buenos': ADJ_MP, 'buenas': ADJ_FP,
    'malo': ADJ_MS, 'mala': ADJ_FS, 'malos': ADJ_MP, 'malas': ADJ_FP,

    # verbos en tercera persona (singular / plural)
    'corre': VERB_3S, 'corren': VERB_3P,
    'camina': VERB_3S, 'caminan': VERB_3P,
    'compra': VERB_3S, 'compran': VERB_3P,
    'lee': VERB_3S, 'leen': VERB_3P,
    'escribe': VERB_3S, 'escriben': VERB_3P,
    'come': VERB_3S, 'comen': VERB_3P,
    'vive': VERB_3S, 'viven': VERB_3P,
    'estudia': VERB_3S, 'estudian': VERB_3P,
    'trabaja': VERB_3S, 'trabajan': VERB_3P,
    'canta': VERB_3S, 'cantan': VERB_3P,
    'baila': VERB_3S, 'bailan': VERB_3P,
    'sabe': VERB_3S, 'saben': VERB_3P,
    'dice': VERB_3S, 'dicen': VERB_3P,
    'mira': VERB_3S, 'miran': VERB_3P,
    'busca': VERB_3S, 'buscan': VERB_3P,
    'quiere': VERB_3S, 'quieren': VERB_3P,
    'duerme': VERB_3S, 'duermen': VERB_3P,
    'abre': VERB_3S, 'abren': VERB_3P,
    'cierra': VERB_3S, 'cierran': VERB_3P,

    # copulas (ser / estar)
    'es': COP_3S, 'son': COP_3P,
    'está': COP_3S, 'están': COP_3P,

    # adverbios
    'rápidamente': ADV, 'despacio': ADV, 'bien': ADV, 'mal': ADV,
    'ayer': ADV, 'hoy': ADV, 'siempre': ADV, 'aquí': ADV,
    'allí': ADV, 'temprano': ADV, 'tarde': ADV, 'mucho': ADV,
    'poco': ADV, 'nunca': ADV,

    # preposiciones
    'en': PREP, 'de': PREP, 'por': PREP, 'con': PREP, 'para': PREP,
    'sin': PREP, 'sobre': PREP, 'entre': PREP, 'hasta': PREP,
    'desde': PREP,

    # complementizador / relativo
    'que': QUE,
}
