#!/usr/bin/env python3
"""Envía los Excel de "./Nueva Carga/" a la Batch API de Anthropic para
clasificarlos con el GPC (Global Product Classification).

Por cada .xlsx:
  1. Lee con pandas (ean13 como texto, para no perder ceros a la izquierda).
  2. drop_duplicates EXCLUSIVAMENTE por ('nombre', 'marca').
  3. Escribe un .jsonl temporal con custom_id = ean13.
  4. Lo envía a la Batch API y registra {batch_id, archivo original, ...} en
     batch_tracker_nueva_carga.json (el batch_tracker.json del pipeline 2024
     no se toca).

Uso:
    python3 submit_batches_nueva_carga.py                  # todos los .xlsx de ./Nueva Carga/
    python3 submit_batches_nueva_carga.py a.xlsx b.xlsx    # solo esos archivos
    python3 submit_batches_nueva_carga.py --dry-run        # valida y genera el .jsonl sin llamar a la API
    python3 submit_batches_nueva_carga.py --force          # reenvía aunque el archivo ya esté en el tracker

Modelo: Claude 3.5 Sonnet fue retirado (28-oct-2025); se usa claude-sonnet-5-5.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #
INPUT_DIR = Path("./Nueva Carga")
TRACKER_FILE = Path("batch_tracker_nueva_carga.json")

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 2000          # con thinking adaptativo, parte del presupuesto lo consume el razonamiento interno
EFFORT = "medium"
# Límite de la Batch API: 100.000 solicitudes / 256 MB por lote. Cada solicitud
# lleva el prompt de sistema (~3-4 KB), así que se parte antes de llegar a 256 MB.
MAX_REQUESTS_PER_BATCH = 40_000

COL_EAN = "ean13"
COL_NOMBRE = "nombre"
COL_MARCA = "marca"

CUSTOM_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# nivel -> nº de dígitos del código GPC
LEVEL_DIGITS = {"Ladrillo": 8, "Clase": 6, "Familia": 4, "Segmento": 2, "NO_MATCH": 0}

log = logging.getLogger("submit_nueva_carga")

# --------------------------------------------------------------------------- #
# Prompt y esquema
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """\
Eres un clasificador experto en el GPC (Global Product Classification) de GS1.
Recibirás un producto con el formato: "Marca: [marca] | Descripción: [nombre]".

JERARQUÍA GPC (de lo más general a lo más específico)
  Segmento (2 dígitos) > Familia (4) > Clase (6) > Ladrillo / Brick (8).

REGLA 1 DEL GPC — IDENTIDAD FÍSICA
Clasifica por lo que el producto ES físicamente (naturaleza, composición y
forma), no por su marca, público objetivo, canal de venta ni uso comercial
declarado. La marca solo ayuda a interpretar la descripción; por sí sola
nunca define la categoría.

PROHIBIDO INVENTAR
No completes información que la descripción no contiene. No inventes códigos
ni nombres: devuelve un código solo si conoces con certeza ese código exacto y
su nombre oficial en ese nivel.

ESCALAMIENTO JERÁRQUICO
Empieza por el nivel más específico y sube solo si falta certeza:
  1. Ladrillo (8 dígitos): identidad física inequívoca y código exacto conocido.
  2. Si no hay certeza para el Ladrillo -> Clase (6 dígitos).
  3. Si no hay certeza para la Clase -> Familia (4 dígitos).
  4. Si no hay certeza para la Familia -> Segmento (2 dígitos).
  5. NO_MATCH únicamente si ni el Segmento puede determinarse (descripción
     vacía, ilegible, solo una marca o un código, o producto indescifrable).

SALIDA (JSON con exactamente estos campos)
  - razonamiento: 1-3 frases sobre la identidad física y por qué se asignó (o
    por qué se subió de) ese nivel.
  - nivel_asignado: Ladrillo | Clase | Familia | Segmento | NO_MATCH
  - gpc_code: solo dígitos (8, 6, 4 o 2 según el nivel); "" si NO_MATCH.
  - gpc_description: nombre oficial del nivel asignado; "" si NO_MATCH.
  - confidence_score: número entre 0 y 1 que refleje tu certeza real; debe ser
    menor cuanto más general (o más dudoso) sea el nivel asignado.
