# Auditoría técnica y de cumplimiento — MiniC

Fecha: **3 de noviembre de 2026** (America/El_Salvador). Revisión: `7936cabb9ec146746215b5674867f1e16ce2bf1e`. Especificación: [README.md:1](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:1), elegida expresamente por el solicitante al confirmar que la ruta inicial era un marcador. No se encontró otro archivo de requisitos ni instrucciones `AGENTS.md` aplicables.

## 1. Resumen Ejecutivo

**Porcentaje global de avance y cumplimiento: 83,21%.** El núcleo de análisis está implementado y los 20 ejemplos originales pasan. El cierre técnico queda condicionado por incumplimientos de compatibilidad léxica con C, diagnósticos incompletos, fallos de presentación de fuentes válidas y ausencia de pruebas originales de la CLI y contratos internos.

Se identificaron **32 requisitos: 13 cumplidos y 19 parciales; ninguno completamente ausente**. No se encontraron funcionalidades sustituidas por mocks o handlers vacíos. Este porcentaje es una valoración técnica trazable de los requisitos, no una medición de horas ejecutadas ni una probabilidad de ausencia de defectos.

### Alcance y método de evaluación

Se leyeron todos los archivos de producto, la gramática, el README, las dependencias y los 20 fixtures. Se siguió el flujo real de datos y se ejecutaron la suite original, medición de cobertura y **90 sondas adicionales**. De estas últimas, **71 satisfacen su expectativa y 19 exponen brechas**; varias corresponden a una misma causa, por lo que no equivalen a 19 defectos independientes. Las sondas de auditoría se conservan separadas y no se cuentan como pruebas preexistentes al puntuar la madurez.

Se aplican los intervalos solicitados: 0% ausente; 1–50% esqueleto o soporte incompleto; 51–85% funcional con faltantes o sin pruebas específicas; 86–100% cumplido con pruebas asociadas y validación del flujo evaluado. Las filas superiores a 85% tienen casos originales asociados y verificación de código; no se otorga 100% mientras queden límites o contratos sin cerrar. Ejecutar una línea no sustituye una aserción sobre su resultado.

La ponderación representa criticidad: **5** para garantías críticas, **4** para capacidades centrales, **3** para funciones del lenguaje y **2** para soporte/operación. Los pesos se muestran en la matriz y no representan prioridades de negocio entregadas por el usuario.

```text
Cumplimiento = Σ(peso × porcentaje) / Σ(peso)
             = 9.070 / 109
             = 83,211009...% → 83,21%
```

El cálculo y los valores por requisito están en [auditoria/matriz_cumplimiento.json](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/auditoria/matriz_cumplimiento.json). No se promedia el porcentaje de tests aprobados ni la cobertura para producir esta cifra.

### Arquitectura, stack e integraciones

Arquitectura de **aplicación CLI modular, ejecutada en un único proceso**, con fases de compilador: carga de gramática → lexer → parser predictivo → presentación del árbol. La separación corresponde a módulos de responsabilidad; no hay capas de dominio/repositorio ni estructura suficiente para denominarla Clean Architecture o MVC. No hay microservicios, frontend web, monorepo de aplicaciones ni servicio desplegable declarado.

```text
main.py
  ├─ Grammar(archivo)
  │    ├─ carga y validación de símbolos
  │    └─ FIRST → FOLLOW → tabla M[A,t]
  └─ parse(fuente, Grammar)
       ├─ tokenize(fuente) con PLY
       ├─ pila y consulta de tabla
       ├─ nltk.Tree + lista de diagnósticos
       └─ pretty_print / representación en corchetes
```

| Elemento | Evidencia y resultado |
|---|---|
| Runtime | Python ≥3.10 declarado; ejecución auditada con CPython 3.14.8 en Windows. |
| Dependencias directas | `ply==3.11`, `nltk==3.10.4`; instalación exacta exitosa en un entorno virtual local. |
| Configuración | `requirements.txt`, `.gitignore`; sin `pyproject.toml`, paquete instalable, Dockerfile o configuración de CI en la revisión. |
| Gramática | 22 no terminales, 44 producciones y 82 celdas de tabla; los conteos ejecutados se conservan en los resultados de las sondas. |
| Integraciones reales | PLY y NLTK como bibliotecas locales; lectura de archivos UTF-8 y escritura de consola mediante biblioteca estándar. |
| Red y persistencia | No hay llamadas de red, base de datos, ORM, credenciales de servicio ni persistencia de entidades. No son obligaciones del README. |
| Pruebas | Ejecutor propio y 9 fuentes válidas + 11 inválidas; sin suites unitarias ni e2e de CLI originales. |
| Reproducibilidad | Dependencias directas fijadas; las transitivas no tienen archivo de bloqueo. El entorno efectivamente instalado se adjunta. |

