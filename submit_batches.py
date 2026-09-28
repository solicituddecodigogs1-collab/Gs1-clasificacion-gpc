#!/usr/bin/env python3
"""Envía una muestra de trabajo de clasificación GPC a la Batch API de Anthropic.

Toma los primeros 5 archivos "Productos*.xlsx" de la raíz del repositorio
(orden alfabético), extrae las primeras 2000 filas de cada uno, deduplica
por (nombre, marca) normalizado y, para cada par único, hace un
pre-filtrado LOCAL (sin costo de API) contra el catálogo oficial GPC
("gpc_catalogo_oficial.csv", generado por build_catalog.py) usando
similitud léxica TF-IDF (n-gramas de palabra + de carácter, con un mapeo
básico de sinónimos venezolanos). Los ~25 Bricks más parecidos, más sus
Class/Family/Segment padres, se incluyen como lista de candidatos dentro
del mensaje enviado a Claude — el modelo solo puede elegir un código de
esa lista o "NO_MATCH", nunca inventar uno.

Para minimizar tokens de salida, el modelo responde únicamente
{"gpc_code": ..., "confidence_score": ...} (sin razonamiento ni
descripción); retrieve_batches.py reconstruye nivel_asignado y
gpc_description localmente a partir del catálogo oficial (candado
ground-truth: un gpc_code que no exista en el catálogo se descarta como
NO_MATCH, nunca se acepta a ciegas).

Los batch_id resultantes se guardan en batch_tracker.json para que
retrieve_batches.py los recupere.

Uso:
    python3 submit_batches.py            # envía los batches reales
    python3 submit_batches.py --dry-run  # sin llamar a la API: muestra
                                          # candidatos y estima tokens/costo
                                          # para 5 productos de Productos1.xlsx
"""

import glob
import hashlib
import json
import logging
import re
import sys
import tempfile
import traceback
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("submit_batches")

INPUT_DIR = Path(".")
# "Productos*.xlsx" en vez de "*.xlsx": la raíz también contiene el
# catálogo oficial GPC ("GPC as of ... .xlsx"), que alfabéticamente
# ordena ANTES de "Productos1.xlsx" y rompería la selección de los 5
# archivos de trabajo si se usara un patrón genérico.
INPUT_GLOB_PATTERN = "Productos*.xlsx"
TRACKER_FILE = Path("batch_tracker.json")
CATALOG_FILE = Path("gpc_catalogo_oficial.csv")
MAX_FILES = 5
MAX_ROWS = 2000
TOP_K_BRICKS = 25

# Claude 3.5 Sonnet fue retirado de la API (28-oct-2025). Se usa su sucesor
# vigente en el mismo nivel de precio/rendimiento.
MODEL = "claude-sonnet-5"
MAX_TOKENS = 45  # recorte radical de salida: solo {"gpc_code","confidence_score"}

# Precios Batch API (50% del precio estándar) usados solo para la
# estimación de costos del --dry-run, en USD por millón de tokens.
BATCH_PRICE_INPUT_PER_MTOK = 1.00
BATCH_PRICE_OUTPUT_PER_MTOK = 5.00

REQUIRED_COLUMNS = ["ean13", "nombre", "marca"]

# Nota importante: Claude Sonnet 5 RECHAZA (HTTP 400) los parámetros de
# muestreo (temperature/top_p/top_k) — no existe forma de fijar
# temperature=0 en este modelo, a diferencia de lo pedido originalmente.
# En su lugar se desactiva explícitamente el "thinking" (sí soportado en
# Sonnet 5) para que los 45 tokens de max_tokens no se gasten en
# razonamiento interno invisible antes de emitir el JSON.
THINKING_CONFIG = {"type": "disabled"}

# Mapeo básico de venezolanismos a términos en español neutro/MX, para
# mejorar el recall de la búsqueda léxica contra el catálogo oficial.
SYNONYMS_VE = {
    "parchita": "maracuya fruta",
    "patilla": "sandia",
    "cambur": "platano banana",
    "caraota": "frijol",
    "chucheria": "snack confiteria dulce",
    "chucherias": "snack confiteria dulce",
}

GPC_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "gpc_code": {"type": "string"},
        "confidence_score": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": ["gpc_code", "confidence_score"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """Eres un clasificador de productos bajo el estándar Global \
Product Classification (GPC) de GS1.

