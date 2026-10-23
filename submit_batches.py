#!/usr/bin/env python3
"""Envía una muestra de trabajo de clasificación GPC (formato "Listado
General 2024") a la Batch API de Anthropic.

Toma archivos "Listado_General_2024_*.xlsx" de "input_2024/" (ver
TARGET_FILES/MAX_FILES para restringir a archivos específicos — p. ej.
esta corrida fija TARGET_FILES a Parte_3/4/5 para no retocar Parte_1
(Sonnet 5) ni Parte_2 (Haiku 4.5), ya recuperados), deduplica por
(marca, descripción) normalizado — ignorando sufijos de empaque como
"X 12 UND" —
y, para cada par único, hace un pre-filtrado LOCAL (sin costo de API)
contra el catálogo oficial GPC ("catalogo/gpc_catalogo_oficial.csv",
generado por build_catalog.py) usando similitud léxica TF-IDF (n-gramas de
palabra + de carácter, con sinónimos venezolanos), enriquecida con las
columnas de categoría internas del Excel (CLASIFICACION, Clasificacion
Macro). Los ~25 Bricks más parecidos, más sus Class/Family/Segment padres,
se incluyen como lista de candidatos dentro del mensaje enviado a Claude —
el modelo solo puede elegir un código de esa lista o "NO_MATCH", nunca
inventar uno.

Para minimizar tokens de salida, el modelo responde únicamente
{"gpc_code": ..., "confidence_score": ...} (sin razonamiento ni
descripción); retrieve_batches.py reconstruye nivel_asignado y
gpc_description localmente a partir del catálogo oficial (candado
ground-truth: un gpc_code que no exista en el catálogo se descarta como
NO_MATCH, nunca se acepta a ciegas).

Los batch_id resultantes se guardan en batch_tracker.json para que
retrieve_batches.py los recupere.

Uso:
    python3 submit_batches.py                        # usa TARGET_FILES/MAX_FILES (ver más abajo)
    python3 submit_batches.py archivo1.xlsx archivo2.xlsx
                                                       # procesa exactamente estos archivos de
                                                       # INPUT_DIR, indicados en la ejecución —
                                                       # ignora TARGET_FILES/MAX_FILES
    python3 submit_batches.py --input-dir "Nueva Carga" archivo1.xlsx
                                                       # igual, pero leyendo de otra carpeta
    python3 submit_batches.py --dry-run [archivo.xlsx]
                                                       # sin llamar a la API: muestra candidatos
                                                       # y estima tokens/costo
"""

import argparse
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

INPUT_DIR = Path("input_2024")
INPUT_GLOB_PATTERN = "Listado_General_2024_*.xlsx"
TRACKER_FILE = Path("batch_tracker.json")
CATALOG_FILE = Path("catalogo/gpc_catalogo_oficial.csv")
# Por defecto se procesan hasta 5 archivos que calcen con
# INPUT_GLOB_PATTERN en INPUT_DIR. En la práctica casi siempre se invoca
# con archivos y --input-dir explícitos por línea de comandos (ver
# parse_args), que tienen prioridad sobre esto — ver get_target_files().
MAX_FILES = 5
# Lista fija opcional para despachos puntuales sin tocar la línea de
# comandos (p. ej. reenviar solo ciertos archivos). None/[] = usar
# INPUT_GLOB_PATTERN/MAX_FILES. El bloque 2024 Parte_3-5 que vivía aquí ya
# se recuperó (ver batch_tracker.json) — queda en None por defecto.
TARGET_FILES: list[str] | None = None
# 25 candidatos por producto (no 8): con 8, el bloque 2024 Parte_3-5 mostró
# un NO_MATCH notablemente más alto (5-10% vs 4.2% con 25) — menos recall
# en el pre-filtro local a cambio de menos tokens. 25 es el valor por
# defecto recomendado salvo que el costo sea la prioridad.
TOP_K_BRICKS = 25

# Modelo vigente para todo el pipeline: Claude Haiku 4.5 (más rápido y
# ~57% más barato que Sonnet 5 en la comparación A/B de 2024, con cobertura
# algo menor — ver reporte de esa comparación).
MODEL = "claude-haiku-5-5"
MAX_TOKENS = 45  # recorte radical de salida: solo {"gpc_code","confidence_score"}

