""" Proposito: Lleva cuentas de un stack de cosas que hacer"""
"""Parser predictivo LL(1) con pila, arbol nltk.Tree y recuperacion de errores
en modo panico (usa los conjuntos FOLLOW de la gramatica)."""
from nltk import Tree
from .grammar import EPS
from .lexer import tokenize
from .diagnostics import Diagnostic
from dataclasses import dataclass


@dataclass
class ParseResult:
    tree: Tree
    diagnostics: list
    tokens: list
    productions: list

    @property
    def accepted(self):
        return not self.diagnostics


def parse_detailed(source, grammar, spanish=False):
    """Analiza `source`. Devuelve (arbol, errores).

    errores es una lista de textos; si esta vacia, la entrada es valida.
    Con errores, el arbol es parcial (los nodos fallidos tienen la hoja
    '<error>').

    Con spanish=False se usa el lexico de MiniC (las palabras son ID).
    Con spanish=True se usa el lexico del espanol (tokens con rasgos).
    """
    if spanish and 'Oracion' in grammar.rules:
        grammar = grammar.for_start('Oracion')
    toks, lex_errors = tokenize(source, spanish)
    errors = list(lex_errors)
    productions = []
    offsets = [0] + [i + 1 for i, char in enumerate(source) if char == '\n']

    def report(line, col, code, message, nonterminal=None):
        errors.append(Diagnostic(line, col, offsets[line - 1] + col - 1,
                                 'syntactic', code, message, nonterminal))

    root = Tree(grammar.start, [])
    # La pila guarda (simbolo, nodo_padre, indice_en_padre)
    stack = [('$', None, None), (grammar.start, root, None)]
    pos = 0
    nonterminals = grammar.nonterminals

    # Stack de elementos que encuentra en el programa
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

        alpha = grammar.table.get((X, ttype))     # X es no terminal, tendrá que ver regla que aplicará según tabla
        if idx is None:                           # simbolo inicial
            node = parent
        else:
            node = Tree(X, [])
            parent[idx] = node

        if alpha is None:
            esperados = sorted(t for (A, t) in grammar.table if A == X)
            report(line, col, 'unexpected_token', f"no se esperaba {lexeme!r}"
                   f" al analizar {X}. Se esperaba: {esperados}", X)
            node.append('<error>')
            # Modo panico: se descartan tokens hasta uno de FOLLOW(X).
            sync = grammar.follow[X] | {'$'}
            while toks[pos][0] not in sync:
                pos += 1
            continue

        productions.append(dict(nonterminal=X, production=list(alpha),
                                lookahead=ttype, line=line, column=col))
        if alpha == [EPS]:
            node.append(EPS)
            continue
        for sym in alpha:
            node.append(Tree(sym, []) if sym in nonterminals else sym)
        for i in range(len(alpha) - 1, -1, -1):
            stack.append((alpha[i], node, i))

    errors.sort(key=lambda error: error.offset)
    return ParseResult(root, errors, toks, productions)


def parse(source, grammar, spanish=False):
    """API compatible: devuelve (nltk.Tree, lista de mensajes)."""
    result = parse_detailed(source, grammar, spanish)
    return result.tree, [str(error) for error in result.diagnostics]
