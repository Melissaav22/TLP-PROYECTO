#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

GOLD_FIELDS = {
    "espanol": "esperado_espanol",
    "gramatica": "esperado_gramatica",
}
CORPUS_REQUIRED = {
    "id", "nivel", "texto", "esperado_espanol", "esperado_gramatica",
    "fenomeno", "categoria_error", "en_vocabulario",
}
LOG_REQUIRED = {
    "id", "tool", "variant", "criterion", "run", "timestamp_utc",
    "tool_version", "model", "corpus_sha256", "criteria_sha256",
    "raw_output", "execution_error", "grammar_followed",
}
KEY_FIELDS = ("id", "tool", "variant", "criterion", "run")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_corpus(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    elif suffix in {".xlsx", ".xls"}:
        if pd is None:
            raise RuntimeError("Para leer Excel instala pandas y openpyxl.")
        frame = pd.read_excel(path, sheet_name="corpus_fase2")
        frame = frame.astype(object).where(pd.notna(frame), None)
        rows = frame.to_dict("records")
    else:
        raise ValueError("El corpus debe ser CSV o XLSX.")

    if not rows:
        raise ValueError("El corpus está vacío.")
    missing = CORPUS_REQUIRED - set(rows[0])
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {sorted(missing)}")

    seen = set()
    for row in rows:
        row["id"] = str(row["id"]).strip()
        if not row["id"] or row["id"] in seen:
            raise ValueError(f"ID vacío o duplicado: {row['id']!r}")
        seen.add(row["id"])
        row["nivel"] = int(row["nivel"])
        for field in GOLD_FIELDS.values():
            label = str(row[field]).strip().lower()
            if label not in {"aceptada", "rechazada"}:
                raise ValueError(f"Etiqueta inválida: {row['id']} / {field}={row[field]!r}")
            row[field] = label
        row["fenomeno"] = str(row.get("fenomeno") or "sin_especificar").strip()
        row["categoria_error"] = str(row.get("categoria_error") or "sin_especificar").strip()
        row["en_vocabulario"] = str(row.get("en_vocabulario") or "sin_especificar").strip().lower()
    return rows


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_number, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}, línea {line_number}: JSON inválido: {exc}") from exc
            missing = LOG_REQUIRED - set(record)
            if missing:
                raise ValueError(
                    f"{path}, línea {line_number}: faltan campos {sorted(missing)}"
                )
            records.append(record)
    return records


def normalize_decision(raw_output: Any) -> tuple[bool | None, str]:
    """
    Normalizador único para todos los enfoques.

    Retorna:
      (True,  'ok')            -> aceptada
      (False, 'ok')            -> rechazada
      (None,  'unreadable')    -> no se pudo interpretar la salida

    No altera raw_output. La salida original permanece en los logs y en
    normalized_records.csv como raw_output_json.
    """
    value = raw_output

    if isinstance(value, bool):
        return value, "ok"

    if isinstance(value, dict):
        if isinstance(value.get("accepted"), bool):
            return value["accepted"], "ok"
        for key in ("decision", "classification", "result", "status", "label"):
            if key in value:
                value = value[key]
                break
        else:
            return None, "unreadable"

    if isinstance(value, str):
        text = value.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text).strip()
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return None, "unreadable"
            if isinstance(parsed, dict) and isinstance(parsed.get("accepted"), bool):
                return parsed["accepted"], "ok"
            return None, "unreadable"
        value = re.sub(r"\s+", " ", text.lower())
        accepted = {
            "aceptada", "aceptado", "accepted", "accept",
            "válida", "valida", "true",
        }
        rejected = {
            "rechazada", "rechazado", "rejected", "reject",
            "inválida", "invalida", "false",
        }
        if value in accepted:
            return True, "ok"
        if value in rejected:
            return False, "ok"

    return None, "unreadable"


