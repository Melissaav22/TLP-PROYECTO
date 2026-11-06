# Parser de español y evaluación experimental

Informe de la Fase 2 del Proyecto TLP02 2026. Versión del 6 de noviembre de 2026 para revisión del grupo. La sección de ejecución LLM permanece pendiente por decisión del usuario.

La implementación incorpora SVO, presente y pretérito perfecto simple a la gramática controlada. El corpus contiene sesenta oraciones distribuidas en tres niveles. Se ejecutaron el parser propio, un etiquetador estadístico NLTK y spaCy sobre todas las entradas, obteniendo ciento ochenta análisis sin errores de ejecución.

El parser coincide con las treinta y tres etiquetas positivas y veintisiete negativas iniciales de pertenencia CFG. La exactitud POS en los 361 tokens de referencia fue de nltk 94.18%, parser 98.34%, spacy 98.61%. Estas cifras corresponden a una anotación preparada para revisión y al vocabulario y fenómenos de este conjunto.

Dimensión | Evidencia guardada

Corpus | 60 frases, 20 por nivel, ejemplos few-shot separados

Comparación | 180 resultados, versiones y tiempos

Métricas | Matriz de confusión CFG y POS común

LLM | 120 solicitudes preparadas, cero respuestas de proveedor

Las tareas se evalúan con contratos separados. El parser decide pertenencia al subconjunto. NLTK y spaCy aportan etiquetas y dependencias; su éxito técnico no define aceptación bajo la CFG. La comparación común utiliza POS grueso y detección de NOUN, con denominadores idénticos. Los errores de ejecución se contabilizan aparte.

El paquete conserva datos, código, configuración y resultados para regenerar tablas y figuras. El cierre académico requiere revisión de etiquetas, autoría y exposición, además de completar el experimento API cuando el responsable lo autorice.


---


# Diseño de la gramática y contratos

La entrada española es Oracion y la raíz efectiva determina FOLLOW y la tabla predictiva. Esto evita aceptar vacío o fragmentos MiniC como frases. La clase Grammar valida producciones, epsilon, símbolos y productividad. FIRST y FOLLOW se obtienen por punto fijo y los conflictos de tabla se reportan con la celda correspondiente.

```text
Oracion -> OracionSG | OracionPL
SV_MS -> VerboSG Cpl_MS | CopulaSG PredCpl_MS
VerboSG -> VERB_3S | VERB_PAST_3S
Cpl_MS -> QUE Oracion | Objeto ModsS
Objeto -> SN | eps
PP -> PREP SN
```

Las variantes femeninas y plurales completan la concordancia nominal y verbal. Las formas de pasado tienen tipos de token propios, por lo que el tiempo permanece identificable en los resultados. El objeto se representa como un nodo Objeto que contiene SN cuando aparece. Se verifican positivos y negativos en ambos tiempos.

El análisis es sintáctico. Los verbos plenos comparten las opciones de complemento y el modelo no verifica plausibilidad ni valencia semántica. Las PP se adjuntan al sintagma verbal. La coordinación, relativas, pronombres, imperfecto y puntuación final están fuera del subconjunto elegido.

La API parse conserva árbol y lista de mensajes. parse_detailed añade diagnósticos con posición, tokens y traza de producciones. La serialización en corchetes usa una pila y tolera profundidad grande. La salida SVG permite inspeccionar las relaciones; su límite de nodos se informa mediante un error controlado.

Caso | Evidencia estructural

El niño lee el libro | Objeto contiene un SN después del verbo

Los niños leyeron los libros | Token VERB_PAST_3P y sujeto plural

La casa fue blanca | Cópula de pasado y atributo femenino singular


---


# Corpus y anotación de referencia

Las sesenta oraciones se prepararon antes de las predicciones de los adaptadores. Cada entrada guarda ID, texto, nivel, fenómeno, esperado_cfg, corrección general, tokens y POS de referencia. La versión de gramática y el hash del corpus identifican el conjunto evaluado. El estado de revisión humana permanece pendiente del grupo.

Nivel | Cantidad | Fenómenos

Simple | 20 | Sujeto, verbo, SVO, concordancia y pasado

Intermedio | 20 | Adjetivos, adverbios, PP y variaciones

Complejo | 20 | Subordinadas, errores distantes y construcciones fuera del subconjunto

