"""Experimento reanudable con una API Chat Completions compatible.

La preparación produce solicitudes revisables. --execute requiere configuración
explícita y una clave local. Las pruebas de transporte usan un servidor local.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from minic.grammar import Grammar
from minic.lexicon_es import LEXICON
from minic.parser import parse_detailed
from .common import ROOT, metadata, read_json, write_json
from .validar_derivacion import validate_answer


def request_id(request):
    encoded = json.dumps(request, ensure_ascii=False, sort_keys=True).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def make_messages(row, variant, grammar, examples):
    instructions = (ROOT / 'prompts/zero_shot.txt').read_text(encoding='utf-8')
    rules = {key: value for key, value in grammar.rules.items()
             if key not in {'Program', 'StmtList', 'Stmt', 'Decl', 'DeclTail', 'Assign',
                            'AssignCore', 'If', 'ElsePart', 'ElseTail', 'While', 'For',
                            'ForInit', 'ForStep', 'Block', 'Cond', 'RelOp', 'Expr',
                            'ExprP', 'Term', 'TermP', 'Factor'}}
    instructions += '\nPRODUCCIONES\n' + json.dumps(rules, ensure_ascii=False)
    instructions += '\nLEXICON\n' + json.dumps(LEXICON, ensure_ascii=False)
    messages = [dict(role='system', content=instructions)]
    if variant == 'few_shot':
        messages[0]['content'] += '\n' + (ROOT / 'prompts/few_shot.txt').read_text(encoding='utf-8')
        for example in examples:
            parsed = parse_detailed(example['texto'], grammar, True)
            if parsed.accepted != example['esperado_cfg']:
                raise ValueError(f'Ejemplo inconsistente: {example["id"]}')
            proof = [dict(nonterminal=s['nonterminal'], production=s['production']) for s in parsed.productions]
            answer = dict(accepted=parsed.accepted, productions=proof if parsed.accepted else [])
            messages.extend([dict(role='user', content=example['texto']),
                             dict(role='assistant', content=json.dumps(answer, ensure_ascii=False))])
    messages.append(dict(role='user', content=row['texto']))
    return messages


def send(endpoint, key, payload):
    url = urlparse(endpoint)
    if url.scheme != 'https' and not (url.scheme == 'http' and url.hostname in {'127.0.0.1', 'localhost', '::1'}):
        raise ValueError('La API requiere HTTPS; HTTP se permite para pruebas locales')
    request = Request(endpoint, data=json.dumps(payload).encode('utf-8'),
                      headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key},
                      method='POST')
    with urlopen(request, timeout=120) as response:
        return json.load(response)


def parse_response(raw):
    content = raw['choices'][0]['message']['content']
    if content.startswith('```'):
        content = content.strip().split('\n', 1)[1].rsplit('```', 1)[0]
    answer = json.loads(content)
    if not isinstance(answer, dict) or type(answer.get('accepted')) is not bool:
        raise ValueError('La respuesta no contiene accepted booleano')
    return answer


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', help='realizar llamadas API')
    parser.add_argument('--model', default=os.getenv('LLM_MODEL'))
    parser.add_argument('--endpoint', default=os.getenv('LLM_ENDPOINT'))
    parser.add_argument('--corpus', default=str(ROOT / 'datos/corpus_es.json'))
    parser.add_argument('--limit', type=int, default=60)
    parser.add_argument('--max-new-calls', type=int, default=120)
    parser.add_argument('--max-completion-tokens', type=int, default=4096)
    parser.add_argument('--input-usd-per-million', type=float)
    parser.add_argument('--output-usd-per-million', type=float)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'resultados/llm')
    args = parser.parse_args(argv)
    if args.limit < 1 or args.max_new_calls < 0 or args.max_completion_tokens < 1:
        parser.error('Los limites deben ser positivos')
    grammar = Grammar(ROOT / 'gramatica_minic.txt')
    examples = read_json(ROOT / 'datos/ejemplos_few_shot.json')
    corpus = read_json(args.corpus)[:args.limit]
    requests = [dict(id=row['id'], text=row['texto'], level=row['nivel'], variant=variant,
                     payload=dict(model=args.model, messages=make_messages(row, variant, grammar, examples),
                                  response_format=dict(type='json_object'),
                                  max_completion_tokens=args.max_completion_tokens))
                for variant in ['zero_shot', 'few_shot'] for row in corpus]
    meta = metadata(args.corpus)
    write_json(args.output_dir / 'solicitudes.json', dict(metadata=meta, requests=requests))
    if not args.execute:
        write_json(args.output_dir / 'estado.json', dict(status='prepared',
                   pending='Ejecucion API real con proveedor, modelo, clave y presupuesto definidos',
                   requests=len(requests), real_responses=0))
        print(f'{len(requests)} solicitudes preparadas. Ejecucion real pendiente.')
        return 0
    key = os.getenv('LLM_API_KEY')
    if not key or not args.model or not args.endpoint:
        write_json(args.output_dir / 'estado.json', dict(status='configuration_required',
                   missing=[name for name, value in [('LLM_API_KEY', key), ('LLM_MODEL', args.model),
                                                    ('LLM_ENDPOINT', args.endpoint)] if not value]))
        print('Configura LLM_API_KEY, LLM_MODEL y LLM_ENDPOINT.')
        return 1
    log = args.output_dir / 'respuestas.jsonl'
    cached = {}
    if log.exists():
        for line in log.read_text(encoding='utf-8').splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError('El log contiene una linea incompleta; revisar antes de reanudar')
            if record.get('transport_completed'):
                cached[record['request_sha256']] = record
    results, new_calls = [], 0
    for row in requests:
        signature = request_id(dict(endpoint=args.endpoint, request=row,
                                    grammar=meta['grammar_sha256'], corpus=meta['corpus_sha256']))
        if signature in cached:
            results.append(cached[signature])
            continue
        if new_calls >= args.max_new_calls:
            continue
        new_calls += 1
        start = perf_counter()
        record = dict(id=row['id'], variant=row['variant'], tool='llm_' + row['variant'],
                      request_sha256=signature, model=args.model, endpoint=args.endpoint,
                      metadata=meta, request=row['payload'], transport_completed=False)
        try:
            raw = send(args.endpoint, key, row['payload'])
            record.update(raw_response=raw, transport_completed=True)
            answer = parse_response(raw)
            record.update(answer=answer, accepted=answer.get('accepted'),
                          adherence=validate_answer(answer, row['text'], grammar), execution_error=None)
            usage = raw.get('usage', {})
            if args.input_usd_per_million is not None and args.output_usd_per_million is not None:
                record['estimated_usd'] = (usage.get('prompt_tokens', 0) * args.input_usd_per_million +
                                           usage.get('completion_tokens', 0) * args.output_usd_per_million) / 1_000_000
        except (HTTPError, URLError, OSError, ValueError, KeyError, TypeError) as exc:
            record['execution_error'] = f'{type(exc).__name__}: {exc}'.replace(key, '[REDACTED]')
            record['adherence'] = dict(valid=False, reason='Respuesta no evaluable')
        record['seconds'] = perf_counter() - start
        serialized = json.dumps(record, ensure_ascii=False).replace(key, '[REDACTED]')
        with log.open('a', encoding='utf-8') as stream:
            stream.write(serialized + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        results.append(json.loads(serialized))
    write_json(args.output_dir / 'resultados.json', dict(metadata=meta, results=results))
    completed = sum(row.get('transport_completed', False) for row in results)
    write_json(args.output_dir / 'estado.json', dict(status='complete' if len(results) == len(requests) and
               all(not row.get('execution_error') for row in results) else 'partial',
               requested=len(requests), real_responses=completed, new_calls=new_calls))
    print(f'{completed}/{len(requests)} respuestas recibidas; {new_calls} llamadas nuevas.')
    return 0 if len(results) == len(requests) and all(not row.get('execution_error') for row in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
