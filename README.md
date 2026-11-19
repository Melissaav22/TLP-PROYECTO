# Proyecto TLP02 2026

Parser LL(1) para fragmentos MiniC y español controlado, árboles SVG y experimentos reproducibles con NLTK y spaCy.

El parser usa la gramática y el léxico integrados en `master`. La Fase 2 incorpora los comandos del benchmark, el corpus ordenado y el registro de Gemini.

## Estado

El corpus de la gramática actual contiene 67 oraciones, con 34 aceptadas y 33 rechazadas. El Excel está en `datos/corpus_ordenado.xlsx`, el archivo para ejecutar el benchmark en `datos/corpus_ordenado.json` y el anexo en `datos/corpus_ordenado.csv`. Los tres conservan el orden de la hoja `corpus_fase2` y sus IDs oficiales `C2-*`, que también identifican los pares mínimos. Los 34 árboles esperados coinciden con el parser de `master` en `40fcd2e`.

La corrida de Gemini sobre este corpus está en `resultados/llm/corpus-ordenado/`. Hay 67 evaluaciones por variante y 14 lotes exitosos. El log conserva también el intento con HTTP 503 que se reintentó.

La corrida histórica usó `datos/corpus_es.json` con 60 oraciones y la CFG anterior, disponible en `4b73411`. Sus 120 respuestas reales, prompts y métricas están en `resultados/llm/`. Las salidas de NLTK, spaCy y el parser sobre ese corpus están en `resultados/nlp/` y `resultados/metricas/`. El PDF en `docs/` precede a la corrida de Gemini.

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

Si prefieres instalar sin `uv`, ejecuta `python -m venv .venv` y `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. También puedes activar el entorno con `.\.venv\Scripts\Activate.ps1` y usar `python` directamente. Las pruebas de archivos esperan 20 casos MiniC y 29 casos de español.

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
.\.venv-nlp\Scripts\python.exe -m experimentos.comparar_nlp --corpus datos/corpus_ordenado.json --output resultados/nlp/corpus-ordenado.json
```

`datos/fase1.json` conserva las oraciones de demostración de `master`. Las pruebas nuevas usan `datos/corpus_ordenado.json`. Para reproducir la gramática y los experimentos del corpus histórico, abre otra copia con `git worktree add --detach ../tlp-fase-dos-historica 4b73411` y sigue su README.

`resultados/` conserva salidas, hashes de fuentes, gramática y corpus. Los tiempos por oración excluyen entrenamiento y carga, registrados por separado. Los cambios locales quedan identificados mediante los hashes además del commit base.

Las huellas de archivos de texto normalizan UTF-8 y saltos LF. Los binarios,
incluido el corpus comprimido descargado, se identifican sin transformación.
Esto conserva la verificación al clonar el proyecto con otros saltos de línea.

## Tareas y métricas

La pertenencia CFG se evalúa para el parser y el LLM. En el corpus histórico los tres analizadores se compararon también en POS grueso, unificando AUX con VERB y PROPN con NOUN. El corpus del Excel tiene etiquetas de aceptación y árboles, y requiere anotación POS por token para ese cálculo.

Los adaptadores NLTK/spaCy devuelven `accepted=null` porque entregan POS o dependencias, sin una decisión propia de pertenencia a esta CFG. La anotación de referencia es inicial y necesita revisión del grupo.

## LLM vía API

Ambas variantes reciben las producciones y el léxico. La variante `few_shot` agrega ejemplos de un archivo separado del corpus. Para recalcular las métricas históricas desde los archivos guardados, ejecuta:

