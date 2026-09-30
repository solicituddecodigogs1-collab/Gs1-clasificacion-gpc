#!/usr/bin/env python3
"""Recupera los lotes enviados por submit_batches_nueva_carga.py y exporta los
Excel clasificados.

Para cada lote de batch_tracker_nueva_carga.json:
  1. Consulta su estado en la Batch API.
  2. Si está 'ended', descarga los resultados a
     ./Output_Clasificado/resultados/<batch_id>.jsonl
  3. Cuando todos los lotes de un archivo están descargados, hace merge
     (how="left") por ean13 contra el Excel original de ./Nueva Carga/.
  4. Exporta a ./Output_Clasificado/ el archivo intacto + las columnas nuevas
     al final: nivel_asignado, gpc_code, gpc_description, confidence_score.
  5. Actualiza el tracker.

Como el envío se desduplicó por ('nombre', 'marca'), solo un ean13 por grupo
viajó a la API. El merge se hace por tanto en dos pasos: resultados -> (ean13)
-> únicos, y únicos -> (nombre, marca) -> archivo completo; así los duplicados
heredan la clasificación de su representante en vez de quedar vacíos.

Uso:
    python3 retrieve_batches_nueva_carga.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from submit_batches_nueva_carga import (
    COL_EAN, COL_MARCA, COL_NOMBRE, LEVEL_DIGITS, TRACKER_FILE,
    build_unique, load_tracker, read_master, save_tracker,
)

OUTPUT_DIR = Path("./Output_Clasificado")
RESULTS_DIR = OUTPUT_DIR / "resultados"
EXCEL_MAX_ROWS = 1_048_575

AI_COLS = ["nivel_asignado", "gpc_code", "gpc_description", "confidence_score"]

log = logging.getLogger("retrieve_nueva_carga")


# --------------------------------------------------------------------------- #
# Descarga y parseo
# --------------------------------------------------------------------------- #
def parse_result(res) -> dict:
    """Convierte un resultado de la Batch API en un registro plano."""
    rec = {"ean13": res.custom_id, "status": res.result.type}
    if res.result.type != "succeeded":
        rec["error"] = str(getattr(res.result, "error", res.result.type))
        return rec
    msg = res.result.message
    text = next((b.text for b in msg.content if b.type == "text"), None)
    if msg.stop_reason == "refusal" or not text:
        rec.update(status="sin_salida", error=f"stop_reason={msg.stop_reason}")
        return rec
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("la salida no es un objeto JSON")
    except (json.JSONDecodeError, ValueError) as e:
        rec.update(status="json_invalido", error=f"{e}; stop_reason={msg.stop_reason}")
        return rec
    rec.update(data)
    return rec


def download_results(client, batch_id: str) -> Path:
    import anthropic

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{batch_id}.jsonl"
    tmp = out.with_suffix(".jsonl.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            # Los resultados llegan en cualquier orden: se indexan por custom_id.
            for res in client.messages.batches.results(batch_id):
                fh.write(json.dumps(parse_result(res), ensure_ascii=False) + "\n")
    except anthropic.APIError:
        tmp.unlink(missing_ok=True)
        raise
    os.replace(tmp, out)
    return out


def load_results(paths: list[Path]) -> tuple[pd.DataFrame, int, int]:
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh if line.strip())
    res = pd.DataFrame(rows, columns=None) if rows else pd.DataFrame(columns=["ean13", "status"])
    for c in ("razonamiento", *AI_COLS, "error"):
        if c not in res.columns:
            res[c] = pd.NA

    ok = res["status"].eq("succeeded")
    nivel = res["nivel_asignado"]
    code = res["gpc_code"].fillna("").astype(str).str.strip()
    conf = pd.to_numeric(res["confidence_score"], errors="coerce")
    esperado = nivel.map(LEVEL_DIGITS)
    # Incoherencias: nivel desconocido, código no numérico o longitud distinta a la del nivel.
    bad = ok & (esperado.isna() | ~code.str.fullmatch(r"\d*") | (code.str.len() != esperado) | conf.isna())
    if bad.any():
        log.warning("  %d respuestas inconsistentes (nivel/código/confianza) -> NO_MATCH", int(bad.sum()))
        res.loc[bad, ["nivel_asignado", "gpc_code", "gpc_description"]] = ["NO_MATCH", "", ""]
        res.loc[bad, "confidence_score"] = 0.0
    res["confidence_score"] = pd.to_numeric(res["confidence_score"], errors="coerce").clip(0, 1)
    res["gpc_code"] = res["gpc_code"].where(~ok | bad, code)

    sin = ~(ok | bad)
    if sin.any():
        log.warning("  %d solicitudes sin resultado válido (quedarán vacías): %s",
                    int(sin.sum()), res.loc[sin, "status"].value_counts().to_dict())
    res = res[ok | bad].drop_duplicates(subset="ean13", keep="last")
    return res[["ean13", *AI_COLS]].rename(columns={"ean13": COL_EAN}), int(sin.sum()), int(bad.sum())


# --------------------------------------------------------------------------- #
# Merge y exportación
# --------------------------------------------------------------------------- #
def merge_and_export(source_path: Path, result_paths: list[Path]) -> tuple[Path, dict]:
    master = read_master(source_path)
    clash = [c for c in AI_COLS if c in master.columns]
    if clash:
        raise ValueError(f"el Excel original ya contiene columnas {clash}")
    n0 = len(master)

    results, n_sin, n_bad = load_results(result_paths)
    sub = build_unique(master)

    # a) resultados -> únicos, por ean13
    sub = sub.merge(results, on=COL_EAN, how="left")
    # b) únicos -> archivo completo, por (nombre, marca): propaga a los duplicados
    merged = master.merge(sub[[COL_NOMBRE, COL_MARCA, *AI_COLS]], on=[COL_NOMBRE, COL_MARCA], how="left")
    if len(merged) != n0:
        raise RuntimeError(f"el merge alteró el número de filas ({n0} -> {len(merged)})")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = source_path.stem
    if n0 <= EXCEL_MAX_ROWS:
        out = OUTPUT_DIR / f"clasificado_{stem}.xlsx"
        tmp = out.with_name(out.stem + ".tmp.xlsx")
        merged.to_excel(tmp, index=False)
        os.replace(tmp, out)
    else:
        out = OUTPUT_DIR / f"clasificado_{stem}.csv"
        log.warning("  %d filas exceden el límite de Excel; se exporta CSV", n0)
        merged.to_csv(out, index=False, encoding="utf-8-sig")

    stats = {
        "rows": n0,
        "rows_classified": int(merged["nivel_asignado"].notna().sum()),
        "requests_without_result": n_sin,
        "responses_inconsistent": n_bad,
    }
    return out, stats


# --------------------------------------------------------------------------- #
def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    tracker = load_tracker()
    if not tracker:
        log.error("%s está vacío o no existe; ejecuta primero submit_batches_nueva_carga.py", TRACKER_FILE)
        return 1

    try:
        import anthropic
        client = anthropic.Anthropic()
    except Exception as e:
        log.error("No se pudo inicializar el cliente de Anthropic: %s", e)
        return 1

    errores = 0

    # 1-2. Estado y descarga de cada lote
    for e in tracker:
        if e.get("results_path") and Path(e["results_path"]).exists():
            continue
        try:
            batch = client.messages.batches.retrieve(e["batch_id"])
            e["status"] = batch.processing_status
            c = batch.request_counts
            log.info("%s [%s] %s: ok=%d err=%d canc=%d exp=%d en_proceso=%d", e["batch_id"], e["status"],
                     e["source_file"], c.succeeded, c.errored, c.canceled, c.expired, c.processing)
            if batch.processing_status == "ended":
                e["results_path"] = str(download_results(client, e["batch_id"]))
                e["num_errors_in_batch"] = c.errored + c.canceled + c.expired
                e["ended_at"] = datetime.now(timezone.utc).isoformat()
        except anthropic.NotFoundError:
            errores += 1
            e["status"] = "not_found"
            log.error("%s: el lote no existe en la API", e["batch_id"])
        except anthropic.APIError as ex:
            errores += 1
            log.error("%s: error de la API al consultar/descargar: %s", e["batch_id"], ex)
        except OSError as ex:
            errores += 1
            log.error("%s: error de disco: %s", e["batch_id"], ex)
        finally:
            save_tracker(tracker)

    # 3-5. Merge por archivo cuando todos sus lotes están descargados
    for source in sorted({e["source_file"] for e in tracker}):
        entries = [e for e in tracker if e["source_file"] == source]
        if all(e.get("retrieved") for e in entries):
            continue
        if not all(e.get("results_path") for e in entries):
            log.info("%s: lotes aún sin terminar; se reintentará en la próxima ejecución", source)
            continue
        try:
            log.info("%s: fusionando ...", source)
            out, stats = merge_and_export(Path(entries[0]["source_path"]),
                                          [Path(e["results_path"]) for e in entries])
            for e in entries:
                e.pop("merge_error", None)
                e.update(retrieved=True, output_path=str(out), retrieved_at=datetime.now(timezone.utc).isoformat(),
                         **{f"merge_{k}": v for k, v in stats.items()})
            log.info("  -> %s (%d/%d filas clasificadas)", out, stats["rows_classified"], stats["rows"])
        except Exception as ex:  # un archivo con error no detiene a los demás
            errores += 1
            for e in entries:
                e["merge_error"] = str(ex)
            log.error("%s: FALLÓ el merge: %s", source, ex, exc_info=not isinstance(ex, (ValueError, FileNotFoundError)))
        finally:
            save_tracker(tracker)

    pendientes = sum(1 for e in tracker if not e.get("retrieved"))
    log.info("Terminado: %d lote(s) pendientes, %d error(es)", pendientes, errores)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
