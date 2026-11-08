"""Carga la gramática desde un archivo y calcula FIRST, FOLLOW y la tabla de
análisis LL(1) que usa el parser."""
from . import lexer
import re

EPS = 'eps'     # cadena vacía en el archivo de gramática


class GrammarError(Exception):
    """Gramática mal formada o que no es LL(1)."""


class Grammar:
    """Gramática libre de contexto con su tabla de análisis LL(1).

    rules: no terminal -> lista de alternativas (cada una, una lista de símbolos).
    start: símbolo inicial.
    nonterminals: conjunto de no terminales.
    first, follow: conjuntos FIRST y FOLLOW de cada no terminal.
    table: table[(A, a)] es la producción que se aplica al expandir A cuando
        el siguiente token es a.
    """

    def __init__(self, path, start=None):
        """Lee la gramática de `path` y calcula FIRST, FOLLOW y la tabla.

        Si `start` es None, el símbolo inicial es el de la primera regla.
        Lanza GrammarError si la gramática es inválida o no es LL(1).
        """
        self.rules = {}          # no terminal -> lista de alternativas
        self.start = None
        self._load(path)
        if not self.rules:
            raise GrammarError('La gramatica esta vacia')
        if start is not None:
            if start not in self.rules:
                raise GrammarError(f'Simbolo inicial desconocido {start!r}')
            self.start = start
        self.nonterminals = set(self.rules)
        self._check_terminals()
        self._check_productivity()
        self.first = self._compute_first()
        self.follow = self._compute_follow()
        self.table = self._build_table()

    # ---------- lectura del archivo ----------
    def _load(self, path):
        """Lee las reglas del archivo, con el formato `A -> alt1 | alt2`.

        Se ignora lo que sigue a '#' y las líneas vacías. Cada no terminal
        se define una sola vez; el primero que aparece es el símbolo inicial.
        """
        with open(path, encoding='utf-8') as f:
            for n, line in enumerate(f, 1):
                line = line.split('#')[0].strip()
                if not line:
                    continue
                if '->' not in line:
                    raise GrammarError(f'{path}:{n}: falta "->"')
                lhs, rhs = (p.strip() for p in line.split('->', 1))
                # el lado izquierdo no puede llamarse como un token del lexer
                if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', lhs) or lhs == EPS or lhs in lexer.tokens:
                    raise GrammarError(f'{path}:{n}: no terminal invalido {lhs!r}')
                alts = [alt.split() for alt in rhs.split('|')]
                if any(not a for a in alts):
                    raise GrammarError(f'{path}:{n}: alternativa vacia '
                                       f'(usa "{EPS}")')
                # eps solo vale como alternativa completa, no mezclada con otros símbolos
                if any(EPS in alt and alt != [EPS] for alt in alts):
                    raise GrammarError(f'{path}:{n}: eps debe ser una alternativa completa')
                if lhs in self.rules:
                    raise GrammarError(f'{path}:{n}: "{lhs}" repetido')
                self.rules[lhs] = alts
                if self.start is None:
                    self.start = lhs

    def _check_terminals(self):
        """Todo símbolo que no sea no terminal debe ser un token del lexer."""
        valid = set(lexer.tokens) | {EPS}
        for lhs, alts in self.rules.items():
            for alt in alts:
                for sym in alt:
                    if sym not in self.nonterminals and sym not in valid:
                        raise GrammarError(
                            f'Simbolo desconocido "{sym}" en la regla {lhs}')

    # ---------- FIRST y FOLLOW (punto fijo) ----------
    def first_of_seq(self, seq, FIRST=None):
        """FIRST de una secuencia de símbolos (alfa).

        Incluye eps solo si toda la secuencia puede derivar la cadena vacía.
        Durante el cálculo por punto fijo se pasa el FIRST parcial en `FIRST`;
        si no se pasa, se usa el ya calculado.
        """
        FIRST = FIRST if FIRST is not None else self.first
        result = set()
        for sym in seq:
            if sym == EPS:
                result.add(EPS)
                return result
            if sym not in self.nonterminals:
                result.add(sym)
                return result
            result |= FIRST[sym] - {EPS}
            if EPS not in FIRST[sym]:
                return result
        result.add(EPS)
        return result

    def _check_productivity(self):
        """Comprueba que todo no terminal pueda derivar una cadena de terminales.

        Un no terminal es productivo si alguna de sus alternativas solo tiene
        terminales o no terminales ya productivos. Se repite hasta que no se
        agregan más; los que queden fuera provocan GrammarError.
        """
        productive = set()
        while True:
            new = {lhs for lhs, alts in self.rules.items() if any(
                all(sym not in self.nonterminals or sym in productive for sym in alt)
                for alt in alts)}
            if new <= productive:
                break
            productive |= new
        missing = self.nonterminals - productive
        if missing:
            raise GrammarError(f'No terminales sin derivacion terminal: {sorted(missing)}')

    def for_start(self, start):
        """Devuelve la misma gramática con otro símbolo inicial.

        FIRST no depende del símbolo inicial y se reutiliza. FOLLOW sí
        depende de él (solo el inicial lleva '$'), así que se recalcula junto
        con la tabla.
        """
        if start == self.start:
            return self
        if start not in self.rules:
            raise GrammarError(f'Simbolo inicial desconocido {start!r}')
        # sin __init__: las reglas ya están cargadas y validadas
        grammar = object.__new__(Grammar)
        grammar.rules = self.rules
        grammar.start = start
        grammar.nonterminals = self.nonterminals
        grammar.first = self.first
        grammar.follow = grammar._compute_follow()
        grammar.table = grammar._build_table()
        return grammar

    def _compute_first(self):
        """Calcula FIRST de cada no terminal por punto fijo.

        Recorre todas las producciones y se detiene cuando ningún conjunto
        crece.
        """
        FIRST = {A: set() for A in self.rules}
        changed = True
        while changed:
            changed = False
            for A, alts in self.rules.items():
                for alpha in alts:
                    new = self.first_of_seq(alpha, FIRST)
                    if not new <= FIRST[A]:
                        FIRST[A] |= new
                        changed = True
        return FIRST

    def _compute_follow(self):
        """Calcula FOLLOW de cada no terminal por punto fijo.

        Para cada B en una producción A -> alfa B beta:
        - FIRST(beta) sin eps se agrega a FOLLOW(B).
        - Si beta está vacía o puede derivar eps, FOLLOW(A) también se
          agrega a FOLLOW(B).
        """
        FOLLOW = {A: set() for A in self.rules}
        FOLLOW[self.start].add('$')           # '$' marca el fin de la entrada
        changed = True
        while changed:
            changed = False
            for A, alts in self.rules.items():
                for alpha in alts:
                    for i, B in enumerate(alpha):
                        if B not in self.nonterminals:
                            continue
                        beta = alpha[i + 1:]
                        fb = self.first_of_seq(beta) if beta else {EPS}
                        add = fb - {EPS}
                        if EPS in fb:
                            add |= FOLLOW[A]
                        if not add <= FOLLOW[B]:
                            FOLLOW[B] |= add
                            changed = True
        return FOLLOW

    # ---------- tabla M[A, t] ----------
    def _build_table(self):
        """Construye la tabla de análisis LL(1) como diccionario (A, a) -> alfa.

        Lanza GrammarError si una celda recibe dos producciones, es decir,
        si la gramática no es LL(1).
        """
        M = {}

        def put(A, t, alpha):
            """Anota alfa en la celda (A, t); una celda ocupada es un conflicto."""
            if (A, t) in M:
                raise GrammarError(f'Conflicto en M[{A},{t}]: '
                                   f'la gramatica NO es LL(1)')
            M[(A, t)] = alpha

        for A, alts in self.rules.items():
            for alpha in alts:
                fa = self.first_of_seq(alpha)
                # Regla 1: por cada token a en FIRST(alfa), alfa va en M[A, a].
                for a in fa - {EPS}:
                    put(A, a, alpha)
                # Regla 2: si alfa puede derivar eps, va también en M[A, b]
                # para cada token b en FOLLOW(A).
                if EPS in fa:
                    for b in self.follow[A]:
                        put(A, b, alpha)
        return M

    def show(self):
        """Imprime FIRST, FOLLOW y la tabla (es lo que muestra `--tabla`)."""
        print('FIRST:')
        for A in self.rules:
            print(f'  {A:11s} {sorted(self.first[A])}')
        print('FOLLOW:')
        for A in self.rules:
            print(f'  {A:11s} {sorted(self.follow[A])}')
        print('TABLA:')
        for (A, t), alpha in sorted(self.table.items()):
            print(f'  M[{A},{t}] = {A} -> {" ".join(alpha)}')
