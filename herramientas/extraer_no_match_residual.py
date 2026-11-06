#!/usr/bin/env python3
"""Extrae los registros que definitivamente quedaron sin clasificar tras
la consolidación de todos los rescates (Haiku 5.5 + Sonnet 5.5), los
exporta agrupados por año a no_match_residual/, y proyecta el costo de
un último intento con Opus 5.5 vía Batch API.

Filtro de "no resuelto" (más estricto que solo nivel_asignado=="NO_MATCH"):
  - nivel_asignado es exactamente "NO_MATCH", o
  - gpc_code está vacío/NaN, o
  - gpc_code no es un código de 8 dígitos presente literalmente en el
    catálogo oficial (revalidación del candado ground-truth: si algo se
    coló más allá del candado por cualquier motivo, se marca residual
    también, nunca se reporta como "clasificado" a ciegas).

Estimación de costo: usa la MISMA metodología de --dry-run de
submit_batches.py (candidatos TF-IDF reales + estimador local de
~4 caracteres/token) aplicada directamente sobre una muestra de los
productos únicos residuales (no sobre un promedio histórico genérico),
con los precios de Batch API de Opus 5.5 (ver OPUS_* más abajo).

Script independiente: solo reutiliza funciones de normalización/
catálogo de submit_batches.py y retrieve_batches.py sin modificarlos.
"""

import sys
from pathlib import Path

import pandas as pd

import submit_batches as sb
import retrieve_batches as rb

OUTPUT_DIR = Path("Output_Clasificado")
RESIDUAL_DIR = Path("no_match_residual")

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

# Precios Batch API de Opus 5.5, en USD por millón de tokens (50% del
# precio estándar). SUPUESTO: se asume que Opus 5.5 mantiene la misma
# tarifa estándar ($15/$75 por MTok) que Opus 4/4.5 — Anthropic no ha
# publicado (al momento de escribir esto) una tarifa distinta para 5.5;
# ajustar si corresponde.
OPUS_BATCH_PRICE_INPUT_PER_MTOK = 7.50
OPUS_BATCH_PRICE_OUTPUT_PER_MTOK = 37.50

SAMPLE_SIZE_PER_YEAR = 40


def is_unresolved(df: pd.DataFrame, catalog_lookup: dict) -> pd.Series:
    nivel = df["nivel_asignado"].astype(str).str.strip().str.upper()
    codigo = df["gpc_code"].astype(str).str.strip()

    es_no_match = nivel == "NO_MATCH"
    vacio = df["gpc_code"].isna() | (codigo == "") | (codigo.str.upper() == "NAN")
    invalido = ~codigo.isin(catalog_lookup.keys()) & ~vacio & ~es_no_match

    return es_no_match | vacio | invalido


