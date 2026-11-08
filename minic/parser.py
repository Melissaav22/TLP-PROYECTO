""" Proposito: Lleva cuentas de un stack de cosas que hacer"""
"""Parser predictivo LL(1) con pila, arbol nltk.Tree y recuperacion de errores
en modo panico (usa los conjuntos FOLLOW de la gramatica)."""
from nltk import Tree
from .grammar import EPS
from .lexer import tokenize


def parse(source, grammar):
    """Analiza `source`. Devuelve (arbol, errores).

    errores es una lista de textos; si esta vacia, la entrada es valida.
    Con errores, el arbol es parcial (los nodos fallidos tienen la hoja
    '<error>').
    """
    toks, lex_errors = tokenize(source)
    errors = [f'Linea {ln}: caracter ilegal {ch!r}' for ln, ch in lex_errors]

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
                errors.append(f"Linea {line}, col {col}: sobra {lexeme!r}")
            break

        if X not in nonterminals:                 # X es un terminal
            if X == ttype:
                parent[idx] = lexeme
                pos += 1
            else:                                 # falta el terminal esperado
                errors.append(f"Linea {line}, col {col}: se esperaba {X} "
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
            errors.append(f"Linea {line}, col {col}: no se esperaba {lexeme!r}"
                          f" al analizar {X}. Se esperaba: {esperados}")
            node.append('<error>')
            # Modo panico: se descartan tokens hasta uno de FOLLOW(X).
            sync = grammar.follow[X] | {'$'}
            while toks[pos][0] not in sync:
                pos += 1
            continue

        if alpha == [EPS]:
            node.append(EPS)
            continue
        for sym in alpha:
            node.append(Tree(sym, []) if sym in nonterminals else sym)
        for i in range(len(alpha) - 1, -1, -1):
            stack.append((alpha[i], node, i))

    return root, errors
