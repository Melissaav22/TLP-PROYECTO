# Parser LL(1) de MiniC y español ampliado

Esta variante parte de `master` (`f1ccab6`) y se desarrolla en `codex/ampliar-espanol`. Valida fragmentos MiniC y un español controlado; construye árboles, informa errores y permite evaluar categorías gramaticales. El motor predictivo usa una pila y una tabla LL(1).

La ampliación admite objetos directos, nombres de masa habilitados como objeto, sujetos coordinados con `y`, inversión simple de verbo y sujeto y pretérito perfecto simple. El caso principal es:

```text
La niña y el niño comen fruta
```

La referencia de fase 1 se conserva en `datos/fase1.json` y `resultados/fase1/`. Los experimentos de esta variante escriben en `resultados/ampliacion/`.

## Preparación

Requiere Python 3.10 o superior para el parser. La variante se verificó con Python 3.14.6. Ejecutar los comandos desde la raíz del proyecto en PowerShell:

```powershell
py -m venv .venv
uv pip sync --python .venv/Scripts/python.exe --require-hashes requirements-core.lock
```

Si `.venv` ya existe, reutilizarlo. La primera línea crea el entorno y la segunda instala las versiones fijadas con verificación de hashes. Como alternativa a `uv`, puede usarse `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

No es obligatorio activar el entorno: los comandos siguientes utilizan directamente su ejecutable. Si se desea activarlo, ejecutar `.\.venv\Scripts\Activate.ps1`; si PowerShell lo bloquea, `Set-ExecutionPolicy -Scope Process Bypass` permite la activación en esa sesión.

## Demostración y pruebas manuales

```powershell
# Aceptación del caso principal y árbol en una línea
.\.venv\Scripts\python.exe main.py tests/es/validos/v12_coordinacion_mixta.txt --es --compacto

# Rechazo: el sujeto coordinado exige verbo plural
.\.venv\Scripts\python.exe main.py tests/es/invalidos/i09_coordinacion_verbo_singular.txt --es

# Inversión: Come la niña pequeña
.\.venv\Scripts\python.exe main.py tests/es/validos/v21_inversion_singular.txt --es

# Árbol SVG
.\.venv\Scripts\python.exe main.py tests/es/validos/v12_coordinacion_mixta.txt --es --svg resultados/manual.svg
Start-Process .\resultados\manual.svg

# MiniC
.\.venv\Scripts\python.exe main.py tests/validos/v01_declaraciones.c --compacto

