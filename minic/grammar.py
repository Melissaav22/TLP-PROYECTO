"""Carga la gramatica desde archivo y calcula FIRST, FOLLOW y la tabla LL(1)."""
from . import lexer

EPS = 'eps'


class GrammarError(Exception):
    pass


class Grammar:
    def __init__(self, path):
        self.rules = {}          # no terminal -> lista de alternativas
        self.start = None
        self._load(path)
        self.nonterminals = set(self.rules)
        self._check_terminals()
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
                alts = [alt.split() for alt in rhs.split('|')]
                if any(not a for a in alts):
                    raise GrammarError(f'{path}:{n}: alternativa vacia '
                                       f'(usa "{EPS}")')
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
