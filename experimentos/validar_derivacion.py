"""Valida una derivación izquierda del LLM sin aceptar reglas inventadas."""
from minic.grammar import EPS
from minic.lexer import tokenize
from minic.parser import parse_detailed


def validate_answer(answer, source, grammar):
    if not isinstance(answer, dict) or type(answer.get('accepted')) is not bool:
        return dict(valid=False, reason='Falta accepted booleano')
    oracle = parse_detailed(source, grammar, True)
    if not answer['accepted']:
        if answer.get('productions') != []:
            return dict(valid=False, reason='Un rechazo debe devolver productions vacio')
        return dict(valid=not oracle.accepted,
                    reason='Rechazo compatible con la CFG' if not oracle.accepted else 'Rechaza una derivacion existente')
    tokens, lexical_errors = tokenize(source, True)
    if lexical_errors:
        return dict(valid=False, reason='Acepta una entrada con errores lexicos')
    steps = answer.get('productions')
    if not isinstance(steps, list) or len(steps) > 10000:
        return dict(valid=False, reason='Lista de producciones ausente o excesiva')
    stack = ['Oracion']
    position = 0
    step_index = 0
    while stack:
        symbol = stack.pop()
        if symbol in grammar.nonterminals:
            if step_index >= len(steps):
                return dict(valid=False, reason='Derivacion incompleta')
            step = steps[step_index]
            if not isinstance(step, dict) or step.get('nonterminal') != symbol:
                return dict(valid=False, reason=f'Expansion fuera de orden en {symbol}')
            production = step.get('production')
            if production not in grammar.rules[symbol]:
                return dict(valid=False, reason=f'Produccion inexistente en {symbol}')
            step_index += 1
            if production != [EPS]:
                stack.extend(reversed(production))
        else:
            if position >= len(tokens) - 1 or tokens[position][0] != symbol:
                return dict(valid=False, reason='Terminales diferentes de la entrada')
            position += 1
    valid = position == len(tokens) - 1 and step_index == len(steps)
    return dict(valid=valid, reason='Derivacion completa' if valid else 'Sobran tokens o producciones')
