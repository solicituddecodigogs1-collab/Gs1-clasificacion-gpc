#!/usr/bin/env python3
"""Recupera los resultados del rescate con Sonnet 5.5 + regla de rescate
(no_match_historico/no_match_<año>.xlsx, enviados con
submit_batches_rescate.py) y exporta cada uno a
Output_Clasificado/no_match_<año>_rescate_sonnet.xlsx — un archivo nuevo,
independiente de los Excel originales por año y del rescate anterior con
Haiku 5.5 (no_match_<año>_reprocesado_haiku55.xlsx), que no sobrescribe.

Busca en el tracker la ÚLTIMA entrada con source_file ==
"no_match_<año>.xlsx (rescate Sonnet 5.5)" (el primer envío falló 100%
por un bug de configuración ya corregido; el reenvío fue el exitoso).

Reutiliza las funciones reales de retrieve_batches.py (fetch_results,
load_catalog_lookup, validate_gpc_code) y submit_batches.py
(make_custom_id) para que el comportamiento, candado ground-truth
incluido, sea idéntico al resto del pipeline.
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd

import submit_batches as sb
import retrieve_batches as rb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("retrieve_rescate_sonnet")

NO_MATCH_DIR = Path("no_match_historico")
OUTPUT_DIR = Path("Output_Clasificado")
TRACKER_FILE = Path("batch_tracker.json")

YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
SOURCE_SUFFIX = " (rescate Sonnet 5.5)"


def find_latest_batch_entry(tracker: list[dict], file_name: str) -> dict | None:
    """Última entrada del tracker con este source_file exacto (la más
    reciente si hay varias, p. ej. un envío fallido seguido del reenvío
    exitoso)."""
    tagged_name = f"{file_name}{SOURCE_SUFFIX}"
    matches = [e for e in tracker if e.get("source_file") == tagged_name]
    return matches[-1] if matches else None


def main() -> int:
    import anthropic

    client = anthropic.Anthropic()
    tracker = json.loads(TRACKER_FILE.read_text(encoding="utf-8")) if TRACKER_FILE.exists() else []
    catalog_lookup = rb.load_catalog_lookup(rb.CATALOG_FILE)

    summary = []

    for year in YEARS:
        file_name = f"no_match_{year}.xlsx"
        entry = find_latest_batch_entry(tracker, file_name)
        if entry is None:
            logger.warning(f"{file_name}: no hay entrada en el tracker, se omite")
            continue

        batch_id = entry["batch_id"]
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status != "ended":
            logger.info(f"{file_name} ({batch_id}): estado actual = {batch.processing_status}")
            continue

        if entry.get("retrieved"):
            logger.info(f"{file_name} ({batch_id}): ya recuperado previamente, se omite")
            continue

        logger.info(f"{file_name} ({batch_id}): batch finalizado, descargando resultados")
        results_by_id, num_errors, num_blocked = rb.fetch_results(client, batch_id, catalog_lookup)
        if num_blocked:
            logger.warning(f"{file_name}: {num_blocked} códigos inventados/no válidos bloqueados por el candado ground-truth")
        if num_errors:
            logger.warning(f"{file_name}: {num_errors} solicitudes con error dentro del batch")

        source_path = NO_MATCH_DIR / file_name
        df = pd.read_excel(source_path)
        initial_no_match = int((df["nivel_asignado"].astype(str).str.upper() == "NO_MATCH").sum())
        descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(df)
        df["_join_key"] = df.apply(lambda r: sb.make_custom_id(r[marca_col], r[descripcion_col]), axis=1)

        rescued = 0
        for idx, row in df.iterrows():
            res = results_by_id.get(row["_join_key"])
            if res is None:
                continue
            df.at[idx, "gpc_code"] = res["gpc_code"]
            df.at[idx, "nivel_asignado"] = res["nivel_asignado"]
            df.at[idx, "gpc_description"] = res["gpc_description"]
            df.at[idx, "confidence_score"] = res["confidence_score"]
            if res["nivel_asignado"] != "NO_MATCH":
                rescued += 1

        df = df.drop(columns=["_join_key"])
        final_no_match = int((df["nivel_asignado"].astype(str).str.upper() == "NO_MATCH").sum())

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / f"no_match_{year}_rescate_sonnet.xlsx"
        df.to_excel(out_path, index=False)
        logger.info(f"{file_name}: exportado a {out_path}")

        entry["status"] = "ended"
        entry["retrieved"] = True
        entry["output_path"] = str(out_path)
        entry["num_errors_in_batch"] = num_errors
        entry["num_codes_blocked"] = num_blocked
        TRACKER_FILE.write_text(json.dumps(tracker, indent=2, ensure_ascii=False), encoding="utf-8")

        summary.append(
            {
                "anio": year,
                "no_match_inicial": initial_no_match,
                "rescatados": rescued,
                "no_match_final": final_no_match,
            }
        )

    if summary:
        print("\n" + "=" * 70)
        print("RESUMEN — Rescate Sonnet 5.5 (regla de rescate, NO_MATCH históricos)")
        print("=" * 70)
        total_inicial = sum(r["no_match_inicial"] for r in summary)
        total_rescatado = sum(r["rescatados"] for r in summary)
        total_final = sum(r["no_match_final"] for r in summary)
        for r in summary:
            print(
                f"  {r['anio']}: NO_MATCH inicial={r['no_match_inicial']} | "
                f"rescatados={r['rescatados']} | NO_MATCH final={r['no_match_final']}"
            )
        print("-" * 70)
        print(f"TOTAL: inicial={total_inicial} | rescatados={total_rescatado} | final={total_final}")
        print("=" * 70)

    logger.info("Proceso de recuperación del rescate Sonnet 5.5 finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
