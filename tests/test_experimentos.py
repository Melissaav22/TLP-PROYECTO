"""Regresiones de corpus, métricas, derivaciones y transporte reanudable."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from experimentos.common import ROOT, digest, read_json
from experimentos.llm import main as llm_main
from experimentos.metricas import binary_metrics
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
                calls.append(payload)
                body = json.dumps(dict(choices=[dict(message=dict(content=json.dumps(answer)))],
                                       usage=dict(prompt_tokens=10, completion_tokens=20))).encode()
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
            with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'LLM_API_KEY': 'local-test-secret'}):
                args = ['--execute', '--model', 'local-fixture', '--endpoint',
                        f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
                        '--limit', '1', '--output-dir', directory]
                self.assertEqual(llm_main(args), 0)
                self.assertEqual(llm_main(args), 0)
                self.assertEqual(len(calls), 2)
                log = (Path(directory) / 'respuestas.jsonl').read_text(encoding='utf-8')
                self.assertNotIn('local-test-secret', log)
                self.assertEqual(len(log.splitlines()), 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
