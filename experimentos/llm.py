"""Experimento reanudable con Gemini o una API Chat Completions compatible.

La preparación produce solicitudes revisables. --execute requiere configuración
explícita y una clave local. Las pruebas de transporte usan un servidor local.
"""
import argparse
from datetime import datetime, timezone
from getpass import getpass
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import sys
from time import perf_counter, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from minic.grammar import Grammar
from minic.lexicon_es import LEXICON
from minic.parser import parse_detailed
from .common import CURRENT_CORPUS, ROOT, metadata, read_json, write_json
from .llm_config import configure
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


def make_requests(corpus, config, grammar, examples):
    for variant in ['zero_shot', 'few_shot']:
        if config.batch_size == 1:
            for row in corpus:
                messages = make_messages(row, variant, grammar, examples)
                yield dict(id=row['id'], text=row['texto'], level=row['nivel'], variant=variant,
                           payload=make_payload(messages, config))
            continue
        for offset in range(0, len(corpus), config.batch_size):
            items = [dict(id=row['id'], texto=row['texto'])
                     for row in corpus[offset:offset + config.batch_size]]
            messages = make_messages(dict(texto=json.dumps(items, ensure_ascii=False)),
                                     variant, grammar, examples)
            messages[0]['content'] += (
                '\nPara el último mensaje, analiza cada elemento de la lista de forma independiente. '
                'Las otras oraciones del lote tampoco son ejemplos resueltos. '
                'Devuelve un único objeto JSON {"results": [...]}. '
                'En cada elemento de results, copia su id y aplica el formato de respuesta '
                'con accepted, productions y reason cuando corresponda. '
                'Devuelve exactamente un elemento por id de entrada.'
            )
            yield dict(id=f'lote-{offset // config.batch_size + 1:03d}', items=items, variant=variant,
                       payload=make_payload(messages, config))


def make_payload(messages, config):
    max_tokens = config.max_completion_tokens
    if config.protocol == 'gemini':
        roles = {'user': 'user', 'assistant': 'model'}
        generation = dict(responseMimeType='application/json', maxOutputTokens=max_tokens)
        if config.thinking_level:
            generation['thinkingConfig'] = dict(thinkingLevel=config.thinking_level)
        return dict(
            systemInstruction=dict(parts=[dict(text=messages[0]['content'])]),
            contents=[dict(role=roles[message['role']], parts=[dict(text=message['content'])])
                      for message in messages[1:]],
            generationConfig=generation,
        )
    if config.protocol == 'anthropic':
        return dict(model=config.model, system=messages[0]['content'], messages=messages[1:], max_tokens=max_tokens)
    payload = dict(model=config.model, messages=messages)
    payload[config.token_field] = max_tokens
    if config.json_mode:
        payload['response_format'] = dict(type='json_object')
    return payload


def send(key, payload, config):
    endpoint = config.endpoint
    url = urlparse(endpoint)
    if url.scheme != 'https' and not (url.scheme == 'http' and url.hostname in {'127.0.0.1', 'localhost', '::1'}):
        raise ValueError('La API requiere HTTPS; HTTP se permite para pruebas locales')
    request = Request(endpoint, data=json.dumps(payload).encode('utf-8'),
                      headers={'Content-Type': 'application/json'}, method='POST')
    if config.protocol == 'gemini':
        request.add_unredirected_header('x-goog-api-key', key)
    elif config.protocol == 'anthropic':
        request.add_unredirected_header('x-api-key', key)
        request.add_header('anthropic-version', config.api_version)
    else:
        request.add_unredirected_header('Authorization', 'Bearer ' + key)
    with urlopen(request, timeout=config.timeout_seconds) as response:
        return json.load(response)


def parse_response(raw, protocol):
    if protocol == 'gemini':
        candidate = (raw.get('candidates') or [{}])[0]
        parts = (candidate.get('content') or {}).get('parts', [])
        content = ''.join(part.get('text', '') for part in parts if not part.get('thought'))
        if not content.strip():
            reason = candidate.get('finishReason') or raw.get('promptFeedback', {}).get('blockReason')
            raise ValueError(f'Gemini no devolvió texto: {reason or "sin motivo informado"}')
    elif protocol == 'anthropic':
        content = ''.join(part['text'] for part in raw['content'] if part['type'] == 'text')
    else:
        content = raw['choices'][0]['message']['content']
    if not isinstance(content, str):
        raise ValueError('La API no devolvió texto')
    content = content.strip()
    if content.startswith('```'):
        content = content.partition('\n')[2].rsplit('```', 1)[0]
    return json.loads(content)


