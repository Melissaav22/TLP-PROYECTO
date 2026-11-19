import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "datos/corpus_fase2.csv"
CRITERIOS = ROOT / "datos/criterios_evaluacion_fase2.txt"
EVALUADOR = ROOT / "experimentos/evaluacion_fase2.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def leer_corpus():
    with CORPUS.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def registro(fila, tool, raw, run=1, variant="principal", criterion="unico",
             error=None, followed=None):
    return {
        "id": fila["id"], "tool": tool, "variant": variant, "criterion": criterion,
        "run": run, "timestamp_utc": "2026-01-01T00:00:00Z",
        "tool_version": "sintetico", "model": None,
        "corpus_sha256": sha(CORPUS), "criteria_sha256": sha(CRITERIOS),
        "raw_output": raw, "execution_error": error, "grammar_followed": followed,
        "synthetic": True,
    }


def escribir(path, registros):
    with Path(path).open("w", encoding="utf-8", newline="\n") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def conteo(corpus, pred, gold):
    """VP, FP, VN, FN calculados a mano. pred/gold: dict id -> bool."""
    vp = fp = vn = fn = 0
    for fila in corpus:
        p, g = pred[fila["id"]], gold[fila["id"]]
        vp += g and p
        fp += (not g) and p
        vn += (not g) and (not p)
        fn += g and (not p)
    return vp, fp, vn, fn


def correr(logs, salida, esperado_ok=True):
    cmd = [sys.executable, str(EVALUADOR), "--corpus", str(CORPUS),
           "--criteria-file", str(CRITERIOS), "--logs", *map(str, logs),
           "--out", str(salida)]
    done = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if esperado_ok:
        assert done.returncode == 0, done.stderr
    return done