# Precios Batch API (50% del precio estándar) usados solo para la
# estimación de costos del --dry-run, en USD por millón de tokens.
# NOTA: estas son las tarifas de Haiku 4.5 ($0.50/$2.50 por MTok estándar,
# la mitad en batch) — para Sonnet 5 eran $1.00/$5.00. Ajustar si MODEL
# cambia de nuevo.
BATCH_PRICE_INPUT_PER_MTOK = 0.50
BATCH_PRICE_OUTPUT_PER_MTOK = 2.50

REQUIRED_COLUMNS = ["gtin", "descripcion", "marca"]
# Columnas auxiliares de categoría interna (Col. I y Col. N del Excel 2024)
# usadas SOLO para enriquecer la búsqueda léxica local — nunca se envían a
# Claude ni se citan como fuente GPC. Si el archivo no las trae, se ignoran.
OPTIONAL_COLUMNS = ["clasificacion", "clasificacion macro"]

# Nota importante: Claude Sonnet 5 RECHAZA (HTTP 400) los parámetros de
# muestreo (temperature/top_p/top_k) — no existe forma de fijar
# temperature=0 en este modelo, a diferencia de lo pedido. En su lugar se
# desactiva explícitamente el "thinking" (sí soportado en Sonnet 5) para
# que los 45 tokens de max_tokens no se gasten en razonamiento interno
# invisible antes de emitir el JSON.
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
    # Algunos proveedores (p. ej. calzado 2021) describen sus productos en
    # inglés; el catálogo oficial GPC está en español, así que sin esto el
    # TF-IDF no encuentra ningún candidato de Calzado para "FOOTWEAR" y el
    # candado ground-truth termina bloqueando todo a NO_MATCH (verificado:
    # 100% de las filas "FOOTWEAR" en Consolidacion 2021 Parte_1/2).
    "footwear": "calzado zapatos",
    "shoes": "zapatos calzado",
    "shoe": "zapato calzado",
    "boots": "botas calzado",
    "boot": "bota calzado",
    "sneakers": "zapatos deportivos calzado",
    "sandals": "sandalias calzado",
    "children": "ninos",
    "kids": "ninos",
    "ladies": "dama mujer",
    "men": "hombre caballero",
    "women": "mujer dama",
    "baby": "bebe",
    # Mismo problema, detectado en Listado completo 2020 (99% de las filas
    # sin CLASIFICACION interna que compense): lubricantes automotrices y
    # ropa descritos en inglés sin ningún candidato de Lubricantes/Prendas
    # de vestir en el pre-filtro (p. ej. "25W-40 SYNT BLEND 4T" o "LEGGING
    # YOGA"), resultando en NO_MATCH masivo aunque el catálogo sí tiene
    # Brick equivalente ("Aceites/líquidos lubricantes", "Pantalones").
    "oil": "aceite lubricante",
    "lubricant": "lubricante",
    "synt": "sintetico aceite",
    "synthetic": "sintetico",
    "legging": "mallas pantalon",
    "leggings": "mallas pantalon",
    "leguing": "legging mallas pantalon",
    "shirt": "camisa",
    "hoodie": "sudadera chaqueta",
    "shorts": "pantalon corto",
    "underwear": "ropa interior",
    "boxer": "ropa interior calzoncillo",
    "shampoo": "champu",
    "silicon": "silicona",
    "silicone": "silicona",
    "mask": "mascarilla",
    "kitchen": "cocina",
    "accessories": "accesorios",
    "sport": "deportivo",
    # Detectado en 2014 (marca I-ONSET): "CASE" (funda/estuche, p.ej.
    # fundas de teléfono "JELLY CASE IP5/S") no tiene overlap léxico
    # con "funda"/"estuche" en el catálogo.
    "case": "funda estuche",
    # Detectado en 2019 Consolidado Parte_1 (marca KOLOSSUS): "COVERALL"
    # (overol/mono de trabajo de cuerpo completo) no tiene overlap de
    # n-gramas con el catálogo en español y no encontraba ningún candidato
    # de Prendas de vestir — sí existe "Prendas de protección – Para todo
    # el cuerpo" (10001394), solo no se veía en la lista de candidatos.
    "coverall": "mono de trabajo prendas de proteccion cuerpo completo",
    "coveralls": "mono de trabajo prendas de proteccion cuerpo completo",
    # Detectado en 2018 Parte_1 (marca VIMAY, ropa infantil venezolana):
    # estos términos regionales no tienen overlap de n-gramas con el
    # catálogo en español estándar y además "bordada/bordado" (bordado a
    # mano) colisiona por n-gramas con "Bordes" (de construcción),
    # desplazando cualquier candidato de ropa relevante.
    "franela": "camiseta camisa",
    "almillas": "camiseta interior bebe",
    "enteritos": "mono bebe cuerpo entero prenda",
    "leggins": "mallas pantalon",
    # Detectado en 2017 Parte_4.
    "cooler": "nevera hielera",
    # Marca EXTELL: solo viene el nombre genérico del fármaco + dosis, sin
    # ningún término en español que conecte con el catálogo; estos 5 son
    # todos antiácidos/H2-bloqueadores/inhibidores de bomba de protones —
    # la Class "Remedios gastrointestinales" sí tiene Brick para esto
    # ("Remedios contra la flatulencia/indigestión/antiácidos").
    "ranitidina": "antiacido gastrointestinal indigestion",
    "cimetidina": "antiacido gastrointestinal indigestion",
    "omeprazol": "antiacido gastrointestinal indigestion",
    "pantoprazol": "antiacido gastrointestinal indigestion",
    "esomeprazol": "antiacido gastrointestinal indigestion",
    # Marca KSKIN (2016 Parte_5): fundas/protectores de pantalla descritos
    # solo como "[marca/modelo de teléfono] PROTECT[OR] ANTI-HUELLA/
    # DIAMANTE/TRANSPARENTE" — sin ningún término que conecte con el
    # catálogo, y "MOTOROLA MOTO" incluso colisiona con partes de
    # motocicleta. Ancla directa por nombre de marca: cubre todos los
    # modelos de teléfono sin tener que listarlos uno por uno.
    "kskin": "accesorios telefono movil smartphone funda protector pantalla",
    # Detectado en 2015 Parte_1: "JEANS [licencia infantil] NNNNNNN" —
    # "jeans" no tiene overlap de n-gramas con "pantalones", y encima la
    # marca (BARBIE, HOT WHEELS, MONSTER HIGH...) colisiona por n-gramas
    # con palabras sin relación ("barba", "barras", "ruibarbo").
    "jeans": "pantalon pantalones mezclilla",
}

