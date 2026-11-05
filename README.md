# Parser LL(1) para MiniC y español (Proyecto TLP02-2026, Fase 1)

Parser predictivo descendente (LL(1)) dirigido por tabla para **MiniC** (un
subconjunto de C) y para **oraciones del español**, con una sola gramática
unificada. Construye el árbol de análisis como `nltk.Tree` y reporta errores
léxicos y sintácticos con línea y columna.

**Integrantes:** 

## Requisitos e instalación

Python 3.10 o superior.

```bash
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py programa.c             # analiza código MiniC
python main.py programa.c --compacto  # árbol en formato de corchetes
python main.py --tabla                # muestra FIRST, FOLLOW y la tabla LL(1)
python main.py frase.txt --es         # analiza una oración (léxico español)
python tests/run_tests.py             # corre todos los casos de MiniC
python tests/run_tests.py --es        # corre los casos de español
```

`--es` es **obligatorio** para analizar oraciones: activa el lexicón español.
Sin `--es`, el parser trata todas las palabras como identificadores de MiniC.
La gramática es la misma en ambos casos (`gramatica_minic.txt`).

Código de salida: `0` si el análisis es exitoso, `1` si hay errores.

## Estructura

```
gramatica_minic.txt   gramática LL(1) unificada MiniC + español (datos)
main.py               interfaz de línea de comandos
minic/lexer.py        analizador léxico (PLY)
minic/lexicon_es.py   lexicón español: palabra -> token con rasgos
minic/grammar.py      lee la gramática; calcula FIRST, FOLLOW y la tabla M[A,t]
minic/parser.py       parser con pila; construye el árbol; recupera errores
tests/validos/        programas que deben ser aceptados
tests/invalidos/      programas que deben ser rechazados (línea de error esperada
                      en la primera línea de cada archivo)
tests/es/             casos del español (.txt, misma convención)
tests/run_tests.py    ejecuta los casos y muestra una tabla de resultados
```

La gramática está separada del motor y es una sola: la primera regla es
`Program -> StmtList | Oracion`, de modo que se extendió la gramática original
de MiniC en vez de crear otra. Si la gramática no es LL(1), `Grammar` lanza un
error indicando la celda `M[A,t]` en conflicto.

## El subconjunto MiniC

Acepta: declaraciones con inicialización opcional (`int x;`, `int x = e;`),
asignaciones, expresiones aritméticas (`+ - * /` y paréntesis, con la
precedencia usual), condiciones con `< > == <= >= !=`, `if / else if / else`,
`while` y `for`.

**Restricciones respecto a C** (todo programa MiniC válido es también C válido;
MiniC acepta menos programas, no cambia el significado de ninguno):

- El cuerpo de `if`, `else`, `while` y `for` debe ir entre llaves `{ }`.
  Esto evita el *dangling else* (conflicto LL(1): `else` pertenecería a
  FIRST(`else …`) y a FOLLOW(`ElsePart`)).
- Una condición debe tener un operador relacional (`while (x)` no se acepta).
- Solo el tipo `int`, una variable por declaración.
- La asignación es una sentencia, no una expresión (no se acepta `a = b = 3`).
- No hay funciones, `return`, `do-while`, `&&`, `||`, ni comentarios `/* */`.

## Extensión al español

La gramática original de MiniC se extendió en el mismo archivo: la primera
regla pasó de `Program -> StmtList` a `Program -> StmtList | Oracion`, y al
final se añadieron las reglas del español. Ambas ramas son LL(1) porque sus
primeros tokens son disjuntos (`INT/ID/IF/WHILE/FOR` frente a `DET_*`).

El léxico se selecciona por CLI: con `--es`, el lexer consulta
`minic/lexicon_es.py` y emite tokens que ya llevan rasgos morfológicos; sin
`--es`, todas las palabras son `ID` y se analizan como MiniC.

Fenómenos cubiertos y cómo se codifican:

| Fenómeno | Cómo se codifica |
|---|---|
| Concordancia sustantivo-adjetivo | tokens `SUST_MS/FS/MP/FP` y `ADJ_MS/FS/MP/FP`; los no terminales `SN_*` y `Adj*` solo combinan rasgos iguales |
| Concordancia sujeto-verbo | `SV_MS/FS` solo admiten `VERB_3S/COP_3S`; `SV_MP/FP` solo `VERB_3P/COP_3P` |
| Modificadores | adjetivos pospuestos (`AdjMS -> ADJ_MS AdjMS`), adverbios y FPs (`ModsS -> ADV ModsS \| PP ModsS \| eps`) |
| Subordinada | sustantiva de complemento con `que`: `Cpl_MS -> QUE Oracion \| ModsS` |
| Concordancia determinante-sustantivo | `SN_MS -> DET_MS SUST_MS ...` (y las otras tres combinaciones) |

Los verbos son de tercera persona; las oraciones se escriben sin punto final
(el lexer no lo acepta). El lexicón es deliberadamente pequeño: cambiarlo no
requiere tocar la gramática.

**Limitaciones:** no hay objetos directos con sintagma nominal, pronombres,
coordinación, tiempos verbales ni concordancia a larga distancia; el atributo
adjetival solo se admite tras cópula (`ser`/`estar`).

## Decisiones de diseño

- **Sin recursión por la izquierda.** Las reglas del tipo `E → E + T` se
  reescriben como `E → T E'`, `E' → + T E' | ε`, porque un parser descendente
  no puede expandir una regla que empieza por sí misma. Se agrupan niveles
  (`Expr / Term / Factor`) para que `*` y `/` tengan mayor precedencia que
  `+` y `-`.
- **Nota sobre asociatividad:** la gramática acepta exactamente las mismas
  cadenas que la versión con recursión izquierda, pero el árbol anida
  `ExprP` hacia la derecha, de modo que *el árbol no codifica* que `-` y `/`
  son asociativos por la izquierda. Si se evaluara el árbol habría que
  recorrerlo acumulando de izquierda a derecha.
- **Palabras reservadas:** el lexer reconoce primero un identificador y luego
  consulta la lista de reservadas, así `integer` es un `ID` y no `int` + `eger`.
- **Recuperación de errores (modo pánico):** ante un error en un no terminal
  `A`, se descartan tokens hasta uno de FOLLOW(`A`) y se continúa.

## Limitaciones conocidas

- La recuperación de errores es básica: **el primer error reportado siempre
  es confiable; los siguientes pueden ser consecuencia del primero.**
- Sin análisis semántico (no verifica que una variable esté declarada antes de
  usarse; eso no puede expresarse con una gramática libre de contexto).