```powershell
.\.venv-nlp\Scripts\python.exe -m experimentos.resumir_llm --corpus datos/corpus_es.json --input resultados/llm/resultados.json
```

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
.\.venv-nlp\Scripts\python.exe -m experimentos.llm --execute --limit 67 --batch-size 10 --max-completion-tokens 8192 --output-dir resultados/llm/corpus-ordenado
if ($LASTEXITCODE -eq 0) {
    .\.venv-nlp\Scripts\python.exe -m experimentos.resumir_llm --input resultados/llm/corpus-ordenado/resultados.json
}
```

`respuestas.jsonl` conserva el prompt, la respuesta completa y la fecha y hora UTC de cada llamada. `resumen.json` contiene las métricas por variante. La corrida actual de Gemini se guarda bajo `resultados/llm/corpus-ordenado/`. Para reanudar, usa el mismo modelo, parámetros y comando. El script comprueba la versión de la CFG antes de cargar o escribir evidencia.

Agrega `--reporte` a `experimentos.resumir_llm` para generar `comparacion_llm.png`, `comparacion_llm.csv` y `detalle_llm.csv` en la carpeta de resultados. La tabla de detalle vincula cada oración con su decisión, el motivo de adherencia y el hash de su llamada. Los errores de ejecución y las oraciones sin registro aparecen por separado y quedan fuera de las métricas de aceptación. La gráfica indica cuántas oraciones fueron evaluables en cada variante.

```powershell
.\.venv-nlp\Scripts\python.exe -m experimentos.resumir_llm --corpus datos/corpus_ordenado.json --input resultados/llm/corpus-ordenado/resultados.json --reporte
```

El perfil de Gemini separa el inicio de cada llamada por al menos `GEMINI_MIN_SECONDS_BETWEEN_CALLS=5.5` segundos. Si el proveedor devuelve HTTP 429, el script guarda el error y detiene la corrida. Revisa la cuota indicada en el último registro y repite el comando cuando se restablezca. Las respuestas guardadas se reutilizan.

Para una corrida por lotes, fija `--batch-size` o `LLM_BATCH_SIZE` en `.env`. Cada llamada recibe las reglas y el léxico una vez, con una lista de oraciones e identificadores. Las dos variantes usan los mismos lotes y el mismo orden. El log conserva un registro por llamada y el evaluador calcula las métricas por oración. Con un lote de 10 se necesitan 14 llamadas para las 67 oraciones.

Para preparar una sola llamada por variante con Gemini, usa `--limit 67 --batch-size 67 --max-completion-tokens 32768`. Sin `--execute` se preparan los prompts localmente. Una respuesta truncada puede dejar un lote incompleto, y las oraciones omitidas se registran como errores de ejecución. Si realizas una corrida por lotes, reporta el tamaño del lote y el límite de salida en la metodología. Usa su propio log y resumen porque las oraciones comparten contexto dentro de cada llamada.

Para evaluar otro corpus, pasa el mismo `--corpus ruta.json` tanto a `experimentos.llm` como a `experimentos.resumir_llm`. En la corrida fija `--limit` al número de oraciones y usa un `--output-dir` propio. El evaluador comprueba que el hash del corpus coincida con el de los resultados.

Para cambiar de proveedor, configura la clave del perfil y cambia `LLM_PROVIDER` a `openai`, `anthropic` o `custom`. También puedes definir otro perfil, por ejemplo `mi-proveedor`, con las variables `MI_PROVEEDOR_PROTOCOL`, `MI_PROVEEDOR_API_KEY`, `MI_PROVEEDOR_MODEL` y `MI_PROVEEDOR_ENDPOINT`. El protocolo determina el formato de la API. Los formatos disponibles son Chat Completions (`chat-completions`), Gemini GenerateContent (`gemini`) y Claude Messages (`anthropic`, con `*_API_VERSION`). Para endpoints compatibles con Chat Completions, usa `*_TOKEN_FIELD` y `*_JSON_MODE` si el proveedor exige parámetros distintos. En el archivo usa una asignación `NOMBRE=valor` por línea y coloca los comentarios en líneas separadas.

Puedes definir el tiempo de espera, límite de llamadas, tokens, carpeta y tarifas por perfil con su prefijo. Los argumentos del comando tienen prioridad sobre la configuración del perfil. Una variable de entorno reemplaza la misma variable del archivo `.env`. Usa `--provider nombre` para una corrida puntual con otro perfil y pásalo también a `experimentos.resumir_llm` para leer sus resultados.

## Informes y defensa

Los borradores históricos de la Fase 2 están en `docs/`. La evaluación de la Fase 2 requiere el informe escrito y sus anexos de evidencia. Al citar las métricas, identifica el corpus y la versión de la CFG que se usaron.

Fuentes de adaptadores y cliente:
- [NLTK](https://www.nltk.org/api/nltk.tag.sequential.html)
- [spaCy español](https://spacy.io/models/es)
- [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
