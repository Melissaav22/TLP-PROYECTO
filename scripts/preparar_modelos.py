"""Descarga el corpus oficial de NLTK usado por el baseline estadístico."""
from pathlib import Path
import hashlib
import json
import nltk

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    nltk.download('cess_esp', download_dir=str(ROOT / '.models/nltk'), raise_on_error=True)
    manifest = json.loads((ROOT / 'datos/modelos.json').read_text(encoding='utf-8'))
    actual = hashlib.sha256((ROOT / '.models/nltk/corpora/cess_esp.zip').read_bytes()).hexdigest()
    if actual != manifest['nltk']['training_sha256']:
        raise ValueError('El corpus CESS-ESP descargado difiere del utilizado en los resultados')
    print('CESS-ESP coincide con la huella del experimento.')
