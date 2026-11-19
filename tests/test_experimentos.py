"""Regresiones de corpus, métricas, derivaciones y transporte reanudable."""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from experimentos.common import ROOT, digest, read_json
from experimentos.llm import main as llm_main, score_batch
from experimentos.metricas import binary_metrics
from experimentos.resumir_llm import main as summarize_llm
from experimentos.validar_corpus import validate
from experimentos.validar_derivacion import validate_answer
from minic.grammar import Grammar
from minic.parser import parse_detailed


class Experiments(unittest.TestCase):
    def test_text_hash_is_portable(self):
        with tempfile.TemporaryDirectory() as directory:
            lf = Path(directory) / 'unix.json'
            crlf = Path(directory) / 'windows.json'
            lf.write_bytes(b'{"a":1}\n')
            crlf.write_bytes(b'{"a":1}\r\n')
            self.assertEqual(digest(lf), digest(crlf))

    def test_corpus_integrity(self):
        corpus = read_json(ROOT / 'datos/corpus_es.json')
        examples = read_json(ROOT / 'datos/ejemplos_few_shot.json')
        self.assertEqual(validate(corpus, examples), [])
        self.assertEqual(len(corpus), 60)
        self.assertTrue(validate(corpus[:-1], examples))
        changed = [dict(row) for row in corpus]
        changed[1]['id'] = changed[0]['id']
        self.assertTrue(validate(changed, examples))

    def test_corpus_expected_acceptance(self):
        grammar = Grammar(ROOT / 'gramatica_minic.txt')
        for row in read_json(ROOT / 'datos/corpus_es.json'):
            with self.subTest(id=row['id']):
                self.assertEqual(parse_detailed(row['texto'], grammar, True).accepted, row['esperado_cfg'])

    def test_confusion_matrix(self):
        result = binary_metrics([True, True, False, False], [True, False, True, False])
        self.assertEqual([result[key] for key in ['tp', 'fp', 'tn', 'fn']], [1, 1, 1, 1])
        self.assertEqual(result['precision'], .5)
        self.assertEqual(result['recall'], .5)
        self.assertEqual(result['correct_rejection'], .5)
        self.assertIsNone(binary_metrics([], [])['precision'])
        with self.assertRaises(ValueError):
            binary_metrics([True], [])

    def test_proof_validation(self):
        grammar = Grammar(ROOT / 'gramatica_minic.txt')
        source = 'El niño leyó el libro'
        result = parse_detailed(source, grammar, True)
        answer = dict(accepted=True, productions=result.productions)
        self.assertTrue(validate_answer(answer, source, grammar)['valid'])
        self.assertFalse(validate_answer(answer, 'Los niños leyó el libro', grammar)['valid'])
        self.assertFalse(validate_answer(dict(accepted=True, productions=[]), source, grammar)['valid'])
        self.assertFalse(validate_answer(dict(accepted=False), source, grammar)['valid'])
        self.assertTrue(validate_answer(dict(accepted=False, productions=[]), 'El niño corren', grammar)['valid'])
        self.assertFalse(validate_answer(dict(accepted=False, productions=[dict(nonterminal='Inventado')]),
                                         'El niño corren', grammar)['valid'])

    def test_api_transport_and_resume_local_fixture(self):
        grammar = Grammar(ROOT / 'gramatica_minic.txt')
        text = read_json(ROOT / 'datos/corpus_es.json')[0]['texto']
        proof = parse_detailed(text, grammar, True).productions
        answer = dict(accepted=True, productions=proof)
        calls = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                gemini = self.path.endswith(':generateContent')
                anthropic = self.path.endswith('/messages')
                auth_header = 'x-goog-api-key' if gemini else 'x-api-key' if anthropic else 'Authorization'
                calls.append((payload, self.headers.get(auth_header), self.path,
                              self.headers.get('anthropic-version')))
                if gemini:
                    reply = dict(candidates=[dict(content=dict(parts=[
                        dict(text='thought', thought=True), dict(text=json.dumps(answer))]))],
                                 modelVersion='local-gemini-fixture')
                elif anthropic:
                    reply = dict(content=[dict(type='text', text=json.dumps(answer))])
                else:
                    reply = dict(choices=[dict(message=dict(content=json.dumps(answer)))])
                body = json.dumps(reply).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for provider, protocol, path, expected_auth in [
                ('otro-proveedor', 'chat-completions', 'v1/chat/completions', 'Bearer local-test-secret'),
                ('gemini', 'gemini', 'v1beta/models/{model}:generateContent', 'local-test-secret'),
                ('anthropic', 'anthropic', 'v1/messages', 'local-test-secret'),
            ]:
                prefix = provider.replace('-', '_').upper()
                inherited = {name: value for name, value in os.environ.items()
                             if not name.startswith(('LLM_', prefix + '_'))}
                with (self.subTest(provider=provider), tempfile.TemporaryDirectory() as directory,
                      patch.dict(os.environ, inherited, clear=True),
                      patch('experimentos.llm_config.ROOT', Path(directory))):
                    calls.clear()
                    (Path(directory) / '.env').write_text(
                        f'# Perfil local\nLLM_PROVIDER={provider}\nLLM_LIMIT=1\n'
                        f'{prefix}_PROTOCOL={protocol}\n{prefix}_MODEL=local-fixture\n'
                        f'{prefix}_ENDPOINT=http://127.0.0.1:{server.server_port}/{path}\n'
                        f'{prefix}_API_KEY="local-test-secret"\n{prefix}_API_VERSION=2023-06-01\n'
                        f'{prefix}_TOKEN_FIELD=max_tokens\n{prefix}_JSON_MODE=false\n'
                        f'{prefix}_OUTPUT_DIR=logs\n',
                        encoding='utf-8')
                    args = ['--execute']
                    before = datetime.now(timezone.utc)
                    self.assertEqual(llm_main(args), 0)
                    self.assertEqual(llm_main(args), 0)
                    self.assertEqual(len(calls), 2)
                    log_dir = Path(directory) / 'logs'
                    log = (log_dir / 'respuestas.jsonl').read_text(encoding='utf-8')
                    self.assertNotIn('local-test-secret', log)
                    rows = [json.loads(line) for line in log.splitlines()]
                    self.assertEqual([row['variant'] for row in rows], ['zero_shot', 'few_shot'])
                    for row, (payload, auth, sent_path, version) in zip(rows, calls):
                        self.assertEqual(sent_path, '/' + path.replace('{model}', 'local-fixture'))
                        self.assertEqual(auth, expected_auth)
                        self.assertEqual(version, '2023-06-01' if protocol == 'anthropic' else None)
                        self.assertEqual(row['request'], payload)
                        self.assertEqual(row['provider'], provider)
                        self.assertIn('raw_response', row)
                        self.assertTrue(row['accepted'])
                        self.assertTrue(before <= datetime.fromisoformat(row['timestamp_utc'])
                                        <= datetime.now(timezone.utc))
                    zero, few = [call[0] for call in calls]
                    if protocol == 'gemini':
                        self.assertIn('PRODUCCIONES', zero['systemInstruction']['parts'][0]['text'])
                        self.assertEqual(zero['contents'], [dict(role='user', parts=[dict(text=text)])])
                        self.assertEqual(few['generationConfig'], zero['generationConfig'])
                        self.assertEqual(few['contents'][-1], zero['contents'][0])
                        self.assertIn('model', [turn['role'] for turn in few['contents']])
                    elif protocol == 'anthropic':
                        self.assertIn('PRODUCCIONES', zero['system'])
                        self.assertEqual(zero['messages'], [dict(role='user', content=text)])
                        self.assertEqual(few['messages'][-1], zero['messages'][0])
                    else:
                        self.assertIn('max_tokens', zero)
                        self.assertNotIn('response_format', zero)
                    with patch.object(sys, 'argv', ['resumir_llm']):
                        summarize_llm()
                    summary = read_json(log_dir / 'resumen.json')
                    self.assertEqual([result['completed'] for result in summary['summaries']], [1, 1])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_grouped_calls_are_scored_by_sentence_id(self):
        grammar = Grammar(ROOT / 'gramatica_minic.txt')
        gold = read_json(ROOT / 'datos/corpus_es.json')[:3]

        def simulate_call(_key, request, _config):
            items = json.loads(request['contents'][-1]['parts'][0]['text'])
            rows = []
            for item in reversed(items):
                parsed = parse_detailed(item['texto'], grammar, True)
                rows.append(dict(id=item['id'], accepted=parsed.accepted,
                                 productions=parsed.productions if parsed.accepted else []))
            return dict(candidates=[dict(content=dict(parts=[dict(text=json.dumps(dict(results=rows)))]))])

        with (tempfile.TemporaryDirectory() as directory,
              patch('experimentos.llm.send', side_effect=simulate_call) as send,
              patch.dict(os.environ, {'GEMINI_API_KEY': 'local-test-key', 'GEMINI_MIN_SECONDS_BETWEEN_CALLS': '0'})):
            args = ['--execute', '--provider', 'gemini', '--model', 'local-fixture', '--limit', '3',
                    '--batch-size', '60', '--output-dir', directory, '--max-new-calls', '2',
                    '--endpoint', 'http://127.0.0.1:80/models/local-fixture:generateContent']
            self.assertEqual(llm_main(args), 0)
            self.assertEqual(llm_main(args), 0)
            self.assertEqual(send.call_count, 2)
            zero, few = [call.args[1] for call in send.call_args_list]
            self.assertEqual(len(zero['contents']), 1)
            self.assertGreater(len(few['contents']), 1)
            self.assertEqual(zero['contents'][-1], few['contents'][-1])
            self.assertEqual(json.loads(zero['contents'][-1]['parts'][0]['text']),
                             [{key: row[key] for key in ['id', 'texto']} for row in gold])
            root = Path(directory)
            self.assertEqual(len((root / 'respuestas.jsonl').read_text(encoding='utf-8').splitlines()), 2)
            results = read_json(root / 'resultados.json')['results']
            self.assertEqual([result['id'] for result in results], [row['id'] for row in gold] * 2)
            self.assertTrue(all(result['adherence']['valid'] for result in results))
            with patch.object(sys, 'argv', ['resumir_llm', '--input', str(root / 'resultados.json')]):
                summarize_llm()
            summary = read_json(root / 'resumen.json')['summaries']
            self.assertEqual([row['cfg']['n'] for row in summary], [3, 3])

        items = [{key: row[key] for key in ['id', 'texto']} for row in gold]
        omitted = score_batch({'results': []}, items, grammar)
        self.assertTrue(all(row.get('execution_error') and 'accepted' not in row for row in omitted))


if __name__ == '__main__':
    unittest.main()
