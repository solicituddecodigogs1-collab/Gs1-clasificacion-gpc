#!/usr/bin/env python3
"""Herencia de Cruce Histórico — rescata filas NO_MATCH de 2020 usando
clasificaciones ya exitosas de otros años, sin gastar tokens de la API.

Script completamente independiente: NO importa ni modifica submit_batches.py
ni retrieve_batches.py. La normalización de texto y el hash (marca,
descripción) están duplicados aquí deliberadamente para que este script no
dependa de ningún otro archivo del repo.

Pasos:
1. Maestro Histórico: lee los archivos ya clasificados de 2021, 2022, 2023
   y 2025 en Output_Clasificado/, se queda solo con filas con gpc_code
   válido (no nulo, no "NO_MATCH").
2. Llave de cruce: hash sha1 de (marca, descripción) normalizados —idéntico
   al custom_id usado en todo el pipeline—, dedupe quedándose con la
   primera aparición.
3. Cruce con 2020: para cada uno de los 5 archivos de 2020, identifica las
   filas NO_MATCH.
4. Herencia: si la llave está en el maestro histórico, sobrescribe
   gpc_code/nivel_asignado/gpc_description con el valor heredado y pone
   confidence_score = "Heredado de histórico" (texto, no número — queda
   trazable en el Excel).
5. Exporta sobrescribiendo los mismos 5 archivos en Output_Clasificado/,
   dejando el resto de columnas y filas intactas.
6. Imprime un resumen: NO_MATCH inicial, heredado, NO_MATCH final — total
   y por archivo.
"""

import hashlib
import re
import unicodedata
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path("Output_Clasificado")

HISTORICAL_GLOBS = {
    2021: "clasificado_Consolidacion 2021_Parte_*.xlsx",
    2022: "clasificado_Listado General (2022)_Parte_*.xlsx",
    2023: "clasificado_Base_2023_Parte_*.xlsx",
    2025: "clasificado_Base_2025_Parte_*.xlsx",
}

TARGET_2020_GLOB = "clasificado_Listado completo 2020_Parte_*.xlsx"

INHERITED_LABEL = "Heredado de histórico"


# --------------------------------------------------------------------------
# Normalización de texto / hash — DUPLICADO deliberadamente de
# submit_batches.py/retrieve_batches.py (mismo algoritmo exacto) para que
# este script sea 100% independiente y no requiera importarlos.
# --------------------------------------------------------------------------

PACKAGING_SUFFIX_RE = re.compile(r"\bx\s*\d+\s*(und|unid|unidades)\b")


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize_text(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        value = ""
    text = strip_accents(str(value)).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_packaging_suffix(text: str) -> str:
    text = PACKAGING_SUFFIX_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_descripcion(descripcion) -> str:
    return strip_packaging_suffix(normalize_text(descripcion))


def make_custom_id(marca, descripcion) -> str:
    key = f"{normalize_text(marca)}|{normalize_descripcion(descripcion)}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:24]


# --------------------------------------------------------------------------
# 1-2. Maestro Histórico
# --------------------------------------------------------------------------

def build_historical_master() -> dict[str, dict]:
    master: dict[str, dict] = {}
    for year in sorted(HISTORICAL_GLOBS):
        pattern = HISTORICAL_GLOBS[year]
        files = sorted(OUTPUT_DIR.glob(pattern))
        if not files:
            print(f"  [AVISO] año {year}: no se encontraron archivos con el patrón '{pattern}'")
            continue
        for f in files:
            df = pd.read_excel(f)
            valid = df[df["gpc_code"].notna() & (df["gpc_code"].astype(str).str.strip().str.upper() != "NO_MATCH")]
            added = 0
            for _, row in valid.iterrows():
                key = make_custom_id(row["MARCA"], row["DESCRIPCION"])
                if key in master:
                    continue  # ya existe una entrada histórica (primera en aparecer gana)
                master[key] = {
                    "gpc_code": row["gpc_code"],
                    "nivel_asignado": row["nivel_asignado"],
                    "gpc_description": row["gpc_description"],
                }
                added += 1
            print(f"  {f.name}: {len(valid)} filas válidas, {added} nuevas llaves agregadas al maestro")
    return master


# --------------------------------------------------------------------------
# 3-5. Cruce + herencia + exportación sobre los 5 archivos de 2020
# --------------------------------------------------------------------------

def inherit_for_2020(master: dict[str, dict]) -> list[dict]:
    report_rows = []
    files = sorted(OUTPUT_DIR.glob(TARGET_2020_GLOB))
    if not files:
        print(f"  [AVISO] no se encontraron archivos de 2020 con el patrón '{TARGET_2020_GLOB}'")
        return report_rows

    for f in files:
        df = pd.read_excel(f)
        is_no_match = df["nivel_asignado"].astype(str).str.strip().str.upper() == "NO_MATCH"
        initial_no_match = int(is_no_match.sum())

        inherited = 0
        no_match_idx = df[is_no_match].index
        # El texto "Heredado de histórico" no cabe en una columna int64; se
        # vuelve object (mixto int/str) solo si de verdad hay algo que heredar.
        df["confidence_score"] = df["confidence_score"].astype(object)
        for idx in no_match_idx:
            key = make_custom_id(df.at[idx, "MARCA"], df.at[idx, "DESCRIPCION"])
            hit = master.get(key)
            if hit is None:
                continue
            df.at[idx, "gpc_code"] = hit["gpc_code"]
            df.at[idx, "nivel_asignado"] = hit["nivel_asignado"]
            df.at[idx, "gpc_description"] = hit["gpc_description"]
            df.at[idx, "confidence_score"] = INHERITED_LABEL
            inherited += 1

        final_no_match = int((df["nivel_asignado"].astype(str).str.strip().str.upper() == "NO_MATCH").sum())

        df.to_excel(f, index=False)

        report_rows.append(
            {
                "archivo": f.name,
                "no_match_inicial": initial_no_match,
                "heredado": inherited,
                "no_match_final": final_no_match,
            }
        )
        print(
            f"  {f.name}: NO_MATCH inicial={initial_no_match} | heredado={inherited} | "
            f"NO_MATCH final={final_no_match}"
        )

    return report_rows


def main() -> int:
    print("=" * 78)
    print("PASO 1-2: Construyendo Maestro Histórico (2021, 2022, 2023, 2025)")
    print("=" * 78)
    master = build_historical_master()
    print(f"\nTotal de llaves únicas en el Maestro Histórico: {len(master)}\n")

    print("=" * 78)
    print("PASO 3-5: Cruzando y heredando sobre los 5 archivos de 2020")
    print("=" * 78)
    report_rows = inherit_for_2020(master)

    print("\n" + "=" * 78)
    print("RESUMEN FINAL — Herencia de Cruce Histórico (2020)")
    print("=" * 78)
    total_inicial = sum(r["no_match_inicial"] for r in report_rows)
    total_heredado = sum(r["heredado"] for r in report_rows)
    total_final = sum(r["no_match_final"] for r in report_rows)
    for r in report_rows:
        print(f"  {r['archivo']}: inicial={r['no_match_inicial']} | heredado={r['heredado']} | final={r['no_match_final']}")
    print("-" * 78)
    print(f"TOTAL — NO_MATCH inicial: {total_inicial}")
    print(f"TOTAL — Heredado del histórico: {total_heredado}")
    print(f"TOTAL — NO_MATCH final (sin rescatar): {total_final}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