# FIRST, FOLLOW y tabla de la gramática unificada
.\.venv\Scripts\python.exe main.py --tabla
```

Para una entrada propia, guardar una oración por archivo en UTF-8 sin BOM y ejecutar:

```powershell
.\.venv\Scripts\python.exe main.py entrada.txt --es
```

`--help` muestra las opciones. `--compacto` serializa el árbol en una línea; `--svg ruta.svg` lo exporta; `-g archivo.txt` o `--gramatica archivo.txt` carga otras reglas con los tokens conocidos por el lexer. El modo español selecciona `Oracion` como raíz. `--tabla` muestra la gramática con la raíz predeterminada `Program`; desde Python, `Grammar(path, start='Oracion')` calcula la tabla con la raíz española.

La salida es 0 al aceptar la entrada, 1 al detectar errores de fuente, gramática o archivos y 2 para argumentos inválidos. Una entrada rechazada puede producir varios diagnósticos al intentar recuperarse del primer fallo. La consola presenta árboles pequeños dibujados y usa corchetes para árboles grandes; la exportación SVG admite hasta 2.000 nodos.

## Construcciones admitidas

| Construcción | Ejemplo |
|---|---|
| Sujeto nominal simple y presente | La niña pequeña canta |
| Objeto directo con determinante | El niño lee el libro |
| Objeto de masa sin determinante | La niña come fruta |
| El mismo sustantivo con determinante | La niña come la fruta |
| Sujeto coordinado | La niña y el niño comen fruta |
| Tres o más miembros coordinados | La niña y el niño y la mujer comen fruta |
| Atributo en coordinación femenina | La niña y la mujer son altas |
| Atributo en coordinación mixta | La niña y el niño son altos |
| Inversión simple | Come la niña pequeña |
| Modificadores en inversión | Come la niña despacio en la casa |
| Pretérito y objeto | El niño leyó el libro |
| Pretérito y coordinación | La niña y el niño comieron fruta |
| Pretérito en inversión | Comieron las niñas pequeñas |
| Subordinada con coordinación | La profesora sabe que la niña y el niño comen fruta |

La coordinación del sujeto exige verbo plural. Para el atributo se utiliza femenino plural si todos los miembros son femeninos y masculino plural si alguno es masculino. Cada miembro conserva su concordancia interna. Las reglas se factorizan después del primer sintagma nominal para decidir entre continuación verbal y `y` sin conflictos LL(1).

`fruta` tiene una categoría explícita para su uso de masa y admite objeto sin artículo. Los singulares contables conservan determinante obligatorio: `El niño lee libro` queda fuera del subconjunto. También se reconoce `las frutas`; los plurales sin determinante, como `come frutas`, quedan fuera de esta entrega.

La inversión se limita a verbo pleno + sujeto simple concordado + modificadores. `Comen la niña y el niño`, `Lee la niña el libro` y las cópulas invertidas requieren ampliaciones adicionales y se rechazan aquí. La variante no pretende cubrir todas las construcciones correctas del español.

El vocabulario incluye presente y pretérito perfecto simple en tercera persona, adjetivos pospuestos, adverbios, preposiciones y `que`. Las cópulas pasadas incluyen `fue/fueron` y `estuvo/estuvieron`; `fue` se interpreta como cópula de `ser` en este subconjunto. Se normalizan acentos a NFC y el español no distingue mayúsculas en la consulta del vocabulario.

El punto final, las preguntas, la negación, los pronombres, las relativas, el imperfecto, los objetos coordinados y la omisión del sujeto siguen fuera del alcance. Las PP sucesivas modifican al sintagma verbal, no al nombre.

MiniC conserva declaraciones `int`, asignaciones, aritmética, comparaciones, `if/else if/else`, `while` y `for` con llaves obligatorias. Admite enteros ASCII en base 10, sin ceros iniciales y de hasta 4.096 dígitos. Las funciones, operadores lógicos, comentarios de bloque y asignaciones encadenadas quedan fuera del alcance. La semántica, los tipos, las declaraciones previas y la ejecución de programas no se comprueban.

## Pruebas automáticas

```powershell
.\.venv\Scripts\python.exe tests/run_tests.py
.\.venv\Scripts\python.exe tests/run_tests.py --es
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Resultados verificados:

- 20/20 casos MiniC.
- 71/71 casos de español: los 19 originales más 52 nuevos (27 válidos y 25 inválidos).
- 24/24 pruebas unitarias. Incluyen matrices de coordinación de dos y tres miembros, concordancia, estructura del árbol, inversión, pasado, aislamiento de MiniC, referencias históricas y la ejecución completa de CLI y métricas.

Una prueba inválida pasa si el parser la rechaza y sitúa el primer error en la línea indicada por `// ESPERA: error en linea N`. Los registros actuales están en `resultados/ampliacion/verificacion/`; los de la base original, en `resultados/ampliacion/base_master/`.

## Evaluación del parser

Los archivos de referencia tienen respuestas esperadas declaradas antes de ejecutar el parser y pendientes de revisión del grupo. Las pruebas verifican integridad, hash de gramática, decisiones y conservación de las etiquetas POS de la muestra comparable.

`datos/ampliacion_es.json` contiene 65 frases: las 13 originales con expectativas CFG adaptadas y 52 ejemplos nuevos. Para recalcular la evaluación ampliada, sin modelos externos:

```powershell
.\.venv\Scripts\python.exe -m experimentos.comparar_nlp --tools parser
.\.venv\Scripts\python.exe -m experimentos.metricas
.\.venv\Scripts\python.exe -m experimentos.registro_fallos
.\.venv\Scripts\python.exe -m experimentos.ambiguedad
```

Las salidas se guardan en `resultados/ampliacion/`. `comparacion.json` contiene las respuestas; `resumen.json`, las métricas; `fallos.json`, tokens, producciones y diagnósticos de todos los casos, incluidos los aceptados. El experimento de ambigüedad exporta dos árboles de una CFG auxiliar y el árbol seleccionado por la gramática LL(1).

Para comparar exactamente las mismas 13 frases y las mismas 73 etiquetas POS de fase 1:

```powershell
.\.venv\Scripts\python.exe -m experimentos.comparar_nlp --corpus datos/comparacion_fase1_ampliada.json --tools parser --output resultados/ampliacion/comparacion_fase1.json
.\.venv\Scripts\python.exe -m experimentos.metricas --corpus datos/comparacion_fase1_ampliada.json --input resultados/ampliacion/comparacion_fase1.json --output resultados/ampliacion/resumen_fase1.json
```

