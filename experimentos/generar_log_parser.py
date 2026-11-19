import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from minic.grammar import Grammar
from minic.parser import parse_detailed
from minic.trees import bracketed

from .common import ROOT, _git, digest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=str(ROOT / "datos/corpus_fase2.csv"))
    ap.add_argument("--criteria-file", default=str(ROOT / "datos/criterios_evaluacion_fase2.txt"))
    ap.add_argument("--output", default=str(ROOT / "resultados/evaluacion/logs/parser_propio.jsonl"))
    ap.add_argument("--run", type=int, default=1)
    args = ap.parse_args(argv)

    import hashlib
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    corpus_hash, criteria_hash = sha(args.corpus), sha(args.criteria_file)
    commit = _git("rev-parse", "HEAD") or "sin-git"
    version = f"commit {commit}; gramatica_sha256 {digest(ROOT / 'gramatica_minic.txt')}"
    grammar = Grammar(ROOT / "gramatica_minic.txt")

    with Path(args.corpus).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    errores = 0
    with out.open("a", encoding="utf-8", newline="\n") as log:
        for row in rows:
            record = dict(id=row["id"], tool="parser_propio", variant="principal",
                          criterion="unico", run=args.run,
                          timestamp_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          tool_version=version, model=None, corpus_sha256=corpus_hash,
                          criteria_sha256=criteria_hash, grammar_followed=None)
            try:
                result = parse_detailed(row["texto"], grammar, True)
                record["raw_output"] = dict(accepted=result.accepted, tree=bracketed(result.tree),
                                            diagnostics=[d.to_dict() for d in result.diagnostics])
                record["execution_error"] = None
            except Exception as exc:  # fallo de la herramienta, no rechazo
                record["raw_output"] = None
                record["execution_error"] = f"{type(exc).__name__}: {exc}"
                errores += 1
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{len(rows)} oraciones, corrida {args.run}, {errores} errores de ejecución -> {out}")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())