def validate_records(records: list[dict[str, Any]], corpus: list[dict[str, Any]],
                     corpus_hash: str, criteria_hash: str) -> None:
    corpus_by_id = {row["id"]: row for row in corpus}
    seen_keys = set()
    for position, record in enumerate(records, 1):
        for field in ("id", "tool", "variant", "criterion"):
            if record[field] is None or str(record[field]).strip() == "":
                raise ValueError(f"Registro {position}: campo {field} vacío.")
        if record["id"] not in corpus_by_id:
            raise ValueError(f"Registro {position}: ID desconocido {record['id']}.")
        if not isinstance(record["run"], int) or record["run"] < 1:
            raise ValueError(f"Registro {position}: run debe ser entero >= 1.")
        key = tuple(record[field] for field in KEY_FIELDS)
        if key in seen_keys:
            raise ValueError(f"Llave duplicada (id, tool, variant, criterion, run): {key}")
        seen_keys.add(key)
        if record["corpus_sha256"] != corpus_hash:
            raise ValueError(f"Hash del corpus incorrecto en registro {position}.")
        if record["criteria_sha256"] != criteria_hash:
            raise ValueError(f"Hash de criterios incorrecto en registro {position}.")
        if record["execution_error"] not in (None, "") and not isinstance(record["execution_error"], str):
            raise ValueError(f"execution_error debe ser texto o null en registro {position}.")
        if record["grammar_followed"] not in (True, False, None):
            raise ValueError(f"grammar_followed debe ser true/false/null en registro {position}.")


