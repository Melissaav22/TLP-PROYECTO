# Estado de implementación del plan

Historial de ramas: `ExtensionEspañol` → `feat/fase-uno` → `feat/fase-dos`.
La primera rama conserva la gramática de fase 1 y sus resultados propios. Esta
rama añade SVO y pasado, actualiza la referencia de la demo y contiene ambas
fases. Los commits se separan por dependencias, correcciones, funcionalidades,
pruebas y documentación con el formato Conventional Commits 1.0.0.

Actualizado el 6 de noviembre de 2026 sobre la base Git c2dcd47 y los cambios
locales identificados en los resultados. La auditoría del 5 de noviembre queda
como fotografía anterior al desarrollo.

## Resultado local

- 39 fixtures originales aprobados, 20 MiniC y 19 español.
- 15 pruebas nuevas de contratos y experimentos aprobadas en Python 3.10 y 3.12.
- 90 sondas de la auditoría anterior aprobadas, frente a las 19 brechas originales.
- Corpus de 60 frases, 20 por nivel, con 33 positivas y 27 negativas CFG.
- 180 análisis reales con parser, NLTK CESS-ESP y spaCy es_core_news_sm.
- Demo de Fase 1 sobre 13 frases y 39 análisis.
- Dos derivaciones de una CFG auxiliar para la frase de las PP.
- Métricas, tablas CSV, gráficas y ocho mediciones de tamaño guardadas.
- Informes de 6 y 8 páginas, con fuentes Markdown.
- Presentaciones editables de 10 y 12 diapositivas con notas.
- Cliente LLM, prompts y validación de derivaciones implementados.

La referencia POS y las etiquetas lingüísticas se prepararon antes de las
predicciones y requieren revisión del grupo. La decisión de dejar la ejecución
API pendiente fue confirmada por el usuario. No hay respuestas de proveedor ni
una comparación LLM zero-shot/few-shot ejecutada.

Las salidas NLP conservan la procedencia de sus corridas originales. El
validador LLM `experimentos/validar_derivacion.py` se endureció después de esas
corridas; por eso su huella histórica difiere del archivo actual. Los
adaptadores, la gramática y los datos utilizados por NLP conservan sus huellas.
Las pruebas de derivaciones verifican la versión actual del validador.

## Estado por bloque

| ID | Estado de ejecución | Evidencia |
|---|---|---|
| T01 | Verificado en código | Diagnósticos ordenados, columna, configuración/E/S y pruebas de regresión |
| T02 | Verificado en código | Raíz española, reservadas C y literales decimales |
| T03 | Verificado en código | Serialización iterativa, SVG y aserciones estructurales |
| T04 | Datos y análisis preparados para revisión | datos/fase1.json, resultados/fase1/fallos.json e informe Fase 1 |
| T05 | Ejecutado con herramientas reales | resultados/fase1/comparacion.json, 39 análisis sin errores |
| T06 | Artefactos preparados | Informe de 6 páginas, presentación y guía reproducible; falta revisión/ensayo/entrega |
| T07 | Verificado en código | SVO, presente y pretérito perfecto simple, concordancia y modificadores |
| T08 | Corpus preparado para revisión humana | 60 entradas, niveles, POS y separación de ejemplos verificados automáticamente |
| T09 | Ejecutado con herramientas reales | 180 análisis, versiones, datos originales y tiempos |
| T10 | Ejecutado y contrastado | Matriz de confusión, clasificación de errores, CSV y PNG |
| T11 | Integración preparada, API pendiente acordada | 120 solicitudes y validación; prueba local de transporte/reanudación |
| T12 | Paquete local preparado, cierre externo pendiente | Locks, instalación limpia, resultados, informes y presentaciones |

## Decisiones de implementación

La comparación común de los tres sistemas utiliza POS grueso y detección de
NOUN frente al resto. La pertenencia a la CFG se evalúa para el parser y se
evaluará para el LLM cuando se ejecute. Los adaptadores NLTK/spaCy mantienen
accepted sin valor. Esta definición evita atribuirles una decisión de rechazo
que sus salidas no contienen.

Se eligieron presente y pretérito perfecto simple. Las PP son modificadores
verbales sucesivos. Los verbos comparten complementos sintácticos permitidos,
con la valencia semántica declarada fuera del modelo actual. Los números MiniC
son decimales ASCII sin ceros iniciales y de hasta 4.096 dígitos.

El resultado 60/60 del parser corresponde al oro inicial controlado. La tabla
POS anotada favorece al lexer propio en el vocabulario compartido. Las cifras
requieren revisión de etiquetas y un corpus ampliado para generalizarse.

## Pendientes para declarar cierre académico

1. Revisar etiquetas, estructuras y fenómenos con el grupo.
2. Revisar el argumento formal y su alcance sobre CFG y español.
3. Completar integrantes y autoría de informes y presentaciones.
4. Ensayar y verificar la duración de 15–20 minutos por exposición.
5. Ejecutar la API LLM cuando el responsable lo decida, incorporar logs y
   regenerar su comparación, costo y sección de resultados.
6. Confirmar compartición, entrega y defensa ante el docente.

## Documentos y resultados

- docs/informe_fase1.pdf y docs/informe_fase1.md
- docs/informe_fase2.pdf y docs/informe_fase2.md
- docs/presentacion_fase1.pptx y docs/presentacion_fase2.pptx
- docs/trazabilidad_requisitos.json
- resultados/fase1 y resultados/nlp
- resultados/metricas y resultados/verificacion
- resultados/llm/estado.json

Los informes y las diapositivas fueron renderizados y revisados visualmente.
Las presentaciones pasaron validación de paquete, geometría, fuentes y
reimportación. La revisión se realizó con el renderer del runtime, sin una
sesión nativa de PowerPoint.

En este host, el proceso del generador PPTX devolvió 1 al finalizar, después
de emitir los dos recibos satisfactorios. Se verificaron por separado los
SHA-256 de ambos archivos, la reimportación y todos sus renders. Esta anomalía
del cierre del proceso sigue pendiente de resolver para automatizar la
regeneración del PPTX con un código de salida confiable.

## Regeneración de documentos

El código fuente de los PDF está en scripts/generar_informes.py y sus
dependencias en requirements-documentos.txt. Se ejecutó con el Python
proporcionado por el runtime de documentos.

El generador de PPTX usa @oai/artifact-tool del runtime de Codex.
CODEX_PRESENTATIONS_SKILL debe apuntar a la habilidad instalada de
presentaciones. Los archivos finales existentes se deben conservar y la
regeneración se valida en un destino nuevo. Las fuentes, datos y notas
también permanecen editables dentro de las presentaciones entregadas.
