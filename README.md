# Proyecto TLP02 2026

Parser LL(1) para fragmentos MiniC y español controlado. El proyecto incluye una interfaz de línea de comandos, exportación de árboles SVG y una evaluación que compara el parser propio, spaCy, NLTK y Gemini.

## 1. Obtener el proyecto e instalar las dependencias

Se requiere Git y conexión a internet para clonar el repositorio, instalar las dependencias y descargar los modelos. La instalación usa `uv`, que descarga Python 3.12.15 si hace falta. Si ya tienes `uv`, puedes pasar directamente al bloque de clonación.

En **Windows (PowerShell)**, instala `uv` con WinGet y vuelve a abrir la terminal.

```powershell
winget install --id=astral-sh.uv -e
```

En **Linux o macOS**, instala `uv` con el instalador oficial y vuelve a abrir la terminal. [Métodos de instalación de uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Los siguientes bloques funcionan desde PowerShell, Bash o Zsh. Ejecuta una línea a la vez desde la raíz del repositorio después de hacer `cd`. `uv run --python .venv-nlp` usa el entorno del proyecto directamente.

```sh
git --version
uv --version
git clone --branch master --single-branch https://github.com/Melissaav22/TLP-PROYECTO.git
cd TLP-PROYECTO
git rev-parse HEAD
uv venv --python 3.12.15 .venv-nlp
uv pip sync --python .venv-nlp --require-hashes requirements-experimentos.lock
uv run --python .venv-nlp python --version
uv run --python .venv-nlp python scripts/preparar_modelos.py
```

Guarda el commit que imprime `git rev-parse HEAD` para identificar la versión evaluada. El lock fija las dependencias e incluye NLTK 3.10.4, spaCy 3.8.18, el modelo `es_core_news_sm` 3.8.0 y Matplotlib 3.11.2. El último comando descarga CESS-ESP en `.models/nltk/` y verifica su SHA-256. Debe mostrar `CESS-ESP coincide con la huella del experimento.`.

## 2. Ejecutar todas las pruebas

```sh
uv run --python .venv-nlp python tests/run_tests.py
uv run --python .venv-nlp python tests/run_tests.py --es
uv run --python .venv-nlp python -m unittest discover -s tests -p "test_*.py" -v
```

Los resultados esperados son **20/20** casos MiniC, **29/29** casos de español y **71 pruebas de `unittest`** con resultado `OK`. Los dos primeros comandos comprueban casos válidos y rechazos esperados. El tercero descubre todas las pruebas de `test_*.py`, incluidas las de equivalencia del corpus, spaCy con su modelo, el evaluador y el cliente LLM. Las pruebas del cliente LLM usan un servidor HTTP local y se ejecutan sin credenciales.

## 3. Ejecutar el parser

```sh
uv run --python .venv-nlp python main.py tests/validos/v01_declaraciones.c --compacto
uv run --python .venv-nlp python main.py tests/es/validos/v07_subordinada.txt --es --svg .build/arbol.svg
uv run --python .venv-nlp python main.py --tabla
```

El primer comando imprime un árbol MiniC en formato de corchetes. El segundo muestra un árbol de español y genera `.build/arbol.svg`, que se puede abrir en el navegador. El tercero imprime FIRST, FOLLOW y la tabla LL(1).

Para comprobar un rechazo, el siguiente ejemplo devuelve un diagnóstico en la línea 4 y termina con código 1. Un análisis correcto termina con código 0 y los argumentos inválidos devuelven 2.

```sh
uv run --python .venv-nlp python main.py tests/invalidos/i01_falta_punto_y_coma.c
```

Para instalar únicamente el parser y ejecutar sus dos suites de archivos, puedes usar el lock mínimo. Para las 71 pruebas y los experimentos se necesita el entorno de la sección 1.

```sh
uv venv --python 3.12.15 .venv
uv pip sync --python .venv --require-hashes requirements-core.lock
uv run --python .venv python tests/run_tests.py
uv run --python .venv python tests/run_tests.py --es
```

## 4. Reproducir las métricas publicadas de la Fase 2

Este paso usa el corpus congelado y los logs incluidos en el repositorio. Se puede repetir sin clave de Gemini. Las salidas locales de la guía se guardan en `.build/`, una carpeta ignorada por Git.

```sh
uv run --python .venv-nlp python -m experimentos.validar_corpus --corpus datos/corpus_ordenado.json
uv run --python .venv-nlp python -m experimentos.evaluacion_fase2 --corpus datos/corpus_fase2.csv --criteria-file datos/criterios_evaluacion_fase2.txt --logs resultados/evaluacion/logs/parser_propio.jsonl resultados/evaluacion/logs/spacy_nltk.jsonl resultados/evaluacion/logs/llm_gemini.jsonl --out .build/evaluacion
git -c core.safecrlf=false diff --no-index --exit-code -- resultados/evaluacion/tabla_comparativa_espanol.csv .build/evaluacion/tabla_comparativa_espanol.csv
git -c core.safecrlf=false diff --no-index --exit-code -- resultados/evaluacion/tabla_comparativa_gramatica.csv .build/evaluacion/tabla_comparativa_gramatica.csv
```

La validación debe indicar **67 oraciones y 0 errores**. El evaluador debe procesar **1.809 registros**, **27 combinaciones de herramienta, variante, criterio y repetición** y **11 casos** en los que difieren las dos etiquetas de referencia. Los dos comandos de comparación deben terminar con código 0 y sin mostrar diferencias. En `.build/evaluacion/` quedan las tablas CSV, `reporte_metricas.json` y las gráficas PNG en `graficas/`.

El corpus canónico es [`datos/corpus_fase2.csv`](datos/corpus_fase2.csv). Tiene 34 oraciones aceptadas y 33 rechazadas según la CFG del proyecto. [`datos/corpus_ordenado.json`](datos/corpus_ordenado.json) contiene los mismos IDs `C2-*`, orden, textos, etiquetas y árboles para el experimento LLM. La prueba `test_corpus_equivalente.py` verifica esa correspondencia. Las copias XLSX y CSV con nombre `corpus_ordenado` son archivos de trabajo.

### Regenerar los logs de evaluación a partir de las evidencias guardadas

El primer comando vuelve a ejecutar el parser propio. El segundo convierte el registro publicado de spaCy y NLTK y las respuestas publicadas de Gemini. Si repites el bloque, elige una carpeta nueva para los tres logs porque el generador del parser impide duplicar el número de corrida dentro del mismo archivo.

```sh
uv run --python .venv-nlp python -m experimentos.generar_log_parser --output .build/logs/parser_propio.jsonl
uv run --python .venv-nlp python -m experimentos.convertir_logs_fase2 --out .build/logs
uv run --python .venv-nlp python -m experimentos.evaluacion_fase2 --corpus datos/corpus_fase2.csv --criteria-file datos/criterios_evaluacion_fase2.txt --logs .build/logs/parser_propio.jsonl .build/logs/spacy_nltk.jsonl .build/logs/llm_gemini.jsonl --out .build/evaluacion-regenerada
```

### Volver a ejecutar los experimentos locales

El primer comando exporta árboles, POS o dependencias según el analizador. El segundo ejecuta spaCy, NLTK con POS grueso y NLTK con etiquetas EAGLES completas. Hace tres repeticiones y debe verificar **1.608 registros**, con cero veredictos distintos y cero pares inestables. Los siguientes comandos evalúan los registros nuevos junto con las respuestas guardadas de Gemini. Al repetir todo el bloque, usa una nueva carpeta de salida para la Fase 2 y ajusta las rutas del bloque.

```sh
uv run --python .venv-nlp python -m experimentos.comparar_nlp --corpus datos/corpus_ordenado.json --output .build/nlp/corpus-ordenado.json
uv run --python .venv-nlp python -m experimentos.correr_fase2 --ensayo --corpus datos/corpus_fase2.csv --repeticiones 3 --salida .build/fase2
uv run --python .venv-nlp python -m experimentos.generar_log_parser --output .build/fase2/logs/parser_propio.jsonl
uv run --python .venv-nlp python -m experimentos.convertir_logs_fase2 --registro .build/fase2/registro.jsonl --meta .build/fase2/meta.json --out .build/fase2/logs
uv run --python .venv-nlp python -m experimentos.evaluacion_fase2 --corpus datos/corpus_fase2.csv --criteria-file datos/criterios_evaluacion_fase2.txt --logs .build/fase2/logs/parser_propio.jsonl .build/fase2/logs/spacy_nltk.jsonl .build/fase2/logs/llm_gemini.jsonl --out .build/fase2/evaluacion
```

La corrida queda marcada como ensayo. Para ejecutar en modo oficial, el corredor exige que el código y el corpus estén limpios en Git y que exista la etiqueta `criterios-v1`.

```sh
git fetch origin tag criterios-v1
uv run --python .venv-nlp python -m experimentos.correr_fase2 --corpus datos/corpus_fase2.csv --repeticiones 3 --salida .build/fase2-oficial
```

La corrida original se identifica en [`resultados/fase2/meta.json`](resultados/fase2/meta.json). Al volver a ejecutar los analizadores, los tiempos, las fechas y los metadatos locales se generan de nuevo.

## 5. Reproducir el experimento con Gemini

### Recalcular las métricas desde las respuestas guardadas

```sh
uv run --python .venv-nlp python -c "from shutil import copytree; copytree('resultados/llm/corpus-ordenado', '.build/llm-guardado', dirs_exist_ok=True)"
uv run --python .venv-nlp python -m experimentos.resumir_llm --corpus datos/corpus_ordenado.json --input .build/llm-guardado/resultados.json --reporte
```

La evidencia publicada cubre **67 oraciones por variante** (`zero_shot` y `few_shot`) y **14 lotes exitosos**. El log también conserva un intento HTTP 503 que se reintentó. El resumen, la gráfica y las tablas quedan en `.build/llm-guardado/`. El detalle vincula cada decisión con el hash de la llamada y el motivo de adherencia a la CFG.

### Generar los prompts localmente

En **PowerShell**:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

En **Linux o macOS**:

```sh
test -f .env || cp .env.example .env
```

Con el perfil Gemini de `.env.example`, este comando genera `.build/llm-prompts/solicitudes.json` con 14 solicitudes sin llamar a la API. Ambas variantes reciben las reglas y el léxico. `few_shot` agrega ejemplos de [`datos/ejemplos_few_shot.json`](datos/ejemplos_few_shot.json).

```sh
uv run --python .venv-nlp python -m experimentos.llm --provider gemini --corpus datos/corpus_ordenado.json --limit 67 --batch-size 10 --max-completion-tokens 8192 --output-dir .build/llm-prompts
```

### Obtener respuestas nuevas de la API (opcional)

Usa el `.env` del paso anterior. Consigue una clave de Gemini e introdúcela cuando la terminal la solicite. El modelo y el endpoint se configuran en ese archivo, que Git ignora. La disponibilidad, cuota y posibles cargos dependen de la cuenta del proveedor. Una corrida nueva puede producir respuestas y métricas distintas de las publicadas. [Google AI Studio](https://aistudio.google.com/api-keys).

```sh
uv run --python .venv-nlp python -m experimentos.llm --provider gemini --execute --ask-api-key --corpus datos/corpus_ordenado.json --limit 1 --batch-size 1 --output-dir .build/llm-prueba
```

Cuando la prueba reciba 2/2 respuestas, ejecuta el corpus completo. Con lotes de 10, el comando espera 14 respuestas de la API y 134 pares de oración y variante evaluables. Ejecuta el resumen cuando concluya la corrida.

```sh
uv run --python .venv-nlp python -m experimentos.llm --provider gemini --execute --ask-api-key --corpus datos/corpus_ordenado.json --limit 67 --batch-size 10 --max-completion-tokens 8192 --output-dir .build/llm-nuevo
uv run --python .venv-nlp python -m experimentos.resumir_llm --corpus datos/corpus_ordenado.json --input .build/llm-nuevo/resultados.json --reporte
```

Para reanudar, repite el mismo comando con el mismo modelo, parámetros y carpeta. Las respuestas que ya se recibieron se reutilizan. Ante un HTTP 429, consulta el último registro de `respuestas.jsonl` y reanuda al restablecerse la cuota. Para incorporar las respuestas nuevas a la evaluación conjunta, ejecuta estos comandos después de generar los logs locales de la sección 4.

```sh
uv run --python .venv-nlp python -m experimentos.convertir_logs_fase2 --registro .build/fase2/registro.jsonl --meta .build/fase2/meta.json --llm .build/llm-nuevo/respuestas.jsonl --out .build/fase2/logs-nuevos
uv run --python .venv-nlp python -m experimentos.evaluacion_fase2 --corpus datos/corpus_fase2.csv --criteria-file datos/criterios_evaluacion_fase2.txt --logs .build/fase2/logs/parser_propio.jsonl .build/fase2/logs-nuevos/spacy_nltk.jsonl .build/fase2/logs-nuevos/llm_gemini.jsonl --out .build/evaluacion-llm-nuevo
```

## 6. Reproducir las demostraciones y métricas históricas

El corpus histórico de 60 oraciones y las 120 respuestas de Gemini corresponden a otra versión de la gramática. Usa el commit `4b73411`. Los siguientes comandos se ejecutan en una copia de trabajo separada porque esos scripts escriben directamente en `resultados/`.

```sh
git worktree add --detach ../TLP-PROYECTO-historico 4b73411
cd ../TLP-PROYECTO-historico
uv venv --python 3.12.15 .venv-nlp
uv pip sync --python .venv-nlp --require-hashes requirements-experimentos.lock
uv run --python .venv-nlp python scripts/preparar_modelos.py
uv run --python .venv-nlp python -m experimentos.validar_corpus
uv run --python .venv-nlp python -m experimentos.registro_fallos
uv run --python .venv-nlp python -m experimentos.demo_fase1
uv run --python .venv-nlp python -m experimentos.ambiguedad
uv run --python .venv-nlp python -m experimentos.comparar_nlp
uv run --python .venv-nlp python -m experimentos.metricas
uv run --python .venv-nlp python -m experimentos.graficas
uv run --python .venv-nlp python -m experimentos.rendimiento
uv run --python .venv-nlp python -m experimentos.resumir_llm --corpus datos/corpus_es.json --input resultados/llm/resultados.json
cd ../TLP-PROYECTO
```

Las demostraciones y los árboles quedan en `resultados/fase1/`, la comparación en `resultados/nlp/` y el resumen de Gemini en `resultados/llm/`. En `resultados/metricas/` se guardan las gráficas de exactitud POS y tiempos, las tablas y el archivo `rendimiento.json`. Los corpus y ejemplos ya están versionados. `scripts/preparar_datos.py` reconstruye la anotación inicial y sobrescribe `datos/corpus_es.json`, `datos/fase1.json` y `datos/ejemplos_few_shot.json`.

## Alcance del parser y de la evaluación

- **MiniC** admite declaraciones `int`, asignaciones, aritmética, comparaciones, `if/else if/else`, `while` y `for`, con cuerpos entre llaves. Valida sintaxis de fragmentos. Los decimales permitidos son `0` o `[1-9][0-9]*`, hasta 4.096 dígitos. Las palabras clave de C están reservadas. Funciones, operadores lógicos, comentarios de bloque, asignaciones encadenadas, análisis semántico y ejecución quedan fuera del alcance.
- **Español controlado** se valida desde `Oracion` con determinante, sujeto nominal y verbo de tercera persona. Incluye presente, pretérito perfecto simple, objeto directo nominal opcional, concordancia de adjetivos, adverbios, sintagmas preposicionales y subordinadas con `que`. Los sintagmas preposicionales sucesivos se adjuntan al sintagma verbal. El léxico se normaliza a NFC y está en `minic/lexicon_es.py`. Coordinación, pronombres, relativas, imperfecto, punto final y valencia semántica quedan fuera del subconjunto.
- **Interfaz de Python**. `parse(source, grammar, spanish=False)` devuelve `(nltk.Tree, list[str])`. `parse_detailed` añade tokens, diagnósticos estructurados y producciones. `Grammar(path, start=...)` y `for_start` calculan FOLLOW y la tabla para la raíz elegida. El SVG admite hasta 2.000 nodos.
- **Etiquetas de referencia**. La corrección general del español y la pertenencia a la CFG se evalúan con tablas distintas. Los adaptadores spaCy y NLTK devuelven POS o dependencias. El corredor de Fase 2 aplica los criterios documentados a esas salidas.
- **Experimento histórico de POS**. Se unificaron AUX con VERB y PROPN con NOUN. Los tiempos de inferencia por oración se midieron con los modelos ya cargados. El corpus ordenado de Fase 2 aporta etiquetas de aceptación y árboles, y carece de la anotación POS por token necesaria para repetir esa métrica sobre las 67 oraciones.

El [informe técnico en PDF](Informe_Tecnico_Proyecto_TEO_PDF.pdf) y su [versión editable](Informe_Tecnico_Proyecto_TEO.docx) están en el repositorio. Los informes, presentación y capturas históricos se pueden consultar en el commit `77fccf2`.

Referencias de los adaptadores y el cliente. [NLTK](https://www.nltk.org/api/nltk.tag.sequential.html), [spaCy español](https://spacy.io/models/es), [Chat Completions](https://developers.openai.com/api/reference/resources/chat/completions/methods/create).