"""

# Las salidas estructuradas no admiten minimum/maximum/pattern en todos los
# casos; las restricciones finas se validan al recuperar (retrieve).
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "razonamiento": {"type": "string"},
        "nivel_asignado": {"type": "string", "enum": list(LEVEL_DIGITS)},
        "gpc_code": {"type": "string"},
        "gpc_description": {"type": "string"},
        "confidence_score": {"type": "number"},
    },
    "required": ["razonamiento", "nivel_asignado", "gpc_code", "gpc_description", "confidence_score"],
    "additionalProperties": False,
}


def build_user_text(marca, nombre) -> str:
    m = "" if pd.isna(marca) else str(marca).strip()
    n = "" if pd.isna(nombre) else str(nombre).strip()
    return f"Marca: {m} | Descripción: {n}"


def make_request(custom_id: str, marca, nombre) -> dict:
    return {
        "custom_id": custom_id,
        "params": {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "output_config": {
                "effort": EFFORT,
                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
            },
            "messages": [{"role": "user", "content": build_user_text(marca, nombre)}],
        },
    }


# --------------------------------------------------------------------------- #
# Lectura y desduplicación (compartido con retrieve_batches_nueva_carga.py)
# --------------------------------------------------------------------------- #
def norm_ean(series: pd.Series) -> pd.Series:
    """ean13 como texto limpio (sin espacios ni sufijo '.0' típico de Excel)."""
    return series.astype("string").str.strip().str.replace(r"\.0+$", "", regex=True)


def read_master(path: Path) -> pd.DataFrame:
    """Lee el Excel original sin alterar sus columnas (ean13 como texto)."""
    df = pd.read_excel(path, dtype={COL_EAN: str})
    missing = [c for c in (COL_EAN, COL_NOMBRE, COL_MARCA) if c not in df.columns]
    if missing:
        raise ValueError(f"faltan columnas obligatorias {missing}; columnas encontradas: {list(df.columns)}")
    return df


def build_unique(df: pd.DataFrame) -> pd.DataFrame:
    """Sub-dataframe con un representante por ('nombre', 'marca').

    Devuelve columnas [ean13, nombre, marca] con ean13 normalizado, único y
    válido como custom_id.
    """
    sub = pd.DataFrame({COL_EAN: norm_ean(df[COL_EAN]), COL_NOMBRE: df[COL_NOMBRE], COL_MARCA: df[COL_MARCA]})

    sin_nombre = sub[COL_NOMBRE].isna() | (sub[COL_NOMBRE].astype("string").str.strip() == "")
    if sin_nombre.any():
        log.warning("  %d filas sin 'nombre' (no se envían)", int(sin_nombre.sum()))
    sub = sub[~sin_nombre]

    sub = sub.drop_duplicates(subset=[COL_NOMBRE, COL_MARCA])

    valido = sub[COL_EAN].fillna("").str.match(CUSTOM_ID_RE)
    if (~valido).any():
        log.warning("  %d filas con ean13 vacío/inválido para custom_id (no se envían)", int((~valido).sum()))
    sub = sub[valido]

    dup = sub.duplicated(subset=[COL_EAN], keep="first")
    if dup.any():
        log.warning("  %d ean13 repetidos con distinto nombre/marca (se envía solo el primero)", int(dup.sum()))
    return sub[~dup].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Tracker
# --------------------------------------------------------------------------- #
def load_tracker() -> list[dict]:
    if not TRACKER_FILE.exists():
        return []
    try:
        data = json.loads(TRACKER_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("se esperaba una lista")
        return data
    except (json.JSONDecodeError, ValueError, OSError) as e:
        # No se sobrescribe un tracker ilegible: se perdería el registro de lotes ya pagados.
        sys.exit(f"ERROR: no se pudo leer {TRACKER_FILE} ({e}). Corrígelo o muévelo antes de continuar.")


def save_tracker(entries: list[dict]) -> None:
    """Escritura atómica: nunca deja el tracker a medias."""
    tmp = TRACKER_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, TRACKER_FILE)


# --------------------------------------------------------------------------- #
# Envío
# --------------------------------------------------------------------------- #
def write_temp_jsonl(chunk: pd.DataFrame) -> Path:
    fd, name = tempfile.mkstemp(suffix=".jsonl", prefix="gpc_batch_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        for ean, nombre, marca in zip(chunk[COL_EAN], chunk[COL_NOMBRE], chunk[COL_MARCA]):
            fh.write(json.dumps(make_request(ean, marca, nombre), ensure_ascii=False) + "\n")
    return Path(name)


def submit_jsonl(client, jsonl: Path):
    """Envía el .jsonl a la Batch API. Los errores transitorios ya los reintenta el SDK."""
    import anthropic

    with open(jsonl, encoding="utf-8") as fh:
        requests = [json.loads(line) for line in fh]
    try:
        return client.messages.batches.create(requests=requests)
    except anthropic.BadRequestError as e:
        raise RuntimeError(f"la API rechazó el lote (400): {e.message}") from e
    except anthropic.AuthenticationError as e:
        raise RuntimeError("credenciales inválidas: revisa ANTHROPIC_API_KEY") from e
    except anthropic.PermissionDeniedError as e:
        raise RuntimeError(f"sin permisos para la Batch API: {e.message}") from e
    except anthropic.RateLimitError as e:
        raise RuntimeError("límite de tasa excedido tras los reintentos; vuelve a ejecutar más tarde") from e
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"error de la API ({e.status_code}): {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise RuntimeError(f"error de red: {e}") from e


def process_file(path: Path, client, tracker: list[dict], dry_run: bool, force: bool) -> bool:
    name = path.name
    previos = [e for e in tracker if e["source_file"] == name]
    if previos and not force:
        log.info("%s: ya registrado en el tracker (%d lote/s); usa --force para reenviar", name, len(previos))
        return True

    log.info("%s: leyendo ...", name)
    df = read_master(path)
    log.info("  %d filas", len(df))
    sub = build_unique(df)
    log.info("  %d únicos por (nombre, marca) a enviar", len(sub))
    if sub.empty:
        log.warning("  nada que enviar")
        return True

    parts = [sub.iloc[i:i + MAX_REQUESTS_PER_BATCH] for i in range(0, len(sub), MAX_REQUESTS_PER_BATCH)]
    for n, chunk in enumerate(parts, start=1):
        jsonl = write_temp_jsonl(chunk)
        try:
            if dry_run:
                log.info("  [dry-run] parte %d/%d: %d solicitudes, %.1f MB -> %s",
                         n, len(parts), len(chunk), jsonl.stat().st_size / 1e6, jsonl)
                jsonl = None  # en dry-run se conserva el archivo para inspección
                continue
            batch = submit_jsonl(client, jsonl)
            tracker.append({
                "batch_id": batch.id,
                "source_file": name,
                "source_path": str(path),
                "part": n,
                "total_parts": len(parts),
                "model": MODEL,
                "num_requests": len(chunk),
                "status": batch.processing_status,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "retrieved": False,
            })
            save_tracker(tracker)  # persistir tras cada lote enviado
            log.info("  parte %d/%d -> %s", n, len(parts), batch.id)
        finally:
            if jsonl is not None:
                jsonl.unlink(missing_ok=True)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="archivos .xlsx de la carpeta de entrada (por defecto, todos)")
    ap.add_argument("--input-dir", default=str(INPUT_DIR))
    ap.add_argument("--dry-run", action="store_true", help="no llama a la API")
    ap.add_argument("--force", action="store_true", help="reenvía aunque ya esté en el tracker")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    in_dir = Path(args.input_dir)
    if not in_dir.is_dir():
        log.error("No existe la carpeta %s", in_dir)
        return 1
    if args.files:
        paths = [in_dir / f for f in args.files]
    else:
        paths = sorted(p for p in in_dir.glob("*.xlsx") if not p.name.startswith("~$"))
    if not paths:
        log.error("No hay archivos .xlsx en %s", in_dir)
        return 1

    client = None
    if not args.dry_run:
        try:
            import anthropic
            client = anthropic.Anthropic()
        except Exception as e:  # falta el paquete o credenciales
            log.error("No se pudo inicializar el cliente de Anthropic: %s", e)
            return 1

    tracker = load_tracker()
    fallos = 0
    for path in paths:
        try:
            if not path.is_file():
                raise FileNotFoundError(path)
            process_file(path, client, tracker, args.dry_run, args.force)
        except Exception as e:  # un archivo con error no detiene a los demás
            fallos += 1
            log.error("%s: FALLÓ: %s", path.name, e, exc_info=not isinstance(e, (ValueError, RuntimeError, FileNotFoundError)))
    log.info("Terminado: %d archivo(s), %d con error", len(paths), fallos)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
