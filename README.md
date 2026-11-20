# Proyecto TLP02 2026

Proyecto de Teoría de Lenguajes de Programación (UCA). Implementa un parser predictivo LL(1) para un subconjunto de C (MiniC) y para un subconjunto controlado del español, ambos descritos por una única gramática libre de contexto (CFG). La Fase 2 compara ese parser con spaCy, NLTK y un modelo de lenguaje grande (LLM) sobre un mismo corpus de 67 oraciones, y registra todo el proceso en logs reproducibles.

Este documento describe qué contiene el repositorio, cómo ejecutarlo y qué función cumple cada archivo. Los resultados y las conclusiones se presentan en el informe de la Fase 2, no aquí.

> **Para reproducir los resultados:** ir directamente a la sección [6. Comandos](#6-comandos). La instalación está en [6.1](#61-instalación) y las métricas de la Fase 2 se reproducen en [6.4](#64-reproducir-las-métricas-de-la-fase-2).

## Contenido

1. [Alcance de cada fase](#1-alcance-de-cada-fase)
2. [Conceptos de la Fase 2](#2-conceptos-de-la-fase-2)
3. [Flujo de datos: de las herramientas a los logs y a las métricas](#3-flujo-de-datos-de-las-herramientas-a-los-logs-y-a-las-métricas)
4. [Qué se fija y qué no: reproducibilidad](#4-qué-se-fija-y-qué-no-reproducibilidad)
5. [Guía de archivos](#5-guía-de-archivos)
6. [Comandos](#6-comandos)
7. [Alcance de la gramática y límites de la evaluación](#7-alcance-de-la-gramática-y-límites-de-la-evaluación)

## 1. Alcance de cada fase

**Fase 1: parser y gramática.** El motor del parser (analizador léxico con PLY, cálculo de FIRST y FOLLOW, tabla LL(1) y análisis con pila explícita) reconoce MiniC y una primera extensión al español. Esta fase se conserva sin cambios en el motor (`minic/`), con sus casos de prueba (`tests/`) y sus salidas históricas (`resultados/fase1/` y carpetas relacionadas). La corrida histórica de 60 oraciones se reproduce desde el commit `4b73411` (sección 6.7).

**Fase 2: evaluación comparativa.** Sobre el motor anterior solo cambió la gramática del español, ampliada para el corpus de 67 oraciones. La fase añade el corpus congelado, los criterios de decisión para spaCy y NLTK, el experimento con el LLM, el evaluador y los logs. Sus archivos están en `experimentos/`, `datos/`, `prompts/` y `resultados/` (sección 5).

## 2. Conceptos de la Fase 2

### 2.1 Corpus y etiquetas de referencia

El corpus es `datos/corpus_fase2.csv`: 67 oraciones en tres niveles (17 simples, 30 intermedias y 20 complejas). Cada oración tiene dos etiquetas de referencia independientes, con valores `aceptada` o `rechazada`:

| Etiqueta | Pregunta que responde | Uso |
|---|---|---|
| `esperado_espanol` | ¿La oración es español correcto? (43 correctas, 24 incorrectas) | Referencia de las métricas de todos los enfoques. |
| `esperado_gramatica` | ¿La CFG del proyecto acepta la oración? (34 aceptadas, 33 rechazadas) | Referencia para determinar si el LLM aplicó las reglas que se le entregaron o su conocimiento general del idioma. |

El parser propio coincide con `esperado_gramatica` por construcción, de modo que esa etiqueta no se usa para evaluarlo. Las dos etiquetas difieren en 11 oraciones del nivel 3, que forman el **subconjunto diagnóstico**: son los casos en los que se distingue si un sistema sigue la gramática o el idioma.

### 2.2 Enfoques y variantes

| Enfoque | Variantes | Naturaleza |
|---|---|---|
| Parser propio | `principal` | Formal: define un lenguaje y rechaza lo que no pertenece a él. |
| spaCy | `principal` (modelo `es_core_news_sm`) | Estadístico: entrega un árbol de dependencias para casi cualquier entrada. |
| NLTK | `nltk` (etiquetas gruesas, el etiquetador de la Fase 1) y `nltk_full` (etiquetas EAGLES completas, con género y número) | Estadístico: entrega solo una etiqueta gramatical por palabra. |
| LLM (Gemini) | `zero_shot` (solo reglas y léxico) y `few_shot` (reglas, léxico y ejemplos) | Generativo: se le entrega la gramática y responde con una decisión y una derivación. |

Una **combinación** es una variante evaluada con un criterio y en una corrida. La evaluación completa tiene 27 combinaciones.

### 2.3 Criterios de decisión para spaCy y NLTK

spaCy y NLTK no devuelven un veredicto de aceptación. Para compararlos con el parser se definen tres criterios sobre su salida (versión `criterios-v1`):

| Criterio | Una oración se acepta si… |
|---|---|
| **C0** | Siempre. Es la línea base: cobertura 1 y rechazo correcto 0 por construcción. |
| **C1** | Tiene estructura mínima. En spaCy, la raíz del árbol es un verbo, o una cópula con atributo. En NLTK, hay al menos un sustantivo y un verbo. El sujeto no es obligatorio. |
| **C2** | Cumple C1 y no hay ninguna discordancia explícita de género o número entre palabras relacionadas. |

Reglas de C2:

- spaCy compara pares relacionados por el árbol: determinante–sustantivo y adjetivo–sustantivo (género y número), sujeto–verbo (número), sujeto–adjetivo predicado (género y número) y sujeto–cópula (número).
- `nltk_full` compara solo pares de palabras adyacentes (determinante seguido de sustantivo, sustantivo seguido de adjetivo), porque NLTK no construye un árbol. `nltk` no tiene C2: sus etiquetas no incluyen género ni número.
- Cada comparación tiene uno de cuatro resultados: `concuerda`, `viola`, `genero_comun` (sustantivo compatible con ambos géneros) o `indeterminado` (falta un dato). Solo `viola` provoca el rechazo.

### 2.4 Métricas

La clase positiva es «aceptada». Con VP, FP, VN y FN (verdaderos y falsos positivos y negativos) se calculan: precisión = VP/(VP+FP), cobertura = VP/(VP+FN), tasa de rechazo correcto = VN/(VN+FP) y exactitud = (VP+VN)/total. Si un denominador es cero, el valor se informa como no aplicable. Los registros con error de ejecución se cuentan por separado y no entran como aceptaciones ni rechazos.

## 3. Flujo de datos: de las herramientas a los logs y a las métricas

```
datos/corpus_fase2.csv  (67 oraciones, dos etiquetas de referencia)
   │
   ├─ correr_fase2.py ──── spaCy y NLTK, 3 repeticiones ────► resultados/fase2/registro.jsonl  + meta.json
   │      (guarda la salida cruda y recalcula el veredicto con criterios.py)
   │
   ├─ generar_log_parser.py ── parser propio ───────────────► logs/parser_propio.jsonl
   │
   └─ llm.py ──── Gemini, zero_shot y few_shot ─────────────► resultados/llm/corpus-ordenado/respuestas.jsonl
                                  │
          convertir_logs_fase2.py │  traduce al formato común de registro
                                  ▼
   resultados/evaluacion/logs/parser_propio.jsonl · spacy_nltk.jsonl · llm_gemini.jsonl
                                  │
                evaluacion_fase2.py  (asocia cada registro con su etiqueta de referencia)
                                  ▼
   resumen_metricas.csv · metricas_por_corrida.csv · registros_normalizados.csv
   tabla_comparativa_espanol.csv · tabla_comparativa_gramatica.csv
   clasificacion_errores.csv · reporte_metricas.json · graficas/
```

1. **Ejecución.** Cada herramienta procesa las 67 oraciones. `correr_fase2.py` guarda la salida cruda de spaCy y NLTK (tokens, etiquetas, dependencias y rasgos morfológicos) y recalcula la decisión con `criterios.py`. El parser propio y el LLM generan sus propios logs.
2. **Conversión.** `convertir_logs_fase2.py` lleva `registro.jsonl` y las respuestas de Gemini al formato común que lee el evaluador (`resultados/evaluacion/logs/`).
3. **Evaluación.** `evaluacion_fase2.py` lee el corpus, el archivo de criterios y los tres logs, valida que los identificadores de oración coincidan, asocia cada registro con `esperado_espanol` y `esperado_gramatica`, y calcula las métricas globales, por nivel, por fenómeno y para el subconjunto diagnóstico.

**Registro de spaCy y NLTK.** Cada línea de `registro.jsonl` contiene: identificador de la oración, herramienta, variante, criterio, número de corrida, fecha, versiones, hashes SHA-256 del corpus y de los criterios, la salida cruda de la herramienta y la decisión (`accepted`, `motivo` y la lista de comparaciones de concordancia). Todos los veredictos provienen de una sola función, `decidir(herramienta, criterio, salida_cruda)`, que lee únicamente la salida cruda; por eso pueden recalcularse sin volver a ejecutar las herramientas.

**Registro del LLM.** Cada línea de `respuestas.jsonl` corresponde a una llamada a la API (un lote de hasta 10 oraciones) y contiene la solicitud completa, su hash SHA-256 (`request_sha256`), el modelo, el punto de acceso, la fecha, la respuesta cruda, las evaluaciones extraídas y los hashes de la gramática, del corpus y del código.

## 4. Qué se fija y qué no: reproducibilidad

| Elemento | Cómo queda fijado | Cómo se comprueba |
|---|---|---|
| Dependencias | `requirements-experimentos.lock` fija versiones con hashes (spaCy 3.8.18, NLTK 3.10.4, `es_core_news_sm` 3.8.0, Matplotlib 3.11.2). | `uv pip sync --require-hashes` rechaza cualquier paquete distinto. |
| Corpus de entrenamiento de NLTK | CESS-ESP, con su huella SHA-256. | `scripts/preparar_modelos.py` verifica la huella. |
| Corpus de evaluación | `datos/corpus_fase2.csv`; su SHA-256 queda en `meta.json` y en cada registro. | `validar_corpus` y la prueba `test_corpus_equivalente.py`. |
| Criterios | Etiqueta de git `criterios-v1` (commit `cac7aa7`) creada antes de ejecutar los experimentos; el SHA-256 de `criterios.py` queda en `meta.json`. | El corredor oficial exige código y corpus limpios en Git y la etiqueta. |
| Registro de spaCy y NLTK | `resultados/fase2/registro.jsonl` con su SHA-256 en `meta.json`; 3 repeticiones. | El corredor recalcula los 1.608 registros: 0 veredictos distintos y 0 pares inestables. |
| Parser propio | Determinista. | `generar_log_parser.py` reproduce el log; una prueba impide duplicar corridas. |
| Evaluador y métricas | Determinista; no usa aleatoriedad. | Las tablas regeneradas coinciden con las publicadas (sección 6.4). |
| **Respuestas del LLM** | Se conservan las respuestas publicadas, con solicitud completa y hash. | Las métricas se recalculan desde esas respuestas (sección 6.6). |

**Limitación del LLM.** Una llamada nueva a la API no está garantizada de reproducir las respuestas publicadas. La solicitud no fija temperatura ni semilla, de modo que se aplican los valores por defecto del proveedor (con `thinkingLevel` en `MINIMAL` y `maxOutputTokens` en 8192), y el modelo `gemini-3.1-flash-lite` es un servicio externo que puede cambiar. Lo que queda fijado es la evidencia: el hash de cada solicitud, la respuesta cruda y la fecha, que permiten recalcular las métricas y auditar cada decisión sin acceso a la API. La corrida publicada tiene una repetición por variante, a diferencia de spaCy y NLTK.

**Entorno de la corrida oficial.** Python 3.12.6 en Windows 11 (ver `meta.json`). Con Python 3.12.15 se reproducen los mismos veredictos.

## 5. Guía de archivos

La columna «Rol» indica la importancia de cada archivo para entender la Fase 2: **Núcleo** (define o produce lo que se evalúa), **Apoyo** (verificación, utilidades o archivos auxiliares) e **Histórico** (Fase 1 o corridas anteriores; no intervienen en las métricas de la Fase 2).

### 5.1 Raíz

| Archivo | Rol | Función |
|---|---|---|
| `main.py` | Núcleo | Línea de comandos del parser: imprime árboles, exporta SVG y muestra la tabla LL(1). |
| `gramatica_minic.txt` | Núcleo | Gramática unificada de MiniC y del español. |
| `requirements-experimentos.lock` | Núcleo | Dependencias de los experimentos, fijadas con hashes. |
| `requirements-experimentos.in` | Apoyo | Lista de origen del `.lock`; fija el modelo `es_core_news_sm` por URL. |
| `requirements-core.lock`, `requirements.txt` | Apoyo | Dependencias mínimas del parser (con y sin hashes). |
| `.env.example` | Apoyo | Plantilla de configuración de la API (modelo, punto de acceso, parámetros). El `.env` real queda fuera de Git. |
| `.gitignore`, `.gitattributes` | Apoyo | Excluyen entornos, modelos descargados, `.env` y `.build/`; fijan los finales de línea. |
| `Informe_Tecnico_Proyecto_TEO*` | Apoyo | Informe técnico del proyecto, en PDF y en versión editable. |

### 5.2 `minic/`: el parser (Fase 1)

| Archivo | Rol | Función |
|---|---|---|
| `parser.py` | Núcleo | Parser predictivo LL(1) con pila explícita. |
| `grammar.py` | Núcleo | Carga la gramática y calcula FIRST, FOLLOW y la tabla de análisis. |
| `lexer.py` | Núcleo | Analizador léxico (PLY). |
| `lexicon_es.py` | Núcleo | Léxico del español, normalizado a NFC. Es el archivo que se amplía al cambiar el corpus. |
| `trees.py` | Apoyo | Serialización de árboles y exportación a SVG sin dependencias adicionales. |
| `diagnostics.py` | Apoyo | Diagnósticos con línea y columna estables para la CLI y los experimentos. |

### 5.3 `experimentos/`: la evaluación (Fase 2)

| Archivo | Rol | Función |
|---|---|---|
| `evaluacion_fase2.py` | Núcleo | **El evaluador.** Lee corpus, criterios y logs; calcula las métricas y escribe las tablas. Escribe además una tabla comparativa por etiqueta de referencia. Es el script que se vuelve a ejecutar para reproducir los resultados. |
| `criterios.py` | Núcleo | Define C0, C1 y C2 (`criterios-v1`) y la función `decidir`, única fuente de veredictos. |
| `correr_fase2.py` | Núcleo | Ejecuta spaCy y NLTK, guarda la salida cruda y verifica los veredictos. Tiene modo ensayo y modo oficial. |
| `convertir_logs_fase2.py` | Núcleo | Convierte el registro de spaCy/NLTK y las respuestas del LLM al formato común del evaluador. |
| `generar_log_parser.py` | Núcleo | Ejecuta el parser propio sobre el corpus y escribe su log. |
| `llm.py`, `llm_config.py` | Núcleo | Cliente reanudable para Gemini (o una API compatible) y su configuración por perfiles. |
| `nltk_full.py` | Núcleo | Entrena el segundo etiquetador de NLTK con etiquetas EAGLES completas (`nltk_full`). |
| `adaptadores.py` | Apoyo | Envuelve el parser, spaCy y NLTK con un contrato común de tokens y etiquetas; define el etiquetador de la Fase 1 (`nltk`). |
| `metricas.py` | Apoyo | Define los indicadores y sus denominadores. |
| `resumir_llm.py`, `graficas_llm.py` | Apoyo | Resumen de las respuestas del LLM, comparación entre variantes y detalle por oración. |
| `validar_corpus.py`, `validar_derivacion.py` | Apoyo | Validan la integridad del corpus y las derivaciones entregadas por el LLM. |
| `common.py` | Apoyo | Persistencia y metadatos compartidos. |
| `comparar_nlp.py`, `demo_fase1.py`, `registro_fallos.py`, `ambiguedad.py`, `rendimiento.py`, `graficas.py` | Histórico | Análisis de la Fase 1 y del corpus de 60 oraciones: comparación de POS, demostración, fallos con trazas, ambigüedad, tiempos y gráficas. |

### 5.4 `datos/`, `prompts/` y `scripts/`

| Archivo | Rol | Función |
|---|---|---|
| `datos/corpus_fase2.csv` | Núcleo | Corpus congelado de 67 oraciones con las dos etiquetas. Fuente canónica. |
| `datos/criterios_evaluacion_fase2.txt` | Núcleo | Descripción en texto de los criterios y de las etiquetas de referencia; es una entrada del evaluador. |
| `prompts/zero_shot.txt`, `prompts/few_shot.txt` | Núcleo | Prompts exactos enviados al LLM. |
| `datos/corpus_ordenado.json` | Núcleo | Copia del corpus en JSON que lee el experimento del LLM. Una prueba verifica que coincida con el CSV. |
| `datos/ejemplos_few_shot.json` | Apoyo | Ejemplos de la variante `few_shot`, guardados aparte del corpus evaluado. |
| `datos/modelos.json` | Apoyo | Versiones y huellas de los modelos usados. |
| `datos/corpus_ordenado.csv`, `datos/corpus_ordenado.xlsx` | Apoyo | Archivos de trabajo del corpus; no intervienen en la evaluación. |
| `datos/corpus_es.json`, `datos/fase1.json` | Histórico | Corpus de 60 oraciones y oraciones de demostración de la Fase 1. |
| `scripts/preparar_modelos.py` | Apoyo | Descarga CESS-ESP y verifica su SHA-256. |
| `scripts/preparar_datos.py` | Histórico | Reconstruye la anotación inicial del corpus histórico; sobrescribe los datos de la Fase 1. |

### 5.5 `tests/`

| Archivo | Rol | Función |
|---|---|---|
| `run_tests.py`, `validos/`, `invalidos/`, `es/` | Apoyo | Casos de archivos (20 de MiniC y 29 de español) con el resultado esperado de cada uno. |
| `test_criterios.py` | Apoyo | Pruebas de los criterios con datos inventados, separadas de los logs reales. |
| `test_correr_fase2.py` | Apoyo | Pruebas del corredor con una salida cruda de juguete (sin spaCy ni CESS-ESP). |
| `test_evaluacion_fase2.py` | Apoyo | Pruebas del evaluador: conteos contra un cálculo independiente, repeticiones, subconjunto diagnóstico, validación de datos y salida determinista. |
| `test_generar_log_parser.py` | Apoyo | Comprueba que el log del parser no duplica registros de una misma corrida. |
| `test_corpus_equivalente.py` | Apoyo | Verifica que el CSV congelado y el JSON del LLM coinciden. |
| `test_experimentos.py`, `test_contratos.py` | Apoyo | Regresiones de corpus, métricas, derivaciones, transporte reanudable y contratos del parser. |

### 5.6 `resultados/`

| Carpeta | Rol | Contenido |
|---|---|---|
| `resultados/evaluacion/` | Núcleo | Salidas del evaluador: `resumen_metricas.csv`, `metricas_por_corrida.csv`, `registros_normalizados.csv`, `clasificacion_errores.csv`, `reporte_metricas.json` y las dos tablas comparativas (`tabla_comparativa_espanol.csv` y `tabla_comparativa_gramatica.csv`, una por etiqueta de referencia, con una fila por herramienta, variante y criterio). En `logs/` están los tres logs de entrada. Las gráficas no se versionan: se generan en la carpeta de salida (sección 6.4). |
| `resultados/fase2/` | Núcleo | Corrida oficial de spaCy y NLTK: `registro.jsonl` (1.608 registros crudos) y `meta.json` (versiones, commit, hashes y verificación). |
| `resultados/llm/corpus-ordenado/` | Núcleo | Corrida de Gemini sobre el corpus actual: respuestas, solicitudes, resumen, comparación y detalle por oración. |
| `resultados/llm/`, `resultados/nlp/`, `resultados/metricas/`, `resultados/fase1/` | Histórico | Salidas de la Fase 1 y del corpus de 60 oraciones. |

## 6. Comandos

Los comandos funcionan desde PowerShell, Bash o Zsh y se ejecutan desde la raíz del repositorio. Las salidas locales se guardan en `.build/`, carpeta ignorada por Git.

### 6.1 Instalación

```sh
git clone --branch master --single-branch https://github.com/Melissaav22/TLP-PROYECTO.git
cd TLP-PROYECTO
git rev-parse HEAD
uv venv --python 3.12.15 .venv-nlp
uv pip sync --python .venv-nlp --require-hashes requirements-experimentos.lock
uv run --python .venv-nlp python scripts/preparar_modelos.py
```

`uv` se instala con `winget install --id=astral-sh.uv -e` (Windows) o `curl -LsSf https://astral.sh/uv/install.sh | sh` (Linux y macOS). El último comando descarga CESS-ESP en `.models/nltk/` y debe imprimir `CESS-ESP coincide con la huella del experimento.` El commit que imprime `git rev-parse HEAD` identifica la versión evaluada.

### 6.2 Pruebas

```sh
uv run --python .venv-nlp python tests/run_tests.py
uv run --python .venv-nlp python tests/run_tests.py --es
uv run --python .venv-nlp python -m unittest discover -s tests -p "test_*.py" -v
```

Salida esperada: 20/20 casos de MiniC, 29/29 casos de español y 71 pruebas `unittest` con resultado `OK`.

### 6.3 Uso del parser

```sh
uv run --python .venv-nlp python main.py tests/validos/v01_declaraciones.c --compacto
uv run --python .venv-nlp python main.py tests/es/validos/v07_subordinada.txt --es --svg .build/arbol.svg
uv run --python .venv-nlp python main.py --tabla
uv run --python .venv-nlp python main.py tests/invalidos/i01_falta_punto_y_coma.c
```

El primer comando imprime un árbol MiniC en formato de corchetes; el segundo, un árbol de español y su SVG; el tercero, FIRST, FOLLOW y la tabla LL(1). El cuarto es un rechazo: informa un error en la línea 4 y termina con código 1. Un análisis correcto termina con 0 y los argumentos inválidos con 2.

### 6.4 Reproducir las métricas de la Fase 2

No requiere clave de Gemini. Usa el corpus congelado y los logs incluidos en el repositorio.

```sh
uv run --python .venv-nlp python -m experimentos.validar_corpus --corpus datos/corpus_ordenado.json
uv run --python .venv-nlp python -m experimentos.evaluacion_fase2 --corpus datos/corpus_fase2.csv --criteria-file datos/criterios_evaluacion_fase2.txt --logs resultados/evaluacion/logs/parser_propio.jsonl resultados/evaluacion/logs/spacy_nltk.jsonl resultados/evaluacion/logs/llm_gemini.jsonl --out .build/evaluacion
git -c core.safecrlf=false diff --no-index --ignore-cr-at-eol --exit-code -- resultados/evaluacion/tabla_comparativa_espanol.csv .build/evaluacion/tabla_comparativa_espanol.csv
git -c core.safecrlf=false diff --no-index --ignore-cr-at-eol --exit-code -- resultados/evaluacion/tabla_comparativa_gramatica.csv .build/evaluacion/tabla_comparativa_gramatica.csv
```

La validación debe informar 67 oraciones y 0 errores. El evaluador debe procesar 1.809 registros (1.608 de spaCy y NLTK, 134 del LLM y 67 del parser), 27 combinaciones y 11 casos en los que difieren las dos etiquetas. Los dos comandos `diff` deben terminar con código 0: comprueban que las tablas regeneradas coinciden con las publicadas. La opción `--ignore-cr-at-eol` compara solo el contenido, porque en Linux y macOS el evaluador escribe los CSV con fin de línea CRLF y el repositorio los guarda con LF. En `.build/evaluacion/` quedan además `reporte_metricas.json` y las gráficas (`graficas/`), que no se incluyen en el repositorio y se regeneran con este mismo comando.

### 6.5 Regenerar los logs y repetir los experimentos

A partir de las evidencias guardadas:

```sh
uv run --python .venv-nlp python -m experimentos.generar_log_parser --output .build/logs/parser_propio.jsonl
uv run --python .venv-nlp python -m experimentos.convertir_logs_fase2 --out .build/logs
uv run --python .venv-nlp python -m experimentos.evaluacion_fase2 --corpus datos/corpus_fase2.csv --criteria-file datos/criterios_evaluacion_fase2.txt --logs .build/logs/parser_propio.jsonl .build/logs/spacy_nltk.jsonl .build/logs/llm_gemini.jsonl --out .build/evaluacion-regenerada
```

Volviendo a ejecutar spaCy y NLTK (3 repeticiones; debe verificar 1.608 registros, con 0 veredictos distintos y 0 pares inestables):

```sh
uv run --python .venv-nlp python -m experimentos.correr_fase2 --ensayo --corpus datos/corpus_fase2.csv --repeticiones 3 --salida .build/fase2
uv run --python .venv-nlp python -m experimentos.generar_log_parser --output .build/fase2/logs/parser_propio.jsonl
uv run --python .venv-nlp python -m experimentos.convertir_logs_fase2 --registro .build/fase2/registro.jsonl --meta .build/fase2/meta.json --out .build/fase2/logs
uv run --python .venv-nlp python -m experimentos.evaluacion_fase2 --corpus datos/corpus_fase2.csv --criteria-file datos/criterios_evaluacion_fase2.txt --logs .build/fase2/logs/parser_propio.jsonl .build/fase2/logs/spacy_nltk.jsonl .build/fase2/logs/llm_gemini.jsonl --out .build/fase2/evaluacion
```

Esta corrida queda marcada como ensayo. El modo oficial exige código y corpus limpios en Git y la etiqueta `criterios-v1`:

```sh
git fetch origin tag criterios-v1
uv run --python .venv-nlp python -m experimentos.correr_fase2 --corpus datos/corpus_fase2.csv --repeticiones 3 --salida .build/fase2-oficial
```

Al repetir un bloque, se usa una carpeta de salida nueva: el generador del parser impide duplicar el número de corrida dentro de un mismo archivo. La corrida original se identifica en `resultados/fase2/meta.json`.

### 6.6 Experimento con Gemini

Sin clave: recalcular las métricas desde las respuestas guardadas y generar las solicitudes.

```sh
uv run --python .venv-nlp python -c "from shutil import copytree; copytree('resultados/llm/corpus-ordenado', '.build/llm-guardado', dirs_exist_ok=True)"
uv run --python .venv-nlp python -m experimentos.resumir_llm --corpus datos/corpus_ordenado.json --input .build/llm-guardado/resultados.json --reporte
```

Para generar las solicitudes sin llamar a la API, primero se copia la configuración (PowerShell: `if (-not (Test-Path .env)) { Copy-Item .env.example .env }`; Linux y macOS: `test -f .env || cp .env.example .env`) y luego:

```sh
uv run --python .venv-nlp python -m experimentos.llm --provider gemini --corpus datos/corpus_ordenado.json --limit 67 --batch-size 10 --max-completion-tokens 8192 --output-dir .build/llm-prompts
```

Se generan 14 solicitudes en `.build/llm-prompts/solicitudes.json`. La evidencia publicada cubre 67 oraciones por variante en 14 lotes exitosos; el log conserva además un intento con HTTP 503 que se reintentó.

Con clave (opcional): requiere una clave de [Google AI Studio](https://aistudio.google.com/api-keys), que la terminal solicita. La disponibilidad, la cuota y los cargos dependen de la cuenta del proveedor, y las respuestas pueden diferir de las publicadas (sección 4).

```sh
uv run --python .venv-nlp python -m experimentos.llm --provider gemini --execute --ask-api-key --corpus datos/corpus_ordenado.json --limit 1 --batch-size 1 --output-dir .build/llm-prueba
uv run --python .venv-nlp python -m experimentos.llm --provider gemini --execute --ask-api-key --corpus datos/corpus_ordenado.json --limit 67 --batch-size 10 --max-completion-tokens 8192 --output-dir .build/llm-nuevo
uv run --python .venv-nlp python -m experimentos.resumir_llm --corpus datos/corpus_ordenado.json --input .build/llm-nuevo/resultados.json --reporte
```

Para reanudar una corrida interrumpida (por ejemplo, tras un HTTP 429), se repite el mismo comando con el mismo modelo, parámetros y carpeta: las respuestas ya recibidas se reutilizan.

### 6.7 Corrida histórica de la Fase 1

El corpus de 60 oraciones y las 120 respuestas de Gemini corresponden a otra versión de la gramática (commit `4b73411`). Se ejecutan en una copia aparte, porque esos scripts escriben directamente en `resultados/`:

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
cd ../TLP-PROYECTO
```

### 6.8 Solo el parser

```sh
uv venv --python 3.12.15 .venv
uv pip sync --python .venv --require-hashes requirements-core.lock
uv run --python .venv python tests/run_tests.py
uv run --python .venv python tests/run_tests.py --es
```

Este entorno mínimo ejecuta las dos suites de archivos. Las 71 pruebas y los experimentos requieren el entorno de la sección 6.1.

## 7. Alcance de la gramática y límites de la evaluación

- **MiniC.** Declaraciones `int`, asignaciones, aritmética, comparaciones, `if/else if/else`, `while` y `for`, con cuerpos entre llaves. Valida sintaxis de fragmentos. Funciones, operadores lógicos, comentarios de bloque, análisis semántico y ejecución quedan fuera.
- **Español controlado.** Se valida desde `Oracion`, con determinante, sujeto nominal y verbo en tercera persona. Incluye presente, pretérito perfecto simple, objeto directo opcional, concordancia de adjetivos, adverbios, sintagmas preposicionales y subordinadas con `que`. Coordinación, pronombres, relativas, imperfecto, sujeto omitido y punto final quedan fuera del subconjunto; son límites de esta gramática, no de toda CFG.
- **Criterios de spaCy y NLTK.** Los resultados dependen de los criterios definidos en la sección 2.3. C2 solo rechaza ante una discordancia explícita: si falta un dato, la comparación queda `indeterminado` y la oración se acepta. `nltk_full` compara solo palabras adyacentes.
- **Etiquetadores de NLTK.** Ambos se entrenaron con todo CESS-ESP; no se midió su exactitud sobre datos apartados.
- **Escala.** El corpus tiene 67 oraciones y no se calcularon intervalos de confianza.
