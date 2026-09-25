#!/usr/bin/env python3
"""Envía una muestra de trabajo de clasificación GPC a la Batch API de Anthropic.

Toma los primeros 5 archivos .xlsx de la raíz del repositorio ("./", orden
alfabético), extrae las primeras 2000 filas de cada uno, deduplica por
(nombre, marca) y envía un lote de clasificación GPC por archivo. Los
batch_id resultantes se guardan en batch_tracker.json para que
retrieve_batches.py los recupere.
"""

import glob
import json
import logging
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import pandas as pd
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("submit_batches")

INPUT_DIR = Path(".")
TRACKER_FILE = Path("batch_tracker.json")
MAX_FILES = 5
MAX_ROWS = 2000

# Claude 3.5 Sonnet fue retirado de la API (28-oct-2025). Se usa su sucesor
# vigente en el mismo nivel de precio/rendimiento.
MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

REQUIRED_COLUMNS = ["ean13", "nombre", "marca"]

GPC_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "razonamiento": {"type": "string"},
        "nivel_asignado": {
            "type": "string",
            "enum": ["Brick", "Class", "Family", "Segment", "NO_MATCH"],
        },
        "gpc_code": {"type": "string"},
        "gpc_description": {"type": "string"},
        "confidence_score": {"type": "number"},
    },
    "required": [
        "razonamiento",
        "nivel_asignado",
        "gpc_code",
        "gpc_description",
        "confidence_score",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """Eres un experto clasificador de productos bajo el estándar \
Global Product Classification (GPC) de GS1.

Tu única fuente de verdad es la IDENTIDAD FÍSICA del producto tal como se \
describe en el texto recibido (Regla 1 del GPC: se clasifica lo que el \
producto ES, no su uso previsto, canal de venta, promoción ni empaque \
adicional). Tienes PROHIBIDO inventar, asumir o alucinar cualquier dato que \
no esté explícita o inequívocamente presente en la Marca y la Descripción \
recibidas.

Si la descripción es ambigua o insuficiente para determinar el nivel más \
específico, aplica esta lógica de ESCALAMIENTO INVERSO, subiendo de nivel \
solo lo estrictamente necesario:

1. Intenta asignar un Ladrillo (Brick) — código GPC de 8 dígitos — el nivel \
más específico.
2. Si la evidencia no alcanza para un Brick pero sí permite identificar la \
Clase (Class) — código de 6 dígitos — asigna ese nivel.
3. Si tampoco alcanza, sube a Familia (Family) — código de 4 dígitos.
4. Si tampoco alcanza, sube a Segmento (Segment) — código de 2 dígitos.
5. Si ni siquiera el Segmento puede determinarse de forma confiable, \
responde nivel_asignado = "NO_MATCH" y gpc_code = "NO_MATCH".

Nunca fuerces un nivel más específico que el que la evidencia realmente \
sustenta: es preferible un nivel superior correcto que un Brick incorrecto \
o inventado.

Recibirás una línea con el formato:
Marca: [marca] | Descripción: [nombre]

Responde ÚNICAMENTE con un objeto JSON que cumpla este esquema:
- razonamiento: explica brevemente en qué evidencia te basaste y, si \
escalaste de nivel, por qué fue necesario.
- nivel_asignado: uno de "Brick", "Class", "Family", "Segment", "NO_MATCH".
- gpc_code: el código GPC asignado (8, 6, 4 o 2 dígitos según \
nivel_asignado), o "NO_MATCH".
- gpc_description: la descripción oficial GPC del código asignado, o \
"NO_MATCH".
- confidence_score: número entre 0 y 1 con tu nivel de confianza.
"""


def get_target_files() -> list[str]:
    if not INPUT_DIR.is_dir():
        raise FileNotFoundError(f"No existe el directorio de entrada: {INPUT_DIR}")
    files = sorted(glob.glob(str(INPUT_DIR / "*.xlsx")))
    if not files:
        raise FileNotFoundError(f"No se encontraron archivos .xlsx en {INPUT_DIR}")
    return files[:MAX_FILES]


def load_sample(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, dtype={"ean13": str})
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas {missing} en {file_path}")

    sample = df.head(MAX_ROWS).copy()
    sample = sample.drop_duplicates(subset=["nombre", "marca"])
    sample["ean13"] = sample["ean13"].astype(str).str.strip()
    sample = sample[sample["ean13"].notna() & (sample["ean13"] != "") & (sample["ean13"] != "nan")]
    return sample


def build_user_content(marca, nombre) -> str:
    marca_str = str(marca).strip() if pd.notna(marca) else "N/D"
    nombre_str = str(nombre).strip() if pd.notna(nombre) else "N/D"
    return f"Marca: {marca_str} | Descripción: {nombre_str}"


def build_request_dicts(sample: pd.DataFrame) -> list[dict]:
    """Construye los dicts de request (forma serializable a JSONL)."""
    request_dicts = []
    seen_ids: set[str] = set()

    for idx, row in sample.iterrows():
        custom_id = row["ean13"]
        if custom_id in seen_ids:
            custom_id = f"{custom_id}_{idx}"
        seen_ids.add(custom_id)

        request_dicts.append(
            {
                "custom_id": custom_id,
                "params": {
                    "model": MODEL,
                    "max_tokens": MAX_TOKENS,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {
                            "role": "user",
                            "content": build_user_content(row.get("marca"), row.get("nombre")),
                        }
                    ],
                    "output_config": {
                        "effort": "low",
                        "format": {"type": "json_schema", "schema": GPC_JSON_SCHEMA},
                    },
                },
            }
        )
    return request_dicts


