"""Corrida de la Fase 2 para spaCy y NLTK: guarda la SALIDA CRUDA y recalcula los veredictos.

Uso (desde la raíz del proyecto, con el entorno del proyecto activo):

    python -m experimentos.correr_fase2 --corpus datos/corpus_fase2.csv

Qué hace, en orden:
  1. Comprueba el estado de git (corrida oficial): el código y los datos deben estar
     commiteados y debe existir la etiqueta `criterios-v1`. Con --ensayo se omite y la
     corrida queda marcada como ensayo (no usar sus números en el informe).
  2. Para cada repetición, herramienta y oración, guarda la salida cruda de la herramienta.
  3. Aplica los criterios con `criterios.decidir` y escribe una línea JSON por
     (oración, herramienta, criterio, repetición) en `registro.jsonl`.
  4. VERIFICA: relee el registro, recalcula cada veredicto solo desde `raw_output` y exige
     que coincida con lo guardado; también exige que las repeticiones den la misma salida.

Archivos de salida (carpeta --salida, por defecto resultados/fase2):
  registro.jsonl   una línea por (id, herramienta, criterio, repeticion)
  meta.json        versiones, huellas SHA-256, commit, fecha, resultado de la verificación

Este script NO calcula métricas contra las etiquetas gold: eso lo hace el script de métricas.
"""
import argparse
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter
import unicodedata

from .common import ROOT, digest, write_json
from . import criterios

ETIQUETA_GIT = 'criterios-v1'
# variante -> criterios que se le aplican (nltk, de la Fase 1, solo tiene categorías gruesas)
CRITERIOS_POR_VARIANTE = {'spacy': ('C0', 'C1', 'C2'),
                          'nltk': ('C0', 'C1'),
                          'nltk_full': ('C0', 'C1', 'C2')}


# ------------------------------------------------------------------------- git
def _git(*args):
    try:
        r = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def estado_git():
    """Commit, si hay cambios sin commitear en código/datos, y a qué commit apunta la etiqueta."""
    commit = _git('rev-parse', 'HEAD')
    if commit is None:
        return dict(es_repositorio=False, commit=None, sucio=None, archivos_sucios=[],
                    etiqueta_commit=None)
    sucios = _git('status', '--porcelain', '--', 'experimentos', 'datos', 'minic',
                  'gramatica_minic.txt', 'main.py', '.gitattributes') or ''
    lineas = [l for l in sucios.splitlines() if l.strip()]
    return dict(es_repositorio=True, commit=commit, sucio=bool(lineas), archivos_sucios=lineas,
                etiqueta_commit=_git('rev-parse', '--verify', '-q', f'{ETIQUETA_GIT}^{{commit}}'))


def comprobar_oficial(estado):
    """Lista de problemas que impiden una corrida oficial (vacía = todo bien)."""
    problemas = []
    if not estado['es_repositorio']:
        problemas.append('no es un repositorio git')
        return problemas
    if estado['sucio']:
        problemas.append('hay cambios sin commitear en código/datos: ' + '; '.join(estado['archivos_sucios']))
    if estado['etiqueta_commit'] is None:
        problemas.append(f'no existe la etiqueta {ETIQUETA_GIT} (congelar antes de correr)')
    return problemas


# ------------------------------------------------------------------- herramientas
def _preparar(nombre):
    """Devuelve (funcion_cruda, info) o lanza la excepción de inicialización."""
    if nombre == 'spacy':
        from .adaptadores import SpacySpanish
        ad = SpacySpanish()
        def cruda(texto):
            return criterios.spacy_raw(ad.nlp(unicodedata.normalize('NFC', texto)))
    elif nombre == 'nltk':
        from .adaptadores import NltkSpanish
        ad = NltkSpanish()
        def cruda(texto):
            r = ad.analyze(texto)
            return criterios.nltk_raw(r['tokens'], r['pos'])
    elif nombre == 'nltk_full':
        from .nltk_full import NltkSpanishFull
        ad = NltkSpanishFull()
        def cruda(texto):
            r = ad.analyze(texto)
            return criterios.nltk_raw(r['tokens'], r['tags'])
    else:
        raise ValueError(nombre)
    return cruda, ad.info


def leer_corpus(ruta):
    with open(ruta, encoding='utf-8', newline='') as f:
        filas = list(csv.DictReader(f))
    for col in ('id', 'texto'):
        if filas and col not in filas[0]:
            raise SystemExit(f'el corpus no tiene la columna «{col}»')
    ids = [f['id'] for f in filas]
    if len(ids) != len(set(ids)):
        raise SystemExit('el corpus tiene ids repetidos')
    return filas


# ------------------------------------------------------------------ verificación
def verificar(ruta_registro):
    """Relee el registro y comprueba (a) que cada veredicto se recalcula igual desde raw_output
    y (b) que las repeticiones de un mismo (id, herramienta) dieron la misma salida cruda."""
    n = distintos = 0
    ejemplos = []
    crudas = {}
    inestables = set()
    with open(ruta_registro, encoding='utf-8') as f:
        for linea in f:
            reg = json.loads(linea)
            if reg['status'] != 'ok':
                continue
            n += 1
            nuevo = criterios.decidir(reg['tool'], reg['criterion'], reg['raw_output'])
            if nuevo['accepted'] != reg['accepted'] or nuevo['motivo'] != reg['decision']['motivo']:
                distintos += 1
                if len(ejemplos) < 5:
                    ejemplos.append(f"{reg['id']} {reg['tool']} {reg['criterion']} run {reg['run']}")
            clave = (reg['id'], reg['tool'])
            salida = json.dumps(reg['raw_output'], sort_keys=True)
            if clave in crudas and crudas[clave] != salida:
                inestables.add(clave)
            crudas.setdefault(clave, salida)
    return dict(registros_verificados=n, veredictos_distintos=distintos,
                ejemplos_distintos=ejemplos, pares_con_salida_inestable=len(inestables),
                correcta=(distintos == 0 and not inestables and n > 0))


