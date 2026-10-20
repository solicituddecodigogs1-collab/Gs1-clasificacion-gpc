#!/usr/bin/env python3
"""Consolida todos los registros NO_MATCH de los años ya procesados
(2019, 2020, 2021, 2022, 2023, 2025) en un único lugar para revisión/
auditoría manual.

Script completamente independiente: no importa submit_batches.py ni
retrieve_batches.py.

Pasos:
1. Crea la carpeta no_match_historico/ (si no existe).
2. Para cada año, lee los archivos finales de Output_Clasificado/ y
   filtra estrictamente las filas donde nivel_asignado == "NO_MATCH"
   (ground-truth lock: toda fila NO_MATCH también tiene gpc_code ==
   "NO_MATCH" exacto; se verifican ambas columnas por si acaso).
3. Exporta un Excel independiente por año a
   no_match_historico/no_match_<año>.xlsx, conservando todas las
   columnas originales.
4. Imprime un resumen en consola con el conteo por año y el total.

Nota: 2024 no está en la lista de años pedida explícitamente por el
usuario (ver mensaje); si fue un olvido, es trivial agregarlo luego.
"""

import sys
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path("Output_Clasificado")
NO_MATCH_DIR = Path("no_match_historico")

YEAR_GLOBS = {
    2019: "clasificado_2019 Consolidado_Parte_*.xlsx",
    2020: "clasificado_Listado completo 2020_Parte_*.xlsx",
    2021: "clasificado_Consolidacion 2021_Parte_*.xlsx",
    2022: "clasificado_Listado General (2022)_Parte_*.xlsx",
    2023: "clasificado_Base_2023_Parte_*.xlsx",
    2025: "clasificado_Base_2025_Parte_*.xlsx",
}


def is_no_match(df: pd.DataFrame) -> pd.Series:
    """Filtro estricto: nivel_asignado o gpc_code exactamente 'NO_MATCH'."""
    nivel = df["nivel_asignado"].astype(str).str.strip().str.upper()
    codigo = df["gpc_code"].astype(str).str.strip().str.upper()
    return (nivel == "NO_MATCH") | (codigo == "NO_MATCH")


def main() -> int:
    NO_MATCH_DIR.mkdir(parents=True, exist_ok=True)

    summary = []

    for year, pattern in YEAR_GLOBS.items():
        files = sorted(OUTPUT_DIR.glob(pattern))
        if not files:
            print(f"[AVISO] año {year}: no se encontraron archivos con el patrón '{pattern}'")
            summary.append({"anio": year, "archivos_leidos": 0, "filas_no_match": 0})
            continue

        year_frames = []
        for f in files:
            df = pd.read_excel(f)
            no_match_mask = is_no_match(df)
            if no_match_mask.any():
                year_frames.append(df[no_match_mask])

        if year_frames:
            year_no_match = pd.concat(year_frames, ignore_index=True)
        else:
            year_no_match = pd.DataFrame()

        out_path = NO_MATCH_DIR / f"no_match_{year}.xlsx"
        year_no_match.to_excel(out_path, index=False)

        summary.append(
            {
                "anio": year,
                "archivos_leidos": len(files),
                "filas_no_match": len(year_no_match),
            }
        )

    print("\n" + "=" * 60)
    print("RESUMEN — NO_MATCH histórico consolidado")
    print("=" * 60)
    print(f"{'Año':<8}{'Archivos':<12}{'Filas NO_MATCH':<16}")
    print("-" * 60)
    total = 0
    for row in summary:
        print(f"{row['anio']:<8}{row['archivos_leidos']:<12}{row['filas_no_match']:<16}")
        total += row["filas_no_match"]
    print("-" * 60)
    print(f"{'TOTAL':<20}{total:<16}")
    print("=" * 60)
    print(f"Archivos guardados en: {NO_MATCH_DIR}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