### Contratos y datos identificados

No existen endpoints HTTP ni entidades persistidas que deban auditarse como API o modelo de base de datos. Los contratos del producto son:

| Contrato / dato | Implementación real |
|---|---|
| `Grammar(path)` | `rules` como diccionario de alternativas, `start`, conjuntos `nonterminals/first/follow` y tabla indexada por `(no_terminal, token)`. |
| `tokenize(source)` | Lista de tuplas `(tipo, lexema, línea, columna)` con EOF `$`; errores léxicos como `(línea, carácter)`, sin columna. |
| `parse(source, grammar)` | Tupla `(nltk.Tree, list[str])`; árbol parcial con `<error>` o `<falta TOKEN>` ante errores. |
| Interfaz CLI | Fuente posicional, `--compacto`, `--tabla` y opción adicional `-g/--gramatica`; códigos de salida y texto de consola. |

No exigir base de datos, autenticación, API o análisis semántico evita penalizar funciones ajenas al alcance. La verificación de declaración previa de variables está **excluida expresamente** por README:87–88. La asociatividad de resta/división se documenta como limitación del árbol y no hay evaluador que deba implementarla en esta fase.

### Calidad y riesgos de cierre

La separación entre lexer, gramática y parser es clara; FIRST/FOLLOW usan punto fijo, la tabla detecta conflictos, el motor evita recursión de llamadas y la reserva de palabras completas evita partir `integer`. El código es pequeño y legible.

La deuda se concentra en contratos: diagnósticos como cadenas, pérdida de posición de errores léxicos, conversión prematura de literales, validación incompleta de gramáticas y excepciones que alcanzan al usuario. El principal cuello de botella es que los ejemplos aprobados no comprueban la semántica de los tokens, el contenido del árbol ni la CLI.

## 2. Matriz de Cumplimiento de Requisitos

Las referencias del README permiten rastrear la extracción completa. Los enlaces de código apuntan al inicio de la implementación pertinente; las líneas adicionales se mantienen en la etiqueta cuando corresponde.

