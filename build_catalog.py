#!/usr/bin/env python3
"""Genera el diccionario oficial ligero de códigos GPC.

Lee la pestaña "Schema" de "catalogo/GPC as of May 2026 v20260520 MX.xlsx"
y extrae los 4 niveles jerárquicos (Segment, Family, Class, Brick),
desduplicados, con sus códigos padre, en "catalogo/gpc_catalogo_oficial.csv".
Este CSV es la única fuente de verdad usada por submit_batches.py (para
armar candidatos) y retrieve_batches.py (para validar que un gpc_code
devuelto por la API exista realmente antes de aceptarlo).
"""

import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_catalog")

CATALOG_DIR = Path("catalogo")
SOURCE_FILE = CATALOG_DIR / "GPC as of May 2026 v20260520 MX.xlsx"
SHEET_NAME = "Schema"
OUTPUT_FILE = CATALOG_DIR / "gpc_catalogo_oficial.csv"

REQUIRED_COLUMNS = [
    "SegmentCode",
    "SegmentTitle",
    "FamilyCode",
    "FamilyTitle",
    "ClassCode",
    "ClassTitle",
    "BrickCode",
    "BrickTitle",
]


def code_to_str(series: pd.Series) -> pd.Series:
    """Convierte códigos a strings exactos de 8 dígitos (sin '.0' ni 'nan')."""
    return series.dropna().astype("int64").astype(str).str.zfill(8)


def build_catalog(source_file: Path) -> pd.DataFrame:
    if not source_file.exists():
        raise FileNotFoundError(f"No se encuentra el catálogo oficial: {source_file}")

    logger.info(f"Leyendo hoja '{SHEET_NAME}' de {source_file} (puede tardar unos segundos)...")
    df = pd.read_excel(source_file, sheet_name=SHEET_NAME, usecols=REQUIRED_COLUMNS)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en la hoja '{SHEET_NAME}': {missing}")

    df = df.dropna(subset=REQUIRED_COLUMNS)

    rows = []

    segments = df[["SegmentCode", "SegmentTitle"]].drop_duplicates(subset=["SegmentCode"])
    for _, r in segments.iterrows():
        rows.append(
            {
                "nivel": "Segment",
                "codigo": str(int(r["SegmentCode"])).zfill(8),
                "titulo": str(r["SegmentTitle"]).strip(),
                "segment_code": str(int(r["SegmentCode"])).zfill(8),
                "family_code": "",
                "class_code": "",
            }
        )

    families = df[["FamilyCode", "FamilyTitle", "SegmentCode"]].drop_duplicates(subset=["FamilyCode"])
    for _, r in families.iterrows():
        rows.append(
            {
                "nivel": "Family",
                "codigo": str(int(r["FamilyCode"])).zfill(8),
                "titulo": str(r["FamilyTitle"]).strip(),
                "segment_code": str(int(r["SegmentCode"])).zfill(8),
                "family_code": str(int(r["FamilyCode"])).zfill(8),
                "class_code": "",
            }
        )

    classes = df[["ClassCode", "ClassTitle", "FamilyCode", "SegmentCode"]].drop_duplicates(subset=["ClassCode"])
    for _, r in classes.iterrows():
        rows.append(
            {
                "nivel": "Class",
                "codigo": str(int(r["ClassCode"])).zfill(8),
                "titulo": str(r["ClassTitle"]).strip(),
                "segment_code": str(int(r["SegmentCode"])).zfill(8),
                "family_code": str(int(r["FamilyCode"])).zfill(8),
                "class_code": str(int(r["ClassCode"])).zfill(8),
            }
        )

    bricks = df[["BrickCode", "BrickTitle", "ClassCode", "FamilyCode", "SegmentCode"]].drop_duplicates(
        subset=["BrickCode"]
    )
    for _, r in bricks.iterrows():
        rows.append(
            {
                "nivel": "Brick",
                "codigo": str(int(r["BrickCode"])).zfill(8),
                "titulo": str(r["BrickTitle"]).strip(),
                "segment_code": str(int(r["SegmentCode"])).zfill(8),
                "family_code": str(int(r["FamilyCode"])).zfill(8),
                "class_code": str(int(r["ClassCode"])).zfill(8),
            }
        )

    catalog = pd.DataFrame(rows, columns=["nivel", "codigo", "titulo", "segment_code", "family_code", "class_code"])

    # Todos los códigos deben ser strings de exactamente 8 dígitos.
    bad_codes = catalog[~catalog["codigo"].str.match(r"^\d{8}$")]
    if not bad_codes.empty:
        raise ValueError(f"Se encontraron códigos que no son de 8 dígitos exactos:\n{bad_codes}")

    dup_codes = catalog[catalog.duplicated(subset=["codigo"], keep=False)]
    if not dup_codes.empty:
        raise ValueError(f"Códigos GPC duplicados entre niveles (no debería ocurrir):\n{dup_codes}")

    return catalog


def main() -> int:
    try:
        catalog = build_catalog(SOURCE_FILE)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return 1

    counts = catalog["nivel"].value_counts()
    logger.info(
        "Niveles: Segment=%d, Family=%d, Class=%d, Brick=%d (total=%d)",
        counts.get("Segment", 0),
        counts.get("Family", 0),
        counts.get("Class", 0),
        counts.get("Brick", 0),
        len(catalog),
    )

    catalog.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    logger.info(f"Catálogo guardado en {OUTPUT_FILE} ({len(catalog)} códigos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
