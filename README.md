# Proyecto TLP02 2026

Parser LL(1) para fragmentos MiniC y español controlado, árboles SVG y experimentos reproducibles con NLTK y spaCy.

## Estado

Rama `feat/fase-uno`, basada en `ExtensionEspañol`. Conserva los 39 fixtures originales e incorpora una demo de 13 frases con parser, NLTK y spaCy. Las pruebas, trazas, métricas e informe de esta rama corresponden a la gramática de fase 1.

La rama `feat/fase-dos` deriva de esta rama y añade SVO, pasado, corpus de 60 frases, evaluación completa e integración LLM.

## Instalación del parser

Python 3.10 o superior. Se verificaron Python 3.10.22 y 3.12.15. Desde la raíz, en PowerShell:

```powershell
uv venv --python 3.10 .venv
uv pip sync --python .venv/Scripts/python.exe --require-hashes requirements-core.lock
.\.venv\Scripts\python.exe tests/run_tests.py
.\.venv\Scripts\python.exe tests/run_tests.py --es
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

En Linux/macOS, sustituye `.venv\Scripts\python.exe` por `.venv/bin/python`.

## Uso

```powershell
.\.venv\Scripts\python.exe main.py tests/validos/v01_declaraciones.c --compacto
.\.venv\Scripts\python.exe main.py tests/es/validos/v07_subordinada.txt --es
.\.venv\Scripts\python.exe main.py tests/es/validos/v07_subordinada.txt --es --svg resultados/arbol.svg
.\.venv\Scripts\python.exe main.py --tabla
```

La salida es 0 si termina correctamente y 1 ante errores de fuente, lectura, gramática o escritura. argparse devuelve 2 para argumentos inválidos. `--compacto` usa serialización iterativa en una línea. La salida habitual presenta un árbol de consola para entradas pequeñas y corchetes para árboles profundos. El SVG admite hasta 2.000 nodos, con error controlado al superar ese límite.

## Estructura del proyecto

```text
main.py                       línea de comandos: analiza un archivo y muestra el árbol
gramatica_minic.txt           gramática LL(1) de MiniC y del español, en un solo archivo
minic/
  lexer.py                    análisis léxico (PLY)
  lexicon_es.py               diccionario del español con género y número
  grammar.py                  lee la gramática y calcula FIRST, FOLLOW y la tabla LL(1)
  parser.py                   parser predictivo con pila, árbol y modo pánico
  trees.py                    árbol en corchetes, en consola y como SVG
  diagnostics.py              errores con línea y columna
tests/
  validos/, invalidos/        casos de MiniC (.c)
  es/validos/, es/invalidos/  casos del español (.txt)
  run_tests.py                corre los casos y muestra una tabla
  test_contratos.py           pruebas unitarias del parser
  test_experimentos.py        pruebas unitarias de la demo
experimentos/                 comparación del parser con NLTK y spaCy
datos/                        oraciones de la demo y datos de los modelos
resultados/                   salidas guardadas de la demo y de las pruebas
scripts/preparar_modelos.py   descarga el corpus de NLTK
```

## Casos de prueba

Hay 39 casos de aceptación y rechazo, y 11 pruebas unitarias.

- `tests/validos/` tiene 9 programas MiniC que el parser debe aceptar, y `tests/invalidos/` tiene 11 que debe rechazar. En los inválidos, la primera línea indica dónde se espera el primer error: `// ESPERA: error en linea N`.
- `tests/es/validos/` tiene 11 oraciones que debe aceptar, y `tests/es/invalidos/` tiene 8 que debe rechazar (concordancia de género y número, falta de `que`, orden del adjetivo). La línea `// ESPERA` funciona igual.
- `tests/run_tests.py` imprime una fila por caso con lo esperado, lo obtenido y `OK`. Sin argumentos corre MiniC, y con `--es` corre el español.
- `test_contratos.py` y `test_experimentos.py` verifican posiciones de errores, números y palabras reservadas, que el español no acepte código MiniC, los árboles y la demo.

## Subconjuntos y contratos

MiniC contiene declaraciones `int`, asignaciones, aritmética, comparaciones, `if/else if/else`, `while` y `for`, con cuerpos entre llaves. Los archivos representan fragmentos sintácticos. El análisis semántico de tipos, declaraciones previas y ejecución queda fuera del alcance.

Se aceptan decimales ASCII `0` o `[1-9][0-9]*`, de hasta 4.096 dígitos, conservando el lexema. Se excluyen octales, ceros iniciales, números Unicode, funciones, operadores lógicos, comentarios de bloque y asignaciones encadenadas. Se impide usar palabras clave C como identificadores.

El español se valida desde `Oracion`. Requiere determinante, sujeto nominal y verbo de tercera persona. Incluye presente, adjetivos concordados, adverbios, PP y subordinadas con `que`. El objeto directo nominal y el pasado se incorporan en fase 2.

Las PP sucesivas modifican al sintagma verbal. El fixture histórico `v06_pp_anidada.txt` contiene dos PP hermanas. `experimentos.ambiguedad` contrasta esa política con dos adjunciones de una CFG auxiliar. Los verbos plenos comparten las posibilidades de complemento. La valencia semántica es una limitación declarada.

El lexicón está en `minic/lexicon_es.py` y admite consulta normalizada NFC. Se excluyen coordinación, pronombres, relativas, imperfecto y punto final. La pertenencia al subconjunto se etiqueta separada de la corrección general del español.

`parse(source, grammar, spanish=False)` conserva `(nltk.Tree, list[str])`. `parse_detailed` añade tokens, diagnósticos estructurados y producciones. `Grammar(path, start=...)` y `for_start` calculan FOLLOW y tabla para la raíz elegida.

## Entorno experimental

Se fija Python 3.12 y las dependencias con hashes:

```powershell
uv venv --python 3.12 .venv-nlp
uv pip sync --python .venv-nlp/Scripts/python.exe --require-hashes requirements-experimentos.lock
.\.venv-nlp\Scripts\python.exe scripts/preparar_modelos.py
```

El lock incluye spaCy 3.8.18, es_core_news_sm 3.8.0, NLTK 3.10.4 y Matplotlib 3.11.2. NLTK entrena un etiquetador unigram con CESS-ESP, respaldo por sufijos y NOUN. Las frases de demostración se mantienen separadas de ese entrenamiento.

## Reproducción

```powershell
.\.venv-nlp\Scripts\python.exe -m experimentos.registro_fallos
.\.venv-nlp\Scripts\python.exe -m experimentos.demo_fase1
.\.venv-nlp\Scripts\python.exe -m experimentos.ambiguedad
.\.venv-nlp\Scripts\python.exe -m experimentos.metricas
```

`datos/fase1.json` guarda 13 frases con etiquetas específicas de esta gramática. Dos casos SVO se rechazan aquí por estar fuera del subconjunto; en fase 2 se amplía la gramática y se actualiza su referencia. Los resultados conservan hashes normalizados de texto UTF-8 con saltos LF, además del commit base.

## Tareas y métricas

La pertenencia CFG se evalúa para el parser. Los tres analizadores se comparan en POS grueso, unificando AUX con VERB y PROPN con NOUN. Se reportan exactitud POS y precisión, recall y rechazo correcto de NOUN frente al resto. Cada tabla conserva sus denominadores. Un denominador cero produce null.

Los adaptadores NLTK/spaCy devuelven `accepted=null` porque entregan POS o dependencias, sin una decisión propia de pertenencia a esta CFG.

Fuentes: [NLTK](https://www.nltk.org/api/nltk.tag.sequential.html) y [spaCy español](https://spacy.io/models/es).
