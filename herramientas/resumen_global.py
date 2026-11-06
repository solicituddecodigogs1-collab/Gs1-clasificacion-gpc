#!/usr/bin/env python3
"""Resumen global del estado actual del proyecto: combina cada archivo
principal por año (Output_Clasificado/clasificado_*) con las rondas de
rescate de NO_MATCH (Haiku 5.5 y/o Sonnet 5.5) para reportar, por año,
cuántos productos quedaron asignados vs. NO_MATCH tras todo el pipeline
hasta la fecha.

No modifica ningún archivo — solo lee y reporta. Script independiente
(no importa submit_batches.py/retrieve_batches.py más que para
normalizar marca+descripción de la misma forma que el resto del
pipeline).
"""

import sys
from pathlib import Path

import pandas as pd

import submit_batches as sb
import retrieve_batches as rb

OUTPUT_DIR = Path("Output_Clasificado")

YEAR_GLOBS = {
    2015: "clasificado_Consolidado_2015_Parte_*.xlsx",
    2016: "clasificado_Consolidado_2016_Parte_*.xlsx",
    2017: "clasificado_Consolidado_2017_Parte_*.xlsx",
    2018: "clasificado_2018_Parte_*.xlsx",
    2019: "clasificado_2019 Consolidado_Parte_*.xlsx",
    2020: "clasificado_Listado completo 2020_Parte_*.xlsx",
    2021: "clasificado_Consolidacion 2021_Parte_*.xlsx",
    2022: "clasificado_Listado General (2022)_Parte_*.xlsx",
    2023: "clasificado_Base_2023_Parte_*.xlsx",
    2024: "clasificado_Listado_General_2024_Parte_*.xlsx",
    2025: "clasificado_Base_2025_Parte_*.xlsx",
}


def build_rescue_lookup(path: Path) -> dict[str, dict]:
    """custom_id -> {gpc_code, nivel_asignado, gpc_description} solo para
    filas que el rescate SÍ resolvió (nivel_asignado != NO_MATCH)."""
    if not path.exists():
        return {}
    df = pd.read_excel(path)
    descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(df)
    rescued = df[df["nivel_asignado"].astype(str).str.upper() != "NO_MATCH"]
    lookup = {}
    for _, row in rescued.iterrows():
        key = sb.make_custom_id(row[marca_col], row[descripcion_col])
        lookup[key] = {
            "gpc_code": row["gpc_code"],
            "nivel_asignado": row["nivel_asignado"],
            "gpc_description": row["gpc_description"],
        }
    return lookup


def main() -> int:
    summary = []
    grand_dist = {}
    grand_total = 0

    for year, pattern in YEAR_GLOBS.items():
        files = sorted(OUTPUT_DIR.glob(pattern))
        if not files:
            print(f"[AVISO] año {year}: no se encontraron archivos con el patrón '{pattern}'")
            continue

        year_frames = [pd.read_excel(f) for f in files]
        df = pd.concat(year_frames, ignore_index=True)

        descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(df)

        haiku_lookup = build_rescue_lookup(OUTPUT_DIR / f"no_match_{year}_reprocesado_haiku55.xlsx")
        sonnet_lookup = build_rescue_lookup(OUTPUT_DIR / f"no_match_{year}_rescate_sonnet.xlsx")

        is_no_match = df["nivel_asignado"].astype(str).str.upper() == "NO_MATCH"
        no_match_idx = df[is_no_match].index

        for idx in no_match_idx:
            key = sb.make_custom_id(df.at[idx, marca_col], df.at[idx, descripcion_col])
            hit = sonnet_lookup.get(key) or haiku_lookup.get(key)
            if hit is not None:
                df.at[idx, "gpc_code"] = hit["gpc_code"]
                df.at[idx, "nivel_asignado"] = hit["nivel_asignado"]
                df.at[idx, "gpc_description"] = hit["gpc_description"]

        total = len(df)
        dist = df["nivel_asignado"].astype(str).value_counts(dropna=False)
        no_match_final = int(dist.get("NO_MATCH", 0))
        error_final = int(dist.get("ERROR", 0))
        asignados = total - no_match_final - error_final

        summary.append(
            {
                "anio": year,
                "total": total,
                "asignados": asignados,
                "no_match": no_match_final,
                "error": error_final,
            }
        )
        for nivel, cnt in dist.items():
            grand_dist[nivel] = grand_dist.get(nivel, 0) + int(cnt)
        grand_total += total

    print("\n" + "=" * 78)
    print("RESUMEN GLOBAL — estado actual por año (tras todas las rondas de rescate)")
    print("=" * 78)
    print(f"{'Año':<8}{'Total':<10}{'Asignados':<14}{'% Asignado':<13}{'NO_MATCH':<12}{'% NO_MATCH':<12}")
    print("-" * 78)
    g_total = g_asig = g_nomatch = 0
    for row in summary:
        pct_asig = 100 * row["asignados"] / row["total"]
        pct_nom = 100 * row["no_match"] / row["total"]
        print(
            f"{row['anio']:<8}{row['total']:<10}{row['asignados']:<14}{pct_asig:<13.1f}"
            f"{row['no_match']:<12}{pct_nom:<12.1f}"
        )
        g_total += row["total"]
        g_asig += row["asignados"]
        g_nomatch += row["no_match"]
    print("-" * 78)
    pct_asig_total = 100 * g_asig / g_total
    pct_nom_total = 100 * g_nomatch / g_total
    print(
        f"{'TOTAL':<8}{g_total:<10}{g_asig:<14}{pct_asig_total:<13.1f}"
        f"{g_nomatch:<12}{pct_nom_total:<12.1f}"
    )
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())