Reglas estrictas:
1. Identidad física únicamente (Regla 1 del GPC): clasifica lo que el \
producto ES, nunca su uso previsto, canal de venta, promoción o empaque.
2. Cada mensaje trae una lista de CANDIDATOS (códigos Brick/Class/Family/\
Segment ya preseleccionados del catálogo oficial GPC) seguida de \
"Marca: ... | Descripción: ...".
3. gpc_code debe ser copiado EXACTAMENTE (8 dígitos) de la lista de \
candidatos recibida. Tienes PROHIBIDO inventar, truncar, combinar o \
construir un código que no esté literalmente en esa lista.
4. Escalamiento inverso: si el Brick candidato más específico aplica, \
úsalo. Si ningún Brick candidato encaja pero sí una Class/Family/Segment \
candidata, sube a ese nivel. Si NINGÚN candidato de la lista corresponde \
razonablemente al producto, responde exactamente "NO_MATCH".
5. confidence_score es un entero de 0 a 100 con tu nivel de confianza.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{"gpc_code": "<código de 8 dígitos tomado de la lista, o NO_MATCH>", \
"confidence_score": <entero 0-100>}
"""


# --------------------------------------------------------------------------
# Normalización de texto / claves (compartida conceptualmente con
# retrieve_batches.py, que recalcula el mismo hash para poder unir por
# (nombre, marca) normalizado en vez de por ean13).
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


def apply_synonyms(text: str) -> str:
    expanded = []
    for word in text.split():
        expanded.append(word)
        if word in SYNONYMS_VE:
            expanded.append(SYNONYMS_VE[word])
    return " ".join(expanded)


def normalize_key(marca, nombre) -> str:
    return f"{normalize_text(marca)}|{normalize_text(nombre)}"


def make_custom_id(marca, nombre) -> str:
    """ID determinista derivado de (marca, nombre) normalizados. Reemplaza
    a ean13 como custom_id porque el merge final ahora se hace por esta
    misma clave normalizada (Regla 4), no por ean13."""
    key = normalize_key(marca, nombre)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:24]


def query_text(marca, nombre) -> str:
    return apply_synonyms(f"{normalize_text(marca)} {normalize_text(nombre)}".strip())


# --------------------------------------------------------------------------
# Catálogo oficial GPC + búsqueda léxica local (costo API = $0)
# --------------------------------------------------------------------------

class GpcCatalog:
    def __init__(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(
                f"No se encuentra {path}. Ejecuta primero: python3 build_catalog.py"
            )
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        required_cols = {"nivel", "codigo", "titulo", "segment_code", "family_code", "class_code"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"{path} no tiene las columnas esperadas: {required_cols}")

        self.df = df
        self.by_code = df.set_index("codigo").to_dict(orient="index")

        self.bricks = df[df["nivel"] == "Brick"].reset_index(drop=True)
        if self.bricks.empty:
            raise ValueError(f"{path} no contiene ningún Brick")

        brick_corpus = [normalize_text(t) for t in self.bricks["titulo"]]

        self.word_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.word_matrix = self.word_vectorizer.fit_transform(brick_corpus)

        self.char_vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
        self.char_matrix = self.char_vectorizer.fit_transform(brick_corpus)

    def top_bricks(self, query: str, k: int = TOP_K_BRICKS) -> pd.DataFrame:
        word_sim = cosine_similarity(self.word_vectorizer.transform([query]), self.word_matrix)[0]
        char_sim = cosine_similarity(self.char_vectorizer.transform([query]), self.char_matrix)[0]
        combined = 0.6 * word_sim + 0.4 * char_sim
        top_idx = np.argsort(combined)[::-1][:k]
        return self.bricks.iloc[top_idx]

    def build_candidates(self, query: str, k: int = TOP_K_BRICKS) -> dict[str, dict[str, str]]:
        """Devuelve {codigo: {"nivel": ..., "titulo": ...}} con los k Bricks
        más cercanos más sus Class/Family/Segment padres (desduplicados)."""
        top = self.top_bricks(query, k)
        candidates: dict[str, dict[str, str]] = {}
        for _, row in top.iterrows():
            candidates[row["codigo"]] = {"nivel": "Brick", "titulo": row["titulo"]}
            for level_col, level_name in (
                ("class_code", "Class"),
                ("family_code", "Family"),
                ("segment_code", "Segment"),
            ):
                parent_code = row[level_col]
                if parent_code and parent_code not in candidates:
                    parent = self.by_code.get(parent_code)
                    if parent:
                        candidates[parent_code] = {"nivel": level_name, "titulo": parent["titulo"]}
        return candidates


def format_candidates(candidates: dict[str, dict[str, str]]) -> str:
    order = {"Brick": 0, "Class": 1, "Family": 2, "Segment": 3}
    items = sorted(candidates.items(), key=lambda kv: (order[kv[1]["nivel"]], kv[0]))
    return "\n".join(f'{codigo}: {info["titulo"]} [{info["nivel"]}]' for codigo, info in items)


# --------------------------------------------------------------------------
# Lectura y preparación de los archivos de productos
# --------------------------------------------------------------------------

def get_target_files() -> list[str]:
    if not INPUT_DIR.is_dir():
        raise FileNotFoundError(f"No existe el directorio de entrada: {INPUT_DIR}")
    files = sorted(glob.glob(str(INPUT_DIR / INPUT_GLOB_PATTERN)))
    if not files:
        raise FileNotFoundError(f"No se encontraron archivos {INPUT_GLOB_PATTERN} en {INPUT_DIR}")
    return files[:MAX_FILES]


def resolve_columns(df: pd.DataFrame, required: list[str]) -> dict[str, str]:
    """Mapea nombres canónicos (minúsculas) a los nombres reales de columna,
    sin importar mayúsculas/minúsculas ni espacios extremos (p. ej. la
    columna real puede llamarse "EAN13" o "Nombre")."""
    lower_map: dict[str, str] = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key not in lower_map:
            lower_map[key] = col
    missing = [r for r in required if r not in lower_map]
    if missing:
        raise ValueError(
            f"Faltan columnas requeridas {missing}. Columnas disponibles: {list(df.columns)}"
        )
    return {r: lower_map[r] for r in required}


def load_sample(file_path: str) -> tuple[pd.DataFrame, dict[str, str]]:
    df = pd.read_excel(file_path)
    cols = resolve_columns(df, REQUIRED_COLUMNS)
    ean_col, nombre_col, marca_col = cols["ean13"], cols["nombre"], cols["marca"]

    sample = df.head(MAX_ROWS).copy()
    sample = sample.drop_duplicates(subset=[nombre_col, marca_col])
    sample = sample[sample[ean_col].notna()]
    sample[ean_col] = sample[ean_col].astype(str).str.strip()
    sample = sample[sample[ean_col] != ""]
    return sample, cols


def build_user_content(marca, nombre, candidates: dict[str, dict[str, str]]) -> str:
    marca_str = str(marca).strip() if pd.notna(marca) else "N/D"
    nombre_str = str(nombre).strip() if pd.notna(nombre) else "N/D"
    candidate_block = format_candidates(candidates)
    return (
        f"CANDIDATOS:\n{candidate_block}\n\n"
        f"Marca: {marca_str} | Descripción: {nombre_str}"
    )


def build_request_dicts(sample: pd.DataFrame, cols: dict[str, str], catalog: GpcCatalog) -> list[dict]:
    """Construye los dicts de request (forma serializable a JSONL)."""
    nombre_col, marca_col = cols["nombre"], cols["marca"]
    request_dicts = []
    seen_ids: set[str] = set()

    for _, row in sample.iterrows():
        marca_val, nombre_val = row.get(marca_col), row.get(nombre_col)
        custom_id = make_custom_id(marca_val, nombre_val)
        if custom_id in seen_ids:
            continue  # (marca, nombre) normalizado ya cubierto por otra fila
        seen_ids.add(custom_id)

        candidates = catalog.build_candidates(query_text(marca_val, nombre_val))

        request_dicts.append(
            {
                "custom_id": custom_id,
                "params": {
                    "model": MODEL,
                    "max_tokens": MAX_TOKENS,
                    "thinking": THINKING_CONFIG,
                    "system": [
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    "messages": [
                        {
                            "role": "user",
                            "content": build_user_content(marca_val, nombre_val, candidates),
                        }
                    ],
                    "output_config": {
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


def read_jsonl_as_requests(jsonl_path: Path):
    import anthropic  # import diferido: no requerido en --dry-run
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

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


def submit_batch_for_file(client, file_path: str, tracker: list[dict], catalog: GpcCatalog) -> None:
    import anthropic

    file_name = Path(file_path).name

    if already_submitted(tracker, file_name):
        logger.info(f"{file_name}: ya existe un batch activo en el tracker, se omite")
        return

    logger.info(f"Leyendo {file_name}")
    try:
        sample, cols = load_sample(file_path)
    except Exception as e:
        logger.error(f"{file_name}: error al leer/preparar el archivo: {e}")
        return

    if sample.empty:
        logger.warning(f"{file_name}: la muestra quedó vacía tras deduplicar/limpiar, se omite")
        return

    request_dicts = build_request_dicts(sample, cols, catalog)
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


# --------------------------------------------------------------------------
# Dry-run: sin llamar a la API de Anthropic, solo prueba local
# --------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Estimación LOCAL aproximada (no exacta): ~4 caracteres por token.
    No se llama a client.messages.count_tokens a propósito, para no hacer
    ninguna llamada a la API de Anthropic durante el dry-run."""
    return max(1, round(len(text) / 4))