def main() -> int:
    RESIDUAL_DIR.mkdir(parents=True, exist_ok=True)
    catalog_lookup = rb.load_catalog_lookup(rb.CATALOG_FILE)
    catalog = sb.GpcCatalog(sb.CATALOG_FILE)

    per_year = []
    grand_total_rows = 0

    for year, pattern in YEAR_GLOBS.items():
        files = sorted(OUTPUT_DIR.glob(pattern))
        if not files:
            print(f"[AVISO] año {year}: no se encontraron archivos con el patrón '{pattern}'")
            continue

        year_frames = [pd.read_excel(f) for f in files]
        df = pd.concat(year_frames, ignore_index=True)

        mask = is_unresolved(df, catalog_lookup)
        residual = df[mask].copy()

        out_path = RESIDUAL_DIR / f"no_match_residual_{year}.xlsx"
        residual.to_excel(out_path, index=False)

        descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(residual) if not residual.empty else (None, None)
        unique_count = 0
        if not residual.empty:
            keys = residual.apply(lambda r: sb.make_custom_id(r[marca_col], r[descripcion_col]), axis=1)
            unique_count = keys.nunique()

        per_year.append(
            {
                "anio": year,
                "filas_residuales": len(residual),
                "productos_unicos": unique_count,
                "df": residual,
                "descripcion_col": descripcion_col,
                "marca_col": marca_col,
            }
        )
        grand_total_rows += len(residual)
        print(f"{out_path}: {len(residual)} filas residuales ({unique_count} productos únicos)")

    # --- Estimación de costo con Opus 5.5 ---
    output_tokens_estimate = min(sb.MAX_TOKENS, sb.estimate_tokens('{"gpc_code": "10002091", "confidence_score": 95}'))

    total_input_tokens = 0.0
    total_output_tokens = 0.0
    total_unique = 0
    cost_rows = []

    for row in per_year:
        residual, descripcion_col, marca_col = row["df"], row["descripcion_col"], row["marca_col"]
        if residual.empty:
            cost_rows.append({**row, "avg_input_tokens": 0, "costo": 0.0})
            continue

        residual_tmp = residual.copy()
        residual_tmp["_dedup_key"] = residual_tmp.apply(
            lambda r: sb.make_custom_id(r[marca_col], r[descripcion_col]), axis=1
        )
        unique_df = residual_tmp.drop_duplicates(subset=["_dedup_key"]).drop(columns=["_dedup_key"])
        sample = unique_df.sample(min(SAMPLE_SIZE_PER_YEAR, len(unique_df)), random_state=1)

        input_tokens_list = []
        for _, r in sample.iterrows():
            marca_val, descripcion_val = r.get(marca_col), r.get(descripcion_col)
            q = sb.query_text(marca_val, descripcion_val, None, None)
            candidates = catalog.build_candidates(q)
            user_content = sb.build_user_content(marca_val, descripcion_val, candidates)
            input_text = sb.SYSTEM_PROMPT + user_content
            input_tokens_list.append(sb.estimate_tokens(input_text))

        avg_input = sum(input_tokens_list) / len(input_tokens_list)
        n_unique = len(unique_df)
        year_input_tokens = avg_input * n_unique
        year_output_tokens = output_tokens_estimate * n_unique
        year_cost = (
            year_input_tokens / 1_000_000 * OPUS_BATCH_PRICE_INPUT_PER_MTOK
            + year_output_tokens / 1_000_000 * OPUS_BATCH_PRICE_OUTPUT_PER_MTOK
        )

        total_input_tokens += year_input_tokens
        total_output_tokens += year_output_tokens
        total_unique += n_unique

        cost_rows.append({**row, "avg_input_tokens": avg_input, "costo": year_cost})

    print("\n" + "=" * 86)
    print("RESUMEN — Residual NO_MATCH tras consolidación + proyección de costo Opus 5.5")
    print("=" * 86)
    print(f"{'Año':<8}{'Filas':<10}{'Únicos':<10}{'avg_tok_in':<12}{'Costo USD'}")
    print("-" * 86)
    total_cost = 0.0
    for row in cost_rows:
        print(
            f"{row['anio']:<8}{row['filas_residuales']:<10}{row['productos_unicos']:<10}"
            f"{row['avg_input_tokens']:<12.0f}${row['costo']:.2f}"
        )
        total_cost += row["costo"]
    print("-" * 86)
    print(f"TOTAL SKUs residuales (filas): {grand_total_rows}")
    print(f"TOTAL productos únicos (lo que realmente se enviaría a la API): {total_unique}")
    print(f"TOTAL input tokens (est.): {total_input_tokens:,.0f}")
    print(f"TOTAL output tokens (est.): {total_output_tokens:,.0f}")
    print(
        f"Precios Batch API Opus 5.5 (supuesto, 50% de ${OPUS_BATCH_PRICE_INPUT_PER_MTOK*2:.2f}/"
        f"${OPUS_BATCH_PRICE_OUTPUT_PER_MTOK*2:.2f} estándar): "
        f"${OPUS_BATCH_PRICE_INPUT_PER_MTOK:.2f} / ${OPUS_BATCH_PRICE_OUTPUT_PER_MTOK:.2f} por MTok"
    )
    print(f"COSTO TOTAL ESTIMADO (Opus 5.5, Batch API, sin cache_control): ${total_cost:.2f} USD")
    print("=" * 86)

    return 0


if __name__ == "__main__":
    sys.exit(main())
