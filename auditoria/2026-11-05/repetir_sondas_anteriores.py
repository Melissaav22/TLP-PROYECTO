"""Reejecuta las 90 sondas previas y conserva sus resultados originales."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'sondas_previas', ROOT / 'auditoria' / 'verificar_auditoria.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
# El script original calcula el destino desde __file__; redirigir solo su salida.
module.__file__ = __file__
module.main()
