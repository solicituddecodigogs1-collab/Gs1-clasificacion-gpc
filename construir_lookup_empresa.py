#!/usr/bin/env python3
"""Construye catalogo/empresa_giro_lookup.json: para cada empresa (Rif o
EMPRESA, según el esquema del año), el Segment GPC dominante entre sus
filas YA clasificadas con confianza real (no heurística, confidence_score
>= 60, nivel_asignado != NO_MATCH) en TODO el histórico del proyecto.

Esto es un dato estadístico derivado de nuestro propio trabajo ya
validado contra el candado ground-truth -- no es una adivinanza del
modelo. Implementa el punto A de la metodología (Fase 2): identificar el
giro comercial de la empresa para desambiguar códigos crípticos o
corregir asignaciones heurísticas erróneas (caso VENOCO).

Requiere al menos MIN_FILAS filas confiables y MIN_CONSISTENCIA de
coincidencia en el mismo Segment para aceptar la empresa en el lookup;
de lo contrario se descarta por ambigua.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

import preclasificador as pc

HIST_DIR = Path("Output_Historico")
CATALOG_FILE = Path("catalogo/gpc_catalogo_oficial.csv")
OUT_FILE = Path("catalogo/empresa_giro_lookup.json")

MIN_FILAS = 3
MIN_CONSISTENCIA = 0.60


def main() -> int:
    cat = pd.read_csv(CATALOG_FILE, dtype=str)
    code_to_segment = dict(zip(cat["codigo"], cat["segment_code"]))
    segment_titulo = dict(
        zip(cat.loc[cat["nivel"] == "Segment", "codigo"], cat.loc[cat["nivel"] == "Segment", "titulo"])
    )

    # empresa_id -> {segment_code: count}
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_rows = 0
    confident_rows = 0

    files = sorted(HIST_DIR.glob("Final_*.xlsx"))
    for f in files:
        df = pd.read_excel(f)
        cols = pc.resolve_schema(df)
        if cols.empresa_col is None:
            print(f"[AVISO] {f.name}: sin columna de empresa (Rif/EMPRESA), se omite")
            continue

        total_rows += len(df)
        conf = pd.to_numeric(df.get("confidence_score"), errors="coerce")
        nivel = df.get("nivel_asignado").astype(str)
        mask = (conf >= 60) & (conf != 40) & (nivel != "NO_MATCH") & (nivel != "nan")
        sub = df[mask]
        confident_rows += len(sub)

        empresa_vals = sub[cols.empresa_col].astype(str).str.strip().str.upper()
        segment_vals = sub["gpc_code"].astype(str).map(code_to_segment)

        for emp, seg in zip(empresa_vals, segment_vals):
            if not emp or emp in ("NAN", "") or pd.isna(seg):
                continue
            counts[emp][seg] += 1
        print(f"{f.name}: {len(sub)} filas confiables (de {len(df)})")

    lookup: dict[str, dict] = {}
    descartadas = 0
    for emp, seg_counts in counts.items():
        n = sum(seg_counts.values())
        if n < MIN_FILAS:
            continue
        top_seg, top_n = max(seg_counts.items(), key=lambda kv: kv[1])
        consistencia = top_n / n
        if consistencia < MIN_CONSISTENCIA:
            descartadas += 1
            continue
        lookup[emp] = {
            "segment_code": top_seg,
            "segment_titulo": segment_titulo.get(top_seg, "?"),
            "filas_soporte": n,
            "consistencia": round(consistencia, 3),
        }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(lookup, fh, ensure_ascii=False, indent=1, sort_keys=True)

    print(f"\n{'='*70}")
    print(f"Filas totales procesadas: {total_rows}")
    print(f"Filas confiables (no heurísticas, confianza>=60): {confident_rows}")
    print(f"Empresas en el lookup final: {len(lookup)}")
    print(f"Empresas descartadas por ambiguas (<60% consistencia): {descartadas}")
    print(f"Guardado en: {OUT_FILE}")
    print(f"{'='*70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
