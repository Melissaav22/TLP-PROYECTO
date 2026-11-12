# Plan de implementación para ampliar el español del parser

Estado: implementado y verificado en `codex/ampliar-espanol`.

Base: rama `master`, commit `f1ccab6`.

## Objetivo

Ampliar el español controlado para aceptar objetos directos, construcciones de verbo seguido de sujeto y sujetos coordinados con `y`, manteniendo concordancia, análisis LL(1), diagnósticos y compatibilidad con MiniC.

Caso principal de aceptación: `La niña y el niño comen fruta`.

Este caso tiene cuatro componentes: dos sintagmas nominales coordinados como sujeto, un verbo plural y un objeto directo sin determinante. No basta con incorporar `y` y `fruta` al vocabulario.

## Alcance y decisiones

- Mantener los sujetos nominales con determinante obligatorio: `la niña`, `el niño`.
- Permitir dos o más miembros de sujeto unidos por `y`.
- Exigir verbo plural cuando hay coordinación, aunque cada miembro sea singular.
- Mantener concordancia de determinantes y adjetivos dentro de cada miembro.
- Para atributos del sujeto coordinado, usar femenino plural si todos los miembros son femeninos; masculino plural si existe un miembro masculino. Se trata de una política explícita para este subconjunto.
- Permitir objetos con determinante y objetos sin determinante de clases expresamente habilitadas. En la primera entrega, habilitar el uso de masa de `fruta`; no permitir automáticamente cualquier sustantivo singular sin artículo.
- Conservar también `la fruta` y añadir `frutas` al vocabulario. La aceptación de objetos plurales sin determinante se hará en un incremento separado y probado.
- Admitir inicialmente la inversión verbo pleno + sujeto en ejemplos como `Come la niña pequeña` y `Comen las niñas pequeñas`. La combinación de inversión, sujeto coordinado y objeto nominal adicional se evaluará aparte por sus ambigüedades.
- Conservar el punto final fuera de la primera entrega. El caso principal se interpreta sin punto; el soporte de puntuación se planifica después.
- Mantener la validación sintáctica; las restricciones de significado y valencia verbal quedan fuera del alcance.

## Orden de implementación

### 1. Registrar la base y separar las referencias históricas

Archivos: `tests/test_experimentos.py`, `datos/fase1.json`, `resultados/fase1/`, nueva ubicación de referencias históricas y nuevo corpus de ampliación.

1. Crear una rama de trabajo `codex/ampliar-espanol` desde la base comprobada, respetando cambios locales existentes.
2. Ejecutar y registrar los 20 casos MiniC, los 19 de español y las 11 pruebas unitarias actuales.
3. Conservar el corpus y los resultados originales de fase 1, identificados por commit y hash. La reproducción histórica exacta usará ese commit, incluido su lexer y su vocabulario.
4. Ajustar la prueba que actualmente exige que el corpus histórico tenga el hash de la gramática activa: separar la comprobación de la referencia histórica de las expectativas del parser ampliado. Si se archiva la gramática de fase 1, copiarla sin alterar sus bytes y validar su hash.
5. Crear `datos/ampliacion_es.json` con decisiones revisadas para la nueva gramática. No obtener las respuestas esperadas automáticamente de las decisiones del parser.

Criterio de salida: existe una base reproducible y los datos antiguos no se sobrescriben para aparentar una mejora de exactitud.

### 2. Añadir objetos directos con determinante

Archivo principal: `gramatica_minic.txt`.

1. Revisar el cambio de objeto nominal de `origin/feat/fase-dos`, especialmente el commit `2211877`.
2. Adaptar únicamente las reglas necesarias a `master`, sin importar el resto de esa rama de forma indiscriminada.
3. Introducir un no terminal `Objeto` opcional en el complemento de verbos plenos, conservando subordinadas con `que` y modificadores.
4. Admitir objetos cuyo género y número sean independientes del sujeto, con concordancia interna propia.

Ejemplos nuevos: `El niño lee el libro`, `Las niñas compran las flores`, `La profesora sabe que el niño lee el libro`.

Criterio de salida: estos ejemplos se aceptan y la tabla LL(1) se construye sin conflictos tanto desde `Program` como desde `Oracion`.

### 3. Incorporar vocabulario y objetos sin determinante

Archivos: `minic/lexicon_es.py`, `gramatica_minic.txt`, `experimentos/adaptadores.py` si corresponde.

1. Añadir `fruta` y `frutas` con sus rasgos.
2. Representar explícitamente la clase que admite uso de masa sin artículo, por ejemplo mediante un token `SUST_MASA_FS`. Documentar que `fruta` tiene usos contables y de masa.
3. Factorizar las reglas nominales para que esa clase también funcione con determinante: `la fruta`.
4. Permitir esa clase en `Objeto` sin trasladar esa excepción a todos los sujetos ni a todos los sustantivos singulares.
5. Verificar que el adaptador POS traduzca cualquier nuevo token nominal a `NOUN`.