def json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def enrich_records(records: list[dict[str, Any]], corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gold = {row["id"]: row for row in corpus}
    enriched = []
    for record in records:
        reference = gold[record["id"]]
        prediction, parse_status = normalize_decision(record["raw_output"])

        if record["execution_error"]:
            status = "execution_error"
            prediction = None
        elif parse_status == "unreadable":
            status = "unreadable"
        else:
            status = "ok"

        spanish_gold = reference["esperado_espanol"] == "aceptada"
        grammar_gold = reference["esperado_gramatica"] == "aceptada"
        enriched.append({
            "id": record["id"],
            "tool": record["tool"],
            "variant": record["variant"],
            "criterion": record["criterion"],
            "run": record["run"],
            "timestamp_utc": record["timestamp_utc"],
            "tool_version": record["tool_version"],
            "model": record["model"],
            "corpus_sha256": record["corpus_sha256"],
            "criteria_sha256": record["criteria_sha256"],
            "raw_output_json": json_compact(record["raw_output"]),
            "raw_response": record.get("raw_response"),
            "execution_error": record["execution_error"],
            # Valor recibido en el log (si el equipo lo registró).
            "grammar_followed_reported": record["grammar_followed"],
            # Cálculo objetivo: en el subconjunto diagnóstico, la predicción
            # coincide con la etiqueta gold de la CFG.
            "grammar_followed_by_output": (
                prediction == grammar_gold
                if status == "ok" and spanish_gold != grammar_gold else None
            ),
            "aligned_with_spanish_gold": (
                prediction == spanish_gold
                if status == "ok" and spanish_gold != grammar_gold else None
            ),
            "predicted_accepted": prediction,
            "decision_status": status,
            "gold_espanol": spanish_gold,
            "gold_gramatica": grammar_gold,
            "etiquetas_difieren": spanish_gold != grammar_gold,
            "nivel": reference["nivel"],
            "fenomeno": reference["fenomeno"],
            "categoria_error": reference["categoria_error"],
            "en_vocabulario": reference["en_vocabulario"],
            "texto": reference["texto"],
        })
    return enriched


def ratio(a: int, b: int) -> float | None:
    return a / b if b else None


def binary_metrics(rows: list[dict[str, Any]], gold_field: str) -> dict[str, Any]:
    valid = [row for row in rows if row["decision_status"] == "ok"]
    expected = [row[gold_field] for row in valid]
    predicted = [row["predicted_accepted"] for row in valid]

    tp = sum(e is True and p is True for e, p in zip(expected, predicted))
    fp = sum(e is False and p is True for e, p in zip(expected, predicted))
    tn = sum(e is False and p is False for e, p in zip(expected, predicted))
    fn = sum(e is True and p is False for e, p in zip(expected, predicted))

    total = len(rows)
    return {
        "n_registros": total,
        "n_evaluables": len(valid),
        "n_no_evaluables": total - len(valid),
        "cobertura_sobre_registros": ratio(len(valid), total),
        "n_diagnostico": sum(r["etiquetas_difieren"] for r in rows),
        "n_diagnostico_interpretable": sum(
            r["etiquetas_difieren"] and r["decision_status"] == "ok" for r in rows
        ),
        "n_sigue_cfg_en_diagnostico": sum(
            r["grammar_followed_by_output"] is True for r in rows
        ),
        "tasa_seguimiento_cfg_diagnostico": ratio(
            sum(r["grammar_followed_by_output"] is True for r in rows),
            sum(r["grammar_followed_by_output"] is not None for r in rows)
        ),
        "VP": tp, "FP": fp, "VN": tn, "FN": fn,
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "tasa_rechazo_correcto": ratio(tn, tn + fp),
        "exactitud": ratio(tp + tn, len(valid)),
    }


def make_metric_rows(enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Una fila de métricas por corrida y etiqueta gold. Esto mantiene visibles
    # las repeticiones y evita ocultarlas dentro de una única predicción.
    groups = defaultdict(list)
    for row in enriched:
        base = (row["tool"], row["variant"], row["criterion"], row["run"])
        groups[base].append(row)

    output = []
    for (tool, variant, criterion, run), rows in sorted(groups.items()):
        metadata = {
            "tool": tool, "variant": variant, "criterion": criterion, "run": run,
            "timestamp_utc": rows[0]["timestamp_utc"],
            "tool_version": rows[0]["tool_version"], "model": rows[0]["model"],
        }
        for gold_name, gold_field in (
            ("espanol", "gold_espanol"),
            ("gramatica", "gold_gramatica"),
        ):
            metric = binary_metrics(rows, gold_field)
            output.append({**metadata, "gold_target": gold_name, "scope": "general",
                           "group_value": "todos", **metric})

            for scope in ("nivel", "fenomeno"):
                values = sorted({str(r[scope]) for r in rows})
                for value in values:
                    subset = [r for r in rows if str(r[scope]) == value]
                    output.append({
                        **metadata, "gold_target": gold_name, "scope": scope,
                        "group_value": value, **binary_metrics(subset, gold_field)
                    })

            diagnostic = [r for r in rows if r["etiquetas_difieren"]]
            output.append({
                **metadata, "gold_target": gold_name, "scope": "diagnostico",
                "group_value": "etiquetas_difieren", **binary_metrics(diagnostic, gold_field)
            })
    return output


def make_run_summary(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Resume por herramienta/variante/criterio/objetivo/segmento.
    Las métricas se promedian entre corridas (macro-promedio descriptivo).
    Los conteos se suman y n_corridas indica cuántas corridas aportaron datos.
    """
    fields = ("tool", "variant", "criterion", "gold_target", "scope", "group_value")
    groups = defaultdict(list)
    for row in metric_rows:
        groups[tuple(row[f] for f in fields)].append(row)

    metric_names = (
        "precision", "recall", "tasa_rechazo_correcto", "exactitud",
        "cobertura_sobre_registros", "tasa_seguimiento_cfg_diagnostico",
    )
    count_names = (
        "n_registros", "n_evaluables", "n_no_evaluables",
        "VP", "FP", "VN", "FN",
    )
    summary = []
    for key, rows in sorted(groups.items(), key=lambda x: str(x[0])):
        item = dict(zip(fields, key))
        item["n_corridas"] = len(rows)
        for name in metric_names:
            vals = [r[name] for r in rows if r[name] is not None]
            item[name + "_promedio_corridas"] = sum(vals) / len(vals) if vals else None
        for name in count_names:
            item[name + "_suma_corridas"] = sum(r[name] for r in rows)
        summary.append(item)
    return summary


def make_comparison_table(summary, gold_target):
    rows = [
        r for r in summary
        if r["scope"] == "general"
        and r["gold_target"] == gold_target
    ]

    columns = [
        "tool",
        "variant",
        "criterion",
        "n_corridas",
        "n_evaluables_suma_corridas",
        "precision_promedio_corridas",
        "recall_promedio_corridas",
        "tasa_rechazo_correcto_promedio_corridas",
        "exactitud_promedio_corridas",
    ]

    return [
        {column: row.get(column) for column in columns}
        for row in rows
    ]



def make_error_rows(enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors = []
    for row in enriched:
        if row["decision_status"] == "execution_error":
            kind = "error_ejecucion"
        elif row["decision_status"] == "unreadable":
            kind = "respuesta_no_interpretable"
        else:
            kind = None

        if kind:
            errors.append({**{k: row[k] for k in (
                "id", "tool", "variant", "criterion", "run", "nivel", "fenomeno"
            )}, "tipo_error": kind, "detalle": row["execution_error"] or row["raw_output_json"]})
            continue

        for gold_name, gold_field in (
            ("espanol", "gold_espanol"), ("gramatica", "gold_gramatica")
        ):
            if row["predicted_accepted"] != row[gold_field]:
                errors.append({
                    **{k: row[k] for k in (
                        "id", "tool", "variant", "criterion", "run", "nivel", "fenomeno"
                    )},
                    "objetivo_gold": gold_name,
                    "tipo_error": "falso_positivo" if row["predicted_accepted"] else "falso_negativo",
                    "detalle": row["raw_output_json"],
                })
    return errors


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def make_plots(summary: list[dict[str, Any]], out_dir: Path) -> None:
    if plt is None:
        print("Aviso: matplotlib no está instalado; se omiten las gráficas.")
        return
    plot_dir = out_dir / "graficas"
    plot_dir.mkdir(parents=True, exist_ok=True)

    # Gráfica de precisión/recall/rechazo correcto para el objetivo español.
    rows = [
        r for r in summary
        if r["scope"] == "general" and r["gold_target"] == "espanol"
    ]
    if rows:
        labels = [f'{r["tool"]}\n{r["variant"]}/{r["criterion"]}' for r in rows]
        metrics = [
            ("precision_promedio_corridas", "Precisión"),
            ("recall_promedio_corridas", "Recall"),
            ("tasa_rechazo_correcto_promedio_corridas", "Rechazo correcto"),
        ]
        x = list(range(len(labels)))
        width = 0.25
        fig, ax = plt.subplots(figsize=(max(10, len(labels) * 1.5), 6))
        for i, (field, label) in enumerate(metrics):
            vals = [r[field] if r[field] is not None else 0 for r in rows]
            positions = [v + (i - 1) * width for v in x]
            ax.bar(positions, vals, width=width, label=label)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha="right")
        ax.set_ylim(0, 1)
        ax.set_ylabel("Proporción")
        ax.set_title("Métricas por enfoque — gold de español")
        ax.legend()
        fig.tight_layout()
        fig.savefig(plot_dir / "metricas_espanol.png", dpi=180)
        plt.close(fig)

    # Gráfica de recall por nivel para el gold español.
    rows = [
        r for r in summary
        if r["scope"] == "nivel" and r["gold_target"] == "espanol"
    ]
    if rows:
        systems = sorted({(r["tool"], r["variant"], r["criterion"]) for r in rows})
        levels = sorted({r["group_value"] for r in rows}, key=lambda v: int(v))
        fig, ax = plt.subplots(figsize=(10, 6))
        width = 0.8 / max(1, len(systems))
        for i, system in enumerate(systems):
            vals = []
            for level in levels:
                matches = [
                    r for r in rows
                    if (r["tool"], r["variant"], r["criterion"]) == system
                    and r["group_value"] == level
                ]
                value = matches[0]["recall_promedio_corridas"] if matches else None
                vals.append(value if value is not None else 0)
            positions = [j - 0.4 + width / 2 + i * width for j in range(len(levels))]
            ax.bar(positions, vals, width=width, label="/".join(system))
        ax.set_xticks(range(len(levels)))
        ax.set_xticklabels([f"Nivel {v}" for v in levels])
        ax.set_ylim(0, 1)
        ax.set_ylabel("Recall promedio entre corridas")
        ax.set_title("Recall por nivel — gold de español")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(plot_dir / "recall_por_nivel.png", dpi=180)
        plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluador de la Fase 2 TLP")
    parser.add_argument("--corpus", required=True, help="CSV canónico congelado del corpus")
    parser.add_argument("--criteria-file", required=True, help="Archivo con criterios compartidos")
    parser.add_argument("--logs", nargs="+", required=True, help="Archivos JSONL originales")
    parser.add_argument("--out", default="resultados/evaluacion", help="Carpeta de salida")
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    criteria_path = Path(args.criteria_file)
    log_paths = [Path(p) for p in args.logs]
    for path in [corpus_path, criteria_path, *log_paths]:
        if not path.is_file():
            raise FileNotFoundError(path)

    corpus_hash = sha256_file(corpus_path)
    criteria_hash = sha256_file(criteria_path)
    corpus = load_corpus(corpus_path)

    records = []
    for log_path in log_paths:
        records.extend(load_jsonl(log_path))

    validate_records(records, corpus, corpus_hash, criteria_hash)
    enriched = enrich_records(records, corpus)
    per_run = make_metric_rows(enriched)
    summary = make_run_summary(per_run)
    errors = make_error_rows(enriched)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "registros_normalizados.csv", enriched)
    write_csv(out / "metricas_por_corrida.csv", per_run)
    write_csv(out / "resumen_metricas.csv", summary)

# Tablas comparativas para cada etiqueta GOLD
    tabla_espanol = make_comparison_table(summary, "espanol")
    tabla_gramatica = make_comparison_table(summary, "gramatica")

    write_csv(
    out / "tabla_comparativa_espanol.csv",
    tabla_espanol
    )

    write_csv(
    out / "tabla_comparativa_gramatica.csv",
    tabla_gramatica
    )

    write_csv(out / "clasificacion_errores.csv", errors)
    make_plots(summary, out)

    # Salida determinista: no se añade hora de generación local.
    report = {
        "corpus_file": corpus_path.name,
        "corpus_sha256": corpus_hash,
        "criteria_file": criteria_path.name,
        "criteria_sha256": criteria_hash,
        "n_oraciones_corpus": len(corpus),
        "n_registros_logs": len(records),
        "n_ids_corpus": len({r["id"] for r in corpus}),
        "n_herramientas": len({r["tool"] for r in records}),
        "n_corridas": len({(r["tool"], r["variant"], r["criterion"], r["run"]) for r in records}),
        "n_subconjunto_diagnostico": sum(
            r["esperado_espanol"] != r["esperado_gramatica"] for r in corpus
        ),
        "metricas_por_corrida": per_run,
        "resumen_metricas": summary,
    }
    (out / "reporte_metricas.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8"
    )

    print(f"Corpus: {len(corpus)} oraciones")
    print(f"Registros evaluados: {len(records)}")
    print(f"Corridas/variantes: {report['n_corridas']}")
    print(f"Subconjunto diagnóstico: {report['n_subconjunto_diagnostico']} oraciones")
    print(f"Resultados guardados en: {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())