def leer_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class PruebasEvaluador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.corpus = leer_corpus()
        cls.g_esp = {f["id"]: f["esperado_espanol"] == "aceptada" for f in cls.corpus}
        cls.g_gra = {f["id"]: f["esperado_gramatica"] == "aceptada" for f in cls.corpus}
        cls.dif = [f["id"] for f in cls.corpus if cls.g_esp[f["id"]] != cls.g_gra[f["id"]]]

        regs = []
        # 1) oráculo de la gramática, dos corridas idénticas (prueba de repeticiones)
        for run in (1, 2):
            regs += [registro(f, "oraculo_gramatica", cls.g_gra[f["id"]], run=run) for f in cls.corpus]
        # 2) oráculo del español
        regs += [registro(f, "oraculo_espanol", cls.g_esp[f["id"]]) for f in cls.corpus]
        # 3) línea base "acepta todo"
        regs += [registro(f, "acepta_todo", True) for f in cls.corpus]
        # 4) criterios distintos de una misma herramienta, usando texto aceptada/rechazada
        regs += [registro(f, "herramienta_x", "aceptada", criterion="criterio_1") for f in cls.corpus]
        regs += [registro(f, "herramienta_x",
                          "aceptada" if cls.g_gra[f["id"]] else "rechazada",
                          criterion="criterio_2") for f in cls.corpus]
        cls.logs_ok = cls.dir / "logs_ok.jsonl"
        escribir(cls.logs_ok, regs)
        cls.out = cls.dir / "out"
        correr([cls.logs_ok], cls.out)
        cls.resumen = leer_csv(cls.out / "resumen_metricas.csv")
        cls.por_corrida = leer_csv(cls.out / "metricas_por_corrida.csv")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def fila(self, tool, gold, scope="general", valor="todos", criterion="unico"):
        hits = [r for r in self.resumen if r["tool"] == tool and r["gold_target"] == gold
                and r["scope"] == scope and r["group_value"] == valor and r["criterion"] == criterion]
        self.assertEqual(len(hits), 1, (tool, gold, scope, valor, criterion))
        return hits[0]

    def test_corpus_y_diagnostico(self):
        self.assertEqual(len(self.corpus), 67)
        self.assertEqual(len(self.dif), 11)

    def test_conteos_contra_calculo_independiente(self):
        for tool, pred in (("oraculo_gramatica", self.g_gra), ("oraculo_espanol", self.g_esp),
                           ("acepta_todo", {i: True for i in self.g_esp})):
            for nombre, gold in (("espanol", self.g_esp), ("gramatica", self.g_gra)):
                vp, fp, vn, fn = conteo(self.corpus, pred, gold)
                r = self.fila(tool, nombre)
                factor = int(r["n_corridas"])
                self.assertEqual([int(r[k + "_suma_corridas"]) for k in ("VP", "FP", "VN", "FN")],
                                 [vp * factor, fp * factor, vn * factor, fn * factor], (tool, nombre))
                if vp + fp:
                    self.assertAlmostEqual(float(r["precision_promedio_corridas"]), vp / (vp + fp))
                self.assertAlmostEqual(float(r["recall_promedio_corridas"]), vp / (vp + fn))
                self.assertAlmostEqual(float(r["tasa_rechazo_correcto_promedio_corridas"]), vn / (vn + fp))

    def test_oraculos_y_valores_a_mano(self):
        # oráculo de la gramática contra su propio gold: todo 1.0
        r = self.fila("oraculo_gramatica", "gramatica")
        for m in ("precision", "recall", "tasa_rechazo_correcto", "exactitud"):
            self.assertAlmostEqual(float(r[m + "_promedio_corridas"]), 1.0)
        # contra el gold de español: 33 VP, 1 FP, 23 VN, 10 FN
        r = self.fila("oraculo_gramatica", "espanol")
        self.assertEqual([int(r[k + "_suma_corridas"]) // 2 for k in ("VP", "FP", "VN", "FN")], [33, 1, 23, 10])
        self.assertAlmostEqual(float(r["precision_promedio_corridas"]), 33 / 34)
        self.assertAlmostEqual(float(r["recall_promedio_corridas"]), 33 / 43)
        self.assertAlmostEqual(float(r["tasa_rechazo_correcto_promedio_corridas"]), 23 / 24)

    def test_linea_base_acepta_todo_coincide_con_hoja_resumen(self):
        # La hoja "resumen" del Excel dice 0.641791 para "aceptar todo" (español).
        r = self.fila("acepta_todo", "espanol")
        self.assertAlmostEqual(float(r["precision_promedio_corridas"]), 43 / 67)
        self.assertAlmostEqual(float(r["precision_promedio_corridas"]), 0.641791, places=6)
        self.assertAlmostEqual(float(r["recall_promedio_corridas"]), 1.0)
        self.assertAlmostEqual(float(r["tasa_rechazo_correcto_promedio_corridas"]), 0.0)

    def test_repeticiones_se_conservan(self):
        corridas = [r for r in self.por_corrida
                    if r["tool"] == "oraculo_gramatica" and r["scope"] == "general"
                    and r["gold_target"] == "espanol"]
        self.assertEqual(sorted(r["run"] for r in corridas), ["1", "2"])
        self.assertEqual(self.fila("oraculo_gramatica", "espanol")["n_corridas"], "2")

    def test_criterios_distintos_no_se_mezclan(self):
        c1 = self.fila("herramienta_x", "espanol", criterion="criterio_1")
        c2 = self.fila("herramienta_x", "espanol", criterion="criterio_2")
        self.assertAlmostEqual(float(c1["tasa_rechazo_correcto_promedio_corridas"]), 0.0)
        self.assertAlmostEqual(float(c2["tasa_rechazo_correcto_promedio_corridas"]), 23 / 24)

    def test_subconjunto_diagnostico(self):
        # Sigue la CFG en los 11 casos / se alinea con el español en 0, y al revés.
        sig = self.fila("oraculo_gramatica", "gramatica", "diagnostico", "etiquetas_difieren")
        self.assertEqual(int(sig["n_registros_suma_corridas"]) // 2, 11)
        self.assertAlmostEqual(float(sig["tasa_seguimiento_cfg_diagnostico_promedio_corridas"]), 1.0)
        esp = self.fila("oraculo_espanol", "gramatica", "diagnostico", "etiquetas_difieren")
        self.assertAlmostEqual(float(esp["tasa_seguimiento_cfg_diagnostico_promedio_corridas"]), 0.0)
        todo = self.fila("acepta_todo", "gramatica", "diagnostico", "etiquetas_difieren")
        self.assertAlmostEqual(float(todo["tasa_seguimiento_cfg_diagnostico_promedio_corridas"]), 1 / 11)

    def test_niveles_suman_el_total(self):
        for tool in ("oraculo_espanol", "acepta_todo"):
            total = int(self.fila(tool, "espanol")["n_registros_suma_corridas"])
            por_nivel = sum(int(self.fila(tool, "espanol", "nivel", n)["n_registros_suma_corridas"])
                            for n in ("1", "2", "3"))
            self.assertEqual(total, por_nivel)
        # nivel 1 no tiene rechazadas: el rechazo correcto debe quedar vacío, no 0 ni 1
        self.assertEqual(self.fila("acepta_todo", "espanol", "nivel", "1")["tasa_rechazo_correcto_promedio_corridas"], "")

    def test_salida_determinista(self):
        otra = self.dir / "out2"
        correr([self.logs_ok], otra)
        for nombre in ("registros_normalizados.csv", "metricas_por_corrida.csv", "resumen_metricas.csv",
                       "clasificacion_errores.csv", "reporte_metricas.json"):
            self.assertEqual(sha(self.out / nombre), sha(otra / nombre), nombre)

    def test_formatos_de_salida_y_estados(self):
        casos = [
            (True, True, "ok"), (False, False, "ok"),
            ("aceptada", True, "ok"), ("Rechazada", False, "ok"), ("  válida ", True, "ok"),
            ({"accepted": True, "productions": []}, True, "ok"),
            ({"decision": "rechazada"}, False, "ok"),
            ("no sé", None, "unreadable"), ({"reason": "x"}, None, "unreadable"), (None, None, "unreadable"),
        ]
        regs = [registro(self.corpus[i], "formatos", raw) for i, (raw, _, _) in enumerate(casos)]
        regs.append(registro(self.corpus[len(casos)], "formatos", None, error="TimeoutError: 120 s"))
        logs = self.dir / "formatos.jsonl"
        escribir(logs, regs)
        out = self.dir / "out_formatos"
        correr([logs], out)
        filas = leer_csv(out / "registros_normalizados.csv")
        for fila, (raw, esperado, estado) in zip(filas, casos):
            self.assertEqual(fila["decision_status"], estado, raw)
            self.assertEqual(fila["predicted_accepted"], "" if esperado is None else str(esperado), raw)
        self.assertEqual(filas[-1]["decision_status"], "execution_error")
        tipos = [e["tipo_error"] for e in leer_csv(out / "clasificacion_errores.csv")]
        self.assertEqual(tipos.count("error_ejecucion"), 1)
        self.assertEqual(tipos.count("respuesta_no_interpretable"), 3)
        # los no evaluables no cuentan como FP/FN: aparecen aparte
        m = [r for r in leer_csv(out / "metricas_por_corrida.csv")
             if r["scope"] == "general" and r["gold_target"] == "espanol"][0]
        self.assertEqual(m["n_registros"], "11")
        self.assertEqual(m["n_evaluables"], "7")
        self.assertEqual(m["n_no_evaluables"], "4")

    def test_validaciones_rechazan_datos_malos(self):
        base = registro(self.corpus[0], "t", True)
        casos = {
            "llave duplicada": [base, dict(base)],
            "id desconocido": [{**base, "id": "C2-999"}],
            "hash de corpus malo": [{**base, "corpus_sha256": "0" * 64}],
            "hash de criterios malo": [{**base, "criteria_sha256": "0" * 64}],
            "run cero": [{**base, "run": 0}],
            "grammar_followed invalido": [{**base, "grammar_followed": "si"}],
            "falta un campo": [{k: v for k, v in base.items() if k != "timestamp_utc"}],
        }
        for nombre, regs in casos.items():
            logs = self.dir / "malo.jsonl"
            escribir(logs, regs)
            done = correr([logs], self.dir / "out_malo", esperado_ok=False)
            self.assertNotEqual(done.returncode, 0, nombre)

    def test_json_dentro_de_texto(self):
        """Un LLM suele devolver el JSON como TEXTO (a veces entre ```)."""
        casos = [
            ('{"accepted": true, "productions": []}', "True", "ok"),
            ('{"accepted": false, "reason": "x"}', "False", "ok"),
            ('```json\n{"accepted": true}\n```', "True", "ok"),
            ('{"accepted": "si"}', "", "unreadable"),
            ('{roto', "", "unreadable"),
        ]
        regs = [registro(self.corpus[i], "llm", raw) for i, (raw, _, _) in enumerate(casos)]
        logs = self.dir / "llm_texto.jsonl"
        escribir(logs, regs)
        out = self.dir / "out_llm_texto"
        correr([logs], out)
        for fila, (raw, pred, estado) in zip(leer_csv(out / "registros_normalizados.csv"), casos):
            self.assertEqual((fila["predicted_accepted"], fila["decision_status"]), (pred, estado), raw)

    def test_grafica_con_metricas_vacias_no_rompe(self):
        """Una herramienta cuyas respuestas son todas ilegibles deja recall vacío."""
        logs = self.dir / "ilegible.jsonl"
        escribir(logs, [registro(self.corpus[0], "ilegible", "no sé")])
        correr([logs], self.dir / "out_ilegible")

if __name__ == "__main__":
    unittest.main(verbosity=2)