| Muestra | Exactitud POS | Aceptación/rechazo contra su referencia CFG |
|---|---|---|
| Fase 1 original, conservada | 69/73 = 94,52 % | 13/13; 3 aceptadas y 10 rechazadas |
| Variante, las mismas 13 frases | 71/73 = 97,26 % | 13/13; 6 aceptadas y 7 rechazadas |
| Variante, 65 frases | 387/392 = 98,72 % | 65/65; 33 aceptadas y 32 rechazadas |

La mejora sobre las 73 etiquetas corresponde a reconocer `y` y `leyó`. En esa muestra siguen sin reconocerse `astronauta` y el punto. Las expectativas CFG cambian en tres frases: dos con objeto nominal y una con sujeto coordinado. El campo `esperado_cfg_fase1` conserva la decisión anterior en la referencia comparable.

La muestra ampliada tiene otros denominadores y no es una comparación directa con el 69/73. El 100 % CFG mide coincidencia con el subconjunto documentado, no corrección de cualquier oración del español. Las etiquetas de referencia no se obtuvieron de la salida del parser y requieren revisión independiente del grupo.

Las métricas separan exactitud POS, detección binaria de sustantivos y pertenencia CFG. Conservan denominadores, devuelven `null` si no hay denominador y excluyen alineaciones de tokens incompatibles. Las salidas incluyen commit, rama, estado de cambios y hashes de fuentes, corpus y gramática. Si `tracked_changes` es verdadero, el commit identifica la base y los hashes identifican las fuentes modificadas utilizadas.

## Comparación opcional con NLTK y spaCy

El parser requiere NLTK como estructura de árbol, pero no entrena modelos para funcionar. Para ejecutar los adaptadores estadísticos, preparar el entorno experimental de Python 3.12:

```powershell
uv venv --python 3.12 .venv-nlp
uv pip sync --python .venv-nlp/Scripts/python.exe --require-hashes requirements-experimentos.lock
.\.venv-nlp\Scripts\python.exe scripts/preparar_modelos.py
.\.venv-nlp\Scripts\python.exe -m experimentos.comparar_nlp
.\.venv-nlp\Scripts\python.exe -m experimentos.metricas
```

NLTK usa CESS-ESP con unigramas, sufijos y respaldo `NOUN`; spaCy usa `es_core_news_sm`. Los adaptadores entregan `accepted=null`, porque no deciden pertenencia a esta CFG. Se comparan sus etiquetas POS normalizando AUX a VERB y PROPN a NOUN. La evaluación nueva guardada en esta variante ejecutó únicamente el parser propio; las cifras anteriores de NLTK y spaCy siguen siendo históricas.

`python -m experimentos.demo_fase1` ejecuta las tres herramientas sobre las 13 frases con las expectativas de la variante y escribe `resultados/ampliacion/comparacion_fase1.json`. No sobrescribe la referencia original.

## Estructura y referencia histórica

- `main.py`: interfaz de consola.
- `gramatica_minic.txt`: reglas activas de MiniC y español.
- `minic/`: lexer, vocabulario, validación de gramática, FIRST/FOLLOW, parser, diagnósticos y árboles.
- `tests/`: fixtures y contratos unitarios.
- `datos/`: corpus, modelos y referencia comparable.
- `datos/historico/fase1/`: copia de la gramática de fase 1 y manifiesto de hashes con el commit base.
- `experimentos/`: adaptadores, métricas, trazas y ambigüedad.
- `resultados/fase1/`: resultados originales preservados.
- `resultados/ampliacion/`: resultados y verificaciones de esta variante.
- `scripts/preparar_modelos.py`: descarga y verificación de CESS-ESP.
- `PLAN_IMPLEMENTACION_ESPANOL.md`: alcance, orden de trabajo y criterios de aceptación.

La reproducción histórica exacta usa el commit `f1ccab6`, incluido su lexer y su vocabulario. La gramática archivada sirve para comprobar la referencia CFG original, pero usarla con el vocabulario nuevo no reproduce por sí solo las métricas POS antiguas. Una prueba comprueba que el corpus y los resultados originales conservan sus hashes.

La API `parse(source, grammar, spanish=False)` mantiene `(nltk.Tree, list[str])`; `parse_detailed` añade tokens, diagnósticos estructurados y producciones. No fue necesario cambiar el algoritmo del parser para incorporar las nuevas construcciones.
