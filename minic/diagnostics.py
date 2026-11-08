"""Diagnósticos con posición estable para CLI y experimentos."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Diagnostic:
    """Un error con su posición.

    line, column: posición en el texto, contadas desde 1.
    offset: desplazamiento desde el inicio del texto (sirve para ordenar errores).
    stage: 'lexical' o 'syntactic'.
    code: identificador corto del error.
    message: texto que se muestra al usuario.
    nonterminal: no terminal que se analizaba, en los errores sintácticos que lo tienen.
    """

    line: int
    column: int
    offset: int
    stage: str
    code: str
    message: str
    nonterminal: str | None = None

    def __str__(self):
        """Texto de una línea, como se muestra en la consola."""
        return f'Linea {self.line}, col {self.column}: {self.message}'

    def to_dict(self):
        """Todos los campos en un diccionario, para guardarlos como JSON."""
        return asdict(self)