# Sufijos de empaque a ignorar al construir la llave de deduplicación
# (p. ej. "X 12 UND", "X 24 UND", "X 48 UND") para no pagar dos veces por
# la unidad individual (GTIN-13) y su caja/display (GTIN-14).
PACKAGING_SUFFIX_RE = re.compile(r"\bx\s*\d+\s*(und|unid|unidades)\b")

GPC_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "gpc_code": {"type": "string"},
        # Nota: output_config.format.schema NO soporta "minimum"/"maximum"
        # en propiedades "integer" (la API rechaza el request con 400 si se
        # incluyen) — el rango 0-100 se exige solo vía el system prompt.
        "confidence_score": {"type": "integer"},
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
# Normalización de texto / claves — retrieve_batches.py recalcula EXACTAMENTE
# las mismas funciones para poder unir por (marca, descripción) normalizado.
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


def strip_packaging_suffix(text: str) -> str:
    """Quita sufijos de empaque tipo "x 12 und" del texto ya normalizado,
    para que la unidad y su caja (GTIN-13/GTIN-14) compartan la misma
    llave de deduplicación."""
    text = PACKAGING_SUFFIX_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_descripcion(descripcion) -> str:
    return strip_packaging_suffix(normalize_text(descripcion))


def apply_synonyms(text: str) -> str:
    expanded = []
    for word in text.split():
        expanded.append(word)
        if word in SYNONYMS_VE:
            expanded.append(SYNONYMS_VE[word])
    return " ".join(expanded)


