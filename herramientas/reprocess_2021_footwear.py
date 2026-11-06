#!/usr/bin/env python3
"""Reprocesamiento puntual: filas NO_MATCH de calzado en inglés en
Consolidacion 2021 Parte_1/2/3.

Diagnóstico (ver commit 7f3ad42): el pre-filtro TF-IDF no encontraba
candidatos de Calzado para descripciones 100% en inglés ("GK FOOTWEAR",
"JEPA FASHION" — p. ej. "BBT294 GOLD 22# CHILDREN FOOTWEAR") porque el
catálogo oficial GPC está en español y estas filas no tenían el campo
CLASIFICACION interno para compensar. Se agregó un puente de sinónimos
inglés->español a SYNONYMS_VE (submit_batches.py) que corrige el
pre-filtro para casos nuevos.

Este script reprocesa SOLO las filas ya entregadas que quedaron NO_MATCH
por este bug específico (filtro: nivel_asignado == "NO_MATCH" y
DESCRIPCION contiene footwear/shoes/boots/sneakers/sandals), usando el
pre-filtro ya corregido, y parchea in-place los 4 archivos
Output_Clasificado/clasificado_Consolidacion 2021_Parte_{1,2,3}.xlsx
(solo esas filas; el resto del archivo queda intacto).

No toca Base_2023_Parte_2.xlsx (10 filas similares) — fuera de alcance,
pendiente de decisión separada del usuario.
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
logger = logging.getLogger("reprocess_2021_footwear")

FOOTWEAR_RE = re.compile(r"FOOTWEAR|SHOES|BOOTS|SNEAKERS|SANDALS", re.IGNORECASE)

TARGET_FILES = [
    "Consolidacion 2021_Parte_1.xlsx",
    "Consolidacion 2021_Parte_2.xlsx",
    "Consolidacion 2021_Parte_3.xlsx",
]

OUTPUT_DIR = Path("Output_Clasificado")
TRACKER_FILE = Path("batch_tracker.json")


def collect_affected_rows() -> dict[str, pd.DataFrame]:
    """Para cada archivo objetivo, devuelve las filas (únicas por marca+
    descripción) actualmente NO_MATCH que matchean el patrón de calzado."""
    affected = {}
    for file_name in TARGET_FILES:
        output_path = OUTPUT_DIR / f"clasificado_{file_name}"
        df = pd.read_excel(output_path)
        mask = (df["nivel_asignado"] == "NO_MATCH") & df["DESCRIPCION"].str.contains(
            FOOTWEAR_RE, na=False
        )
        rows = df[mask].copy()
        rows["_dedup_key"] = rows.apply(
            lambda r: sb.make_custom_id(r["MARCA"], r["DESCRIPCION"]), axis=1
        )
        unique_rows = rows.drop_duplicates(subset=["_dedup_key"])
        logger.info(
            f"{file_name}: {len(rows)} filas NO_MATCH de calzado en inglés "
            f"({len(unique_rows)} productos únicos a reprocesar)"
        )
        affected[file_name] = unique_rows
    return affected


def main() -> int:
    import anthropic

    client = anthropic.Anthropic()
    catalog = sb.GpcCatalog(sb.CATALOG_FILE)

    affected = collect_affected_rows()
    total_unique = sum(len(df) for df in affected.values())
    if total_unique == 0:
        logger.info("No hay filas que reprocesar.")
        return 0

    tracker = json.loads(TRACKER_FILE.read_text(encoding="utf-8")) if TRACKER_FILE.exists() else []

    batch_info = {}  # file_name -> {"batch_id":..., "custom_ids": set(...)}

    for file_name, sample in affected.items():
        if sample.empty:
            continue
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
                "source_file": f"{file_name} (reproceso calzado EN)",
                "source_path": str((Path("input_2021") / file_name).resolve()),
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

    # --- Polling + retrieval + patch in-place ---
    catalog_lookup = rb.load_catalog_lookup(rb.CATALOG_FILE)

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

        # Parchear in-place el Output_Clasificado ya entregado.
        output_path = OUTPUT_DIR / f"clasificado_{file_name}"
        df = pd.read_excel(output_path)
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
        df.to_excel(output_path, index=False)
        logger.info(f"{file_name}: {updated} filas actualizadas in-place en {output_path}")

        # Actualizar tracker.
        for entry in tracker:
            if entry.get("batch_id") == batch_id:
                entry["status"] = "ended"
                entry["retrieved"] = True
                entry["output_path"] = str(output_path)
                entry["num_errors_in_batch"] = num_errors
                entry["num_codes_blocked"] = num_blocked
        TRACKER_FILE.write_text(json.dumps(tracker, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("Reprocesamiento finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
