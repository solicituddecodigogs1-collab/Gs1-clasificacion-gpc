#!/usr/bin/env python3
"""Recupera los resultados de los lotes de clasificación GPC enviados por
submit_batches.py.

Lee batch_tracker.json, consulta el estado de cada batch en la Batch API de
Anthropic y, para los que ya terminaron ("ended"), descarga los resultados
(que ahora solo traen {"gpc_code","confidence_score"} — ver submit_batches.py).

Candado ground-truth: cada gpc_code devuelto se valida contra
"gpc_catalogo_oficial.csv" (build_catalog.py). Si el código existe
literalmente en el catálogo, se autocompletan nivel_asignado y
gpc_description con los valores oficiales; si no existe, es nulo, o el
modelo no lo devolvió, se fuerza gpc_code="NO_MATCH",
nivel_asignado="NO_MATCH", gpc_description="Sin coincidencia válida" — sin
excepción y sin construir códigos por defecto.

El merge hacia los Excel originales se hace por (nombre, marca)
normalizado (el mismo hash que submit_batches.py usa como custom_id), no
por ean13, para que las filas con nombre+marca repetidos pero distinto
ean13 también reciban su clasificación.

Exporta a "./Output_Clasificado/", conservando todas las columnas
originales y agregando únicamente las columnas nuevas al final.
"""

import json
import logging
import random
import re
import sys
import time
import traceback
import unicodedata
import hashlib
from pathlib import Path
from typing import Any, Callable, TypeVar

import anthropic
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("retrieve_batches")

TRACKER_FILE = Path("batch_tracker.json")
INPUT_DIR = Path(".")
OUTPUT_DIR = Path("./Output_Clasificado")
CATALOG_FILE = Path("gpc_catalogo_oficial.csv")
MAX_ROWS = 2000

RESULT_COLUMNS = ["gpc_code", "nivel_asignado", "gpc_description", "confidence_score"]

CODE_PATTERN = re.compile(r"^\d{8}$")
NO_MATCH_DESCRIPTION = "Sin coincidencia válida"

T = TypeVar("T")


# --------------------------------------------------------------------------
# Normalización de texto / claves — debe ser IDÉNTICA a submit_batches.py
# para que el hash de (marca, nombre) coincida en ambos scripts.
# --------------------------------------------------------------------------

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


def normalize_key(marca, nombre) -> str:
    return f"{normalize_text(marca)}|{normalize_text(nombre)}"


def make_custom_id(marca, nombre) -> str:
    key = normalize_key(marca, nombre)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:24]


# --------------------------------------------------------------------------
# Candado ground-truth contra el catálogo oficial
# --------------------------------------------------------------------------

def load_catalog_lookup(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"No se encuentra {path}. Ejecuta primero: python3 build_catalog.py"
        )
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    required_cols = {"nivel", "codigo", "titulo"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"{path} no tiene las columnas esperadas: {required_cols}")
    return df.set_index("codigo")[["nivel", "titulo"]].to_dict(orient="index")


def validate_gpc_code(raw_code: Any, catalog_lookup: dict[str, dict[str, str]]) -> tuple[str, str, str, bool]:
    """Aplica el candado ground-truth. Devuelve
    (gpc_code, nivel_asignado, gpc_description, fue_codigo_inventado_bloqueado).

    Prohibido construir códigos por defecto (p. ej. concatenar "10000" con
    un valor nulo): si el código no es un string de 8 dígitos presente en
    el catálogo, siempre se cae a NO_MATCH tal cual."""
    if isinstance(raw_code, str) and raw_code.strip().upper() == "NO_MATCH":
        return "NO_MATCH", "NO_MATCH", NO_MATCH_DESCRIPTION, False

    code = raw_code.strip() if isinstance(raw_code, str) else None
    if code and CODE_PATTERN.match(code) and code in catalog_lookup:
        info = catalog_lookup[code]
        return code, info["nivel"], info["titulo"], False

    # El modelo devolvió algo que no es un código real del catálogo: se
    # bloquea (nunca se acepta a ciegas) y se cuenta como intento de
    # código inventado, salvo que ya viniera vacío/nulo.
    was_invented_attempt = code is not None
    return "NO_MATCH", "NO_MATCH", NO_MATCH_DESCRIPTION, was_invented_attempt