Hay treinta y tres etiquetas positivas y veintisiete negativas para pertenencia CFG. Una frase correcta del español puede tener etiqueta negativa si utiliza un pronombre, una relativa, un tiempo o una palabra fuera del vocabulario. Por ejemplo, El astronauta lee el libro es correcta en español general y queda fuera del lexicón controlado.

La anotación POS usa categorías amplias y una tabla léxica explícita, independiente de las predicciones de NLTK y spaCy. Este procedimiento favorece al lexer propio en las palabras que comparte con esa tabla; se declara como característica del conjunto y justifica ampliar y revisar el oro antes de generalizar las cifras.

Los tres ejemplos few-shot tienen IDs y textos distintos del conjunto evaluado. El validador comprueba tamaño mínimo, niveles, duplicados, etiquetas y versión de gramática. Los cambios manuales deben conservarse en Git. Volver a ejecutar el constructor de datos restablece deliberadamente la anotación inicial y exige revisar los resultados asociados.


---


# Herramientas y metodología de comparación

NLTK 3.10.4 entrena un UnigramTagger sobre 6030 oraciones y 192686 tokens de CESS-ESP. Utiliza un AffixTagger de sufijos de tres caracteres y NOUN como respaldo final. El archivo descargado queda identificado por SHA-256. El corpus experimental no se usa para entrenar el etiquetador.

spaCy 3.8.18 carga es_core_news_sm 3.8.0, que aporta POS, dependencias, lemas y morfología. Se guarda la salida original necesaria para revisar diferencias. Los modelos y su ámbito de entrenamiento difieren del vocabulario reducido del proyecto [1, 2].

Los tres sistemas procesan los mismos IDs. Las etiquetas se normalizan agrupando AUX con VERB y PROPN con NOUN. La detección nominal es una tarea binaria por token, donde NOUN es la clase positiva. Sobre ella se calculan precisión, recall y tasa de rechazo correcto. También se calcula exactitud POS global.

Para pertenencia CFG se calculan TP, FP, TN y FN sobre frases. Esa tarea se aplica al parser y se aplicará al LLM cuando existan respuestas. Los adaptadores externos mantienen accepted sin valor. La salida diferencia una decisión lingüística, un desalineamiento de tokens y un fallo técnico.

Los tiempos por oración usan perf_counter con modelos ya cargados y entrenamiento excluido. La inicialización se registra por separado. Son mediciones locales de una ejecución; la carga del sistema y el hardware afectan su valor. Los datos incluyen plataforma, versiones, hashes y parámetros para describir el contexto.

Sistema | Precisión NOUN | Recall NOUN | Rechazo NOUN

nltk | 97.27% | 97.27% | 98.80%

parser | 100.00% | 99.09% | 100.00%

spacy | 98.21% | 100.00% | 99.20%


---


# Resultados cuantitativos obtenidos

La evaluación POS utiliza 361 tokens de referencia en todos los sistemas. El parser conserva una X para símbolos fuera de su léxico en esta tarea, incluida la puntuación no admitida, para mantener un denominador común. Los errores de tokenización se registran y el conjunto actual no presenta desalineamientos.

Sistema | Tokens POS | Exactitud POS | Tiempo ms

nltk | 361 | 94.18% | 0.013

parser | 361 | 98.34% | 0.685

spacy | 361 | 98.61% | 5.189

![resultados/metricas/exactitud_pos.png](resultados/metricas/exactitud_pos.png)

En pertenencia CFG el parser obtuvo TP=33, TN=27, FP=0 y FN=0 en la anotación inicial. Precisión, recall y rechazo correcto son 1,00 en ese conjunto. La selección controlada y la revisión humana pendiente limitan la interpretación externa de este resultado.

La comparación de POS incluye una regla léxica controlada, un baseline estadístico entrenado y un pipeline general. Las diferencias deben interpretarse junto con el tipo de tarea y el origen de las etiquetas. La tabla completa por nivel y la clasificación de errores se conservan en resultados/metricas.


---


# Errores y comportamiento experimental

El resumen clasifica falsos positivos, falsos negativos, errores POS, desalineamientos y errores de ejecución. La pertenencia CFG no produjo FP/FN sobre la referencia inicial. Los errores POS permiten revisar palabras desconocidas y diferencias de clase. La anotación debe revisarse antes de concluir qué decisión es lingüísticamente preferible.

Lenguaje | Tamaño | Tiempo medio ms

minic | 10 | 0.470

minic | 100 | 1.947

minic | 500 | 14.369