def write_jsonl_temp(request_dicts: list[dict]) -> Path:
    fd, tmp_path = tempfile.mkstemp(suffix=".jsonl", prefix="gpc_batch_")
    tmp_path = Path(tmp_path)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            for entry in request_dicts:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    return tmp_path


def read_jsonl_as_requests(jsonl_path: Path) -> list[Request]:
    requests = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                requests.append(
                    Request(
                        custom_id=entry["custom_id"],
                        params=MessageCreateParamsNonStreaming(**entry["params"]),
                    )
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Línea {line_num} inválida en {jsonl_path}: {e}")
    return requests


def load_tracker() -> list[dict]:
    if not TRACKER_FILE.exists():
        return []
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"No se pudo leer {TRACKER_FILE} ({e}); se inicia un tracker nuevo")
        return []


def save_tracker(tracker: list[dict]) -> None:
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(tracker, f, ensure_ascii=False, indent=2)


def already_submitted(tracker: list[dict], file_name: str) -> bool:
    terminal_failed = {"failed", "canceled", "expired", "errored"}
    for entry in tracker:
        if entry.get("source_file") == file_name and entry.get("status") not in terminal_failed:
            return True
    return False


def submit_batch_for_file(client: anthropic.Anthropic, file_path: str, tracker: list[dict]) -> None:
    file_name = Path(file_path).name

    if already_submitted(tracker, file_name):
        logger.info(f"{file_name}: ya existe un batch activo en el tracker, se omite")
        return

    logger.info(f"Leyendo {file_name}")
    try:
        sample = load_sample(file_path)
    except Exception as e:
        logger.error(f"{file_name}: error al leer/preparar el archivo: {e}")
        return

    if sample.empty:
        logger.warning(f"{file_name}: la muestra quedó vacía tras deduplicar/limpiar, se omite")
        return

    request_dicts = build_request_dicts(sample)
    logger.info(f"{file_name}: {len(request_dicts)} solicitudes preparadas")

    jsonl_path = write_jsonl_temp(request_dicts)
    try:
        requests = read_jsonl_as_requests(jsonl_path)
        if not requests:
            logger.error(f"{file_name}: no se generaron requests válidos, se omite")
            return

        try:
            batch = client.messages.batches.create(requests=requests)
        except anthropic.AuthenticationError:
            logger.error("Credenciales de Anthropic inválidas. Revisa ANTHROPIC_API_KEY.")
            raise
        except anthropic.RateLimitError as e:
            logger.error(f"{file_name}: límite de tasa alcanzado al crear el batch: {e}")
            return
        except anthropic.APIStatusError as e:
            logger.error(f"{file_name}: error de la API ({e.status_code}) al crear el batch: {e.message}")
            return
        except anthropic.APIConnectionError as e:
            logger.error(f"{file_name}: error de conexión al crear el batch: {e}")
            return
    finally:
        jsonl_path.unlink(missing_ok=True)

    logger.info(f"{file_name}: batch creado {batch.id} (status={batch.processing_status})")

    tracker.append(
        {
            "batch_id": batch.id,
            "source_file": file_name,
            "source_path": str(Path(file_path).resolve()),
            "status": batch.processing_status,
            "num_requests": len(requests),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "retrieved": False,
        }
    )
    save_tracker(tracker)


def main() -> int:
    try:
        client = anthropic.Anthropic()
    except Exception as e:
        logger.error(f"No se pudo inicializar el cliente de Anthropic: {e}")
        return 1

    try:
        files = get_target_files()
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    logger.info(f"Se procesarán {len(files)} archivo(s): {[Path(f).name for f in files]}")

    tracker = load_tracker()

    for file_path in files:
        try:
            submit_batch_for_file(client, file_path, tracker)
        except anthropic.AuthenticationError:
            return 1
        except Exception as e:
            logger.error(f"Error inesperado procesando {Path(file_path).name}: {e}")
            logger.debug(traceback.format_exc())
            continue

    logger.info("Proceso de envío finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
