#!/usr/bin/env python3
"""Extrae el remanente NO_MATCH de los años ya procesados (aislados en
Output_Historico/) para trabajarlos de forma separada, uno a uno.

Itera sobre TODOS los Excel dentro de Output_Historico/, los agrupa por
año (detectado del nombre del archivo — un año puede tener 1 archivo ya
consolidado, p. ej. Final_2025.xlsx, o varias partes, p. ej.
clasificado_Consolidado_2010_Parte_1..5.xlsx), y extrae estricta y
únicamente las filas donde nivel_asignado == "NO_MATCH" (sin ampliar el
filtro a códigos vacíos/inválidos, a diferencia de
extraer_no_match_residual.py).

Exporta un archivo independiente por año a
Remanentes_NO_MATCH/NO_MATCH_<año>.xlsx, y termina con la tabla de
métrica de control: SKUs originales, NO_MATCH extraídos y match rate
por año.

Script independiente, de solo lectura sobre Output_Historico/ (no
modifica ningún archivo de origen).
"""

import re
import sys
from pathlib import Path

import pandas as pd

HIST_DIR = Path("Output_Historico")
OUT_DIR = Path("Remanentes_NO_MATCH")

YEAR_RE = re.compile(r"(20\d{2})")


def group_files_by_year() -> dict[int, list[Path]]:
    files_by_year: dict[int, list[Path]] = {}
    for f in sorted(HIST_DIR.glob("*.xlsx")):
        m = YEAR_RE.search(f.name)
        if not m:
            print(f"[AVISO] no se pudo determinar el año de '{f.name}', se omite")
            continue
        year = int(m.group(1))
        files_by_year.setdefault(year, []).append(f)
    return files_by_year


def main() -> int:
    if not HIST_DIR.exists():
        print(f"[ERROR] no existe {HIST_DIR}/")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files_by_year = group_files_by_year()

    summary = []
    for year in sorted(files_by_year):
        files = files_by_year[year]
        frames = [pd.read_excel(f) for f in files]
        df = pd.concat(frames, ignore_index=True)

        total = len(df)
        mask = df["nivel_asignado"].astype(str).str.strip() == "NO_MATCH"
        no_match = df[mask].copy()
        n_no_match = len(no_match)

        out_path = OUT_DIR / f"NO_MATCH_{year}.xlsx"
        no_match.to_excel(out_path, index=False)

        match_rate = 100 * (total - n_no_match) / total if total else 0.0
        summary.append((year, total, n_no_match, match_rate))
        print(
            f"{year}: {len(files)} archivo(s) -> total={total} | "
            f"NO_MATCH={n_no_match} -> {out_path}"
        )

    print("\n" + "=" * 70)
    print("MÉTRICA DE CONTROL — Remanente NO_MATCH por año (Output_Historico/)")
    print("=" * 70)
    print(f"{'Año':<8}{'Total SKUs':<14}{'NO_MATCH':<12}{'Match Rate':<12}")
    print("-" * 70)
    g_total = g_nm = 0
    for year, total, nm, rate in summary:
        print(f"{year:<8}{total:<14}{nm:<12}{rate:<12.1f}")
        g_total += total
        g_nm += nm
    print("-" * 70)
    g_rate = 100 * (g_total - g_nm) / g_total if g_total else 0.0
    print(f"{'TOTAL':<8}{g_total:<14}{g_nm:<12}{g_rate:<12.1f}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
