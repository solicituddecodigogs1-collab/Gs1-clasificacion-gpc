#!/usr/bin/env python3
"""Cierre oficial del primer bloque de 10 años (2015-2025): consolida
todas las partes fragmentadas de cada año en un único archivo final por
año, incorporando el rescate heurístico Marca->Segment aplicado sobre
no_match_residual/, y los agrupa en Output_Clasificado/Lote_2015_2025/.

Fusión por año: concatena verticalmente las N partes de cada año (los
mismos patrones YEAR_GLOBS usados en todo este pipeline para localizar
los archivos reales de cada año, ya que los nombres varían mucho entre
años). Luego, para las filas que sigan en nivel_asignado=="NO_MATCH",
aplica el lookup construido desde no_match_residual_<año>.xlsx (que ya
contiene el rescate heurístico de marca->Segment aplicado en el paso
anterior) para traer esos datos al archivo final.

No modifica ningún archivo de origen (ni las partes en
Output_Clasificado/ ni no_match_residual/) — solo lee y escribe el
nuevo archivo consolidado Final_<año>.xlsx.

Script independiente (reutiliza solo funciones de
submit_batches.py/retrieve_batches.py, no las modifica).
"""

import sys
from pathlib import Path

import pandas as pd

import submit_batches as sb
import retrieve_batches as rb

OUTPUT_DIR = Path("Output_Clasificado")
RESIDUAL_DIR = Path("no_match_residual")
LOTE_DIR = OUTPUT_DIR / "Lote_2015_2025"

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


def build_residual_lookup(year: int) -> dict[str, dict]:
    """custom_id -> {gpc_code, nivel_asignado, gpc_description, confidence_score}
    solo para filas que el rescate heurístico de no_match_residual_<año>.xlsx
    SÍ resolvió (nivel_asignado != NO_MATCH)."""
    path = RESIDUAL_DIR / f"no_match_residual_{year}.xlsx"
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


def main() -> int:
    LOTE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("CIERRE DE BLOQUE — Consolidación final 2015-2025")
    print("=" * 78)

    total_partes_global = 0
    total_final_global = 0
    rows_summary = []

    for year, pattern in YEAR_GLOBS.items():
        files = sorted(OUTPUT_DIR.glob(pattern))
        if not files:
            print(f"[AVISO] año {year}: no se encontraron archivos con el patrón '{pattern}'")
            continue

        frames = [pd.read_excel(f) for f in files]
        suma_partes = sum(len(f_df) for f_df in frames)
        df_year = pd.concat(frames, ignore_index=True)

        descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(df_year)
        residual_lookup = build_residual_lookup(year)

        is_no_match = df_year["nivel_asignado"].astype(str).str.upper() == "NO_MATCH"
        patched = 0
        for idx in df_year[is_no_match].index:
            key = sb.make_custom_id(df_year.at[idx, marca_col], df_year.at[idx, descripcion_col])
            hit = residual_lookup.get(key)
            if hit is None:
                continue
            df_year.at[idx, "gpc_code"] = hit["gpc_code"]
            df_year.at[idx, "nivel_asignado"] = hit["nivel_asignado"]
            df_year.at[idx, "gpc_description"] = hit["gpc_description"]
            df_year.at[idx, "confidence_score"] = hit["confidence_score"]
            patched += 1

        out_path = LOTE_DIR / f"Final_{year}.xlsx"
        df_year.to_excel(out_path, index=False)

        total_final = len(df_year)
        ok = "OK" if total_final == suma_partes else "¡DISCREPANCIA!"
        total_partes_global += suma_partes
        total_final_global += total_final
        rows_summary.append((year, len(files), suma_partes, total_final, patched))

        print(
            f"Año {year}: {len(files)} partes -> suma_partes={suma_partes} | "
            f"filas_final={total_final} | heurística_incorporada={patched} | {ok} "
            f"-> {out_path}"
        )

    print("-" * 78)
    ok_global = "OK" if total_final_global == total_partes_global else "¡DISCREPANCIA!"
    print(
        f"TOTAL: suma_partes={total_partes_global} | filas_final={total_final_global} | {ok_global}"
    )
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())
