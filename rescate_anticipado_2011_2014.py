#!/usr/bin/env python3
"""Rescate anticipado del sub-bloque 2011-2014 (NO esperar al cierre de
la década 2004-2014): consolida TODO el NO_MATCH de estos 4 años y lo
somete a las mismas 2 capas de rescate ya usadas en 2015-2025:

  1. Sonnet 5.5 + regla de rescate (submit_batches_rescate.py), vía
     Batch API, sobre el NO_MATCH completo de cada año.
  2. Heurística Marca->Segment (misma lógica de
     rescate_marca_segment.py) sobre lo que Sonnet deje sin resolver.

A diferencia de 2015-2025 (donde la heurística solo tocó los archivos
de no_match_residual/, pendiente de la consolidación final de década),
aquí SÍ se parchan los archivos principales
Output_Clasificado/clasificado_Consolidado_<año>_Parte_N.xlsx con
AMBAS capas, porque el objetivo es un número de match rate accionable
AHORA (decidir si seguir con 2010 hacia atrás), no un archivo de
auditoría para después.

Deliberadamente scoped SOLO a 2011-2014 — nunca toca ni re-envía nada
de no_match_historico/no_match_residual de 2015-2025 (evita el tipo de
reenvío duplicado que ya ocurrió una vez con 2013).

Script independiente: reutiliza las funciones de
submit_batches.py / submit_batches_rescate.py / retrieve_batches.py
sin modificarlas.
"""

import json
import logging
import sys
import time
from pathlib import Path

import pandas as pd

import submit_batches as sb
import submit_batches_rescate as sbr
import retrieve_batches as rb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rescate_anticipado_2011_2014")

OUTPUT_DIR = Path("Output_Clasificado")
NO_MATCH_HIST_DIR = Path("no_match_historico")
NO_MATCH_RESIDUAL_DIR = Path("no_match_residual")
TRACKER_FILE = Path("batch_tracker.json")

YEARS = [2011, 2012, 2013, 2014]
YEAR_GLOBS = {
    2011: "clasificado_Consolidado_2011_Parte_*.xlsx",
    2012: "clasificado_Consolidado_2012_Parte_*.xlsx",
    2013: "clasificado_Consolidado_2013_Parte_*.xlsx",
    2014: "clasificado_Consolidado_2014_Parte_*.xlsx",
}
SOURCE_SUFFIX = " (rescate anticipado Sonnet 5.5)"

# Heurística Marca->Segment (igual que rescate_marca_segment.py).
HAIKU_MODEL = "claude-haiku-5-5"
CHUNK_SIZE = 150
HEURISTIC_CONFIDENCE = 40
MAX_RETRIES = 3
PROMPT_TEMPLATE = (
    "Actúa como clasificador GS1. Para cada marca o proveedor de esta lista, "
    "identifica su industria principal y asígnale el código exacto de 8 "
    "dígitos del Segmento GPC (Segment) correspondiente (ej. 50000000 para "
    "Alimentos). Devuelve EXCLUSIVAMENTE un objeto JSON válido donde la clave "
    "sea el nombre de la marca y el valor sea el código GPC.\n\n"
    "Marcas:\n{marcas}"
)


def build_rescue_lookup(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    df = pd.read_excel(path)
    if df.empty:
        return {}
    descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(df)
    rescued = df[df["nivel_asignado"].astype(str).str.upper() != "NO_MATCH"]
    lookup = {}
    for _, row in rescued.iterrows():
        key = sb.make_custom_id(row[marca_col], row[descripcion_col])
        lookup[key] = {
            "gpc_code": row["gpc_code"],
            "nivel_asignado": row["nivel_asignado"],
            "gpc_description": row["gpc_description"],
            "confidence_score": row["confidence_score"],
        }
    return lookup


def is_unresolved(df: pd.DataFrame, catalog_lookup: dict) -> pd.Series:
    nivel = df["nivel_asignado"].astype(str).str.strip().str.upper()
    codigo = df["gpc_code"].astype(str).str.strip()
    es_no_match = nivel == "NO_MATCH"
    vacio = df["gpc_code"].isna() | (codigo == "") | (codigo.str.upper() == "NAN")
    invalido = ~codigo.isin(catalog_lookup.keys()) & ~vacio & ~es_no_match
    return es_no_match | vacio | invalido


def build_segment_lookup() -> dict[str, str]:
    df = pd.read_csv(sb.CATALOG_FILE, dtype=str)
    segments = df[df["nivel"] == "Segment"]
    return dict(zip(segments["codigo"], segments["titulo"]))


def parse_json_response(text: str) -> dict:
    import re

    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def call_haiku_chunk(client, brands_chunk: list[str]) -> dict[str, str]:
    marcas_text = "\n".join(f"- {b}" for b in brands_chunk)
    prompt = PROMPT_TEMPLATE.format(marcas=marcas_text)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=4096,
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": prompt}],
            )
            text_parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
            return parse_json_response("".join(text_parts))
        except Exception as exc:
            logger.warning(f"  [reintento {attempt}/{MAX_RETRIES}] error en chunk heurística: {exc}")
            if attempt == MAX_RETRIES:
                return {}
            time.sleep(3 * attempt)
    return {}


