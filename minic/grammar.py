"""Carga la gramatica desde archivo y calcula FIRST, FOLLOW y la tabla LL(1)."""
from . import lexer
import re

EPS = 'eps'


class GrammarError(Exception):
    pass


class Grammar:
    def __init__(self, path, start=None):
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
        with open(path, encoding='utf-8') as f:
            for n, line in enumerate(f, 1):
                line = line.split('#')[0].strip()
                if not line:
                    continue
                if '->' not in line:
                    raise GrammarError(f'{path}:{n}: falta "->"')
                lhs, rhs = (p.strip() for p in line.split('->', 1))
                if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', lhs) or lhs == EPS or lhs in lexer.tokens:
                    raise GrammarError(f'{path}:{n}: no terminal invalido {lhs!r}')
                alts = [alt.split() for alt in rhs.split('|')]
                if any(not a for a in alts):
                    raise GrammarError(f'{path}:{n}: alternativa vacia '
                                       f'(usa "{EPS}")')
                if any(EPS in alt and alt != [EPS] for alt in alts):
                    raise GrammarError(f'{path}:{n}: eps debe ser una alternativa completa')
                if lhs in self.rules:
                    raise GrammarError(f'{path}:{n}: "{lhs}" repetido')
                self.rules[lhs] = alts
                if self.start is None:
                    self.start = lhs

    def _check_terminals(self):
        """Todo simbolo que no sea no terminal debe ser un token del lexer."""
        valid = set(lexer.tokens) | {EPS}
        for lhs, alts in self.rules.items():
            for alt in alts:
                for sym in alt:
                    if sym not in self.nonterminals and sym not in valid:
                        raise GrammarError(
                            f'Simbolo desconocido "{sym}" en la regla {lhs}')

    # ---------- FIRST y FOLLOW (punto fijo) ----------
    def first_of_seq(self, seq, FIRST=None):
        """FIRST de una secuencia de simbolos (alpha)."""
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
        """Reutiliza producciones y FIRST, recalculando FOLLOW/tabla para la raiz."""
        if start == self.start:
            return self
        if start not in self.rules:
            raise GrammarError(f'Simbolo inicial desconocido {start!r}')
        grammar = object.__new__(Grammar)
        grammar.rules = self.rules
        grammar.start = start
        grammar.nonterminals = self.nonterminals
        grammar.first = self.first
        grammar.follow = grammar._compute_follow()
        grammar.table = grammar._build_table()
        return grammar

    def _compute_first(self):
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
        FOLLOW = {A: set() for A in self.rules}
        FOLLOW[self.start].add('$')
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
        M = {}

        def put(A, t, alpha):
            if (A, t) in M:
                raise GrammarError(f'Conflicto en M[{A},{t}]: '
                                   f'la gramatica NO es LL(1)')
            M[(A, t)] = alpha

        for A, alts in self.rules.items():
            for alpha in alts:
                fa = self.first_of_seq(alpha)
                for a in fa - {EPS}:              # regla 1
                    put(A, a, alpha)
                if EPS in fa:                     # regla 2
                    for b in self.follow[A]:
                        put(A, b, alpha)
        return M

    def show(self):
        print('FIRST:')
        for A in self.rules:
            print(f'  {A:11s} {sorted(self.first[A])}')
        print('FOLLOW:')
        for A in self.rules:
            print(f'  {A:11s} {sorted(self.follow[A])}')
        print('TABLA:')
        for (A, t), alpha in sorted(self.table.items()):
            print(f'  M[{A},{t}] = {A} -> {" ".join(alpha)}')