def score_answer(answer, text, grammar):
    if not isinstance(answer, dict) or type(answer.get('accepted')) is not bool:
        raise ValueError('La respuesta no contiene accepted booleano')
    return dict(answer=answer, accepted=answer['accepted'],
                adherence=validate_answer(answer, text, grammar), execution_error=None)


def score_batch(answer, items, grammar):
    if not isinstance(answer, dict) or not isinstance(answer.get('results'), list):
        raise ValueError('El lote debe devolver un objeto JSON con una lista results')
    expected_ids = {item['id'] for item in items}
    by_id = {}
    for row in answer['results']:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or row['id'] not in expected_ids:
            raise ValueError('El lote devolvió un elemento con un id ajeno o inválido')
        if row['id'] in by_id:
            raise ValueError(f'El lote devolvió el id {row["id"]} más de una vez')
        by_id[row['id']] = row
    results = []
    for item in items:
        item_id = item['id']
        try:
            if item_id not in by_id:
                raise ValueError('La respuesta del lote omitió esta oración')
            result = score_answer(by_id[item_id], item['texto'], grammar)
        except ValueError as exc:
            result = dict(execution_error=str(exc))
        results.append(dict(id=item_id, **result))
    return results


def sentence_results(call):
    if 'item_ids' not in call:
        return [call]
    scores = call.get('evaluations')
    if scores is None:
        scores = [dict(id=item_id, execution_error=call['execution_error']) for item_id in call['item_ids']]
    return [dict(variant=call['variant'], request_sha256=call['request_sha256'],
                 timestamp_utc=call['timestamp_utc'], **score) for score in scores]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', help='realizar llamadas API')
    parser.add_argument('--provider', help='perfil a usar en lugar de LLM_PROVIDER en .env')
    parser.add_argument('--ask-api-key', action='store_true', help='pedir la clave en la terminal sin mostrarla')
    parser.add_argument('--model')
    parser.add_argument('--endpoint')
    parser.add_argument('--corpus', type=Path, default=CURRENT_CORPUS)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--batch-size', type=int, help='oraciones por llamada, por cada variante')
    parser.add_argument('--max-new-calls', type=int)
    parser.add_argument('--max-completion-tokens', type=int)
    parser.add_argument('--input-usd-per-million', type=float)
    parser.add_argument('--output-usd-per-million', type=float)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args(argv)
    explicit_output_dir = args.output_dir is not None
    try:
        key = configure(args)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    limits = (args.batch_size, args.max_completion_tokens, args.timeout_seconds)
    if min(limits) < 1 or (args.limit is not None and args.limit < 1):
        parser.error('Los límites y el tiempo de espera deben ser positivos')
    if args.max_new_calls is not None and args.max_new_calls < 0:
        parser.error('--max-new-calls debe ser un número no negativo')
    if args.batch_size > 1 and not explicit_output_dir:
        args.output_dir = args.output_dir / f'lotes-{args.batch_size}'
    status_path = args.output_dir / 'estado.json'
    if status_path.exists() and read_json(status_path).get('batch_size', 1) != args.batch_size:
        parser.error('La carpeta ya contiene una corrida con otro tamaño de lote. Usa --output-dir.')
    interval = args.min_seconds_between_calls
    if not isfinite(interval) or interval < 0:
        parser.error('MIN_SECONDS_BETWEEN_CALLS debe ser un número no negativo')

    meta = metadata(args.corpus)
    corpus = read_json(args.corpus)[:args.limit]
    if any(row.get('grammar_version') not in (None, meta['grammar_sha256']) for row in corpus):
        parser.error('El corpus declara otra versión de la CFG. Usa el corpus de la versión actual.')
    manifest_path = args.output_dir / 'solicitudes.json'
    if manifest_path.exists():
        recorded = read_json(manifest_path)['metadata']
        if any(recorded[key] != meta[key] for key in ('corpus_sha256', 'grammar_sha256')):
            parser.error('La carpeta contiene evidencia de otro corpus o CFG. Usa --output-dir.')

    if args.execute:
        if args.ask_api_key:
            if not sys.stdin.isatty():
                parser.error('--ask-api-key requiere una terminal interactiva')
            key = getpass(f'{args.key_var}: ').strip()
        missing = [name for name, value in [(args.key_var, key), ('modelo', args.model),
                                            ('endpoint', args.endpoint)] if not value]
        if args.protocol == 'anthropic' and not args.api_version:
            missing.append('versión de API de Anthropic')
        if missing:
            parser.error(f'Completa el perfil {args.provider} en .env: {", ".join(missing)}')

    grammar = Grammar(ROOT / 'gramatica_minic.txt')
    examples = read_json(ROOT / 'datos/ejemplos_few_shot.json')
    requests = list(make_requests(corpus, args, grammar, examples))
    if args.batch_size > 1:
        meta['batch_size'] = args.batch_size
    write_json(manifest_path, dict(metadata=meta, requests=requests))
    if not args.execute:
        write_json(status_path, dict(status='prepared', batch_size=args.batch_size,
                   pending='Ejecucion API real con proveedor, modelo, clave y presupuesto definidos',
                   requests=len(requests), real_responses=0))
        print(f'{len(requests)} solicitudes preparadas. Ejecucion real pendiente.')
        return 0
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
    calls, new_calls = [], 0
    previous_start = None
    for row in requests:
        request_details = dict(endpoint=args.endpoint, request=row,
                               grammar=meta['grammar_sha256'], corpus=meta['corpus_sha256'])
        if args.api_version:
            request_details['api_version'] = args.api_version
        signature = request_id(request_details)
        if signature in cached:
            calls.append(cached[signature])
            continue
        if args.max_new_calls is not None and new_calls >= args.max_new_calls:
            continue
        if previous_start is not None:
            remaining = interval - (perf_counter() - previous_start)
            if remaining > 0:
                sleep(remaining)
        new_calls += 1
        start = perf_counter()
        previous_start = start
        record = dict(id=row['id'], variant=row['variant'], tool='llm_' + row['variant'],
                      timestamp_utc=datetime.now(timezone.utc).isoformat(),
                      request_sha256=signature, model=args.model, endpoint=args.endpoint, provider=args.provider,
                      protocol=args.protocol, api_version=args.api_version, timeout_seconds=args.timeout_seconds,
                      min_seconds_between_calls=interval,
                      metadata=meta, request=row['payload'], transport_completed=False)
        if 'items' in row:
            record['item_ids'] = [item['id'] for item in row['items']]
        stop_status = None
        try:
            raw = send(key, row['payload'], args)
            record.update(raw_response=raw, transport_completed=True)
            answer = parse_response(raw, args.protocol)
            if 'items' in row:
                record.update(evaluations=score_batch(answer, row['items'], grammar), execution_error=None)
            else:
                record.update(score_answer(answer, row['text'], grammar))
            if args.input_usd_per_million is not None and args.output_usd_per_million is not None:
                if args.protocol == 'gemini':
                    usage = raw.get('usageMetadata', {})
                    input_tokens = usage.get('promptTokenCount', 0)
                    output_tokens = usage.get('candidatesTokenCount', 0) + usage.get('thoughtsTokenCount', 0)
                elif args.protocol == 'anthropic':
                    usage = raw.get('usage', {})
                    input_tokens = usage.get('input_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0)
                else:
                    usage = raw.get('usage', {})
                    input_tokens = usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0)
                record['estimated_usd'] = (input_tokens * args.input_usd_per_million +
                                           output_tokens * args.output_usd_per_million) / 1_000_000
        except (URLError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            record['execution_error'] = f'{type(exc).__name__}: {exc}'.replace(key, '[REDACTED]')
            record['adherence'] = dict(valid=False, reason='Respuesta no evaluable')
            if isinstance(exc, HTTPError):
                record['http_status'] = exc.code
                with exc:
                    record['raw_error_response'] = exc.read().decode('utf-8', errors='replace')
                if exc.code in {400, 401, 403, 404, 429}:
                    stop_status = exc.code
        record['seconds'] = perf_counter() - start
        serialized = json.dumps(record, ensure_ascii=False).replace(key, '[REDACTED]')
        with log.open('a', encoding='utf-8') as stream:
            stream.write(serialized + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        calls.append(json.loads(serialized))
        if stop_status is not None:
            print(f'La API respondió HTTP {stop_status}. Consulta el último registro de {log} antes de reanudar.')
            break
    results = [row for call in calls for row in sentence_results(call)]
    payload = dict(metadata=meta, results=results)
    complete = len(results) == 2 * len(corpus) and all(not row.get('execution_error') for row in results)
    completed = sum(call['transport_completed'] for call in calls)
    status = dict(status='complete' if complete else 'partial',
                  requested=len(requests), real_responses=completed, new_calls=new_calls)
    if args.batch_size > 1:
        payload['calls'] = [dict(variant=call['variant'], estimated_usd=call.get('estimated_usd'))
                            for call in calls]
        status.update(batch_size=args.batch_size, expected_pairs=2 * len(corpus),
                      evaluable_pairs=sum(not row.get('execution_error') for row in results))
        print(f'{status["evaluable_pairs"]}/{status["expected_pairs"]} pares oración-variante evaluables.')
    write_json(args.output_dir / 'resultados.json', payload)
    write_json(status_path, status)
    print(f'{completed}/{len(requests)} respuestas recibidas; {new_calls} llamadas nuevas.')
    return 0 if complete else 1


if __name__ == '__main__':
    raise SystemExit(main())
