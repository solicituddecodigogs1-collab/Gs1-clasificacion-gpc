#!/usr/bin/env python3
"""Reprocesamiento puntual de 2014: filas NO_MATCH solucionables con los
3 ajustes agregados a submit_batches.py (ver commit de esta misma
sesión):

  1. SYNONYMS_VE: "leguing" -> "legging mallas pantalon" (typo de
     "legging" detectado en la marca NIGHT AND DAY, 954 filas).
  2. SYNONYMS_VE: "case" -> "funda estuche" (fundas de teléfono
     "JELLY CASE ..." de la marca I-ONSET, 159 filas).
  3. split_glued_words(): separa palabras pegadas sin espacios
     (p.ej. "jeansdecolor8403" -> "jeans de color 8403") detectado en
     la marca KE, 526 filas.

Deliberadamente NO toca los códigos de SKU sin texto descriptivo real
(FILA, ARROW, STEFANO ZINI, PIER PAOLO, BAIRON, MISURA, PINA,
ZAPIVER FEVECO, etc., ~3700 filas) — esos quedan en NO_MATCH para la
heurística Marca->Segment al cierre de la década, tal como se decidió.

Reprocesa SOLO las filas ya entregadas que siguen NO_MATCH para las
marcas NIGHT AND DAY / I-ONSET / KE, usando el pre-filtro ya corregido,
y parchea in-place los 5 archivos
Output_Clasificado/clasificado_Consolidado_2014_Parte_{1..5}.xlsx
(solo esas filas; el resto de cada archivo queda intacto).
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import submit_batches as sb
import retrieve_batches as rb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reprocess_2014_leguing_case_camelcase")

TARGET_BRANDS = {"NIGHT AND DAY", "I-ONSET", "KE"}

TARGET_FILES = [f"Consolidado_2014_Parte_{i}.xlsx" for i in range(1, 6)]

OUTPUT_DIR = Path("Output_Clasificado")
TRACKER_FILE = Path("batch_tracker.json")


def collect_affected_rows() -> dict[str, pd.DataFrame]:
    """Para cada archivo objetivo, devuelve las filas (únicas por marca+
    descripción) actualmente NO_MATCH de las marcas objetivo."""
    affected = {}
    for file_name in TARGET_FILES:
        output_path = OUTPUT_DIR / f"clasificado_{file_name}"
        df = pd.read_excel(output_path)
        mask = (df["nivel_asignado"].astype(str) == "NO_MATCH") & df["Marca"].isin(TARGET_BRANDS)
        rows = df[mask].copy()
        rows["_dedup_key"] = rows.apply(
            lambda r: sb.make_custom_id(r["Marca"], r["Nombre"]), axis=1
        )
        unique_rows = rows.drop_duplicates(subset=["_dedup_key"])
        logger.info(
            f"{file_name}: {len(rows)} filas NO_MATCH de marcas objetivo "
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

    batch_info = {}  # file_name -> {"batch_id":..., "num_requests":...}

    for file_name, sample in affected.items():
        if sample.empty:
            continue
        cols = {
            "descripcion": "Nombre",
            "marca": "Marca",
            "clasificacion": "Clasificación Global del Producto",
            "clasificacion macro": None,
        }
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
                "source_file": f"{file_name} (reproceso leguing/case/camelcase 2014)",
                "source_path": str((Path(".") / file_name).resolve()),
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

        output_path = OUTPUT_DIR / f"clasificado_{file_name}"
        df = pd.read_excel(output_path)
        df["_join_key"] = df.apply(lambda r: sb.make_custom_id(r["Marca"], r["Nombre"]), axis=1)

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

        for entry in tracker:
            if entry.get("batch_id") == batch_id:
                entry["status"] = "ended"
                entry["retrieved"] = True
                entry["output_path"] = str(output_path)
                entry["num_errors_in_batch"] = num_errors
                entry["num_codes_blocked"] = num_blocked
        TRACKER_FILE.write_text(json.dumps(tracker, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("Reprocesamiento finalizado.")

    # --- Reporte general 2014 ---
    total = 0
    dist = {}
    for i in range(1, 6):
        f = OUTPUT_DIR / f"clasificado_Consolidado_2014_Parte_{i}.xlsx"
        df = pd.read_excel(f)
        total += len(df)
        for nivel, cnt in df["nivel_asignado"].astype(str).value_counts().items():
            dist[nivel] = dist.get(nivel, 0) + int(cnt)

    no_match = dist.get("NO_MATCH", 0)
    clasificados = total - no_match
    print("\n" + "=" * 78)
    print("REPORTE GENERAL Y DEFINITIVO — 2014 (post-reprocesamiento Haiku 5.5)")
    print("=" * 78)
    print(f"Total de SKUs (filas) del año 2014: {total}")
    print(f"Distribución: {dist}")
    print(f"Clasificados con éxito hasta ahora: {clasificados}")
    print(f"Remanente en NO_MATCH: {no_match}")
    print(f"Match rate actual: {100*clasificados/total:.1f}%")
    print(
        "Nota: el remanente NO_MATCH incluye ~998 placeholders sin producto "
        "real (GENERICO N/VARIAS MARCAS) y ~3700 códigos de SKU sin texto "
        "descriptivo (FILA, ARROW, STEFANO ZINI, PIER PAOLO, BAIRON, MISURA, "
        "PINA, ZAPIVER FEVECO, etc.), postergados para Sonnet 5.5 + la "
        "heurística Marca->Segment al cierre del bloque 2004-2014."
    )
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())
