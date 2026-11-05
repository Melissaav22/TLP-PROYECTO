"""Analizador lexico (PLY). Convierte texto en una lista de tokens.

Ademas del vocabulario de MiniC, reconoce palabras del espanol y les asigna
un token con sus rasgos morfologicos (ver minic/lexicon_es.py)."""
import ply.lex as lex

from . import lexicon_es

reserved = {'int': 'INT', 'if': 'IF', 'else': 'ELSE', 'while': 'WHILE',
            'for': 'FOR'}

tokens = ['ID', 'NUM', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'LPAREN',
          'RPAREN', 'LBRACE', 'RBRACE', 'SEMI', 'ASSIGN', 'EQ', 'LT',
          'GT', 'LE', 'GE', 'NE'] + list(reserved.values()) + lexicon_es.TOKENS

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_SEMI = r';'
# PLY prueba primero las reglas de string con regex mas larga,
# por eso '==' gana sobre '=' y '<=' sobre '<'.
t_EQ = r'=='
t_ASSIGN = r'='
t_LE = r'<='
t_GE = r'>='
t_NE = r'!='
t_LT = r'<'
t_GT = r'>'
t_ignore = ' \t\r'


def t_ID(t):
    r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ_][A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ_]*'
    # Primero las reservadas de C (sensibles a mayusculas) y despues el
    # lexico del espanol (sin distinguir mayusculas), asi "integer" sigue
    # siendo un ID y no "int" + "eger".
    if t.value in reserved:
        t.type = reserved[t.value]
        return t
    if getattr(t.lexer, 'spanish', False):
        t.type = lexicon_es.LEXICON.get(t.value.lower(), 'ID')
    else:
        t.type = 'ID'
    return t


def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_comment(t):
    r'//.*'
    pass  # los comentarios de linea se descartan


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    t.lexer.errors.append((t.lineno, t.value[0]))
    t.lexer.skip(1)


_base_lexer = lex.lex()


def _column(source, lexpos):
    return lexpos - (source.rfind('\n', 0, lexpos) + 1) + 1


def tokenize(source, spanish=False):
    """Devuelve (tokens, errores_lexicos).

    tokens: lista de (tipo, lexema, linea, columna) terminada en '$'.
    errores_lexicos: lista de (linea, caracter_ilegal).
    Con spanish=True las palabras del lexico español llevan sus rasgos.
    """
    lx = _base_lexer.clone()
    lx.errors = []
    lx.lineno = 1
    lx.spanish = spanish
    lx.input(source)
    out = [(tok.type, str(tok.value), tok.lineno, _column(source, tok.lexpos))
           for tok in lx]
    out.append(('$', '$', lx.lineno, _column(source, len(source))))
    return out, lx.errors
