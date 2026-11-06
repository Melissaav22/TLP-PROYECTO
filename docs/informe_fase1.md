# Gramáticas formales y análisis del español

Informe técnico de la Fase 1 del Proyecto TLP02 2026. Versión del 6 de noviembre de 2026 preparada para revisión de etiquetas, autoría y defensa por el grupo.

El trabajo implementa un parser LL(1) dirigido por tabla para fragmentos MiniC y extiende la misma gramática a un español controlado. El motor produce árboles concretos y diagnósticos con posición. La comparación ejecutada utiliza el parser propio, un etiquetador estadístico NLTK y un pipeline español de spaCy sobre las mismas trece oraciones de demostración.

Los casos demuestran concordancia local, subordinación recursiva y modificadores. También permiten rastrear rechazos hasta tokens o no terminales. Una CFG auxiliar genera dos análisis de una frase preposicional, mientras el subconjunto LL(1) adopta una adjunción determinada. Las conclusiones diferencian una decisión del diseño y una afirmación sobre la capacidad expresiva de todas las CFG.

## Método y evidencia

Se conservaron los veinte fixtures MiniC y los diecinueve del español. Las nuevas pruebas verifican posiciones, recuperación, FIRST/FOLLOW, estructuras de árboles y ejecución CLI. Los resultados de demo y sus trazas están en resultados/fase1. Los hashes de código, gramática y datos permiten identificar la revisión ejecutada aunque existan cambios locales sobre el commit base.

Componente | Implementación

Motor | Pila predictiva y tabla calculada desde producciones

Léxico | PLY y diccionario español con rasgos

Árbol | nltk.Tree, corchetes iterativos y SVG

Comparación | NLTK CESS-ESP y spaCy es_core_news_sm

La anotación es una referencia inicial preparada antes de las predicciones. El grupo debe revisarla y completar la autoría antes de entregar el informe. Los resultados corresponden al conjunto controlado y las tareas descritas en estas páginas.


---


# Motor formal y gramática de MiniC

La clase Grammar carga alternativas, valida símbolos, comprueba productividad y calcula FIRST mediante punto fijo. FOLLOW incorpora FIRST del sufijo y propaga FOLLOW del padre cuando el sufijo es anulable. La tabla selecciona una producción por no terminal y token de anticipación. Una colisión genera GrammarError con la celda implicada.

El parser mantiene símbolos y nodos pendientes en una pila explícita. Una coincidencia terminal consume un token y conserva su lexema como hoja. Una expansión no terminal construye los hijos de la producción. Las alternativas vacías producen la hoja eps. Este procedimiento separa las reglas declaradas del mecanismo que las ejecuta.

```text
Decl -> INT ID DeclTail SEMI
DeclTail -> ASSIGN Expr | eps
Expr -> Term ExprP
ExprP -> PLUS Term ExprP | MINUS Term ExprP | eps
Term -> Factor TermP
TermP -> TIMES Factor TermP | DIVIDE Factor TermP | eps
```

Los niveles Expr, Term y Factor establecen la precedencia aritmética. La forma del árbol conserva las continuaciones derechas introducidas al eliminar recursión izquierda. Un evaluador futuro necesitaría acumular resta y división de izquierda a derecha. En esta entrega se analiza sintaxis y se construye el árbol.

Ante un terminal ausente se registra la posición esperada. Ante un no terminal sin entrada de tabla se descartan tokens hasta FOLLOW o fin de archivo. Los diagnósticos incluyen etapa, código, línea, columna y desplazamiento; su presentación respeta el orden del fuente. Las producciones utilizadas se registran para examinar el recorrido.

MiniC representa fragmentos de sentencias con declaraciones int y estructuras entre llaves. Los literales admitidos son decimales ASCII sin ceros iniciales, conservando la escritura original. La comprobación de declaración previa, tipos y comportamiento de ejecución corresponde a análisis semántico y queda declarada fuera del alcance.


---


# Extensión controlada al español

La rama española utiliza Oracion como entrada efectiva. Esta selección impide que una declaración MiniC o la cadena vacía se interpreten como una oración. El lexer consulta un vocabulario finito y asocia las palabras a categorías que codifican género y número. La consulta normaliza NFC y mayúsculas sin modificar las posiciones del texto original.

Fenómeno | Codificación de la gramática

Concordancia nominal | SN_MS, SN_FS, SN_MP y SN_FP combinan determinante, nombre y adjetivo compatibles

Sujeto y verbo | VerboSG y VerboPL restringen tercera persona

Subordinación | QUE Oracion permite inclusión recursiva

Modificadores | Adjetivos pospuestos, ADV y PREP SN

Tiempos y objeto | Presente, pretérito perfecto simple y SN objeto opcional

La duplicación de categorías por un número finito de rasgos permite expresar la concordancia elegida dentro de una CFG. El crecimiento de reglas es un costo de mantenimiento observable. La subordinación también usa recursión de producciones y admite más de un nivel. La prueba de dos niveles comprueba tres nodos Oracion en el árbol.

Las frases preposicionales sucesivas se adjuntan al sintagma verbal. El fixture denominado históricamente pp_anidada contiene dos PP hermanas. Se conserva como regresión y se añade una aserción estructural para hacer explícita esa interpretación. La gramática auxiliar de ambigüedad permite además una adjunción nominal.

