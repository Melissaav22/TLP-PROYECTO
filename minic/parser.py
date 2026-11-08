"""Parser predictivo LL(1) con pila explícita.

Usa la tabla de análisis de la gramática para elegir qué producción aplicar,
construye el árbol como nltk.Tree y se recupera de los errores en modo pánico
(con los conjuntos FOLLOW)."""
from nltk import Tree
from .grammar import EPS
from .lexer import tokenize
from .diagnostics import Diagnostic
from dataclasses import dataclass


@dataclass
class ParseResult:
    """Resultado de analizar una entrada.

    tree: árbol de análisis (parcial si hubo errores).
    diagnostics: errores léxicos y sintácticos, ordenados por posición.
    tokens: lista de (tipo, lexema, línea, columna), terminada en '$'.
    productions: producciones aplicadas, en orden, con el token que decidió cada una.
    """

    tree: Tree
    diagnostics: list
    tokens: list
    productions: list

    @property
    def accepted(self):
        """True si no hubo ningún error."""
        return not self.diagnostics


def parse_detailed(source, grammar, spanish=False):
    """Analiza `source` con la gramática dada y devuelve un ParseResult.

    Se usa una pila: se saca el símbolo de la cima; si es un terminal debe
    coincidir con el token actual, y si es un no terminal se consulta la tabla
    con ese token para elegir la producción, cuyos símbolos se apilan.

    Con errores el árbol queda parcial: donde no había producción aplicable
    el nodo lleva la hoja '<error>', y un terminal que falta aparece como
    '<falta TOKEN>'.

    Con spanish=False se usa el léxico de MiniC (las palabras son ID).
    Con spanish=True se usa el léxico del español y se analiza desde Oracion.
    """
    if spanish and 'Oracion' in grammar.rules:
        grammar = grammar.for_start('Oracion')
    toks, lex_errors = tokenize(source, spanish)
    errors = list(lex_errors)
    productions = []
    # posición del texto donde empieza cada línea, para calcular el desplazamiento
    offsets = [0] + [i + 1 for i, char in enumerate(source) if char == '\n']

    def report(line, col, code, message, nonterminal=None):
        """Agrega un error sintáctico con su posición a `errors`."""
        errors.append(Diagnostic(line, col, offsets[line - 1] + col - 1,
                                 'syntactic', code, message, nonterminal))

    root = Tree(grammar.start, [])
    # La pila guarda (símbolo, nodo_padre, índice_en_padre); '$' queda al fondo
    stack = [('$', None, None), (grammar.start, root, None)]
    pos = 0
    nonterminals = grammar.nonterminals

    # Cada vuelta procesa el símbolo de la cima, hasta vaciar la pila
    while stack:
        X, parent, idx = stack.pop()
        ttype, lexeme, line, col = toks[pos]

        if X == '$':
            if ttype != '$':
                report(line, col, 'extra_token', f"sobra {lexeme!r}")
            break

        if X not in nonterminals:                 # X es un terminal
            if X == ttype:
                parent[idx] = lexeme
                pos += 1
            else:                                 # falta el terminal esperado
                report(line, col, 'missing_terminal', f"se esperaba {X} "
                       f"pero llego {lexeme!r}")
                parent[idx] = f'<falta {X}>'      # se "inserta" y se sigue
            continue

        # X es un no terminal: la tabla da la producción según el token actual
        alpha = grammar.table.get((X, ttype))
        if idx is None:                           # símbolo inicial (es la raíz)
            node = parent
        else:
            node = Tree(X, [])
            parent[idx] = node

        if alpha is None:
            esperados = sorted(t for (A, t) in grammar.table if A == X)
            report(line, col, 'unexpected_token', f"no se esperaba {lexeme!r}"
                   f" al analizar {X}. Se esperaba: {esperados}", X)
            node.append('<error>')
            # Modo pánico: se descartan tokens hasta uno de FOLLOW(X) (o '$'),
            # para poder seguir analizando después de X.
            sync = grammar.follow[X] | {'$'}
            while toks[pos][0] not in sync:
                pos += 1
            continue

        # se guarda la producción usada, para las trazas
        productions.append(dict(nonterminal=X, production=list(alpha),
                                lookahead=ttype, line=line, column=col))
        if alpha == [EPS]:
            node.append(EPS)
            continue
        # los hijos se crean en orden; los no terminales se completan al salir de la pila
        for sym in alpha:
            node.append(Tree(sym, []) if sym in nonterminals else sym)
        # se apilan al revés para que el primer símbolo quede en la cima
        for i in range(len(alpha) - 1, -1, -1):
            stack.append((alpha[i], node, i))

    # errores léxicos y sintácticos juntos, en el orden del texto
    errors.sort(key=lambda error: error.offset)
    return ParseResult(root, errors, toks, productions)


def parse(source, grammar, spanish=False):
    """Versión simple de parse_detailed: devuelve (árbol, lista de mensajes).

    Una lista vacía significa que la entrada es válida.
    """
    result = parse_detailed(source, grammar, spanish)
    return result.tree, [str(error) for error in result.diagnostics]
