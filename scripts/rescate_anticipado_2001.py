#!/usr/bin/env python3
"""Rescate anticipado de 2001 (copia scoped de rescate_anticipado_2002.py):
consolida TODO el NO_MATCH de 2001 y lo somete a Sonnet 5.5 + regla de
rescate (submit_batches_rescate.py) vía Batch API.

Deliberadamente NO aplica la capa de heurística/preclasificación (FASE 6 en
2002+): por decisión explícita del usuario (2026-11-06), se procesa
"hasta el parche con Sonnet" y el residual que Sonnet no resuelva queda
como NO_MATCH real, sin heurística Marca->Segment ni regex/lookup empresa.

Parcha los archivos principales Output_Clasificado/clasificado_Parte_N_2001.xlsx
solo con el rescate Sonnet.

Deliberadamente scoped SOLO a 2001 — nunca toca ni re-envía nada de
no_match_historico/no_match_residual de otros años.

Script independiente: reutiliza las funciones de
submit_batches.py / submit_batches_rescate.py / retrieve_batches.py
sin modificarlas.
"""

import logging
import sys
import time
from pathlib import Path

import pandas as pd

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "lib"))
import submit_batches as sb
import submit_batches_rescate as sbr
import retrieve_batches as rb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rescate_anticipado_2001")

OUTPUT_DIR = Path("Output_Clasificado")
NO_MATCH_HIST_DIR = Path("no_match_historico")
NO_MATCH_RESIDUAL_DIR = Path("no_match_residual")
TRACKER_FILE = Path("batch_tracker.json")

YEARS = [2001]
YEAR_GLOBS = {
    2001: "clasificado_Parte_*_2001.xlsx",
}
SOURCE_SUFFIX = " (rescate anticipado Sonnet 5.5 (2001))"


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


def main() -> int:
    import anthropic

    client = anthropic.Anthropic()
    catalog = sbr.GpcCatalog(sbr.CATALOG_FILE)

    NO_MATCH_HIST_DIR.mkdir(parents=True, exist_ok=True)
    NO_MATCH_RESIDUAL_DIR.mkdir(parents=True, exist_ok=True)

    # ======================================================================
    # FASE 1 — Exportar NO_MATCH histórico de 2001
    # ======================================================================
    print("=" * 78)
    print("FASE 1 — Consolidando NO_MATCH de 2001 en no_match_historico/")
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

    TERMINAL_FAILED = {"failed", "canceled", "expired", "errored"}
    for year in YEARS:
        file_path = NO_MATCH_HIST_DIR / f"no_match_{year}.xlsx"
        file_name = file_path.name
        suffixed_name = f"{file_name}{SOURCE_SUFFIX}"

        # already_submitted() de submit_batches_rescate compara contra el
        # nombre SIN sufijo, pero esta misma FASE renombra la entrada del
        # tracker con SOURCE_SUFFIX justo después de crearla -- así que al
        # reanudar el script (p.ej. tras un kill) nunca la reconocería y
        # reenviaría un batch duplicado. Se busca primero la entrada ya
        # renombrada antes de llamar a submit_batch_for_file.
        existing = next(
            (
                e
                for e in tracker
                if e.get("source_file") == suffixed_name and e.get("status") not in TERMINAL_FAILED
            ),
            None,
        )
        if existing is not None:
            batch_ids_by_year[year] = existing["batch_id"]
            logger.info(
                f"{year}: ya existe un batch enviado ({existing['batch_id']}, "
                f"status={existing.get('status')}), se omite reenvío"
            )
            continue

        before = len(tracker)
        sbr.submit_batch_for_file(client, str(file_path), tracker, catalog)
        new_entries = tracker[before:]
        for entry in new_entries:
            entry["source_file"] = suffixed_name
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
    # FASE 6 — Reporte final de recuperación 2001
    # ======================================================================
    print("\n" + "=" * 78)
    print("REPORTE DE RECUPERACIÓN — 2001 (post Sonnet, sin heurística)")
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
