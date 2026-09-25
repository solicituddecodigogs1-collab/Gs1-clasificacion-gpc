#!/usr/bin/env python3
"""Recupera los resultados de los lotes de clasificación GPC enviados por
submit_batches.py.

Lee batch_tracker.json, consulta el estado de cada batch en la Batch API de
Anthropic y, para los que ya terminaron ("ended"), descarga los resultados,
los une (merge left, por ean13) con las primeras 2000 filas del Excel
original y exporta el archivo final a "./Output_Clasificado/", conservando
todas las columnas originales y agregando las columnas nuevas al final.
"""

import json
import logging
import random
import sys
import time
import traceback
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
MAX_ROWS = 2000

RESULT_COLUMNS = [
    "razonamiento",
    "nivel_asignado",
    "gpc_code",
    "gpc_description",
    "confidence_score",
]

T = TypeVar("T")


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
    row = {col: None for col in RESULT_COLUMNS}
    row["razonamiento"] = f"ERROR: {reason}"
    row["nivel_asignado"] = "ERROR"
    return row


def fetch_results(client: anthropic.Anthropic, batch_id: str) -> tuple[dict[str, dict], int]:
    """Descarga y parsea todos los resultados de un batch. Devuelve
    (resultados_por_custom_id, num_errores)."""
    results_by_id: dict[str, dict] = {}
    num_errors = 0

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
                results_by_id[cid] = {col: data.get(col) for col in RESULT_COLUMNS}
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

    return results_by_id, num_errors


def resolve_ean_column(df: pd.DataFrame) -> str:
    """Encuentra la columna ean13 sin importar mayúsculas/minúsculas (p. ej.
    la columna real puede llamarse "EAN13")."""
    for col in df.columns:
        if str(col).strip().lower() == "ean13":
            return col
    raise ValueError(f"No se encontró una columna 'ean13'. Columnas disponibles: {list(df.columns)}")


def merge_and_export(source_path: Path, results_by_id: dict[str, dict], file_name: str) -> Path:
    if not source_path.exists():
        raise FileNotFoundError(f"No se encuentra el archivo original: {source_path}")

    df = pd.read_excel(source_path)
    ean_col = resolve_ean_column(df)
    sample = df.head(MAX_ROWS).copy()
    sample[ean_col] = sample[ean_col].astype(str).str.strip()

    results_df = (
        pd.DataFrame.from_dict(results_by_id, orient="index")
        .reset_index()
        .rename(columns={"index": ean_col})
    )
    if results_df.empty:
        results_df = pd.DataFrame(columns=[ean_col] + RESULT_COLUMNS)

    # Nota: la deduplicación en submit_batches.py se hizo por (nombre, marca),
    # no por ean13. Las filas cuyo (nombre, marca) era duplicado no se
    # enviaron a la API y, al unir solo por ean13, quedarán con las columnas
    # de clasificación en NaN (comportamiento esperado del merge left pedido).
    merged = sample.merge(results_df, how="left", on=ean_col)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"clasificado_{file_name}"
    merged.to_excel(output_path, index=False)
    return output_path


def process_entry(client: anthropic.Anthropic, entry: dict) -> dict:
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
        results_by_id, num_errors = fetch_results(client, batch_id)
    except anthropic.AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"{file_name}: error descargando resultados del batch {batch_id}: {e}")
        logger.debug(traceback.format_exc())
        return entry

    if num_errors:
        logger.warning(f"{file_name}: {num_errors} solicitudes con error dentro del batch")

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
    return entry


def main() -> int:
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
            updated_entry = process_entry(client, entry)
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
