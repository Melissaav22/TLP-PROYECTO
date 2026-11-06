# Proyecto TLP02 2026

Parser LL(1) para fragmentos MiniC y español controlado, árboles SVG y experimentos reproducibles con NLTK y spaCy.

La rama `feat/fase-uno` parte de `ExtensionEspañol` y conserva el alcance de la primera fase. Esta rama, `feat/fase-dos`, deriva de `feat/fase-uno` e incorpora SVO, pasado, el corpus completo y la integración LLM. Contiene ambas fases y actualiza la demo de fase 1 para la gramática ampliada.

## Estado

Los 39 fixtures originales se conservan. El corpus experimental contiene 60 frases, 20 por nivel, con 33 positivas y 27 negativas para la CFG. Hay análisis reales de los tres sistemas, métricas y gráficas. La ejecución API del LLM queda pendiente por decisión del usuario. Las etiquetas iniciales y los documentos requieren revisión del grupo. Consulta `docs/ESTADO_IMPLEMENTACION.md`.

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

## Subconjuntos y contratos

MiniC contiene declaraciones `int`, asignaciones, aritmética, comparaciones, `if/else if/else`, `while` y `for`, con cuerpos entre llaves. Los archivos representan fragmentos sintácticos. El análisis semántico de tipos, declaraciones previas y ejecución queda fuera del alcance.

Se aceptan decimales ASCII `0` o `[1-9][0-9]*`, de hasta 4.096 dígitos, conservando el lexema. Se excluyen octales, ceros iniciales, números Unicode, funciones, operadores lógicos, comentarios de bloque y asignaciones encadenadas. Se impide usar palabras clave C como identificadores.

El español se valida desde `Oracion`. Requiere determinante, sujeto nominal y verbo de tercera persona. Incluye presente, pretérito perfecto simple, objeto directo nominal opcional, adjetivos concordados, adverbios, PP y subordinadas con `que`.

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

El lock incluye spaCy 3.8.18, es_core_news_sm 3.8.0, NLTK 3.10.4 y Matplotlib 3.11.2. NLTK entrena un etiquetador unigram con CESS-ESP, respaldo por sufijos y NOUN. El corpus evaluado y los ejemplos few-shot se mantienen separados de ese entrenamiento.

## Reproducción

```powershell
.\.venv-nlp\Scripts\python.exe -m experimentos.validar_corpus
.\.venv-nlp\Scripts\python.exe -m experimentos.registro_fallos
.\.venv-nlp\Scripts\python.exe -m experimentos.demo_fase1
.\.venv-nlp\Scripts\python.exe -m experimentos.ambiguedad
.\.venv-nlp\Scripts\python.exe -m experimentos.comparar_nlp
.\.venv-nlp\Scripts\python.exe -m experimentos.metricas
.\.venv-nlp\Scripts\python.exe -m experimentos.graficas
.\.venv-nlp\Scripts\python.exe -m experimentos.rendimiento
.\.venv-nlp\Scripts\python.exe -m experimentos.llm
```

`datos/corpus_es.json` es el conjunto versionado. `scripts/preparar_datos.py` reconstruye deliberadamente la anotación inicial y sobrescribe esos datos. Después de revisar manualmente el oro se deben conservar las modificaciones en Git.

`resultados/` conserva salidas, hashes de fuentes, gramática y corpus. Los tiempos por oración excluyen entrenamiento y carga, registrados por separado. Los cambios locales quedan identificados mediante los hashes además del commit base.

Las huellas de archivos de texto normalizan UTF-8 y saltos LF. Los binarios,
incluido el corpus comprimido descargado, se identifican sin transformación.
Esto conserva la verificación al clonar el proyecto con otros saltos de línea.

## Tareas y métricas

La pertenencia CFG se evalúa para parser y, cuando se ejecute, LLM. Los tres analizadores se comparan en POS grueso, unificando AUX con VERB y PROPN con NOUN. Se reportan exactitud POS y precisión, recall y rechazo correcto de NOUN frente al resto. Cada tabla conserva sus denominadores. Un denominador cero produce null.

Los adaptadores NLTK/spaCy devuelven `accepted=null` porque entregan POS o dependencias, sin una decisión propia de pertenencia a esta CFG. La anotación de referencia es inicial y necesita revisión del grupo.

## LLM vía API

La preparación produce 120 solicitudes sobre las 60 frases y dos variantes. El usuario indicó dejar pendiente la ejecución real. No hay respuestas de proveedor guardadas.

Para ejecutar posteriormente, configurar `LLM_API_KEY`, `LLM_MODEL` y `LLM_ENDPOINT` en el entorno. El endpoint debe ser HTTPS Chat Completions compatible con JSON y `max_completion_tokens`. `.env.example` documenta los nombres, pero el programa no carga archivos .env automáticamente.

```powershell
.\.venv-nlp\Scripts\python.exe -m experimentos.llm --execute --max-new-calls 2
.\.venv-nlp\Scripts\python.exe -m experimentos.llm --execute --max-new-calls 120
.\.venv-nlp\Scripts\python.exe -m experimentos.resumir_llm
```

Se guardan prompts, respuestas, configuración, uso y validación de derivaciones. El hash permite reanudar sin duplicar llamadas completadas. Los argumentos `--input-usd-per-million` y `--output-usd-per-million` permiten estimar costo con tarifas del responsable. Ajustar límite de llamadas y tokens al presupuesto. Las claves quedan fuera de logs y Git.

## Informes y defensa

Los informes y sus fuentes editables están en `docs/`, junto con las presentaciones y sus notas de exposición. La Fase 2 identifica la sección LLM pendiente. El grupo debe revisar el oro, registrar integrantes, ensayar 15–20 minutos por presentación y verificar entrega/compartición.

Fuentes de adaptadores y cliente:
- [NLTK](https://www.nltk.org/api/nltk.tag.sequential.html)
- [spaCy español](https://spacy.io/models/es)
- [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
