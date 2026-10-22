#!/usr/bin/env python3
"""Rescate heurístico de última instancia para el remanente NO_MATCH en
no_match_residual/: en vez de clasificar por descripción de producto
(como hace todo el resto del pipeline), infiere el Segment GPC a partir
de la MARCA/PROVEEDOR del producto, vía una llamada directa (no Batch
API) a Haiku 5.5.

Es deliberadamente una clasificación de bajísima precisión comparada
con el resto del pipeline (una marca puede vender en varios Segments;
muchos valores de "Marca" en los datos son en realidad códigos SKU
internos, no marcas reales) — se usa solo porque ya se agotaron las
rondas de rescate basadas en descripción (Haiku 5.5 + Sonnet 5.5) y el
usuario pidió explícitamente este último intento heurístico.

Candado ground-truth: el código Segment que devuelva Haiku para cada
marca se valida contra el catálogo oficial (debe existir literalmente
como fila nivel=="Segment"); si no es válido, se descarta esa marca
(no se inventa ni se fuerza un código). La descripción (gpc_description)
usada es SIEMPRE la del catálogo oficial, nunca el texto libre de Haiku.

Estructura de columnas: este pipeline no tiene columnas separadas por
nivel (Brick/Class/Family/Segment); el nivel se registra en la columna
única "nivel_asignado" (igual que para cualquier clasificación Segment
del pipeline principal), así que una fila rescatada por este método
queda con gpc_code=<segment>, nivel_asignado="Segment",
gpc_description=<título oficial del segmento>, confidence_score=40
(marcador fijo indicando "heurística por marca", muy por debajo del
score ~85-99 típico de una clasificación real basada en descripción).

Script independiente (reutiliza solo funciones de
submit_batches.py/retrieve_batches.py, no las modifica).
"""

import json
import re
import sys
import time
from pathlib import Path

import anthropic
import pandas as pd

import submit_batches as sb
import retrieve_batches as rb

RESIDUAL_DIR = Path("no_match_residual")
MODEL = "claude-haiku-5-5"
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


def build_segment_lookup() -> dict[str, str]:
    """codigo de Segment (8 dígitos) -> título oficial del catálogo."""
    df = pd.read_csv(sb.CATALOG_FILE, dtype=str)
    segments = df[df["nivel"] == "Segment"]
    return dict(zip(segments["codigo"], segments["titulo"]))


def extract_unique_brands() -> tuple[dict[str, str], dict[int, tuple[Path, str, str]]]:
    """Devuelve:
    - brand_display: clave normalizada (upper/strip) -> primer valor original visto
    - file_info: lista de (path, df, descripcion_col, marca_col) por archivo
    """
    brand_display: dict[str, str] = {}
    file_info = []
    for f in sorted(RESIDUAL_DIR.glob("no_match_residual_*.xlsx")):
        df = pd.read_excel(f)
        descripcion_col, marca_col = rb.resolve_descripcion_marca_columns(df)
        file_info.append((f, df, descripcion_col, marca_col))
        vals = df[marca_col].dropna().astype(str).str.strip()
        vals = vals[vals.str.len() >= 3]
        for v in vals:
            key = v.upper()
            if key not in brand_display:
                brand_display[key] = v
    return brand_display, file_info


def parse_json_response(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def call_haiku_chunk(client: "anthropic.Anthropic", brands_chunk: list[str]) -> dict[str, str]:
    marcas_text = "\n".join(f"- {b}" for b in brands_chunk)
    prompt = PROMPT_TEMPLATE.format(marcas=marcas_text)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": prompt}],
            )
            text_parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
            raw = "".join(text_parts)
            return parse_json_response(raw)
        except Exception as exc:
            print(f"  [reintento {attempt}/{MAX_RETRIES}] error en chunk: {exc}")
            if attempt == MAX_RETRIES:
                return {}
            time.sleep(3 * attempt)
    return {}


def main() -> int:
    client = anthropic.Anthropic()
    segment_lookup = build_segment_lookup()
    valid_codes = set(segment_lookup.keys())

    print("Extrayendo marcas únicas de no_match_residual/ ...")
    brand_display, file_info = extract_unique_brands()
    brands = sorted(brand_display.keys())
    print(f"Marcas únicas detectadas (>=3 caracteres): {len(brands)}")

    chunks = [brands[i : i + CHUNK_SIZE] for i in range(0, len(brands), CHUNK_SIZE)]
    print(f"Consultando Haiku 5.5 en {len(chunks)} llamadas directas (chunk={CHUNK_SIZE}) ...")

    brand_to_code: dict[str, str] = {}
    invalid_codes = 0
    for i, chunk in enumerate(chunks, 1):
        display_chunk = [brand_display[k] for k in chunk]
        result = call_haiku_chunk(client, display_chunk)
        for brand_raw, code in result.items():
            key = str(brand_raw).strip().upper()
            code_clean = re.sub(r"\D", "", str(code))
            if code_clean in valid_codes:
                brand_to_code[key] = code_clean
            else:
                invalid_codes += 1
        print(f"  [{i}/{len(chunks)}] recibidas {len(result)} marcas, acumulado válido={len(brand_to_code)}")

    print(f"\nMarcas con Segment válido asignado: {len(brand_to_code)} / {len(brands)}")
    print(f"Códigos devueltos por Haiku que NO existen en el catálogo (descartados): {invalid_codes}")

    total_rows_patched = 0
    total_rows_residual = 0
    per_year_summary = []

    for f, df, descripcion_col, marca_col in file_info:
        total_rows_residual += len(df)
        patched = 0
        for idx in df.index:
            marca_val = df.at[idx, marca_col]
            if pd.isna(marca_val):
                continue
            key = str(marca_val).strip().upper()
            if len(key) < 3:
                continue
            code = brand_to_code.get(key)
            if code is None:
                continue
            df.at[idx, "gpc_code"] = code
            df.at[idx, "nivel_asignado"] = "Segment"
            df.at[idx, "gpc_description"] = segment_lookup[code]
            df.at[idx, "confidence_score"] = HEURISTIC_CONFIDENCE
            patched += 1

        df.to_excel(f, index=False)
        total_rows_patched += patched
        per_year_summary.append((f.name, len(df), patched))
        print(f"{f.name}: {patched} / {len(df)} filas rescatadas (heurística marca->Segment)")

    print("\n" + "=" * 78)
    print("RESUMEN — Rescate heurístico Marca -> Segment GPC (Haiku 5.5, llamada directa)")
    print("=" * 78)
    for name, total, patched in per_year_summary:
        pct = 100 * patched / total if total else 0.0
        print(f"  {name}: {patched}/{total} ({pct:.1f}%)")
    print("-" * 78)
    pct_total = 100 * total_rows_patched / total_rows_residual if total_rows_residual else 0.0
    print(
        f"TOTAL: {total_rows_patched} / {total_rows_residual} registros residuales "
        f"rescatados ({pct_total:.1f}%) y guardados en no_match_residual/"
    )
    print(
        "Nota: clasificación de alto nivel (Segment) basada en heurística de "
        "marca/proveedor, confidence_score fijo = "
        f"{HEURISTIC_CONFIDENCE} para distinguirla de una clasificación real "
        "por descripción de producto."
    )
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())