Ejemplos: aceptar `La niña come fruta` y `La niña come la fruta`; seguir rechazando `El niño lee libro` en el subconjunto acordado.

Criterio de salida: la excepción para nombres de masa está acotada y no debilita la concordancia nominal existente.

### 4. Añadir sujetos coordinados

Archivos: `minic/lexicon_es.py`, `gramatica_minic.txt`, `experimentos/adaptadores.py`.

1. Añadir un token específico, como `CONJ_Y`, y asociarlo a `y`.
2. Mapearlo a `CCONJ` en la evaluación POS.
3. Factorizar las oraciones que comienzan por el mismo sintagma nominal. Evitar alternativas independientes `SN SV` y `SN CONJ_Y ...`, porque comparten FIRST y producirían un conflicto LL(1).
4. Tras leer el primer miembro, usar una continuación que distinga el inicio del predicado de `CONJ_Y`.
5. Llevar en los no terminales el estado finito de concordancia: sujeto simple o coordinado y coordinación femenina o con algún miembro masculino.
6. Al aparecer `y`, pasar a un predicado plural; admitir más miembros mediante una continuación por la derecha.
7. Conservar la concordancia de cada miembro y comprobar la de atributos coordinados.
8. Revisar FIRST y FOLLOW en contexto de subordinadas, no solo en oraciones aisladas.

Criterio de salida principal: aceptar `La niña y el niño comen fruta` y rechazar `La niña y el niño come fruta`.

### 5. Añadir inversión de verbo y sujeto

Archivo principal: `gramatica_minic.txt`.

1. Añadir alternativas que comiencen con verbo pleno singular o plural.
2. Restringir los sujetos posteriores según el número del verbo.
3. Reutilizar sintagmas nominales y modificadores sin duplicar toda la gramática.
4. Revisar su interacción con la coordinación antes de ampliar a objetos adicionales o cópulas invertidas.

Ejemplos: aceptar `Come la niña pequeña` y `Comen las niñas pequeñas`; rechazar `Come las niñas pequeñas`.

Criterio de salida: inversión simple y orden habitual funcionan con una sola tabla LL(1), sin reinterpretar concordancias inválidas como objetos.

### 6. Incorporar pasado como incremento posterior

Archivos: `minic/lexicon_es.py`, `gramatica_minic.txt` y pruebas de ampliación.

1. Aprovechar selectivamente las formas y categorías de pretérito de `2211877`.
2. Conservar el tiempo en tokens diferenciados y agrupar presente/pasado en no terminales verbales por número.
3. Probar objetos, coordinación e inversión en pasado antes de declararlos soportados.
4. Mantener el imperfecto fuera de alcance hasta añadir su vocabulario y sus pruebas explícitamente.

Ejemplo: `La niña y el niño comieron fruta`.

## Pruebas de aceptación

Crear fixtures nuevos en `tests/es/validos/` y `tests/es/invalidos/`, además de `tests/test_ampliacion_es.py` para comprobar estructura, concordancia y contratos. En los fixtures inválidos conservar el encabezado de línea esperada que utiliza el ejecutor actual.

| Entrada | Resultado esperado | Motivo |
|---|---|---|
| La niña y el niño comen fruta | Aceptar | Caso principal |
| El niño y la niña comen fruta | Aceptar | Orden de los miembros |
| La niña y la mujer comen fruta | Aceptar | Coordinación femenina |
| La niña y el niño y la mujer comen fruta | Aceptar | Más de dos miembros |
| La niña y el niño come fruta | Rechazar | El sujeto coordinado exige plural |
| La niña y los niño comen fruta | Rechazar | Discordancia dentro de un miembro |
| La niña y comen fruta | Rechazar | Falta un miembro |
| La niña y y el niño comen fruta | Rechazar | Coordinación incompleta |
| La niña y el niño son altos | Aceptar | Atributo masculino plural en coordinación mixta |
| La niña y la mujer son altas | Aceptar | Atributo femenino plural |
| La niña y el niño son altas | Rechazar | Política de concordancia mixta |
| La niña y la mujer son alto | Rechazar | Atributo singular |
| La niña come fruta | Aceptar | Objeto de masa sin artículo |
| La niña come la fruta | Aceptar | La misma palabra con artículo |
| El niño lee el libro | Aceptar | Objeto con determinante |
| El niño lee libro | Rechazar | Singular contable sin artículo, fuera del subconjunto |
| Come la niña pequeña | Aceptar | Inversión simple |
| Comen las niñas pequeñas | Aceptar | Inversión plural |
| Come las niñas pequeñas | Rechazar | Discordancia en inversión |
| La profesora sabe que la niña y el niño comen fruta | Aceptar | Coordinación en subordinada |
| La niña y el niño comieron fruta | Aceptar tras el incremento de pasado | Pretérito plural |