# ------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--corpus', default='datos/corpus_fase2.csv')
    ap.add_argument('--salida', default='resultados/fase2')
    ap.add_argument('--repeticiones', type=int, default=3)
    ap.add_argument('--herramientas', nargs='+', default=list(CRITERIOS_POR_VARIANTE),
                    choices=list(CRITERIOS_POR_VARIANTE))
    ap.add_argument('--ensayo', action='store_true',
                    help='omite la exigencia de git limpio y etiqueta; la corrida queda marcada como ensayo')
    args = ap.parse_args(argv)

    corpus = Path(args.corpus)
    if not corpus.is_absolute():
        corpus = ROOT / corpus
    salida = Path(args.salida)
    if not salida.is_absolute():
        salida = ROOT / salida

    git = estado_git()
    problemas = comprobar_oficial(git)
    if problemas and not args.ensayo:
        print('NO se puede hacer una corrida oficial:', file=sys.stderr)
        for p in problemas:
            print('  -', p, file=sys.stderr)
        print('Corrige lo anterior, o usa --ensayo para una prueba (sus números no van al informe).',
              file=sys.stderr)
        return 2

    filas = leer_corpus(corpus)
    herramientas, info, no_disponibles = {}, {}, {}
    for nombre in args.herramientas:
        try:
            herramientas[nombre], info[nombre] = _preparar(nombre)
        except Exception as e:                                   # noqa: BLE001 (se registra tal cual)
            no_disponibles[nombre] = f'{type(e).__name__}: ' + ' '.join(str(e).replace('*', ' ').split())[:300]
            print(f'AVISO: {nombre} no disponible ({no_disponibles[nombre]})', file=sys.stderr)

    salida.mkdir(parents=True, exist_ok=True)
    ruta_reg = salida / 'registro.jsonl'
    inicio = datetime.now(timezone.utc)
    corpus_sha = digest(corpus)
    crit_sha = criterios.hash_criterios()
    errores = 0
    with open(ruta_reg, 'w', encoding='utf-8', newline='\n') as out:
        for rep in range(1, args.repeticiones + 1):
            for nombre, cruda in herramientas.items():
                for fila in filas:
                    t0 = perf_counter()
                    try:
                        raw, err = cruda(fila['texto']), None
                    except Exception as e:                       # noqa: BLE001
                        raw, err = None, f'{type(e).__name__}: {e}'
                    seg = perf_counter() - t0
                    for crit in CRITERIOS_POR_VARIANTE[nombre]:
                        reg = dict(id=fila['id'], tool=nombre, criterion=crit, run=rep,
                                   timestamp_utc=datetime.now(timezone.utc).isoformat(),
                                   corpus_sha256=corpus_sha, criterios_sha256=crit_sha,
                                   criterios_version=criterios.CRITERIOS_VERSION,
                                   seconds=round(seg, 6))
                        if err is None:
                            dec = criterios.decidir(nombre, crit, raw)
                            reg.update(status='ok', error=None, raw_output=raw,
                                       accepted=dec['accepted'], decision=dec)
                        else:
                            errores += 1
                            reg.update(status='error', error=err, raw_output=None,
                                       accepted=None, decision=None)
                        out.write(json.dumps(reg, ensure_ascii=False, sort_keys=True) + '\n')

    ver = verificar(ruta_reg)
    meta = dict(ensayo=bool(args.ensayo), problemas_git=problemas, git=git,
                inicio_utc=inicio.isoformat(), fin_utc=datetime.now(timezone.utc).isoformat(),
                corpus=str(corpus.relative_to(ROOT)) if corpus.is_relative_to(ROOT) else str(corpus),
                corpus_sha256=corpus_sha, n_oraciones=len(filas), repeticiones=args.repeticiones,
                criterios_version=criterios.CRITERIOS_VERSION, criterios_sha256=crit_sha,
                herramientas=info, herramientas_no_disponibles=no_disponibles,
                registros_con_error=errores,
                registro_sha256=hashlib.sha256(ruta_reg.read_bytes()).hexdigest(),
                python=sys.version.split()[0], plataforma=platform.platform(),
                verificacion=ver)
    write_json(salida / 'meta.json', meta)

    print(f"{'ENSAYO' if args.ensayo else 'OFICIAL'}: {len(filas)} oraciones x {len(herramientas)} "
          f"herramientas x {args.repeticiones} repeticiones -> {ruta_reg}")
    print(f"verificación: {ver['registros_verificados']} registros recalculados, "
          f"{ver['veredictos_distintos']} distintos, {ver['pares_con_salida_inestable']} pares inestables"
          f" -> {'CORRECTA' if ver['correcta'] else 'FALLA'}")
    if no_disponibles or errores or not ver['correcta']:
        print('Hay herramientas no disponibles, errores o una verificación fallida: revisar meta.json.',
              file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