| ID | Requerimiento / Feature y origen | Peso | Archivo(s) de código fuente | Estado | % Cumplimiento | Evidencia técnica / faltantes |
|---|---|---:|---|---|---:|---|
| REQ-01 | Python ≥3.10 e instalación declarada. [README.md:11-16](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:11) | 2 | [requirements.txt:1](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/requirements.txt:1); [main.py:8](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:8) | Parcial / funcional | 85% | Instalación exacta correcta en Python 3.14.8; no hay matriz de versiones ni validación del mínimo 3.10. |
| REQ-02 | Tokenización mediante PLY. [README.md:35,78-79](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:35) | 3 | [minic/lexer.py:2,61,68](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:2) | Parcial / funcional | 85% | PLY real, regex, clon por análisis y EOF; tests de aceptación y un carácter ilegal. Faltan contratos unitarios de tokens; límites numéricos y compatibilidad C en REQ-27. |
| REQ-03 | Gramática separada y cambio de lenguaje por datos. [README.md:33,44-46](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:33) | 3 | [minic/grammar.py:23,42](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:23); [main.py:21](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:21) | Parcial / funcional | 75% | Cambiar producciones dentro del alfabeto de tokens funciona. Tokens nuevos exigen editar lexer.py; la carga admite formatos incoherentes y falla con gramática vacía. |
| REQ-04 | Cálculo de FIRST y nulabilidad. [README.md:36](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:36) | 4 | [minic/grammar.py:53,70](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:53) | Parcial / funcional | 85% | Algoritmo de punto fijo funcional; sonda con no terminales anulables correcta. La suite original no compara conjuntos esperados. |
| REQ-05 | Cálculo de FOLLOW. [README.md:36](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:36) | 4 | [minic/grammar.py:83](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:83) | Parcial / funcional | 85% | Propaga FIRST del sufijo y FOLLOW del padre; oráculo independiente de gramática pequeña correcto. Sin aserciones dedicadas originales. |
| REQ-06 | Tabla LL(1) y conflicto con celda M[A,t]. [README.md:36,45-46](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:36) | 4 | [minic/grammar.py:105](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:105) | Parcial / funcional | 85% | Construye tabla real y rechaza conflictos FIRST/FIRST y FIRST/FOLLOW indicando celda. Sin pruebas originales de conflictos. |
| REQ-07 | Parser predictivo descendente dirigido por tabla y pila. [README.md:3,37](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:3) | 5 | [minic/parser.py:18,24,43,64](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:18) | Cumplido | 95% | Consume tokens y expande producciones reales; 20 casos originales pasan; 1.200 declaraciones se analizan sin recursión del motor. |
| REQ-08 | Construcción de árbol nltk.Tree. [README.md:4,37](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:4) | 4 | [minic/parser.py:3,18,47,61](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:3) | Parcial / funcional | 85% | Árbol concreto con hojas y eps comprobado en sondas. Las pruebas originales descartan el árbol y no verifican su contrato. |
| REQ-09 | Declaraciones con inicialización opcional. [README.md:50](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:50) | 3 | [gramatica_minic.txt:15](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:15); [minic/parser.py:43](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:43) | Cumplido | 95% | Ambas variantes operan; v01 y negativos i01/i09 las ejercitan. Sin análisis semántico por exclusión expresa. |
| REQ-10 | Asignaciones. [README.md:51](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:51) | 3 | [gramatica_minic.txt:17](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:17); [minic/parser.py:43](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:43) | Cumplido | 95% | AssignCore exige ID = Expr y punto y coma; casos válidos y i11 rechazan expresión ausente. |
| REQ-11 | Aritmética, paréntesis, precedencia y árbol sin recursión izquierda. [README.md:51-52,68-77](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:51) | 5 | [gramatica_minic.txt:35](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:35); [minic/parser.py:64](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:64) | Parcial / funcional | 85% | Expr/Term/Factor correctos; sondas verifican agrupación y ExprP a la derecha, tal como se documenta. v02 solo verifica aceptación, no estructura. |
| REQ-12 | Seis operadores relacionales. [README.md:52](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:52) | 3 | [minic/lexer.py:22](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:22); [gramatica_minic.txt:31](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:31) | Cumplido | 95% | < > == <= >= != operativos; distribuidos en v03-v07 y corroborados individualmente por sondas. |
| REQ-13 | if / else if / else y anidamiento. [README.md:52](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:52) | 4 | [gramatica_minic.txt:21](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:21); [minic/parser.py:43](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:43) | Cumplido | 95% | ElseTail permite bloque o If; v03/v07 y negativos i03/i04 verifican flujos y errores. |
| REQ-14 | while. [README.md:53](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:53) | 3 | [gramatica_minic.txt:24](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:24) | Cumplido | 95% | Operativo en v04/v07; i07 comprueba condición inválida y i08 bloque incompleto. |
| REQ-15 | for completo y opciones de inicialización/paso. [README.md:53](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:53) | 4 | [gramatica_minic.txt:25](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:25) | Cumplido | 95% | ForInit acepta declaración/asignación/eps y ForStep asignación/eps; v05/v06 e i06. Condición vacía no declarada como obligatoria en README. |
| REQ-16 | Cuerpos de control con llaves y resolución de else. [README.md:58-60](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:58) | 3 | [gramatica_minic.txt:21,24,25,28](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:21) | Cumplido | 95% | Block obligatorio; i03 y sondas rechazan cuerpos sin llaves. else if es la alternativa explícita permitida. |
| REQ-17 | Condiciones con comparación obligatoria. [README.md:61](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:61) | 3 | [gramatica_minic.txt:31](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:31) | Cumplido | 95% | Cond exige Expr RelOp Expr; i07 rechaza while(x). |
| REQ-18 | Solo int y una variable por declaración. [README.md:62](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:62) | 3 | [gramatica_minic.txt:15](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:15); [minic/lexer.py:4](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:4) | Parcial / funcional | 85% | Producción única y sin coma; sondas rechazan float x e int x,y. Faltan negativos dedicados en suite original. |
| REQ-19 | Asignación solo como sentencia, sin encadenamiento. [README.md:63](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:63) | 3 | [gramatica_minic.txt:18,31,39](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:18) | Parcial / funcional | 85% | Factor/Expr no incluyen asignación; sondas rechazan a=b=3 y asignación en condición. Sin casos originales específicos. |
| REQ-20 | Excluir funciones, return, do-while, &&, || y comentarios de bloque. [README.md:64](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:64) | 3 | [gramatica_minic.txt:12,39](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:12); [minic/lexer.py:7](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:7) | Parcial / funcional | 85% | Constructos rechazados en sondas; sin batería original de exclusiones. Palabras C usadas como ID constituyen la brecha separada REQ-27. |
| REQ-21 | Comentarios de línea y programa vacío. [README.md:38; tests/validos/v08_solo_comentarios.c:1](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:38) | 2 | [minic/lexer.py:46](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:46); [gramatica_minic.txt:11](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:11) | Cumplido | 95% | Comentarios se descartan y StmtList admite eps; v08 y sondas con vacío/comentario intercalado pasan. |
| REQ-22 | Reconocer reservadas después del identificador completo. [README.md:78-79](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:78) | 3 | [minic/lexer.py:32](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:32) | Cumplido | 95% | reserved.get sobre ID completo; v09 comprueba integer, iffy, format y elsewhere. Reservadas ajenas a MiniC se evalúan en REQ-27. |
| REQ-23 | Errores léxicos con línea y columna. [README.md:4-5](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:4) | 5 | [minic/lexer.py:56](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:56); [minic/parser.py:15](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:15) | Parcial / funcional | 60% | Se conserva línea/carácter pero se pierde lexpos/columna; el mensaje de @ carece de col. i05 únicamente compara línea. |
| REQ-24 | Errores sintácticos con línea y columna. [README.md:4-5](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:4) | 4 | [minic/lexer.py:64](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:64); [minic/parser.py:38,52](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:38) | Cumplido | 90% | Mensajes incluyen posición actual y esperado; 11 negativos originales validan línea y una sonda verifica columna. Falta contrato estructurado. |
| REQ-25 | Recuperación en modo pánico mediante FOLLOW. [README.md:80-81](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:80) | 4 | [minic/parser.py:50](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:50) | Parcial / funcional | 85% | Descarta hasta FOLLOW(X) o EOF y continúa; recupera declaración posterior. Originales solo comprueban primera línea, sin aserciones de recuperación. |
| REQ-26 | Confiabilidad del primer error reportado. [README.md:85-86](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:85) | 5 | [minic/parser.py:15](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:15) | Parcial / funcional | 60% | La tokenización completa antepone todos los errores léxicos. En entrada con sintaxis rota en línea 1 y @ en línea 2, el primer diagnóstico es de línea 2; la localización es real pero no la primera del fuente. |
| REQ-27 | MiniC como subconjunto de C sin alterar significado. [README.md:55-56](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:55) | 5 | [minic/lexer.py:4,32,40,78](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:4); [gramatica_minic.txt:10](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/gramatica_minic.txt:10) | Parcial / esqueleto | 40% | Acepta int return;, int x=08; y dígitos Unicode; 010 se convierte en 10. Además acepta sentencias a nivel raíz: debe definirse compatibilidad de fragmentos, pues no son unidades de traducción C. |
| REQ-28 | CLI de análisis y presentación del árbol. [README.md:22](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:22) | 2 | [main.py:18,39,49](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:18) | Parcial / funcional | 75% | Salida textual pretty_print funcional en entrada corta. Fuente válida de 1.200 declaraciones provoca RecursionError al presentar; archivos inexistentes producen traceback; sin tests CLI originales. |
| REQ-29 | CLI --compacto en formato de corchetes. [README.md:23](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:23) | 2 | [main.py:25,46](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:25) | Parcial / funcional | 75% | Imprime representación nltk.Tree en casos normales, puede ocupar varias líneas. Falla por RecursionError con fuente válida extensa; sin pruebas CLI originales. |
| REQ-30 | CLI --tabla con FIRST, FOLLOW y M[A,t]. [README.md:24](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:24) | 2 | [main.py:23,34](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:23); [minic/grammar.py:124](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:124) | Parcial / funcional | 85% | Las tres secciones se imprimen con éxito en sonda; show no se ejecuta en tests originales. |
| REQ-31 | Contrato CLI: 0 éxito y 1 error. [README.md:28](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:28) | 3 | [main.py:29,37,41,51](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:29) | Parcial / funcional | 70% | 0/1 se respetan en fuente válida/inválida; GrammarError retorna 2, distinto de README. OSError, KeyError, ValueError y RecursionError escapan sin diagnóstico controlado. |
| REQ-32 | Ejecutor de casos válidos/ inválidos y línea esperada. [README.md:25,38-41](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/README.md:25) | 3 | [tests/run_tests.py:28](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/tests/run_tests.py:28) | Cumplido | 90% | 9 válidos + 11 inválidos: 20/20; tabla y salida 0/1 implementadas. Metadatos de fixtures no se validan estrictamente; faltan pruebas unitarias/CLI, no exigidas como cantidad por README. |
| **TOTAL** | **32 requisitos** | **109** | | **13 cumplidos / 19 parciales** | **83,21% ponderado** | **Σ(peso × porcentaje) = 9.070** |

