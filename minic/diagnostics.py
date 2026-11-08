"""Diagnósticos con posición estable para CLI y experimentos."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Diagnostic:
    line: int
    column: int
    offset: int
    stage: str
    code: str
    message: str
    nonterminal: str | None = None

    def __str__(self):
        return f'Linea {self.line}, col {self.column}: {self.message}'

    def to_dict(self):
        return asdict(self)