def _build_segmentation_vocab() -> set[str]:
    """Vocabulario para separar palabras pegadas sin espacios (detectado
    en 2014, marca KE: "JEANSDECOLOR8403", "CAMISAPERFLIVIANAM/CORTACC...").
    Usa las mismas palabras que el catálogo oficial ya sabe reconocer
    (para que una palabra separada tenga sentido para el TF-IDF), más
    conectores españoles comunes y el propio vocabulario de SYNONYMS_VE."""
    vocab = {
        "de", "del", "la", "el", "los", "las", "y", "con", "sin", "para",
        "por", "en", "color", "talla", "unidad", "unidades", "corta",
        "corto", "larga", "largo",
    }
    try:
        catalog_df = pd.read_csv(CATALOG_FILE, dtype=str)
        for titulo in catalog_df["titulo"].dropna():
            for w in normalize_text(titulo).split():
                if len(w) >= 3:
                    vocab.add(w)
    except Exception:
        pass
    for key, value in SYNONYMS_VE.items():
        vocab.add(key)
        vocab.update(value.split())
    return vocab


_SEGMENTATION_VOCAB = _build_segmentation_vocab()


def _segment_glued_word(run: str) -> list[str] | None:
    """Segmentación por programación dinámica: devuelve la lista de
    palabras si `run` se descompone POR COMPLETO en palabras conocidas,
    o None si no se puede. La exigencia de descomposición completa es
    la salvaguarda: un código de SKU real (sin palabras reales, p.ej.
    "velcro" o "fk51") simplemente no se segmenta y queda intacto."""
    n = len(run)
    dp: list[list[str] | None] = [None] * (n + 1)
    dp[0] = []
    for i in range(1, n + 1):
        for j in range(max(0, i - 15), i):
            if dp[j] is None:
                continue
            word = run[j:i]
            if len(word) >= 2 and word in _SEGMENTATION_VOCAB:
                dp[i] = dp[j] + [word]
                break
    return dp[n]


def split_glued_words(text: str) -> str:
    """Separa palabras en español pegadas sin espacios (p.ej.
    "jeansdecolor8403" -> "jeans de color 8403"). Solo se usa para el
    texto de búsqueda del pre-filtro TF-IDF (query_text) — NUNCA para
    normalize_key/make_custom_id, así que no afecta la deduplicación ni
    el merge con retrieve_batches.py."""
    out: list[str] = []
    for token in text.split():
        for chunk in re.findall(r"[a-z]+|[0-9]+", token):
            if chunk.isalpha() and len(chunk) >= 4 and chunk not in _SEGMENTATION_VOCAB:
                segmented = _segment_glued_word(chunk)
                if segmented:
                    out.extend(segmented)
                    continue
            out.append(chunk)
    return " ".join(out)


def normalize_key(marca, descripcion) -> str:
    return f"{normalize_text(marca)}|{normalize_descripcion(descripcion)}"


def make_custom_id(marca, descripcion) -> str:
    """ID determinista derivado de (marca, descripción_limpia). Es tanto la
    llave de deduplicación como el custom_id de la Batch API y, en
    retrieve_batches.py, la llave de merge — así una unidad y su caja
    (mismo producto, distinto GTIN) comparten clasificación."""
    key = normalize_key(marca, descripcion)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:24]


def query_text(marca, descripcion, clasificacion=None, clasificacion_macro=None) -> str:
    """Texto de búsqueda para el pre-filtro léxico: enriquece la
    descripción con las columnas de categoría interna del Excel (si
    existen) para mejorar la precisión del TF-IDF."""
    parts = [normalize_text(marca), normalize_descripcion(descripcion)]
    if clasificacion:
        parts.append(normalize_text(clasificacion))
    if clasificacion_macro:
        parts.append(normalize_text(clasificacion_macro))
    combined = split_glued_words(" ".join(p for p in parts if p))
    return apply_synonyms(combined)


