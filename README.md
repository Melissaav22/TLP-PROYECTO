# Proyecto TLP02 2026

Parser LL(1) para fragmentos MiniC y español controlado, árboles SVG y experimentos reproducibles con NLTK y spaCy.

La rama `feat/fase-uno` parte de `ExtensionEspañol` y conserva el alcance de la primera fase. Esta rama, `feat/fase-dos`, deriva de `feat/fase-uno` e incorpora SVO, pasado, el corpus completo y la integración LLM. Contiene ambas fases y actualiza la demo de fase 1 para la gramática ampliada.

## Estado

El corpus experimental tiene 60 frases, 20 por nivel, con 33 aceptadas y 27 rechazadas por la CFG. Se conservan las salidas de los tres analizadores y las 120 respuestas reales de Gemini. Los prompts completos, las marcas de tiempo y el resumen por variante están en `resultados/llm/`. Los informes en `docs/` corresponden a una versión anterior a la corrida de Gemini.

El Excel original del corpus ordenado de 67 oraciones está en `datos/corpus_ordenado.xlsx`. Se incluye `datos/corpus_ordenado.json` para ejecutar el benchmark y `datos/corpus_ordenado.csv` como anexo. Sus árboles de referencia corresponden a la gramática de `master` en `40fcd2e`. Los resultados publicados de Gemini corresponden al corpus original de 60 oraciones y a la gramática de esta rama.

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

El experimento produce 120 solicitudes, una por cada una de las 60 oraciones en cada variante. Ambas reciben las producciones y el lexicón. La variante `few_shot` agrega ejemplos de un archivo separado del corpus.

Si todavía no existe `.env`, créalo desde PowerShell en la raíz del proyecto.

```powershell
Copy-Item .env.example .env
```

El perfil activo se elige con `LLM_PROVIDER`. Para Gemini, deja `LLM_PROVIDER=gemini` y completa `GEMINI_API_KEY` con tu clave de [Google AI Studio](https://aistudio.google.com/api-keys). El archivo ya contiene el modelo, el endpoint y los parámetros de la corrida. Guarda las claves en el `.env` local, que Git ignora. También puedes dejar la clave vacía y pasar `--ask-api-key` para ingresarla sin mostrarla en la terminal.

Para probar una oración en ambas variantes, ejecuta:

```powershell
.\.venv-nlp\Scripts\python.exe -m experimentos.llm --execute --limit 1 --output-dir .build/llm-prueba
```

Si la prueba devuelve `2/2` y el comando termina correctamente, consulta la cuota de tu proveedor y ejecuta el corpus completo.

```powershell
.\.venv-nlp\Scripts\python.exe -m experimentos.llm --execute
.\.venv-nlp\Scripts\python.exe -m experimentos.resumir_llm
```

`respuestas.jsonl` conserva el prompt, la respuesta completa y la fecha y hora UTC de cada llamada. `resumen.json` contiene las métricas por variante. Gemini escribe en `resultados/llm/` y los demás perfiles configurados tienen su propia subcarpeta. Para reanudar, usa el mismo modelo, parámetros y comando.

El perfil de Gemini separa el inicio de cada llamada por al menos `GEMINI_MIN_SECONDS_BETWEEN_CALLS=5.5` segundos. Si el proveedor devuelve HTTP 429, el script guarda el error y detiene la corrida. Revisa la cuota indicada en el último registro y repite el comando cuando se restablezca. Las respuestas guardadas se reutilizan.

Para una corrida por lotes, fija `--batch-size` o `LLM_BATCH_SIZE` en `.env`. Cada llamada recibe las reglas y el lexicón una vez, con una lista de oraciones e identificadores. Las dos variantes usan los mismos lotes y el mismo orden. Solo `few_shot` recibe ejemplos resueltos. El log conserva un registro por llamada y el evaluador calcula las métricas por oración. Con un lote de 10 se necesitan 12 llamadas para las 60 oraciones.

```powershell
.\.venv-nlp\Scripts\python.exe -m experimentos.llm --execute --batch-size 10 --max-completion-tokens 8192
.\.venv-nlp\Scripts\python.exe -m experimentos.resumir_llm --input resultados/llm/lotes-10/resultados.json
```

Para preparar una sola llamada por variante con Gemini, usa `--batch-size 60 --max-completion-tokens 32768`. Sin `--execute` se preparan los prompts localmente. Una respuesta truncada puede dejar un lote incompleto, y las oraciones omitidas se registran como errores de ejecución. Si realizas una corrida por lotes, reporta el tamaño del lote y el límite de salida en la metodología. Usa su propio log y resumen porque las oraciones comparten contexto dentro de cada llamada.

Para evaluar otro corpus, pasa el mismo `--corpus ruta.json` tanto a `experimentos.llm` como a `experimentos.resumir_llm`. En la corrida fija `--limit` al número de oraciones y usa un `--output-dir` propio. El evaluador comprueba que el hash del corpus coincida con el de los resultados.

Para cambiar de proveedor, configura la clave del perfil y cambia `LLM_PROVIDER` a `openai`, `anthropic` o `custom`. También puedes definir otro perfil, por ejemplo `mi-proveedor`, con las variables `MI_PROVEEDOR_PROTOCOL`, `MI_PROVEEDOR_API_KEY`, `MI_PROVEEDOR_MODEL` y `MI_PROVEEDOR_ENDPOINT`. El protocolo determina el formato de la API. Los formatos disponibles son Chat Completions (`chat-completions`), Gemini GenerateContent (`gemini`) y Claude Messages (`anthropic`, con `*_API_VERSION`). Para endpoints compatibles con Chat Completions, usa `*_TOKEN_FIELD` y `*_JSON_MODE` si el proveedor exige parámetros distintos. En el archivo usa una asignación `NOMBRE=valor` por línea y coloca los comentarios en líneas separadas.

Puedes definir el tiempo de espera, límite de llamadas, tokens, carpeta y tarifas por perfil con su prefijo. Los argumentos del comando tienen prioridad sobre la configuración del perfil. Una variable de entorno reemplaza la misma variable del archivo `.env`. Usa `--provider nombre` para una corrida puntual con otro perfil y pásalo también a `experimentos.resumir_llm` para leer sus resultados.

## Informes y defensa

Los informes y sus fuentes editables están en `docs/`, junto con las presentaciones y sus notas de exposición. La Fase 2 identifica la sección LLM pendiente. El grupo debe revisar el oro, registrar integrantes, ensayar 15–20 minutos por presentación y verificar entrega/compartición.

Fuentes de adaptadores y cliente:
- [NLTK](https://www.nltk.org/api/nltk.tag.sequential.html)
- [spaCy español](https://spacy.io/models/es)
- [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
