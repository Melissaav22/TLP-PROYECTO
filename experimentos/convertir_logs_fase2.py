
import argparse
import csv
import hashlib
import json
from pathlib import Path

from .common import ROOT


def sha(path, normalizar_lf=False):
    datos = Path(path).read_bytes()
    if normalizar_lf:
        datos = datos.replace(b"\r\n", b"\n")
    return hashlib.sha256(datos).hexdigest()


def rel(path):
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def leer_corpus(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def comprobar_corpus_json(corpus, ruta_json):
    """El corpus JSON del LLM debe ser el mismo que el CSV canónico."""
    datos = json.loads(Path(ruta_json).read_text(encoding="utf-8"))
    problemas = []
    if [d["id"] for d in datos] != [c["id"] for c in corpus]:
        problemas.append("los ids o su orden difieren")
    else:
        for d, c in zip(datos, corpus):
            if d["texto"] != c["texto"]:
                problemas.append(f"{c['id']}: texto distinto")
            if (d["esperado_cfg"] is True) != (c["esperado_gramatica"] == "aceptada"):
                problemas.append(f"{c['id']}: etiqueta de gramática distinta")
            if (d["gramatical_espanol"] is True) != (c["esperado_espanol"] == "aceptada"):
                problemas.append(f"{c['id']}: etiqueta de español distinta")
    if problemas:
        raise SystemExit("El corpus JSON del LLM no coincide con el CSV canónico:\n  "
                         + "\n  ".join(problemas[:10]))


def base(corpus_hash, criteria_hash):
    return dict(corpus_sha256=corpus_hash, criteria_sha256=criteria_hash, variant="principal",
                criterion=None, run=1, model=None, tool_version=None, grammar_followed=None)


def convertir_registro(ruta, ruta_meta, corpus_hash, criteria_hash):
    """spaCy / NLTK / NLTK-full: una fila convertida por línea del registro."""
    meta = json.loads(Path(ruta_meta).read_text(encoding="utf-8"))
    sha_lf = sha(ruta, normalizar_lf=True)
    if sha_lf != meta["registro_sha256"]:
        raise SystemExit("registro.jsonl no coincide con el SHA-256 guardado en meta.json "
                         "(¿se modificó el archivo?).")
    if meta["corpus_sha256"] != corpus_hash:
        raise SystemExit("La corrida de spaCy/NLTK usó otro corpus que el CSV canónico.")
    versiones = {}
    for nombre, info in meta["herramientas"].items():
        versiones[nombre] = (f"{info['tool']} {info['version']}", info.get("model"))
    salida = []
    with Path(ruta).open(encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            r = json.loads(linea)
            version, modelo = versiones[r["tool"]]
            reg = base(corpus_hash, criteria_hash)
            reg.update(id=r["id"], tool=r["tool"], criterion=r["criterion"], run=r["run"],
                       timestamp_utc=r["timestamp_utc"], tool_version=version, model=modelo,
                       execution_error=r["error"],
                       raw_output=None if r["status"] != "ok" else
                       {"accepted": r["accepted"], "motivo": r["decision"]["motivo"]},
                       raw_response={"fuente": rel(ruta), "linea": n, "fuente_sha256_lf": sha_lf},
                       source_corpus_sha256=r["corpus_sha256"],
                       source_criterios_sha256=r["criterios_sha256"],
                       source_criterios_version=r["criterios_version"])
            salida.append(reg)
    return salida


def convertir_llm(ruta, corpus, corpus_hash, criteria_hash):
    """Gemini: cada llamada por lotes se parte en un registro por oración."""
    fuente_sha = sha(ruta, normalizar_lf=True)
    llamadas = []
    with Path(ruta).open(encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            llamadas.append((n, json.loads(linea)))
    llamadas = [(n, r) for n, r in llamadas if r.get("transport_completed")]
    llamadas.sort(key=lambda x: x[1]["timestamp_utc"])
    corridas, salida = {}, []
    for n, r in llamadas:
        for e in r.get("evaluations", []):
            clave = (r["variant"], e["id"])
            corridas[clave] = corridas.get(clave, 0) + 1
            reg = base(corpus_hash, criteria_hash)
            reg.update(id=e["id"], tool="llm_gemini", variant=r["variant"], criterion="unico",
                       run=corridas[clave], timestamp_utc=r["timestamp_utc"], model=r["model"],
                       execution_error=e.get("execution_error"),
                       raw_output=e.get("answer") if not e.get("execution_error") else None,
                       grammar_followed=(e.get("adherence") or {}).get("valid"),
                       raw_response={"fuente": rel(ruta), "linea": n, "lote": r["id"],
                                     "fuente_sha256_lf": fuente_sha},
                       batch_id=r["id"], batch_size=r["metadata"].get("batch_size"),
                       provider=r.get("provider"),
                       adherence_reason=(e.get("adherence") or {}).get("reason"),
                       source_corpus_sha256=r["metadata"].get("corpus_sha256"))
            salida.append(reg)
    # oraciones sin respuesta en una variante: se registran como error de ejecución
    for variante in sorted({v for v, _ in corridas}):
        for fila in corpus:
            if (variante, fila["id"]) not in corridas:
                reg = base(corpus_hash, criteria_hash)
                reg.update(id=fila["id"], tool="llm_gemini", variant=variante, criterion="unico",
                           timestamp_utc=llamadas[-1][1]["timestamp_utc"],
                           model=llamadas[-1][1]["model"], raw_output=None,
                           execution_error="sin_registro: el log no tiene respuesta para esta oración",
                           raw_response={"fuente": rel(ruta), "fuente_sha256_lf": fuente_sha})
                salida.append(reg)
    return salida


def escribir(path, registros):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(ROOT / "datos/corpus_fase2.csv"))
    ap.add_argument("--corpus-json", default=str(ROOT / "datos/corpus_ordenado.json"))
    ap.add_argument("--criteria-file", default=str(ROOT / "datos/criterios_evaluacion_fase2.txt"))
    ap.add_argument("--registro", default=str(ROOT / "resultados/fase2/registro.jsonl"))
    ap.add_argument("--meta", default=str(ROOT / "resultados/fase2/meta.json"))
    ap.add_argument("--llm", default=str(ROOT / "resultados/llm/corpus-ordenado/respuestas.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "resultados/evaluacion/logs"))
    args = ap.parse_args(argv)

    corpus = leer_corpus(args.corpus)
    comprobar_corpus_json(corpus, args.corpus_json)
    corpus_hash, criteria_hash = sha(args.corpus), sha(args.criteria_file)

    nlp = convertir_registro(args.registro, args.meta, corpus_hash, criteria_hash)
    llm = convertir_llm(args.llm, corpus, corpus_hash, criteria_hash)
    out = Path(args.out)
    escribir(out / "spacy_nltk.jsonl", nlp)
    escribir(out / "llm_gemini.jsonl", llm)
    print(f"corpus: {len(corpus)} oraciones (JSON del LLM coincide con el CSV)")
    print(f"spaCy/NLTK: {len(nlp)} registros -> {rel(out / 'spacy_nltk.jsonl')}")
    print(f"LLM: {len(llm)} registros -> {rel(out / 'llm_gemini.jsonl')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())