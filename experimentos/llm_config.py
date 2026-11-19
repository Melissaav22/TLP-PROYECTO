"""Configuración local y perfiles de API para el benchmark."""
import os
from pathlib import Path
import re
from urllib.parse import quote

from .common import ROOT

PROTOCOLS = {'chat-completions', 'gemini', 'anthropic'}


def read_env(path):
    if not path.exists():
        return {}
    settings = {}
    for number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, sep, value = line.partition('=')
        name, value = name.strip(), value.strip()
        if not sep or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
            raise ValueError(f'{path}:{number}: se esperaba NOMBRE=valor')
        if value.startswith(('"', "'")):
            if len(value) < 2 or not value.endswith(value[0]):
                raise ValueError(f'{path}:{number}: faltan las comillas de cierre')
            value = value[1:-1]
        settings[name] = value
    return settings


def load_profile(provider=None, env_file=None):
    path = env_file if env_file is not None else ROOT / '.env'
    env = {**read_env(path), **os.environ}
    name = (provider or env.get('LLM_PROVIDER') or 'chat-completions').strip().lower()
    if not re.fullmatch(r'[a-z][a-z0-9_-]*', name):
        raise ValueError('El nombre del perfil solo admite letras, números, guiones y guiones bajos')
    prefix = name.replace('-', '_').upper()
    protocol = env.get(f'{prefix}_PROTOCOL') or (name if name in PROTOCOLS else None)
    if protocol not in PROTOCOLS:
        raise ValueError(f'Configura {prefix}_PROTOCOL con uno de estos valores: {", ".join(sorted(PROTOCOLS))}')
    return name, prefix, protocol, env


def output_directory(profile, prefix, env):
    path = env.get(f'{prefix}_OUTPUT_DIR') or env.get('LLM_OUTPUT_DIR')
    if path:
        return ROOT / Path(path)
    base = ROOT / 'resultados/llm'
    return base if profile in {'chat-completions', 'gemini'} else base / profile


def configure(args):
    name, prefix, protocol, env = load_profile(args.provider)

    def value(setting, default=None, *, global_option=True):
        return (env.get(f'{prefix}_{setting}')
                or (env.get(f'LLM_{setting}') if global_option else None) or default)

    legacy = name == 'chat-completions'
    args.model = args.model or value('MODEL', global_option=legacy)
    args.endpoint = args.endpoint or value('ENDPOINT', global_option=legacy)
    if args.endpoint and args.model:
        args.endpoint = args.endpoint.replace('{model}', quote(args.model, safe=''))
    args.output_dir = args.output_dir or output_directory(name, prefix, env)

    for param, convert, default in [
        ('limit', int, 60), ('batch_size', int, 1), ('max_new_calls', int, 120), ('max_completion_tokens', int, 4096),
        ('timeout_seconds', int, 120), ('min_seconds_between_calls', float, 0),
        ('input_usd_per_million', float, None),
        ('output_usd_per_million', float, None),
    ]:
        if getattr(args, param, None) is not None:
            continue
        raw = value(param.upper(), default)
        try:
            setattr(args, param, convert(raw) if raw is not None else None)
        except ValueError:
            raise ValueError(f'{prefix}_{param.upper()} o LLM_{param.upper()} requiere un número válido') from None

    token_field = value('TOKEN_FIELD', 'max_completion_tokens', global_option=False)
    json_mode = value('JSON_MODE', 'true', global_option=False).lower()
    if token_field not in {'max_completion_tokens', 'max_tokens'}:
        raise ValueError(f'{prefix}_TOKEN_FIELD debe ser max_completion_tokens o max_tokens')
    if json_mode not in {'true', 'false'}:
        raise ValueError(f'{prefix}_JSON_MODE debe ser true o false')
    args.provider = name
    args.protocol = protocol
    args.token_field = token_field
    args.json_mode = json_mode == 'true'
    args.thinking_level = value('THINKING_LEVEL', global_option=False)
    args.api_version = value('API_VERSION', global_option=False) if protocol == 'anthropic' else None
    args.key_var = 'LLM_API_KEY' if legacy else f'{prefix}_API_KEY'
    return value('API_KEY', global_option=legacy)
