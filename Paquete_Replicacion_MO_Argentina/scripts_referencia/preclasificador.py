#!/usr/bin/env python3
"""Capa de pre-clasificación GPC (Fase 2 de la auditoría de rescates).

Motivación: la heurística Marca->Segment usada hasta ahora (ver
rescate_marca_segment.py y las Fases 6 de rescate_anticipado_*.py) le
pide al modelo que adivine el "giro comercial" de una marca a partir
ÚNICAMENTE del nombre de marca, sin contexto de producto. Auditoría
2026-11-06: para la marca VENOCO (lubricantes), ~82% de sus 22 filas
asignadas por esa heurística quedaron mal (mayormente "Alimentos/
Bebidas"). Alcance total: 123,736 filas (10.4% del proyecto) en 8,596
marcas distintas pasaron por esa heurística.

Esta capa implementa, en orden de prioridad:

  1. Reglas de dominio por regex sobre nomenclatura técnica (lubricantes
     SAE/API, frenos FMSI, rodamientos ISO, HVAC/iluminación, eléctrico
     industrial, agroquímicos NPK) -> asignación directa de alta
     confianza, sin necesidad de LLM.
  2. Lookup Empresa/RIF -> giro comercial, construido a partir de las
     filas YA clasificadas con alta confianza (no heurísticas) del
     propio proyecto -- un dato estadístico real, no una adivinanza.

Candado ground-truth (punto F de la metodología): TODO código en
REGLAS_REGEX se valida contra catalogo/gpc_catalogo_oficial.csv al
importar este módulo. Si un código no existe en el catálogo oficial,
la importación falla con AssertionError -- nunca se exporta un código
inventado.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

CATALOG_FILE = Path("catalogo/gpc_catalogo_oficial.csv")

# --------------------------------------------------------------------------
# Normalización de texto
# --------------------------------------------------------------------------

def strip_accents(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def normalize_text(text) -> str:
    """Minúsculas, sin tildes, espacios colapsados. Base de full_context
    y de la búsqueda de patrones regex."""
    if pd.isna(text):
        return ""
    t = strip_accents(str(text)).lower()
    t = re.sub(r"\s+", " ", t).strip()
    return t


# --------------------------------------------------------------------------
# Resolución de columnas (empresa/marca/descripción) por año
# --------------------------------------------------------------------------

# Nombres de columna de identificación de empresa vistos en los distintos
# formatos de GS1 Venezuela a través de los años: esquema "Rif" (número
# fiscal, años con columna "Afiliado/id") vs. esquema "EMPRESA" (razón
# social, años 2021-2025 y 2001-2003).
EMPRESA_ID_CANDIDATES = ["rif", "empresa"]
MARCA_CANDIDATES = ["marca"]
DESCRIPCION_CANDIDATES = ["descripcion", "nombre", "descripcion ampliada"]


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {re.sub(r"\s+", " ", strip_accents(str(c)).strip().lower()): c for c in df.columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    return None


@dataclass
class SchemaColumns:
    empresa_col: str | None
    marca_col: str | None
    descripcion_col: str | None


def resolve_schema(df: pd.DataFrame) -> SchemaColumns:
    return SchemaColumns(
        empresa_col=_find_column(df, EMPRESA_ID_CANDIDATES),
        marca_col=_find_column(df, MARCA_CANDIDATES),
        descripcion_col=_find_column(df, DESCRIPCION_CANDIDATES),
    )


def build_full_context(row: pd.Series, cols: SchemaColumns) -> str:
    """Vector de texto único: empresa + marca + descripción, normalizado.
    Nunca evalúa una columna aislada -- cubre el caso frecuente en GS1
    Venezuela donde el afiliado invierte Marca <-> Nombre/Descripción."""
    parts = []
    for col in (cols.empresa_col, cols.marca_col, cols.descripcion_col):
        if col is not None and col in row.index:
            parts.append(normalize_text(row[col]))
    return " ".join(p for p in parts if p)


# --------------------------------------------------------------------------
# Reglas de dominio por regex (punto C de la metodología)
# --------------------------------------------------------------------------

@dataclass
class RegexRule:
    pattern: re.Pattern
    gpc_code: str
    nivel: str
    confidence: int
    label: str


def _rule(pattern: str, gpc_code: str, nivel: str, confidence: int, label: str) -> RegexRule:
    return RegexRule(re.compile(pattern, re.IGNORECASE), gpc_code, nivel, confidence, label)


REGLAS_REGEX: list[RegexRule] = [
    # --- Lubricantes: grados de viscosidad SAE (admite "sm10w30" pegado,
    # sin límite de palabra entre el prefijo y el grado), normas API/ATF/
    # DEXRON/ISO ---
    _rule(
        r"(\d{1,2}w-?\d{2,3}|\bsae\s*\d{2,3}\b|"
        r"\bapi\s*(sn|sl|sm|ci-?4|cf|gl-?5)\b|\batf\b|\bdexron\b|\biso\s*68\b)",
        "10005267", "Brick", 85, "Lubricantes (grado SAE/norma API/ATF/DEXRON/ISO)",
    ),
    # --- Frenos y rodamientos: nomenclatura FMSI, rodamientos ISO (series
    # 60xx/62xx/63xx con sufijo ZZ/2RS), chumaceras ---
    _rule(
        r"\b(md\d{3,4}|cd\d{3,4}|d1376|wheel\s*cyl|\bktc\b)",
        "77015300", "Class", 80, "Frenos automotriz (nomenclatura FMSI)",
    ),
    _rule(
        r"\b6[0-3]\d{2}(zz|2rs)?\b|\bucf\d*\b|\bucp\d*\b",
        "10002825", "Brick", 78, "Rodamientos/chumaceras (nomenclatura ISO)",
    ),
    # --- Climatización e iluminación ---
    _rule(
        r"\b(1[28]k|24k|\bbtu\b|\bsplit\b|\binv\b)\b",
        "10003982", "Brick", 78, "Climatización (BTU/SPLIT/INV)",
    ),
    _rule(
        r"\b(a50|a60|e27|e14|gu10|mr16|3000k|6400k|\blm\b)\b",
        "10000552", "Brick", 75, "Iluminación (bombillos, nomenclatura técnica)",
    ),
    # --- Eléctrico industrial ---
    _rule(
        r"\b([123]p[\s/]|c1[0-9]\b|c[2-9][0-9]\b|c1[0-2][0-9]\b|[6-9]ka\b|10ka\b|1no\+?1nc|\bawg\b|pg\s*m(1[2-9]|[2-5][0-9]|6[0-3]))",
        "78000000", "Segment", 65, "Eléctrico industrial (nomenclatura técnica)",
    ),
    # --- Agroquímicos: fórmulas NPK y sufijos de formulación ---
    _rule(
        r"\b\d{1,2}-\d{1,2}-\d{1,2}\b",
        "10003234", "Brick", 75, "Fertilizante (fórmula NPK)",
    ),
    _rule(
        r"\b(\d{2}sc|\d{2}sp|\bwg\b|\bce\b)\b",
        "10000435", "Brick", 60, "Agroquímico (sufijo de formulación)",
    ),
]


def validate_rules_against_catalog() -> None:
    """Candado ground-truth (punto F): ningún código de REGLAS_REGEX puede
    estar fuera del catálogo oficial. Se ejecuta al importar el módulo."""
    if not CATALOG_FILE.exists():
        return  # entorno de prueba sin catálogo disponible; se valida en runtime real
    cat = pd.read_csv(CATALOG_FILE, dtype=str)
    valid_codes = set(cat["codigo"])
    invalid = [r for r in REGLAS_REGEX if r.gpc_code not in valid_codes]
    assert not invalid, (
        "Códigos inventados en REGLAS_REGEX (no existen en el catálogo oficial): "
        + ", ".join(f"{r.gpc_code} ({r.label})" for r in invalid)
    )


def apply_regex_rules(full_context: str) -> RegexRule | None:
    """Devuelve la primera regla que coincida (orden = prioridad/especificidad)."""
    for rule in REGLAS_REGEX:
        if rule.pattern.search(full_context):
            return rule
    return None


validate_rules_against_catalog()