def with_retry(fn: Callable[[], T], description: str, max_retries: int = 4) -> T:
    """Reintenta con backoff exponencial ante errores transitorios de la API."""
    delay = 2.0
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except anthropic.RateLimitError as e:
            if attempt == max_retries:
                raise
            retry_after = e.response.headers.get("retry-after") if e.response else None
            wait = float(retry_after) if retry_after else delay
            logger.warning(f"{description}: rate limit (intento {attempt}/{max_retries}), reintentando en {wait:.0f}s")
            time.sleep(wait)
            delay = min(delay * 2, 60.0)
        except anthropic.APIConnectionError as e:
            if attempt == max_retries:
                raise
            logger.warning(f"{description}: error de conexión (intento {attempt}/{max_retries}): {e}")
            time.sleep(delay + random.uniform(0, 1))
            delay = min(delay * 2, 60.0)
        except anthropic.APIStatusError as e:
            if e.status_code < 500 or attempt == max_retries:
                raise
            logger.warning(f"{description}: error {e.status_code} (intento {attempt}/{max_retries})")
            time.sleep(delay + random.uniform(0, 1))
            delay = min(delay * 2, 60.0)
    raise RuntimeError(f"{description}: se agotaron los reintentos")


def load_tracker() -> list[dict]:
    if not TRACKER_FILE.exists():
        raise FileNotFoundError(f"No existe {TRACKER_FILE}. Ejecuta submit_batches.py primero.")
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tracker(tracker: list[dict]) -> None:
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(tracker, f, ensure_ascii=False, indent=2)


def parse_succeeded_result(message: Any) -> dict:
    text = next((b.text for b in message.content if b.type == "text"), None)
    if text is None:
        return {"error": "sin bloque de texto en la respuesta"}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"JSON inválido: {e}"}
    return {"data": parsed}


def error_row(reason: str) -> dict:
    """Fila para fallas de infraestructura del batch (no confundir con un
    NO_MATCH legítimo del modelo, que se marca con nivel_asignado=NO_MATCH)."""
    return {
        "gpc_code": "NO_MATCH",
        "nivel_asignado": "ERROR",
        "gpc_description": f"ERROR: {reason}",
        "confidence_score": None,
    }


def fetch_results(
    client: anthropic.Anthropic, batch_id: str, catalog_lookup: dict[str, dict[str, str]]
) -> tuple[dict[str, dict], int, int]:
    """Descarga, parsea y valida (candado ground-truth) todos los resultados
    de un batch. Devuelve (resultados_por_custom_id, num_errores_infra,
    num_codigos_inventados_bloqueados)."""
    results_by_id: dict[str, dict] = {}
    num_errors = 0
    num_blocked = 0

    result_iter = with_retry(
        lambda: list(client.messages.batches.results(batch_id)),
        f"descarga de resultados de {batch_id}",
    )

    for result in result_iter:
        cid = result.custom_id
        rtype = result.result.type

        if rtype == "succeeded":
            outcome = parse_succeeded_result(result.result.message)
            if "data" in outcome:
                data = outcome["data"]
                raw_code = data.get("gpc_code")
                raw_confidence = data.get("confidence_score")
                gpc_code, nivel_asignado, gpc_description, blocked = validate_gpc_code(raw_code, catalog_lookup)
                if blocked:
                    num_blocked += 1
                    logger.warning(f"[{cid}] código no válido bloqueado por el candado ground-truth: {raw_code!r}")
                confidence_score = raw_confidence if isinstance(raw_confidence, (int, float)) else None
                results_by_id[cid] = {
                    "gpc_code": gpc_code,
                    "nivel_asignado": nivel_asignado,
                    "gpc_description": gpc_description,
                    "confidence_score": confidence_score,
                }
            else:
                num_errors += 1
                results_by_id[cid] = error_row(outcome["error"])
        elif rtype == "errored":
            num_errors += 1
            err_type = getattr(result.result.error, "type", "desconocido")
            results_by_id[cid] = error_row(f"solicitud fallida ({err_type})")
        else:  # canceled / expired
            num_errors += 1
            results_by_id[cid] = error_row(rtype)

    return results_by_id, num_errors, num_blocked


def resolve_nombre_marca_columns(df: pd.DataFrame) -> tuple[str, str]:
    """Encuentra las columnas nombre/marca sin importar mayúsculas/minúsculas
    (p. ej. la columna real puede llamarse "Nombre")."""
    lower_map: dict[str, str] = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key not in lower_map:
            lower_map[key] = col
    missing = [r for r in ("nombre", "marca") if r not in lower_map]
    if missing:
        raise ValueError(
            f"Faltan columnas requeridas {missing} para el merge. Columnas disponibles: {list(df.columns)}"
        )
    return lower_map["nombre"], lower_map["marca"]