def clean_gtin(value) -> str:
    """Convierte un GTIN a string entero exacto, sin importar si pandas lo
    leyó como int, float (incl. notación científica) o texto ("1.23E+12",
    "7593394001720.0", etc.). Nunca deja ".0" ni "nan"."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(round(value)))
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    try:
        return str(int(float(text)))
    except ValueError:
        digits = re.sub(r"\D", "", text)
        return digits


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
# Lectura y preparación de los archivos "Listado General 2024"
# --------------------------------------------------------------------------

def get_target_files(cli_files: list[str] | None = None, input_dir: Path | None = None) -> list[str]:
    """Resuelve qué archivos procesar. Prioridad:
    1. `cli_files` — archivos indicados explícitamente en la línea de
       comandos al ejecutar el script (lo que pide el flujo de "Nueva
       Carga": decidir el archivo en el momento de correr, no en el código).
    2. `TARGET_FILES` — lista fija en este módulo (usada en despachos
       puntuales, p. ej. reenviar solo Parte_3/4/5).
    3. `INPUT_GLOB_PATTERN` + `MAX_FILES` — comportamiento por defecto.
    """
    base_dir = input_dir if input_dir is not None else INPUT_DIR
    if not base_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio de entrada: {base_dir}")

    if cli_files:
        files = [str(base_dir / f) for f in cli_files]
        missing = [f for f in files if not Path(f).exists()]
        if missing:
            raise FileNotFoundError(f"Archivo(s) indicados no encontrados: {missing}")
        return files

    if TARGET_FILES:
        files = [str(base_dir / f) for f in TARGET_FILES]
        missing = [f for f in files if not Path(f).exists()]
        if missing:
            raise FileNotFoundError(f"TARGET_FILES no encontrados: {missing}")
        return files

    files = sorted(glob.glob(str(base_dir / INPUT_GLOB_PATTERN)))
    if not files:
        raise FileNotFoundError(f"No se encontraron archivos {INPUT_GLOB_PATTERN} en {base_dir}")
    return files[:MAX_FILES]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Envía productos a clasificar a la Batch API de Anthropic."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Nombres de archivo .xlsx (dentro de --input-dir) a procesar explícitamente. "
        "Si se omite, se usa TARGET_FILES/MAX_FILES definidos en el script.",
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help=f"Directorio donde buscar los .xlsx (por defecto: {INPUT_DIR}). "
        'Ej.: --input-dir "Nueva Carga"',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No llama a la API: solo muestra candidatos y estima tokens/costo.",
    )
    return parser.parse_args(argv)


# Alias de nombres de columna vistos en formatos de años más antiguos
# (p. ej. 2017: "Nombre"/"EAN13"/"Clasificación Global del Producto" en
# vez de "DESCRIPCION"/"GTIN"/"CLASIFICACION"). Claves y valores ya
# normalizados (sin acentos, minúsculas) — ver _normalize_col_key.
COLUMN_ALIASES: dict[str, list[str]] = {
    "descripcion": ["nombre"],
    "gtin": ["ean13", "ean-13", "ean 13"],
    "clasificacion": ["clasificacion global del producto"],
}


def _normalize_col_key(value) -> str:
    return strip_accents(str(value)).strip().lower()


def resolve_columns(df: pd.DataFrame, required: list[str], optional: list[str] | None = None) -> dict[str, str | None]:
    """Mapea nombres canónicos (minúsculas, sin acentos) a los nombres
    reales de columna, sin importar mayúsculas/minúsculas, acentos ni
    espacios extremos (p. ej. la columna real puede llamarse "GTIN",
    "DESCRIPCION", o un alias de un formato de año distinto como "Nombre"
    o "EAN13" — ver COLUMN_ALIASES). Las columnas `optional` que no
    existan quedan en None en vez de fallar."""
    lower_map: dict[str, str] = {}
    for col in df.columns:
        key = _normalize_col_key(col)
        if key not in lower_map:
            lower_map[key] = col

    def find(canonical: str) -> str | None:
        if canonical in lower_map:
            return lower_map[canonical]
        for alias in COLUMN_ALIASES.get(canonical, []):
            if alias in lower_map:
                return lower_map[alias]
        return None

    missing = [r for r in required if find(r) is None]
    if missing:
        raise ValueError(
            f"Faltan columnas requeridas {missing}. Columnas disponibles: {list(df.columns)}"
        )
    result: dict[str, str | None] = {r: find(r) for r in required}
    for opt in optional or []:
        result[opt] = find(opt)
    return result


# Esquema estándar observado en todos los años (2021-2025) cuando el Excel
# llega sin fila de encabezado real (se pierde en la exportación interna y
# la primera fila queda como basura literal "Unnamed: N").
STANDARD_COLUMNS = [
    "EMPRESA", "PREFIJO", "TIPO GTIN", "GTIN", "DESCRIPCION", "MARCA",
    "ESTATUS", "CODIGO", "CLASIFICACION", "PAISES COMERCIALIZACION",
    "ORIGEN", "FECHA CREACION", "FECHA MODIFICACION",
]


def _looks_like_header_row(values: list) -> bool:
    text = {_normalize_col_key(v) for v in values if pd.notna(v)}
    tiene_descripcion = "descripcion" in text or any(
        alias in text for alias in COLUMN_ALIASES["descripcion"]
    )
    return tiene_descripcion and "marca" in text


def load_sample(file_path: str) -> tuple[pd.DataFrame, dict[str, str | None]]:
    # Detección robusta de la fila de encabezado: algunos archivos traen
    # una fila basura inicial (texto literal "Unnamed: N") y/o pierden la
    # fila de encabezado real durante la exportación interna.
    raw = pd.read_excel(file_path, header=None, nrows=10)
    header_row = None
    for i in range(len(raw)):
        if _looks_like_header_row(raw.iloc[i].tolist()):
            header_row = i
            break

    if header_row is not None:
        df = pd.read_excel(file_path, header=header_row)
    else:
        logger.warning(
            f"{file_path}: no se encontró fila de encabezado real en las primeras 10 filas; "
            f"se asume esquema estándar {STANDARD_COLUMNS} tras descartar la primera fila."
        )
        df = pd.read_excel(file_path, header=None, skiprows=1)
        df = df.iloc[:, : len(STANDARD_COLUMNS)]
        df.columns = STANDARD_COLUMNS
        df = df.dropna(how="all")

    cols = resolve_columns(df, REQUIRED_COLUMNS, OPTIONAL_COLUMNS)
    gtin_col, descripcion_col, marca_col = cols["gtin"], cols["descripcion"], cols["marca"]

    df[gtin_col] = df[gtin_col].apply(clean_gtin)
    df = df[df[gtin_col] != ""]

    # Deduplicación inteligente: misma llave que make_custom_id (marca +
    # descripción sin sufijos de empaque), así una unidad (GTIN-13) y su
    # caja/display (GTIN-14) del mismo producto no se pagan dos veces.
    df["_dedup_key"] = df.apply(lambda r: make_custom_id(r[marca_col], r[descripcion_col]), axis=1)
    sample = df.drop_duplicates(subset=["_dedup_key"]).drop(columns=["_dedup_key"]).copy()
    return sample, cols


def build_user_content(marca, descripcion, candidates: dict[str, dict[str, str]]) -> str:
    marca_str = str(marca).strip() if pd.notna(marca) else "N/D"
    descripcion_str = str(descripcion).strip() if pd.notna(descripcion) else "N/D"
    candidate_block = format_candidates(candidates)
    return (
        f"CANDIDATOS:\n{candidate_block}\n\n"
        f"Marca: {marca_str} | Descripción: {descripcion_str}"
    )


def build_request_dicts(sample: pd.DataFrame, cols: dict[str, str | None], catalog: GpcCatalog) -> list[dict]:
    """Construye los dicts de request (forma serializable a JSONL)."""
    descripcion_col, marca_col = cols["descripcion"], cols["marca"]
    clasificacion_col, clasificacion_macro_col = cols.get("clasificacion"), cols.get("clasificacion macro")
    request_dicts = []
    seen_ids: set[str] = set()

    for _, row in sample.iterrows():
        marca_val, descripcion_val = row.get(marca_col), row.get(descripcion_col)
        clasificacion_val = row.get(clasificacion_col) if clasificacion_col else None
        clasificacion_macro_val = row.get(clasificacion_macro_col) if clasificacion_macro_col else None

        custom_id = make_custom_id(marca_val, descripcion_val)
        if custom_id in seen_ids:
            continue  # (marca, descripción) normalizado ya cubierto por otra fila
        seen_ids.add(custom_id)

        q = query_text(marca_val, descripcion_val, clasificacion_val, clasificacion_macro_val)
        candidates = catalog.build_candidates(q)

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
                            "content": build_user_content(marca_val, descripcion_val, candidates),
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
            "model": MODEL,
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


def run_dry_run(cli_files: list[str] | None = None, input_dir: Path | None = None, num_products: int = 5) -> int:
    try:
        catalog = GpcCatalog(CATALOG_FILE)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return 1

    try:
        files = get_target_files(cli_files, input_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    demo_file = files[0]
    demo_file_name = Path(demo_file).name

    try:
        raw_df = pd.read_excel(demo_file)
        sample, cols = load_sample(demo_file)
    except Exception as e:
        logger.error(f"Error preparando {demo_file_name}: {e}")
        return 1

    descripcion_col, marca_col = cols["descripcion"], cols["marca"]
    clasificacion_col = cols.get("clasificacion")
    clasificacion_macro_col = cols.get("clasificacion macro")

    print("=" * 78)
    print(f"DRY RUN — {demo_file_name} (SIN llamar a la API)")
    print("=" * 78)
    print(f"Filas totales en el archivo:                {len(raw_df)}")
    print(f"Productos únicos tras deduplicación inteligente (marca+descripción, sin sufijos de empaque): {len(sample)}")

    demo_rows = sample.head(num_products)

    per_row_input_tokens = []
    example_output_json = '{"gpc_code": "10002091", "confidence_score": 95}'
    output_tokens_estimate = min(MAX_TOKENS, estimate_tokens(example_output_json))

    for i, (_, row) in enumerate(demo_rows.iterrows(), start=1):
        marca_val, descripcion_val = row.get(marca_col), row.get(descripcion_col)
        clasificacion_val = row.get(clasificacion_col) if clasificacion_col else None
        clasificacion_macro_val = row.get(clasificacion_macro_col) if clasificacion_macro_col else None

        q = query_text(marca_val, descripcion_val, clasificacion_val, clasificacion_macro_val)
        candidates = catalog.build_candidates(q)
        user_content = build_user_content(marca_val, descripcion_val, candidates)

        input_text = SYSTEM_PROMPT + user_content
        input_tokens = estimate_tokens(input_text)
        per_row_input_tokens.append(input_tokens)

        n_bricks = sum(1 for v in candidates.values() if v["nivel"] == "Brick")
        n_others = len(candidates) - n_bricks

        print(f"\n--- Producto {i}: Marca={marca_val!r} | Descripción={descripcion_val!r} ---")
        if clasificacion_val or clasificacion_macro_val:
            print(f"    (categoría interna usada solo para la búsqueda: {clasificacion_val!r} / {clasificacion_macro_val!r})")
        print(f"Candidatos seleccionados: {n_bricks} Bricks + {n_others} Class/Family/Segment padres")
        print(format_candidates(candidates))
        print(f"[Estimado LOCAL, ~4 chars/token] input≈{input_tokens} tok | output≈{output_tokens_estimate} tok (máx {MAX_TOKENS})")

    avg_input_tokens = sum(per_row_input_tokens) / len(per_row_input_tokens)
    total_unique_requests = len(sample)

    total_input_tokens = avg_input_tokens * total_unique_requests
    total_output_tokens = output_tokens_estimate * total_unique_requests

    input_cost = total_input_tokens / 1_000_000 * BATCH_PRICE_INPUT_PER_MTOK
    output_cost = total_output_tokens / 1_000_000 * BATCH_PRICE_OUTPUT_PER_MTOK
    total_cost = input_cost + output_cost

    print("\n" + "=" * 78)
    print(f"PROYECCIÓN PARA {demo_file_name}")
    print("=" * 78)
    print("(Estimación LOCAL con heurística ~4 caracteres/token — NO es el conteo")
    print(" exacto del tokenizador de Anthropic, porque esta prueba no llama a la API.")
    print(" El system prompt usa cache_control, así que el costo real debería ser")
    print(" MENOR a esta cifra a partir de la 2ª solicitud.)")
    print(f"Solicitudes únicas (tras dedup marca+descripción, sin sufijos de empaque): {total_unique_requests}")
    print(f"Input promedio/fila≈{avg_input_tokens:.0f} tok | Output/fila≈{output_tokens_estimate} tok (tope duro: {MAX_TOKENS})")
    print(f"Total input≈{total_input_tokens:,.0f} tok | Total output≈{total_output_tokens:,.0f} tok")
    print(
        f"Costo proyectado (Batch API, sin contar el descuento de cache_control): "
        f"${input_cost:.4f} (input) + ${output_cost:.4f} (output) = ${total_cost:.4f} USD"
    )
    print("=" * 78)
    return 0


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    args = parse_args(sys.argv[1:])
    input_dir = Path(args.input_dir) if args.input_dir else None
    cli_files = args.files or None

    if args.dry_run:
        return run_dry_run(cli_files, input_dir)

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
        files = get_target_files(cli_files, input_dir)
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
