#!/usr/bin/env python3
"""Reprocesamiento puntual: filas NO_MATCH de 2019 con "COVERALL" (overol/
mono de trabajo, marca KOLOSSUS) que el fix de SYNONYMS_VE ahora resuelve.

Diagnóstico: 2019 casi no trae el campo CLASIFICACION interno (97.5%-99.9%
vacío), lo que elevó el NO_MATCH general, especialmente en Parte_1 (30.3%).
"COVERALL" no tenía overlap de n-gramas con el catálogo en español y no
encontraba ningún candidato de Prendas de vestir, aunque sí existe el Brick
correcto ("Prendas de protección – Para todo el cuerpo", 10001394). Se
agregó coverall/coveralls a SYNONYMS_VE (submit_batches.py) y se verificó
localmente que ahora aparece como candidato.

Este script reprocesa SOLO esas filas ya entregadas que coinciden con
"COVERALL" y siguen NO_MATCH, usando el pre-filtro ya corregido, y parchea
in-place los archivos Output_Clasificado/clasificado_2019 Consolidado_Parte_
{1..5}.xlsx afectados (solo esas filas; el resto del archivo queda
intacto).
"""

import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import submit_batches as sb
import retrieve_batches as rb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reprocess_2019_coverall")

FIXABLE_RE = re.compile(r"\bCOVERALL\b", re.IGNORECASE)

TARGET_FILES = [f"2019 Consolidado_Parte_{i}.xlsx" for i in range(1, 6)]

OUTPUT_DIR = Path("Output_Clasificado")
TRACKER_FILE = Path("batch_tracker.json")


def collect_affected_rows() -> dict[str, pd.DataFrame]:
    affected = {}
    for file_name in TARGET_FILES:
        output_path = OUTPUT_DIR / f"clasificado_{file_name}"
        df = pd.read_excel(output_path)
        mask = (df["nivel_asignado"] == "NO_MATCH") & df["DESCRIPCION"].str.contains(
            FIXABLE_RE, na=False, regex=True
        )
        rows = df[mask].copy()
        if rows.empty:
            logger.info(f"{file_name}: 0 filas NO_MATCH con COVERALL")
            affected[file_name] = rows
            continue
        rows["_dedup_key"] = rows.apply(
            lambda r: sb.make_custom_id(r["MARCA"], r["DESCRIPCION"]), axis=1
        )
        unique_rows = rows.drop_duplicates(subset=["_dedup_key"])
        logger.info(
            f"{file_name}: {len(rows)} filas NO_MATCH con COVERALL "
            f"({len(unique_rows)} productos únicos a reprocesar)"
        )
        affected[file_name] = unique_rows
    return affected


def main() -> int:
    import anthropic

    client = anthropic.Anthropic()
    catalog = sb.GpcCatalog(sb.CATALOG_FILE)

    affected = {k: v for k, v in collect_affected_rows().items() if not v.empty}
    total_unique = sum(len(df) for df in affected.values())
    if total_unique == 0:
        logger.info("No hay filas que reprocesar.")
        return 0
    logger.info(f"Total de productos únicos a reprocesar: {total_unique}")

    tracker = json.loads(TRACKER_FILE.read_text(encoding="utf-8")) if TRACKER_FILE.exists() else []

    batch_info = {}

    for file_name, sample in affected.items():
        cols = {"descripcion": "DESCRIPCION", "marca": "MARCA", "clasificacion": "CLASIFICACION", "clasificacion macro": None}
        request_dicts = sb.build_request_dicts(sample, cols, catalog)
        logger.info(f"{file_name}: {len(request_dicts)} solicitudes de reprocesamiento preparadas")

        jsonl_path = sb.write_jsonl_temp(request_dicts)
        try:
            requests = sb.read_jsonl_as_requests(jsonl_path)
            batch = client.messages.batches.create(requests=requests)
        finally:
            jsonl_path.unlink(missing_ok=True)

        logger.info(f"{file_name}: batch de reprocesamiento creado {batch.id} (status={batch.processing_status})")
        batch_info[file_name] = {"batch_id": batch.id, "num_requests": len(requests)}

        tracker.append(
            {
                "batch_id": batch.id,
                "source_file": f"{file_name} (reproceso coverall 2019)",
                "source_path": str((Path("input_2019") / file_name).resolve()),
                "model": sb.MODEL,
                "status": batch.processing_status,
                "num_requests": len(requests),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "retrieved": False,
                "output_path": None,
                "num_errors_in_batch": None,
                "num_codes_blocked": None,
            }
        )
        TRACKER_FILE.write_text(json.dumps(tracker, indent=2, ensure_ascii=False), encoding="utf-8")

    catalog_lookup = rb.load_catalog_lookup(rb.CATALOG_FILE)
    summary = []

    for file_name, info in batch_info.items():
        batch_id = info["batch_id"]
        logger.info(f"{file_name}: esperando a que termine el batch {batch_id}...")
        while True:
            batch = client.messages.batches.retrieve(batch_id)
            if batch.processing_status == "ended":
                break
            time.sleep(15)

        results_by_id, num_errors, num_blocked = rb.fetch_results(client, batch_id, catalog_lookup)
        logger.info(
            f"{file_name}: {len(results_by_id)} resultados recibidos, {num_errors} errores, "
            f"{num_blocked} bloqueados por ground-truth"
        )

        output_path = OUTPUT_DIR / f"clasificado_{file_name}"
        df = pd.read_excel(output_path)
        initial_no_match = int((df["nivel_asignado"] == "NO_MATCH").sum())
        df["_join_key"] = df.apply(lambda r: sb.make_custom_id(r["MARCA"], r["DESCRIPCION"]), axis=1)

        updated = 0
        for idx, row in df.iterrows():
            key = row["_join_key"]
            if key in results_by_id and row["nivel_asignado"] == "NO_MATCH":
                res = results_by_id[key]
                df.at[idx, "gpc_code"] = res["gpc_code"]
                df.at[idx, "nivel_asignado"] = res["nivel_asignado"]
                df.at[idx, "gpc_description"] = res["gpc_description"]
                df.at[idx, "confidence_score"] = res["confidence_score"]
                updated += 1

        df = df.drop(columns=["_join_key"])
        final_no_match = int((df["nivel_asignado"] == "NO_MATCH").sum())
        df.to_excel(output_path, index=False)
        logger.info(
            f"{file_name}: {updated} filas actualizadas in-place | "
            f"NO_MATCH {initial_no_match} -> {final_no_match}"
        )
        summary.append(
            {
                "archivo": file_name,
                "no_match_inicial": initial_no_match,
                "actualizadas": updated,
                "no_match_final": final_no_match,
            }
        )

        for entry in tracker:
            if entry.get("batch_id") == batch_id:
                entry["status"] = "ended"
                entry["retrieved"] = True
                entry["output_path"] = str(output_path)
                entry["num_errors_in_batch"] = num_errors
                entry["num_codes_blocked"] = num_blocked
        TRACKER_FILE.write_text(json.dumps(tracker, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 78)
    print("RESUMEN — Reprocesamiento COVERALL 2019")
    print("=" * 78)
    for r in summary:
        print(
            f"  {r['archivo']}: NO_MATCH inicial={r['no_match_inicial']} | "
            f"actualizadas={r['actualizadas']} | NO_MATCH final={r['no_match_final']}"
        )
    print("=" * 78)

    logger.info("Reprocesamiento finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