En REQ-27, el 40% refleja soporte parcial de una promesa transversal: existe la base léxica/sintáctica, pero se contradicen garantías centrales del subconjunto C. No significa que todo el parser sea un esqueleto.

## 3. Hallazgos Técnicos Clave

### H-01 — Alta: se aceptan palabras clave de C como identificadores

**Evidencia:** [minic/lexer.py:4](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:4) y [minic/lexer.py:32](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:32). Solo `int/if/else/while/for` están reservadas; el resto de palabras clave se convierten en ID.

```c
int return;
int float;
int do;
int switch;
```

Cada entrada anterior produce cero errores en `parse`. El lenguaje omite las construcciones `return` o `do-while`, pero también debe impedir usar sus palabras clave como identificadores si se mantiene la compatibilidad C. Las palabras clave no pueden funcionar como identificadores en C. [Referencia primaria: Microsoft, C Keywords](https://learn.microsoft.com/en-us/cpp/c-language/c-keywords?view=msvc-170).

**Impacto:** falsos positivos y contradicción de README:55–56. **REQ-27.** Sondas `c_keyword_return/float/do/switch`.

### H-02 — Alta: literales aceptados fuera de C y pérdida de su representación

**Evidencia:** [minic/lexer.py:40](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:40) convierte `t.value` mediante `int()`; [minic/lexer.py:78](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:78) reconstruye luego el texto con `str()`.

| Entrada | Resultado observado | Problema |
|---|---|---|
| `int x = 08;` | Aceptada; NUM queda como `8`. | Una constante octal C no admite el dígito 8. |
| `int x = 010;` | Aceptada; NUM y hoja quedan como `10`. | El literal original es octal y representa 8; se pierde su escritura y se introduce una representación decimal de otro valor. |
| `int x = ١;` (U+0661) | Aceptada; NUM queda como `1`. | `\\d+` admite dígitos Unicode fuera del alfabeto de constantes enteras C usado como referencia. |

En C, el prefijo cero indica octal y sus dígitos van de 0 a 7. [Referencia primaria: Microsoft, C Integer Constants](https://learn.microsoft.com/en-us/cpp/c-language/c-integer-constants?view=msvc-170).

El producto no evalúa expresiones; **no se afirma que exista un resultado de ejecución incorrecto**. El defecto demostrado es la aceptación de entradas incompatibles y la alteración del literal representado en el árbol, que impide garantizar preservación de significado si se consume ese árbol. **REQ-27**, con efecto sobre el contrato de árbol de REQ-08.

### H-03 — Alta: los errores léxicos omiten la columna

**Evidencia:** [minic/lexer.py:56](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:56) conserva únicamente línea/carácter; [minic/parser.py:16](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:16) forma el mensaje sin columna.

```text
Fuente:   int x = @1;
Obtenido: Linea 1: caracter ilegal '@'
Esperado: posición con línea 1 y columna 9
```

La columna sí se calcula para tokens válidos, de modo que el problema está en el contrato de errores, no en la inexistencia de infraestructura de posición. `i05` solo valida línea y permite que la omisión pase inadvertida. **REQ-23.** Sonda `lexical_error_has_column`.

### H-04 — Alta: el primer diagnóstico no sigue el orden del fuente

**Evidencia:** [minic/parser.py:15](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/parser.py:15) tokeniza toda la entrada y antepone todos los errores léxicos antes de analizar sintaxis.

```c
int = 1;
int x = @2;
```

Resultado real:

```text
Linea 2: caracter ilegal '@'
Linea 1, col 5: se esperaba ID pero llego '='
```

Ambas localizaciones corresponden a errores reales. La contradicción con la garantía del primer error en README:85–86 es su orden y utilidad para localizar el fallo inicial; no se ha demostrado que ese mensaje léxico sea falso. El runner compara `errores[0]`, por lo que el orden afecta directamente a su contrato. **REQ-26.** Sonda `first_error_source_order`.

### H-05 — Alta: fuentes válidas fallan al presentar el árbol

**Evidencia:** [main.py:46](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:46) usa `print(tree)` y [main.py:49](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:49) usa `tree.pretty_print()`. La recursión derecha de `StmtList` acumula profundidad por sentencia.

Una fuente con `int x;\n` repetido **1.200 veces** es aceptada por `parse`, pero ambas modalidades CLI terminan con `RecursionError: maximum recursion depth exceeded`. Se repiten declaraciones deliberadamente: el análisis semántico está fuera del alcance y el programa es válido según esta gramática.

El parser iterativo funciona; la falla ocurre al serializar/presentar el árbol a través de NLTK. No hay un tamaño máximo documentado ni un tratamiento controlado del límite. El umbral observado depende del runtime y no se extrapola como límite universal. **REQ-28/29.** Sondas `long_valid_source_compact/pretty` y observación `long_source_parse_without_render`.

### H-06 — Alta: contrato de salida inconsistente y excepciones sin manejar

**Evidencia:** [main.py:29](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:29) solo captura `GrammarError`; devuelve 2. [main.py:39](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/main.py:39) abre la fuente sin capturar errores de E/S.

| Escenario reproducido | Resultado |
|---|---|
| Fuente válida / inválida normal | Salida 0 / 1, respectivamente. |
| Gramática con conflicto LL(1) | Diagnóstico controlado, pero salida **2**, frente al 1 documentado para errores. |
| Fuente o gramática inexistente | `FileNotFoundError` y traceback; salida 1 del intérprete. |
| Gramática vacía | `KeyError: None` en FOLLOW y traceback. |
| Literal de 5.000 dígitos | `ValueError` en `int(t.value)` y traceback; límite observado de 4.300 dígitos en este runtime. |
| Fuente válida extensa | `RecursionError` durante la salida del árbol. |

Tener salida 1 por una excepción sin capturar no constituye manejo robusto del contrato. La conversión de grandes enteros sucede en el lexer antes de poder emitir diagnósticos. **REQ-01/03/28/29/31**, sin convertir cada escenario en un requisito adicional.

### H-07 — Media: validación incompleta de la gramática configurable

**Evidencia:** [minic/grammar.py:23](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:23), [minic/grammar.py:58](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:58) y [minic/grammar.py:85](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:85).

- Archivo vacío: llega a `FOLLOW[None]` y lanza `KeyError`, en lugar de `GrammarError`.
- `S -> eps NUM`: se acepta la carga; FIRST trata `eps` como final de secuencia, mientras el parser solo lo reconoce como producción vacía si la alternativa completa es `[eps]`. Los dos módulos no interpretan igual esa entrada.
- ` -> ID`: se acepta un lado izquierdo vacío.
- `S -> S`: se acepta sin producción productiva; se registra como carencia de validación de productividad, no como demostración de un conflicto de tabla ignorado.

La carga sí rechaza flechas ausentes, alternativas vacías, reglas repetidas, símbolos desconocidos y conflictos de tabla cuando existen. Las sondas verificaron estos rechazos reales. **REQ-03/06** y robustez del contrato de configuración.

### H-08 — Media: dos promesas del README requieren delimitarse

**Cambio de lenguaje:** README:44–45 afirma que editar la gramática basta. [minic/grammar.py:44](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:44) limita los terminales a `lexer.tokens`; agregar palabras clave, operadores o tipos de token exige cambiar [minic/lexer.py:4](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:4) y sus reglas. La separación real permite variar la gramática **sobre el alfabeto léxico existente**. La sonda con `S -> ID` confirma ese caso válido. **REQ-03.**

**Compatibilidad C:** `Program -> StmtList` acepta asignaciones, `if`, `while` y `for` al nivel raíz, mientras se excluyen funciones. El README parece describir fragmentos de cuerpo de función, pero los denomina programas C válidos. En C, una unidad de traducción se compone de declaraciones externas y definiciones, no de sentencias de control sueltas. [Referencia primaria: Microsoft, Source Files and Source Programs](https://learn.microsoft.com/en-us/cpp/c-language/source-files-and-source-programs?view=msvc-170). Esta comparación es una inferencia aplicada a la gramática inspeccionada.

La exclusión expresa de análisis semántico también impide garantizar compilabilidad completa. Se requiere distinguir compatibilidad **léxica/sintáctica de fragmentos** de validez de programas C completos. No corresponde añadir funciones o análisis semántico sin una revisión explícita del alcance. **REQ-27.**

### H-09 — Alta: la suite prueba aceptación, pero deja contratos centrales sin aserciones

**Evidencia:** [tests/run_tests.py:32](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/tests/run_tests.py:32) descarta el árbol y comprueba ausencia de errores. En [tests/run_tests.py:42](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/tests/run_tests.py:42) se extrae la línea esperada de los negativos y se compara solo la primera línea reportada.

No hay tests originales que comprueben valores exactos de FIRST/FOLLOW, conflictos de tabla, árbol/precedencia/asociatividad, columnas, recuperación hasta una sentencia posterior, orden mixto de diagnósticos, CLI, gramáticas alternativas o fallos de E/S. Esos flujos fueron comprobados mediante las sondas de esta auditoría; estas no reparan las brechas del producto.

| Archivo de producto | Líneas ejecutables cubiertas | Cobertura de líneas | Ramas cubiertas | Cobertura de ramas |
|---|---:|---:|---:|---:|
| `main.py` | 0 / 36 | 0,00% | 0 / 12 | 0,00% |
| `minic/grammar.py` | 96 / 110 | 87,27% | 57 / 68 | 83,82% |
| `minic/lexer.py` | 44 / 44 | 100,00% | 0 / 0 | N/A |
| `minic/parser.py` | 45 / 45 | 100,00% | 21 / 22 | 95,45% |
| **Total producto** | **185 / 235** | **78,72%** | **78 / 102** | **76,47%** |

La medición corresponde exclusivamente a `tests/run_tests.py`, incluye código de producto sin ejecutar y excluye las sondas añadidas y el propio runner. `minic/__init__.py` no tiene sentencias ejecutables. Coverage muestra un **78,04% combinado** de líneas y ramas; no debe confundirse con el 78,72% de líneas ni con el 83,21% de cumplimiento.

La cobertura de 100% del lexer y de líneas del parser no impide los defectos demostrados: ejecutar código no verifica todos sus contratos. La falta de negativos sobre exclusiones, asignación encadenada y tipos adicionales explica las puntuaciones de hasta 85% pese a que las sondas los rechazaron correctamente.

### Lógica mockeada, incompleta y exclusiones

La búsqueda de `TODO/FIXME/HACK/mock/stub/NotImplemented` no encontró implementaciones pendientes en el producto. Los dos `pass` son legítimos: el cuerpo de [GrammarError](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/grammar.py:7) y [el descarte de comentarios](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/minic/lexer.py:46). No hay respuestas hardcodeadas que simulen análisis: la gramática, tabla y árbol se construyen realmente.

Como observaciones de alcance, `for (;;) {}`, `int x = -1;` y un bloque autónomo se rechazan. El README no promete expresamente condición vacía del `for`, operadores unarios ni bloques sueltos; por ello **no se califican automáticamente como funcionalidades ausentes**. Conviene documentarlos para evitar extrapolar toda la sintaxis de C al subconjunto.

### Evidencias y reproducción

Los archivos siguientes permiten revisar el diagnóstico sin modificar el código original:

- [auditoria/verificar_auditoria.py](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/auditoria/verificar_auditoria.py): 90 sondas y caracterizaciones; usa archivos temporales y subprocess para CLI.
- [auditoria/resultados_sondas.json](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/auditoria/resultados_sondas.json): expectativas y resultados, excepciones y metadatos de ejecución.
- [auditoria/salida_sondas.txt](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/auditoria/salida_sondas.txt): salida resumida de la última ejecución.
- [auditoria/pruebas_existentes.txt](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/auditoria/pruebas_existentes.txt): 20/20 casos originales.
- [auditoria/cobertura_existente.json](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/auditoria/cobertura_existente.json) y [auditoria/cobertura_existente.txt](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/auditoria/cobertura_existente.txt): cobertura exclusiva de la suite original.
- [auditoria/entorno_auditoria.txt](C:/Users/Cristopher-Diaz-TDW/Desktop/TLP-PROYECTO/auditoria/entorno_auditoria.txt): versiones instaladas, incluyendo Coverage 7.17.1 como herramienta de auditoría.

Desde la raíz, en PowerShell:

```powershell
.\.venv\Scripts\python.exe tests/run_tests.py
.\.venv\Scripts\python.exe auditoria/verificar_auditoria.py

# Coverage es herramienta de auditoría, no dependencia del producto.
.\.venv\Scripts\python.exe -m pip install coverage==7.17.1
.\.venv\Scripts\python.exe -m coverage run --branch --source=. '--omit=tests/*,auditoria/*,.venv/*' --data-file=auditoria/.coverage tests/run_tests.py
.\.venv\Scripts\python.exe -m coverage report --data-file=auditoria/.coverage -m
.\.venv\Scripts\python.exe -m coverage json --data-file=auditoria/.coverage -o auditoria/cobertura_existente.json
```

El script de sondas devuelve 0 al completar la recopilación, incluso si hay expectativas incumplidas: es una herramienta de diagnóstico. El campo `failed` de su JSON y el resumen de consola indican las brechas; no debe conectarse a CI como si ese código de salida certificara conformidad.

Solo se verificó ejecución en Python 3.14.8/Windows. El mínimo 3.10 y otros sistemas operativos quedan sin validar; no se declaran incompatibles. No se ejecutó un compilador C como oráculo: las discrepancias léxicas se contrastaron con referencias primarias y comportamiento observado. No se midió rendimiento para afirmar un SLA ni se realizó una revisión de vulnerabilidades publicadas de dependencias.

## 4. Roadmap Priorizado de Remediación

“Bloqueante” indica una decisión/garantía que impide certificar el cumplimiento del README; no implica que el programa no arranque.

| Prioridad | Acción concreta | Requisitos / hallazgos | Criterio verificable de cierre |
|---|---|---|---|
| **Bloqueante** | Precisar en la especificación si se analizan fragmentos de cuerpo C o unidades completas; delimitar la afirmación de validez C y la ausencia de semántica. Mantener esa decisión versionada. | REQ-27; H-08 | README y gramática describen el mismo tipo de entrada; no quedan promesas incompatibles con la exclusión de funciones/semántica. Cambiar el alcance requiere aceptación explícita del responsable del producto. |
| **Alta** | Reservar o rechazar todas las palabras clave del estándar C adoptado, conservando la coincidencia completa de identificadores. | REQ-22/27; H-01 | `int return;`, `int float;`, `int do;` y `int switch;` se rechazan; `integer/iffy` siguen aceptándose; tests permanentes. |
| **Alta** | Conservar lexema numérico original; usar alfabeto ASCII y definir política decimal/octal compatible con el alcance. Validar el literal completo antes de aceptarlo. | REQ-08/27; H-02 | `08` y U+0661 se rechazan; `010` se rechaza por estar fuera del subconjunto o se conserva correctamente, sin reinterpretarlo como decimal 10; tests verifican tokens y hojas. |
| **Alta** | Unificar diagnósticos en datos con etapa, posición absoluta, línea, columna y mensaje; ordenar o emitir en orden del fuente. | REQ-23/24/26; H-03/H-04 | `@` reporta columna 9; la fuente mixta reporta primero el fallo de línea 1; casos con varios errores verifican posiciones y orden. |
| **Alta** | Hacer la salida de árbol tolerante a profundidad mediante serialización iterativa y una estrategia de presentación adecuada; definir límites explícitos si son necesarios. | REQ-28/29; H-05 | La fuente de 1.200 declaraciones se analiza y presenta sin traceback en ambas modalidades dentro del alcance anunciado; añadir regresión CLI. |
| **Alta** | Manejar errores de archivos, codificación, gramática y límites numéricos con diagnósticos de usuario; alinear códigos de salida al contrato documentado. | REQ-01/03/31; H-06 | Fuente/gramática inexistentes, gramática vacía, conflicto y literal largo tienen salida controlada y código documentado; los 0/1 de análisis normal se mantienen. |
| **Alta** | Incorporar pruebas permanentes de FIRST/FOLLOW y tabla con oráculos pequeños, árbol/precedencia, recuperación y CLI; convertir las regresiones confirmadas de esta auditoría en aserciones del proyecto. | REQ-04/05/06/08/11/25/28-32; H-09 | Los defectos actuales hacen fallar los tests antes de corregirlos; después pasan los nuevos contratos y los 20 fixtures existentes. La CLI deja de tener cobertura cero. |
| **Media** | Rechazar gramática vacía, lado izquierdo inválido y `eps` mezclado; validar productividad y símbolos especiales con errores claros. | REQ-03/06; H-07 | Todas las gramáticas malformadas tienen `GrammarError` contextual; las alternativas anulables válidas y conflictos controlados conservan su comportamiento. |
| **Media** | Documentar que la parametrización gramatical usa tokens existentes o hacer configurable también el lexer si se mantiene una extensibilidad mayor. | REQ-03; H-08 | Una gramática alternativa demostrada funciona sin editar el motor; la documentación explicita cuándo hay que cambiar reglas léxicas. |
| **Media** | Automatizar pruebas en el mínimo Python 3.10 y una versión actual soportada; fijar dependencias transitivas con un mecanismo reproducible. | REQ-01/32 | Instalación limpia y tests pasan en la matriz anunciada; se puede reconstruir el entorno sin depender de resoluciones transitivas futuras. |
| **Media** | Añadir negativos permanentes para tipos, declaraciones múltiples, encadenamiento y construcciones excluidas; documentar límites de `for`, operadores unarios y bloques. | REQ-18/19/20/32 | La suite comprueba las restricciones explícitas y el README evita expectativas no acordadas sobre el resto de C. |

Para certificar el 100%, cada fila debe demostrar implementación y contratos completos dentro de un alcance coherente, con regresiones permanentes, ejecución satisfactoria de los flujos críticos y sin las brechas anteriores. No se exige añadir persistencia, endpoints o análisis semántico que la especificación no contempla.