Agregar comprobaciones de árbol para confirmar que la coordinación pertenece al sujeto, que `fruta` pertenece al objeto y que los adjetivos modifican al miembro correcto. Comprobar tokens, posiciones y etiquetas `CCONJ`/`NOUN`.

Los 39 fixtures originales deben seguir pasando, salvo cualquier cambio de alcance que se acuerde explícitamente. Las nuevas pruebas de inversión, masa y coordinación deben incluir pares mínimos válidos e inválidos.

## Evaluación y resultados

Archivos: nuevo `datos/ampliacion_es.json`, `experimentos/comparar_nlp.py`, `experimentos/metricas.py`, `datos/modelos.json` y nuevas salidas en `resultados/ampliacion/`.

- Revisar las expectativas de los casos SVO y de coordinación que ahora pasarán a estar dentro del subconjunto. No modificar la etiqueta de corrección general del español por conveniencia del parser.
- Guardar versión de gramática, corpus, código y commit para cada ejecución nueva.
- Recalcular aceptación/rechazo, exactitud POS y detección de sustantivos por separado.
- Para comparar con el 69/73 original, usar las mismas 13 frases y etiquetas POS, identificando expresamente las expectativas CFG que cambian. Informar aparte las cifras del corpus ampliado.
- No prometer una exactitud nueva antes de ejecutar la evaluación.
- Si solo se evalúa el parser, no es necesario descargar modelos externos. Si se comparan las tres herramientas, preparar el entorno NLP existente.
- Actualizar la referencia de modelo del parser en `datos/modelos.json` cuando corresponda; la actual no coincide con el hash activo.

## Validación final

Desde la raíz del proyecto, una vez preparado el entorno:

```powershell
.\.venv\Scripts\python.exe tests/run_tests.py
.\.venv\Scripts\python.exe tests/run_tests.py --es
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m experimentos.comparar_nlp --corpus datos/ampliacion_es.json --tools parser --output resultados/ampliacion/comparacion.json
.\.venv\Scripts\python.exe -m experimentos.metricas --corpus datos/ampliacion_es.json --input resultados/ampliacion/comparacion.json --output resultados/ampliacion/resumen.json
```

Criterios de cierre:

- La tabla LL(1) no tiene conflictos con ninguna raíz utilizada.
- El caso principal y sus variantes acordadas se aceptan.
- Los pares con discordancias y estructuras incompletas se rechazan.
- MiniC, posiciones de errores, recuperación y exportación de árboles conservan su funcionamiento.
- Las expectativas históricas y nuevas están separadas y son auditables.
- El README documenta estructuras admitidas, límites y comandos de demostración.
- No se sobrescriben los resultados originales ni los archivos personales del usuario.

## Ampliaciones siguientes

Negación, pronombres, adjetivos antepuestos, punto final opcional, interrogativas y relativas se tratarán como incrementos separados. Cada uno requiere definir su alcance, ajustar tokens y reglas, comprobar LL(1) y añadir casos positivos y negativos. No quedan incluidos automáticamente por ampliar objetos o coordinación.

## Resultado de la implementación

- Completadas las seis etapas, incluido el incremento de pretérito perfecto simple.
- El motor de `minic/parser.py` conserva su algoritmo y su API; las nuevas estructuras se resuelven en la gramática y el vocabulario.
- Gramática activa: 72 no terminales, 141 producciones, 298 celdas desde `Program` y 295 desde `Oracion`, sin conflictos LL(1).
- Base registrada antes de editar: 20/20 casos MiniC, 19/19 de español y 11/11 unitarias.
- Verificación de la variante: 20/20 casos MiniC, 71/71 de español y 24/24 pruebas unitarias. Las pruebas de coordinación incluyen combinaciones de dos y tres miembros.
- Añadidos 52 fixtures de español y un corpus de 65 frases con decisiones y etiquetas declaradas antes de ejecutar la variante, pendientes de revisión del grupo.
- La muestra comparable mantiene las mismas 13 frases y 73 etiquetas POS: 71/73 correctas (97,26 %), frente a 69/73 de la base. Cambian tres expectativas CFG por la ampliación de objetos y coordinación.
- El corpus ampliado obtiene 387/392 etiquetas POS (98,72 %) y 65/65 decisiones CFG correctas frente a su referencia. No se equipara esta muestra con la original.
- Se preservaron `datos/fase1.json` y `resultados/fase1/`; los comandos experimentales escriben ahora en `resultados/ampliacion/`.
- Resultados guardados únicamente del parser propio; no se volvió a ejecutar NLTK ni spaCy.
- Los límites de inversión, los nombres de masa habilitados y las ampliaciones pendientes están documentados en el README.
