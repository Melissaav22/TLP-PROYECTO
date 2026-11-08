"""Analizador léxico (PLY). Convierte texto en una lista de tokens.

Además del vocabulario de MiniC, reconoce palabras del español y les asigna
un token con sus rasgos morfológicos (ver minic/lexicon_es.py)."""
import ply.lex as lex
import unicodedata

from . import lexicon_es
from .diagnostics import Diagnostic

# palabras reservadas de MiniC; t_ID las distingue de un identificador
reserved = {'int': 'INT', 'if': 'IF', 'else': 'ELSE', 'while': 'WHILE',
            'for': 'FOR'}
# palabras clave de C que MiniC no implementa; no se aceptan como identificadores
C_KEYWORDS = set('auto break case char const continue default do double enum '
                 'extern float goto inline long register restrict return short '
                 'signed sizeof static struct switch typedef union unsigned void '
                 'volatile _Alignas _Alignof _Atomic _Bool _Complex _Generic '
                 '_Imaginary _Noreturn _Static_assert _Thread_local'.split())
MAX_NUM_DIGITS = 4096     # máximo de dígitos de un literal numérico

# lista de tokens que PLY exige; incluye los del léxico del español
tokens = ['ID', 'NUM', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'LPAREN',
          'RPAREN', 'LBRACE', 'RBRACE', 'SEMI', 'ASSIGN', 'EQ', 'LT',
          'GT', 'LE', 'GE', 'NE', 'C_KEYWORD'] + list(reserved.values()) + lexicon_es.TOKENS

# operadores y símbolos de un carácter
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_SEMI = r';'
# PLY prueba primero las reglas de string con la expresión regular más larga,
# por eso '==' gana sobre '=' y '<=' sobre '<'.
t_EQ = r'=='
t_ASSIGN = r'='
t_LE = r'<='
t_GE = r'>='
t_NE = r'!='
t_LT = r'<'
t_GT = r'>'
t_ignore = ' \t\r'      # se saltan; el salto de línea lo maneja t_newline


def t_ID(t):
    r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ_][A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ_\u0300-\u036f]*'
    # Primero las reservadas de C (sensibles a mayúsculas) y después el
    # léxico del español (sin distinguir mayúsculas), así "integer" sigue
    # siendo un ID y no "int" + "eger".
    if t.value in reserved:
        t.type = reserved[t.value]
        return t
    # modo español: se busca la palabra en el diccionario; si no está, se reporta
    if getattr(t.lexer, 'spanish', False):
        word = unicodedata.normalize('NFC', t.value).lower()
        t.type = lexicon_es.LEXICON.get(word, 'ID')
        if t.type == 'ID':
            _error(t.lexer, t.lexpos, 'unknown_word', f'palabra fuera del vocabulario {t.value!r}')
    else:
        # modo MiniC: una palabra clave de C no implementada queda como C_KEYWORD
        t.type = 'C_KEYWORD' if t.value in C_KEYWORDS else 'ID'
    return t


def t_NUM(t):
    r'[0-9]+'
    # un número muy largo o con cero inicial (como 08) se reporta,
    # pero el token se devuelve igual para que el análisis siga
    if len(t.value) > MAX_NUM_DIGITS:
        _error(t.lexer, t.lexpos, 'number_too_long',
               f'numero excede el limite de {MAX_NUM_DIGITS} digitos')
    elif len(t.value) > 1 and t.value.startswith('0'):
        _error(t.lexer, t.lexpos, 'leading_zero',
               'solo se admiten decimales sin ceros iniciales')
    return t


def t_comment(t):
    r'//.*'
    pass  # los comentarios de línea (//) se descartan


def t_newline(t):
    r'\n+'
    # se cuentan las líneas para poder dar la posición de los errores
    t.lexer.lineno += len(t.value)


def t_error(t):
    # carácter que no pertenece a ningún token: se reporta y se salta
    _error(t.lexer, t.lexpos, 'illegal_character', f'caracter ilegal {t.value[0]!r}')
    t.lexer.skip(1)


def _error(lexer, offset, code, message):
    """Agrega un error léxico a la lista del lexer, con su línea y columna."""
    lexer.errors.append(Diagnostic(lexer.lineno, _column(lexer.lexdata, offset),
                                   offset, 'lexical', code, message))


# lexer base de PLY; tokenize() lo clona en cada llamada para no compartir estado
_base_lexer = lex.lex()


def _column(source, lexpos):
    """Columna, contada desde 1, de la posición `lexpos` dentro de su línea."""
    return lexpos - (source.rfind('\n', 0, lexpos) + 1) + 1


def tokenize(source, spanish=False):
    """Devuelve (tokens, errores_lexicos).

    tokens: lista de (tipo, lexema, línea, columna) terminada en '$'.
    errores_lexicos: lista de Diagnostic con posición, código y mensaje.
    Con spanish=True las palabras del español llevan sus rasgos en el tipo.
    """
    lx = _base_lexer.clone()
    lx.errors = []
    lx.lineno = 1
    lx.spanish = spanish
    lx.input(source)
    out = [(tok.type, str(tok.value), tok.lineno, _column(source, tok.lexpos))
           for tok in lx]
    # '$' marca el fin de la entrada
    out.append(('$', '$', lx.lineno, _column(source, len(source))))
    return out, lx.errors