def run_dry_run(num_products: int = 5) -> int:
    try:
        catalog = GpcCatalog(CATALOG_FILE)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return 1

    demo_file = "Productos1.xlsx"
    if not Path(demo_file).exists():
        logger.error(f"No se encuentra {demo_file} para el dry-run")
        return 1

    try:
        sample, cols = load_sample(demo_file)
    except Exception as e:
        logger.error(f"Error preparando {demo_file}: {e}")
        return 1

    nombre_col, marca_col = cols["nombre"], cols["marca"]
    demo_rows = sample.head(num_products)

    print("=" * 78)
    print(f"DRY RUN — {num_products} productos reales de {demo_file} (SIN llamar a la API)")
    print("=" * 78)

    per_row_input_tokens = []
    example_output_json = '{"gpc_code": "10002091", "confidence_score": 95}'
    output_tokens_estimate = min(MAX_TOKENS, estimate_tokens(example_output_json))

    for i, (_, row) in enumerate(demo_rows.iterrows(), start=1):
        marca_val, nombre_val = row.get(marca_col), row.get(nombre_col)
        candidates = catalog.build_candidates(query_text(marca_val, nombre_val))
        user_content = build_user_content(marca_val, nombre_val, candidates)

        input_text = SYSTEM_PROMPT + user_content
        input_tokens = estimate_tokens(input_text)
        per_row_input_tokens.append(input_tokens)

        n_bricks = sum(1 for v in candidates.values() if v["nivel"] == "Brick")
        n_others = len(candidates) - n_bricks

        print(f"\n--- Producto {i}: Marca={marca_val!r} | Descripción={nombre_val!r} ---")
        print(f"Candidatos seleccionados: {n_bricks} Bricks + {n_others} Class/Family/Segment padres")
        print(format_candidates(candidates))
        print(f"[Estimado LOCAL, ~4 chars/token] input≈{input_tokens} tok | output≈{output_tokens_estimate} tok (máx {MAX_TOKENS})")

    avg_input_tokens = sum(per_row_input_tokens) / len(per_row_input_tokens)

    print("\n" + "=" * 78)
    print("PROYECCIÓN PARA LOS 5 ARCHIVOS COMPLETOS")
    print("=" * 78)
    print("(Estimación LOCAL con heurística ~4 caracteres/token — NO es el conteo")
    print(" exacto del tokenizador de Anthropic, porque esta prueba no llama a la API.")
    print(" El system prompt usa cache_control, así que el costo real debería ser")
    print(" MENOR a esta cifra a partir de la 2ª solicitud de cada archivo.)")

    try:
        total_unique_requests = 0
        for file_path in get_target_files():
            s, c = load_sample(file_path)
            total_unique_requests += len(
                {make_custom_id(r.get(c["marca"]), r.get(c["nombre"])) for _, r in s.iterrows()}
            )
    except Exception as e:
        logger.warning(f"No se pudo contar solicitudes reales de los 5 archivos ({e}); se usa el promedio observado x5")
        total_unique_requests = round(avg_input_tokens and len(demo_rows) * 5)

    total_input_tokens = avg_input_tokens * total_unique_requests
    total_output_tokens = output_tokens_estimate * total_unique_requests

    input_cost = total_input_tokens / 1_000_000 * BATCH_PRICE_INPUT_PER_MTOK
    output_cost = total_output_tokens / 1_000_000 * BATCH_PRICE_OUTPUT_PER_MTOK
    total_cost = input_cost + output_cost

    print(f"Solicitudes únicas estimadas (5 archivos, tras dedup por nombre+marca): {total_unique_requests}")
    print(f"Input promedio/fila≈{avg_input_tokens:.0f} tok | Output/fila≈{output_tokens_estimate} tok (tope duro: {MAX_TOKENS})")
    print(f"Total input≈{total_input_tokens:,.0f} tok | Total output≈{total_output_tokens:,.0f} tok")
    print(
        f"Costo proyectado (Batch API, sin contar el descuento de cache_control): "
        f"${input_cost:.2f} (input) + ${output_cost:.2f} (output) = ${total_cost:.2f} USD"
    )
    print("=" * 78)
    return 0


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    if "--dry-run" in sys.argv:
        return run_dry_run()

    import anthropic

    try:
        catalog = GpcCatalog(CATALOG_FILE)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return 1

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
            submit_batch_for_file(client, file_path, tracker, catalog)
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