minic | 1200 | 27.832

espanol | 1 | 0.958

espanol | 5 | 0.652

espanol | 10 | 0.771

espanol | 25 | 1.333

Se midieron cinco repeticiones por tamaño con gramática cargada. MiniC se evaluó hasta 1.200 declaraciones y español hasta 25 niveles de subordinación. Todos esos análisis se aceptaron. La desviación temporal de cada grupo está guardada en rendimiento.json. Las medidas describen parsing y no incluyen dibujar árboles.

En robustez se verifican caracteres ilegales, palabras nuevas, formatos numéricos, concordancia y selección de lenguaje. La ambigüedad preposicional se examina con dos derivaciones de una CFG auxiliar sobre la misma frase. El parser propio sigue su política de PP verbales. El número de categorías crece al codificar rasgos finitos, un costo de mantenimiento visible al extender el subconjunto.


---


# Experimento LLM preparado

El usuario indicó preparar la integración y mantener pendiente la ejecución API. Se generaron ciento veinte solicitudes, sesenta zero-shot y sesenta few-shot. El directorio LLM conserva el estado prepared y cero respuestas reales. La comparación de precisión entre variantes sigue pendiente.

Cada prompt proporciona el símbolo Oracion, las producciones españolas y el lexicón. La respuesta solicitada es un objeto JSON con accepted y una lista ordenada de expansiones izquierdas. Few-shot añade tres ejemplos de un archivo separado; los ejemplos positivos contienen derivaciones completas verificadas por el parser.

El validador comprueba que cada no terminal se expanda en el orden correspondiente, que la alternativa exista y que los terminales coincidan con la entrada. Incluye epsilon y comprueba consumo completo. Un rechazo se contrasta con el reconocimiento formal. Se conserva el razonamiento de validación junto con el acierto o fallo de decisión.

El cliente usa un endpoint HTTPS Chat Completions compatible, con modelo, clave y configuración definidos en el entorno. Registra el prompt, la respuesta original, tokens y costo estimado si el responsable suministra tarifas. La huella de solicitud permite reanudar llamadas completadas. Los secretos quedan excluidos de los archivos.

La prueba automatizada del transporte ejecuta un servidor HTTP local y comprueba reanudación y ausencia de claves en logs. Es evidencia de integración de software. Los resultados del LLM requieren llamadas reales al proveedor y se incorporarán mediante experimentos.resumir_llm cuando se ejecute el experimento.

```text
python -m experimentos.llm
# Tras configurar proveedor, modelo y clave local
python -m experimentos.llm --execute --max-new-calls 2
python -m experimentos.resumir_llm
```


---


# Conclusiones y condiciones de cierre

El desarrollo incorpora los mínimos sintácticos SVO y dos tiempos, además de concordancia, modificadores y subordinación. El conjunto experimental tiene sesenta frases y permite reproducir ciento ochenta análisis con datos por sistema y nivel. Las métricas separan la pertenencia al subconjunto de las tareas POS comparables.

Las cifras obtenidas respaldan el comportamiento del modelo controlado sobre la anotación inicial. El grupo debe revisar oro, adjunción, valencia y casos fuera del vocabulario antes de ampliar las conclusiones. La comparación LLM y su efecto zero-shot/few-shot permanecen pendientes y no se les asignan cifras.

El cierre requiere completar esa ejecución cuando el responsable lo decida, regenerar sus métricas, actualizar la discusión de costo y robustez, registrar integrantes y ensayar la presentación. El repositorio contiene instrucciones, locks con hashes y resultados reales locales. Se verificaron pruebas del núcleo en Python 3.10 y 3.12 y un entorno experimental limpio de Python 3.12.

## Reproducción y referencias

```text
python -m experimentos.validar_corpus
python -m experimentos.comparar_nlp
python -m experimentos.metricas
python -m experimentos.graficas
python -m experimentos.rendimiento
```

[1] NLTK, etiquetadores secuenciales y lectores de corpus. https://www.nltk.org/api/nltk.tag.sequential.html

[2] spaCy, modelos españoles. https://spacy.io/models/es

[3] NLTK Book, capítulos 8 y 9, estructura, ambigüedad y rasgos. https://www.nltk.org/book/

[4] OpenAI, contrato Chat Completions. https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create

[5] Especificación docente TLP02-2026, Fase 2, archivo suministrado por el solicitante. El grupo revisará autoría, etiquetas y defensa antes de entrega.


---
