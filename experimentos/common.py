"""Persistencia y metadatos compartidos por los experimentos."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    path = Path(path)
    content = (path.read_text(encoding='utf-8').encode('utf-8')
               if path.suffix in {'.py', '.txt', '.json', '.mjs'} else path.read_bytes())
    return hashlib.sha256(content).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def metadata(corpus):
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    sources = [ROOT / 'main.py']
    for directory in ['minic', 'experimentos']:
        sources.extend((ROOT / directory).glob('*.py'))
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in sorted(sources)}
    return dict(created_utc=datetime.now(timezone.utc).isoformat(), commit=commit,
                hash_policy='SHA-256; texto UTF-8 con saltos LF, binarios sin transformacion',
                source_hashes=source_hashes,
                tracked_changes=bool(subprocess.run(['git', 'diff', '--name-only'], cwd=ROOT,
                                      capture_output=True, text=True, check=True).stdout.strip()),
                grammar_sha256=digest(ROOT / 'gramatica_minic.txt'),
                corpus_sha256=digest(corpus))