El vocabulario excluye pronombres, coordinación, relativas e imperfecto. El punto final también está fuera de esta versión. Todos los verbos plenos comparten los complementos permitidos y la gramática no comprueba valencia semántica. Esas decisiones se registran para interpretar las etiquetas del corpus y las diferencias con un analizador general.


---


# Fallos trazables y jerarquía de Chomsky

El registro de cada caso conserva texto, etiqueta esperada, fenómeno, tokens, producciones y diagnósticos. El primer punto de fallo identifica un símbolo inesperado o una palabra ausente del vocabulario. Esta trazabilidad permite explicar por qué se acepta o rechaza una entrada concreta y revisar la regla responsable.

Caso | Resultado y clase de limitación

La niño corre | Rechazo por incompatibilidad DET_FS y SUST_MS

Los niños corre | Rechazo de verbo singular tras sujeto plural

El astronauta lee el libro | Rechazo léxico por nombre fuera del vocabulario

El niño y la niña corren | Rechazo por coordinación fuera de la CFG definida

Una CFG de tipo 2 expande un único no terminal en cada producción. Su reconocimiento se relaciona con autómatas de pila. Los patrones regulares forman el nivel tipo 3, y las gramáticas sensibles al contexto forman el tipo 1. La clasificación se refiere a familias de cadenas y al mecanismo necesario para reconocerlas, con las convenciones usuales sobre la cadena vacía.

La familia abstracta a^n b^n c^n ofrece un contraste formal. En un argumento de bombeo con longitud p, la ventana de hasta p símbolos dentro de a^p b^p c^p no puede abarcar simultáneamente un a y un c. Bombear modifica como máximo dos bloques o rompe el orden, dejando sin mantener la igualdad de los tres conteos. Esa familia queda fuera de las CFG.

El contraste anterior ilustra una prueba sobre una familia formal. Para trasladarla a una construcción del español se necesitaría definir esa familia lingüística y justificar una reducción o un argumento equivalente. Los ejemplos finitos de esta entrega acreditan límites del subconjunto implementado. La concordancia finita y la subordinación observadas sí están codificadas mediante CFG [1, 2].


---


# Comparación ejecutada y ambigüedad

La demo ejecutó trece frases idénticas en los tres sistemas, con identificadores compartidos y sin errores de ejecución. NLTK entrena unigramas con respaldo por sufijos sobre CESS-ESP. spaCy utiliza es_core_news_sm 3.8.0. La tarea común utiliza etiquetas POS gruesas, agrupando AUX con VERB y PROPN con NOUN.

Sistema | Tokens POS | Exactitud POS | Tiempo ms

nltk | 73 | 95.89% | 0.051

parser | 73 | 95.89% | 0.687

spacy | 73 | 98.63% | 10.691

El parser coincidió con las trece etiquetas de pertenencia al subconjunto de la demo. Los adaptadores externos aportan POS y, en spaCy, dependencias y morfología. accepted permanece sin valor en esos adaptadores porque su tarea no emite una decisión de pertenencia a esta CFG. El informe identifica por separado procesamiento, etiquetado y aceptación.

La oración La mujer vive en la casa de la ciudad se procesó además mediante nltk.ChartParser con una CFG auxiliar que permite NP con PP y VP con PP. La ejecución produjo exactamente dos derivaciones. En una, de la ciudad modifica el nombre casa. En la otra, aparece como otra PP del predicado. Ambas derivaciones y sus SVG quedaron guardados.

La existencia de esos dos árboles muestra ambigüedad estructural dentro de una CFG [2]. La gramática LL(1) del proyecto elige PP verbales sucesivas. Las dos decisiones tienen consecuencias en el árbol aunque acepten la misma cadena. La demo permite examinar esta diferencia con resultados obtenidos por ejecución.


---


# Conclusiones y reproducción de la Fase 1

El motor formal y su extensión española producen resultados trazables y conservan los ejemplos originales. Las categorías morfológicas permiten verificar concordancia local, y la producción recursiva permite subordinación. Los rechazos por coordinación, palabras nuevas o puntuación identifican el alcance actual de la implementación.

La comparación proporciona evidencia de diferencias de etiquetado y de interpretación estructural. La CFG auxiliar representa dos adjunciones, mientras el parser predictivo sigue una política explícita. El análisis formal distingue esas decisiones de diseño de una demostración general sobre el lenguaje español. El grupo debe revisar esta interpretación y defender los argumentos con las producciones y árboles disponibles.

## Comandos de demostración

```text
python tests/run_tests.py
python tests/run_tests.py --es
python -m experimentos.registro_fallos
python -m experimentos.demo_fase1
python -m experimentos.ambiguedad
```

Las instalaciones y modelos se describen en README.md y los archivos requirements con hashes. Los datos de demo están en datos/fase1.json. Los resultados y las dos derivaciones auxiliares están en resultados/fase1. Las pruebas de contrato y de experimentos usan unittest y se verificaron en Python 3.10 y 3.12.

## Referencias y revisión

[1] NLTK Book, capítulo 9, Building Feature Based Grammars. https://www.nltk.org/book/ch09.html

[2] NLTK Book, capítulo 8, Analyzing Sentence Structure. https://www.nltk.org/book/ch08.html

[3] spaCy, pipelines entrenados para español. https://spacy.io/models/es

[4] Especificación docente TLP02-2026, Fase 1, archivo suministrado por el solicitante. Autoría, etiquetas y exposición requieren revisión final del grupo.


---
