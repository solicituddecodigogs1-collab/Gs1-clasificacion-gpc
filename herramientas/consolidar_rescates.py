#!/usr/bin/env python3
"""Consolida los rescates de NO_MATCH (Haiku 5.5 y Sonnet 5.5) de vuelta
en los archivos principales por año, parcheando in-place solo las filas
que seguían NO_MATCH — el resto de cada archivo queda intacto.

Jerarquía de rescate: si una fila tiene resultado exitoso en el rescate
Sonnet 5.5, ese prevalece; si no, se usa el de Haiku 5.5 (solo existe
para 2019-2025); si ninguno rescató la fila, queda NO_MATCH tal cual.

No se agregan ni quitan columnas: se sobrescriben únicamente gpc_code,
nivel_asignado, gpc_description y confidence_score de las filas
rescatadas, igual que en todos los reprocesamientos anteriores de este
pipeline.

Script independiente (reutiliza solo las funciones de normalización de
submit_batches.py/retrieve_batches.py, no las modifica).
"""

import sys
from pathlib import Path

import pandas as pd

import submit_batches as sb
import retrieve_batches as rb

OUTPUT_DIR = Path("Output_Clasificado")

# (año -> patrón de los archivos principales "Parte_N" de ese año)
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
            "confidence_score": row["confidence_score"],
        }
    return lookup


def main() -> int:
    grand_summary = []

    for year, pattern in YEAR_GLOBS.items():
        files = sorted(OUTPUT_DIR.glob(pattern))
        if not files:
            print(f"[AVISO] año {year}: no se encontraron archivos con el patrón '{pattern}'")
            continue

        # Jerarquía: Sonnet 5.5 prevalece sobre Haiku 5.5.
        haiku_lookup = build_rescue_lookup(OUTPUT_DIR / f"no_match_{year}_reprocesado_haiku55.xlsx")
        sonnet_lookup = build_rescue_lookup(OUTPUT_DIR / f"no_match_{year}_rescate_sonnet.xlsx")

        for f in files:
            df = pd.read_excel(f)
            descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(df)

            is_no_match = df["nivel_asignado"].astype(str).str.upper() == "NO_MATCH"
            initial_no_match = int(is_no_match.sum())
            no_match_idx = df[is_no_match].index

            patched_sonnet = 0
            patched_haiku = 0
            for idx in no_match_idx:
                key = sb.make_custom_id(df.at[idx, marca_col], df.at[idx, descripcion_col])
                hit = sonnet_lookup.get(key)
                source = "sonnet"
                if hit is None:
                    hit = haiku_lookup.get(key)
                    source = "haiku"
                if hit is None:
                    continue
                df.at[idx, "gpc_code"] = hit["gpc_code"]
                df.at[idx, "nivel_asignado"] = hit["nivel_asignado"]
                df.at[idx, "gpc_description"] = hit["gpc_description"]
                df.at[idx, "confidence_score"] = hit["confidence_score"]
                if source == "sonnet":
                    patched_sonnet += 1
                else:
                    patched_haiku += 1

            final_no_match = initial_no_match - patched_sonnet - patched_haiku

            df.to_excel(f, index=False)

            grand_summary.append(
                {
                    "anio": year,
                    "archivo": f.name,
                    "no_match_inicial": initial_no_match,
                    "patched_sonnet": patched_sonnet,
                    "patched_haiku": patched_haiku,
                    "no_match_final": final_no_match,
                }
            )
            print(
                f"{f.name}: NO_MATCH inicial={initial_no_match} | "
                f"rescatado_sonnet={patched_sonnet} | rescatado_haiku={patched_haiku} | "
                f"NO_MATCH final={final_no_match}"
            )

    print("\n" + "=" * 78)
    print("RESUMEN — Consolidación de rescates por año")
    print("=" * 78)
    by_year: dict[int, dict] = {}
    for row in grand_summary:
        y = by_year.setdefault(
            row["anio"], {"no_match_inicial": 0, "patched_sonnet": 0, "patched_haiku": 0, "no_match_final": 0}
        )
        y["no_match_inicial"] += row["no_match_inicial"]
        y["patched_sonnet"] += row["patched_sonnet"]
        y["patched_haiku"] += row["patched_haiku"]
        y["no_match_final"] += row["no_match_final"]

    total_inicial = total_sonnet = total_haiku = total_final = 0
    for year, y in by_year.items():
        print(
            f"  {year}: NO_MATCH inicial={y['no_match_inicial']} | "
            f"rescatado_sonnet={y['patched_sonnet']} | rescatado_haiku={y['patched_haiku']} | "
            f"NO_MATCH final={y['no_match_final']}"
        )
        total_inicial += y["no_match_inicial"]
        total_sonnet += y["patched_sonnet"]
        total_haiku += y["patched_haiku"]
        total_final += y["no_match_final"]
    print("-" * 78)
    print(
        f"TOTAL: NO_MATCH inicial={total_inicial} | rescatado_sonnet={total_sonnet} | "
        f"rescatado_haiku={total_haiku} | NO_MATCH final={total_final}"
    )
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())