def merge_and_export(source_path: Path, results_by_id: dict[str, dict], file_name: str) -> Path:
    if not source_path.exists():
        raise FileNotFoundError(f"No se encuentra el archivo original: {source_path}")

    df = pd.read_excel(source_path)
    nombre_col, marca_col = resolve_nombre_marca_columns(df)
    sample = df.head(MAX_ROWS).copy()

    join_col = "_gpc_join_key"
    sample[join_col] = sample.apply(lambda r: make_custom_id(r[marca_col], r[nombre_col]), axis=1)

    results_df = (
        pd.DataFrame.from_dict(results_by_id, orient="index")
        .reset_index()
        .rename(columns={"index": join_col})
    )
    if results_df.empty:
        results_df = pd.DataFrame(columns=[join_col] + RESULT_COLUMNS)

    # Merge por (nombre, marca) normalizado: a diferencia de un merge por
    # ean13, las filas con nombre+marca repetidos y distinto ean13 sí
    # reciben la clasificación (comparten la misma _gpc_join_key).
    merged = sample.merge(results_df, how="left", on=join_col)
    merged = merged.drop(columns=[join_col])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"clasificado_{file_name}"
    merged.to_excel(output_path, index=False)
    return output_path


def process_entry(client: anthropic.Anthropic, entry: dict, catalog_lookup: dict[str, dict[str, str]]) -> dict:
    batch_id = entry.get("batch_id")
    file_name = entry.get("source_file", "?")

    if entry.get("retrieved"):
        logger.info(f"{file_name} ({batch_id}): ya recuperado previamente, se omite")
        return entry

    try:
        batch = with_retry(
            lambda: client.messages.batches.retrieve(batch_id),
            f"consulta de estado de {batch_id}",
        )
    except anthropic.NotFoundError:
        logger.error(f"{file_name}: batch {batch_id} no encontrado (¿expiró o el ID es incorrecto?)")
        entry["status"] = "not_found"
        return entry
    except anthropic.AuthenticationError:
        logger.error("Credenciales de Anthropic inválidas. Revisa ANTHROPIC_API_KEY.")
        raise
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
        logger.error(f"{file_name}: error consultando estado del batch {batch_id}: {e}")
        return entry

    entry["status"] = batch.processing_status

    if batch.processing_status != "ended":
        logger.info(f"{file_name} ({batch_id}): estado actual = {batch.processing_status}")
        return entry

    logger.info(f"{file_name} ({batch_id}): batch finalizado, descargando resultados")
    try:
        results_by_id, num_errors, num_blocked = fetch_results(client, batch_id, catalog_lookup)
    except anthropic.AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"{file_name}: error descargando resultados del batch {batch_id}: {e}")
        logger.debug(traceback.format_exc())
        return entry

    if num_errors:
        logger.warning(f"{file_name}: {num_errors} solicitudes con error dentro del batch")
    if num_blocked:
        logger.warning(f"{file_name}: {num_blocked} códigos inventados/no válidos bloqueados por el candado ground-truth")

    source_path = Path(entry.get("source_path") or (INPUT_DIR / file_name))
    try:
        output_path = merge_and_export(source_path, results_by_id, file_name)
    except Exception as e:
        logger.error(f"{file_name}: error al unir/exportar resultados: {e}")
        logger.debug(traceback.format_exc())
        return entry

    logger.info(f"{file_name}: exportado a {output_path}")
    entry["retrieved"] = True
    entry["output_path"] = str(output_path)
    entry["num_errors_in_batch"] = num_errors
    entry["num_codes_blocked"] = num_blocked
    return entry


def main() -> int:
    try:
        catalog_lookup = load_catalog_lookup(CATALOG_FILE)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return 1

    try:
        client = anthropic.Anthropic()
    except Exception as e:
        logger.error(f"No se pudo inicializar el cliente de Anthropic: {e}")
        return 1

    try:
        tracker = load_tracker()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(str(e))
        return 1

    if not tracker:
        logger.info("El tracker está vacío. Nada que recuperar.")
        return 0

    updated_tracker = []
    for entry in tracker:
        try:
            updated_entry = process_entry(client, entry, catalog_lookup)
        except anthropic.AuthenticationError:
            updated_tracker.append(entry)
            updated_tracker.extend(tracker[len(updated_tracker):])
            save_tracker(updated_tracker)
            return 1
        except Exception as e:
            logger.error(f"Error inesperado procesando {entry.get('source_file', '?')}: {e}")
            logger.debug(traceback.format_exc())
            updated_entry = entry
        updated_tracker.append(updated_entry)
        save_tracker(updated_tracker)

    logger.info("Proceso de recuperación finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