def main() -> int:
    import anthropic

    client = anthropic.Anthropic()
    catalog = sbr.GpcCatalog(sbr.CATALOG_FILE)

    NO_MATCH_HIST_DIR.mkdir(parents=True, exist_ok=True)
    NO_MATCH_RESIDUAL_DIR.mkdir(parents=True, exist_ok=True)

    # ======================================================================
    # FASE 1 — Exportar NO_MATCH histórico de 2011-2014
    # ======================================================================
    print("=" * 78)
    print("FASE 1 — Consolidando NO_MATCH de 2011-2014 en no_match_historico/")
    print("=" * 78)
    for year in YEARS:
        files = sorted(OUTPUT_DIR.glob(YEAR_GLOBS[year]))
        frames = [pd.read_excel(f) for f in files]
        df = pd.concat(frames, ignore_index=True)
        nm = df[df["nivel_asignado"].astype(str).str.upper() == "NO_MATCH"].copy()
        out_path = NO_MATCH_HIST_DIR / f"no_match_{year}.xlsx"
        nm.to_excel(out_path, index=False)
        print(f"  {year}: {len(nm)} filas NO_MATCH -> {out_path}")

    # ======================================================================
    # FASE 2 — Envío a Sonnet 5.5 (Batch API)
    # ======================================================================
    print("\n" + "=" * 78)
    print("FASE 2 — Enviando a Sonnet 5.5 + regla de rescate (Batch API)")
    print("=" * 78)
    tracker = sbr.load_tracker()
    batch_ids_by_year: dict[int, str] = {}

    for year in YEARS:
        file_path = NO_MATCH_HIST_DIR / f"no_match_{year}.xlsx"
        file_name = file_path.name
        before = len(tracker)
        sbr.submit_batch_for_file(client, str(file_path), tracker, catalog)
        new_entries = tracker[before:]
        for entry in new_entries:
            entry["source_file"] = f"{file_name}{SOURCE_SUFFIX}"
            batch_ids_by_year[year] = entry["batch_id"]
        sbr.save_tracker(tracker)

    print("batch_id por año:")
    for year, bid in batch_ids_by_year.items():
        print(f"  {year}: {bid}")

    # ======================================================================
    # FASE 3 — Esperar + recuperar resultados (candado ground-truth)
    # ======================================================================
    print("\n" + "=" * 78)
    print("FASE 3 — Esperando y recuperando resultados de Sonnet 5.5")
    print("=" * 78)
    catalog_lookup = rb.load_catalog_lookup(rb.CATALOG_FILE)
    sonnet_summary = []

    for year in YEARS:
        batch_id = batch_ids_by_year[year]
        logger.info(f"{year}: esperando el batch {batch_id}...")
        while True:
            batch = client.messages.batches.retrieve(batch_id)
            if batch.processing_status == "ended":
                break
            time.sleep(30)

        results_by_id, num_errors, num_blocked = rb.fetch_results(client, batch_id, catalog_lookup)
        logger.info(f"{year}: {len(results_by_id)} resultados | {num_errors} errores | {num_blocked} bloqueados")

        source_path = NO_MATCH_HIST_DIR / f"no_match_{year}.xlsx"
        df = pd.read_excel(source_path)
        initial_no_match = len(df)
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

        out_path = OUTPUT_DIR / f"no_match_{year}_rescate_sonnet.xlsx"
        df.to_excel(out_path, index=False)

        for entry in tracker:
            if entry.get("batch_id") == batch_id:
                entry["status"] = "ended"
                entry["retrieved"] = True
                entry["output_path"] = str(out_path)
                entry["num_errors_in_batch"] = num_errors
                entry["num_codes_blocked"] = num_blocked
        sbr.save_tracker(tracker)

        sonnet_summary.append({"anio": year, "no_match_inicial": initial_no_match, "rescatados": rescued})
        print(f"  {year}: {rescued} / {initial_no_match} rescatados por Sonnet 5.5 -> {out_path}")

    # ======================================================================
    # FASE 4 — Parchar los archivos principales con el rescate Sonnet
    # ======================================================================
    print("\n" + "=" * 78)
    print("FASE 4 — Parchando archivos principales con el rescate Sonnet 5.5")
    print("=" * 78)
    for year in YEARS:
        sonnet_lookup = build_rescue_lookup(OUTPUT_DIR / f"no_match_{year}_rescate_sonnet.xlsx")
        files = sorted(OUTPUT_DIR.glob(YEAR_GLOBS[year]))
        for f in files:
            df = pd.read_excel(f)
            descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(df)
            is_no_match = df["nivel_asignado"].astype(str).str.upper() == "NO_MATCH"
            patched = 0
            for idx in df[is_no_match].index:
                key = sb.make_custom_id(df.at[idx, marca_col], df.at[idx, descripcion_col])
                hit = sonnet_lookup.get(key)
                if hit is None:
                    continue
                df.at[idx, "gpc_code"] = hit["gpc_code"]
                df.at[idx, "nivel_asignado"] = hit["nivel_asignado"]
                df.at[idx, "gpc_description"] = hit["gpc_description"]
                df.at[idx, "confidence_score"] = hit["confidence_score"]
                patched += 1
            df.to_excel(f, index=False)
            print(f"  {f.name}: {patched} filas parchadas con Sonnet 5.5")

    # ======================================================================
    # FASE 5 — Extraer residual NO_MATCH post-Sonnet
    # ======================================================================
    print("\n" + "=" * 78)
    print("FASE 5 — Extrayendo residual NO_MATCH post-Sonnet a no_match_residual/")
    print("=" * 78)
    catalog_lookup_valid = rb.load_catalog_lookup(rb.CATALOG_FILE)
    residual_info = []  # year -> (df, descripcion_col, marca_col)
    for year in YEARS:
        files = sorted(OUTPUT_DIR.glob(YEAR_GLOBS[year]))
        frames = [pd.read_excel(f) for f in files]
        df = pd.concat(frames, ignore_index=True)
        mask = is_unresolved(df, catalog_lookup_valid)
        residual = df[mask].copy()
        out_path = NO_MATCH_RESIDUAL_DIR / f"no_match_residual_{year}.xlsx"
        residual.to_excel(out_path, index=False)
        descripcion_col, marca_col = (None, None)
        if not residual.empty:
            descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(residual)
        residual_info.append((year, residual, descripcion_col, marca_col))
        print(f"  {year}: {len(residual)} filas residuales -> {out_path}")

    # ======================================================================
    # FASE 6 — Heurística Marca->Segment sobre el residual 2011-2014
    # ======================================================================
    print("\n" + "=" * 78)
    print("FASE 6 — Heurística Marca->Segment (Haiku 5.5, llamada directa)")
    print("=" * 78)
    segment_lookup = build_segment_lookup()
    valid_codes = set(segment_lookup.keys())

    brand_display: dict[str, str] = {}
    for year, residual, descripcion_col, marca_col in residual_info:
        if residual.empty:
            continue
        vals = residual[marca_col].dropna().astype(str).str.strip()
        vals = vals[vals.str.len() >= 3]
        for v in vals:
            key = v.upper()
            if key not in brand_display:
                brand_display[key] = v

    brands = sorted(brand_display.keys())
    print(f"Marcas únicas detectadas en el residual (>=3 caracteres): {len(brands)}")

    chunks = [brands[i : i + CHUNK_SIZE] for i in range(0, len(brands), CHUNK_SIZE)]
    brand_to_code: dict[str, str] = {}
    invalid_codes = 0
    for i, chunk in enumerate(chunks, 1):
        display_chunk = [brand_display[k] for k in chunk]
        result = call_haiku_chunk(client, display_chunk)
        for brand_raw, code in result.items():
            key = str(brand_raw).strip().upper()
            code_clean = "".join(ch for ch in str(code) if ch.isdigit())
            if code_clean in valid_codes:
                brand_to_code[key] = code_clean
            else:
                invalid_codes += 1
        print(f"  [{i}/{len(chunks)}] recibidas {len(result)} marcas, acumulado válido={len(brand_to_code)}")

    print(f"Marcas con Segment válido asignado: {len(brand_to_code)} / {len(brands)}")
    print(f"Códigos inválidos descartados: {invalid_codes}")

    # Parchar no_match_residual/ (snapshot) y los archivos principales.
    heuristic_summary = []
    for year, residual, descripcion_col, marca_col in residual_info:
        residual_path = NO_MATCH_RESIDUAL_DIR / f"no_match_residual_{year}.xlsx"
        patched_residual = 0
        heuristic_lookup: dict[str, dict] = {}
        if not residual.empty:
            for idx in residual.index:
                marca_val = residual.at[idx, marca_col]
                if pd.isna(marca_val):
                    continue
                key = str(marca_val).strip().upper()
                if len(key) < 3:
                    continue
                code = brand_to_code.get(key)
                if code is None:
                    continue
                residual.at[idx, "gpc_code"] = code
                residual.at[idx, "nivel_asignado"] = "Segment"
                residual.at[idx, "gpc_description"] = segment_lookup[code]
                residual.at[idx, "confidence_score"] = HEURISTIC_CONFIDENCE
                patched_residual += 1
                join_key = sb.make_custom_id(marca_val, residual.at[idx, descripcion_col])
                heuristic_lookup[join_key] = {
                    "gpc_code": code,
                    "nivel_asignado": "Segment",
                    "gpc_description": segment_lookup[code],
                    "confidence_score": HEURISTIC_CONFIDENCE,
                }
            residual.to_excel(residual_path, index=False)

        # Parchar también los archivos principales del año.
        patched_main = 0
        files = sorted(OUTPUT_DIR.glob(YEAR_GLOBS[year]))
        for f in files:
            df = pd.read_excel(f)
            descripcion_col_m, marca_col_m = rb.resolve_descripcion_marca_columns(df)
            is_no_match = df["nivel_asignado"].astype(str).str.upper() == "NO_MATCH"
            file_patched = 0
            for idx in df[is_no_match].index:
                key = sb.make_custom_id(df.at[idx, marca_col_m], df.at[idx, descripcion_col_m])
                hit = heuristic_lookup.get(key)
                if hit is None:
                    continue
                df.at[idx, "gpc_code"] = hit["gpc_code"]
                df.at[idx, "nivel_asignado"] = hit["nivel_asignado"]
                df.at[idx, "gpc_description"] = hit["gpc_description"]
                df.at[idx, "confidence_score"] = hit["confidence_score"]
                file_patched += 1
            if file_patched:
                df.to_excel(f, index=False)
            patched_main += file_patched

        heuristic_summary.append({"anio": year, "rescatados_heuristica": patched_main})
        print(f"  {year}: {patched_main} filas rescatadas por heurística (residual: {patched_residual})")

    # ======================================================================
    # FASE 7 — Reporte final de recuperación 2011-2014
    # ======================================================================
    print("\n" + "=" * 78)
    print("REPORTE DE RECUPERACIÓN — Sub-bloque 2011-2014 (post Sonnet + heurística)")
    print("=" * 78)
    print(f"{'Año':<8}{'Total':<10}{'Asignados':<14}{'% Asignado':<13}{'NO_MATCH':<12}{'% NO_MATCH':<12}")
    print("-" * 78)
    g_total = g_asig = g_nomatch = 0
    for year in YEARS:
        files = sorted(OUTPUT_DIR.glob(YEAR_GLOBS[year]))
        frames = [pd.read_excel(f) for f in files]
        df = pd.concat(frames, ignore_index=True)
        total = len(df)
        dist = df["nivel_asignado"].astype(str).value_counts(dropna=False)
        no_match = int(dist.get("NO_MATCH", 0))
        error = int(dist.get("ERROR", 0))
        asignados = total - no_match - error
        pct_asig = 100 * asignados / total
        pct_nom = 100 * no_match / total
        print(f"{year:<8}{total:<10}{asignados:<14}{pct_asig:<13.1f}{no_match:<12}{pct_nom:<12.1f}")
        g_total += total
        g_asig += asignados
        g_nomatch += no_match
    print("-" * 78)
    pct_asig_total = 100 * g_asig / g_total
    pct_nom_total = 100 * g_nomatch / g_total
    print(f"{'TOTAL':<8}{g_total:<10}{g_asig:<14}{pct_asig_total:<13.1f}{g_nomatch:<12}{pct_nom_total:<12.1f}")
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())
