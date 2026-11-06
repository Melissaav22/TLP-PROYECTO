"""Construye la anotación inicial versionada, previa a las predicciones."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimentos.common import digest, write_json
CASES = [
    ('El niño corre', True, True, 'sujeto_verbo'),
    ('Los niños corren', True, True, 'numero_plural'),
    ('La niña canta', True, True, 'genero_femenino'),
    ('Las niñas cantan', True, True, 'numero_plural'),
    ('El niño lee el libro', True, True, 'SVO'),
    ('Los niños leen los libros', True, True, 'SVO_plural'),
    ('La mujer compró la flor', True, True, 'SVO_pasado'),
    ('Las mujeres compraron las flores', True, True, 'SVO_pasado_plural'),
    ('El perro corrió', True, True, 'pasado'),
    ('Los gatos durmieron', True, True, 'pasado_plural'),
    ('La casa es blanca', True, True, 'atributo'),
    ('Las casas fueron nuevas', True, True, 'atributo_pasado'),
    ('El niños corre', False, False, 'numero_determinante'),
    ('La niño corre', False, False, 'genero_determinante'),
    ('Los niños corre', False, False, 'numero_verbo'),
    ('La niña cantaron', False, False, 'numero_verbo_pasado'),
    ('El niño lee las libro', False, False, 'numero_objeto'),
    ('La casa es blancos', False, False, 'concordancia_atributo'),
    ('La niña es alto', False, False, 'genero_atributo'),
    ('Los perro corrieron', False, False, 'numero_sustantivo'),
    ('El niño alto corre rápidamente en el parque', True, True, 'adjetivo_adverbio_PP'),
    ('La niña pequeña cantó bien', True, True, 'adjetivo_pasado_adverbio'),
    ('Los niños altos leyeron los libros nuevos', True, True, 'SVO_adjetivos'),
    ('Las niñas pequeñas compraron las flores rojas', True, True, 'SVO_adjetivos_plural'),
    ('La mujer vive en la casa de la ciudad', True, True, 'PP_sucesivas'),
    ('El profesor escribió el libro en la escuela', True, True, 'SVO_pasado_PP'),
    ('Los profesores estudiaron temprano en el parque', True, True, 'adverbio_PP'),
    ('La casa blanca estuvo en la ciudad', True, True, 'copula_pasado_PP'),
    ('Las casas pequeñas son nuevas hoy', True, True, 'atributo_adverbio'),
    ('El hombre caminó despacio por el parque', True, True, 'pasado_adverbio_PP'),
    ('La niña pequeña leyó el libro viejo ayer', True, True, 'SVO_pasado_modificadores'),
    ('Las mujeres trabajan despacio en la escuela', True, True, 'adverbio_PP_plural'),
    ('El niño alta corre', False, False, 'genero_adjetivo'),
    ('La niña pequeños cantó', False, False, 'numero_adjetivo'),
    ('Los profesores escribió el libro', False, False, 'numero_pasado'),
    ('Las casas blancas fue nuevas', False, False, 'numero_copula_pasado'),
    ('El niño corre en la parques', False, False, 'concordancia_PP'),
    ('La mujer compró los flores rojas', False, False, 'genero_objeto'),
    ('Los niños leyeron la libro', False, False, 'genero_objeto'),
    ('Las niñas cantaron en el parque blanco', True, True, 'adjetivo_en_PP'),
    ('La profesora sabe que el niño lee el libro', True, True, 'subordinada_SVO'),
    ('Los profesores dijeron que las niñas compraron las flores', True, True, 'subordinada_pasado'),
    ('El niño dice que la mujer sabe que los gatos duermen', True, True, 'subordinada_doble'),
    ('Las mujeres saben que las casas son blancas', True, True, 'subordinada_atributo'),
    ('La profesora supo que el niño dijo que las niñas cantaron', True, True, 'subordinada_doble_pasado'),
    ('Los niños dicen que la casa estuvo en la ciudad', True, True, 'subordinada_PP'),
    ('La niña alta dijo que los perros corrieron rápidamente en el parque', True, True, 'subordinada_modificadores'),
    ('Las profesoras saben que el niño leyó el libro nuevo', True, True, 'subordinada_objeto_adjetivo'),
    ('El profesor sabe que los niños lee el libro', False, False, 'concordancia_subordinada'),
    ('Las mujeres dijeron que la casa fueron blancas', False, False, 'concordancia_copula_subordinada'),
    ('El niño dice la mujer corre', False, False, 'falta_que'),
    ('La profesora sabe que los gatos duerme', False, False, 'concordancia_distante'),
    ('El niño y la niña corren', False, True, 'coordinacion_fuera_del_subconjunto'),
    ('Él lee el libro', False, True, 'pronombre_fuera_del_vocabulario'),
    ('El niño que corre lee el libro', False, True, 'relativa_fuera_de_gramatica'),
    ('El astronauta lee el libro', False, True, 'sustantivo_fuera_del_vocabulario'),
    ('El niño leyó el libro.', False, True, 'puntuacion_fuera_de_gramatica'),
    ('La niña cantaba', False, True, 'imperfecto_fuera_del_vocabulario'),
    ('El niño lee el libro que compró la mujer', False, True, 'relativa_objeto'),
    ('El niño lee el libro y la niña canta', False, True, 'coordinacion_oraciones'),
]

# Oro léxico explícito, independiente de las predicciones de los adaptadores.
WORD_GROUPS = {
    'DET': 'el la los las un una unos unas',
    'NOUN': 'niño niños niña niñas mujer mujeres hombre hombres casa casas perro perros gato gatos libro libros flor flores profesor profesores profesora profesoras parque parques ciudad escuela astronauta',
    'ADJ': 'alto alta altos altas blanco blanca blancos blancas nuevo nueva nuevos nuevas pequeño pequeña pequeños pequeñas rojo roja rojos rojas viejo vieja viejos viejas',
    'VERB': 'corre corren canta cantan lee leen compró compraron corrió durmieron es son fue fueron cantaron leyeron cantó vive escribió estudiaron estuvo caminó leyó trabajan sabe dijeron dice duermen supo dijo dicen corrieron saben duerme cantaba compran',
    'ADV': 'rápidamente bien temprano hoy despacio ayer',
    'ADP': 'en de por',
    'SCONJ': 'que',
    'CCONJ': 'y',
    'PRON': 'él',
    'PUNCT': '.',
}
GOLD = {word: tag for tag, words in WORD_GROUPS.items() for word in words.split()}


def entry(index, text, expected, grammatical, phenomenon, grammar_hash):
    words = re.findall(r'[^\W\d_]+|[^\w\s]', text, re.UNICODE)
    tags = [GOLD[word.lower()] for word in words]
    return dict(id=f'ES-{index:03d}', texto=text,
                nivel=['simple', 'intermedio', 'complejo'][(index - 1) // 20],
                fenomenos=[phenomenon], esperado_cfg=expected,
                gramatical_espanol=grammatical, tokens_esperados=words,
                pos_esperado=tags, grammar_version=grammar_hash,
                revision_humana='pendiente_del_grupo')


def main():
    grammar_hash = digest(ROOT / 'gramatica_minic.txt')
    corpus = [entry(i, *case, grammar_hash) for i, case in enumerate(CASES, 1)]
    write_json(ROOT / 'datos/corpus_es.json', corpus)
    selected = [1, 5, 13, 14, 15, 21, 25, 33, 41, 49, 53, 56, 57]
    write_json(ROOT / 'datos/fase1.json', [row for row in corpus if int(row['id'][3:]) in selected])
    examples = [
        dict(id='DEMO-01', texto='El hombre lee el libro', esperado_cfg=True),
        dict(id='DEMO-02', texto='Las mujeres canta', esperado_cfg=False),
        dict(id='DEMO-03', texto='La niña dijo que el gato duerme', esperado_cfg=True),
    ]
    write_json(ROOT / 'datos/ejemplos_few_shot.json', examples)
    print('Corpus inicial guardado: 60 frases, 20 por nivel; etiquetas pendientes de revisión del grupo.')


if __name__ == '__main__':
    main()
