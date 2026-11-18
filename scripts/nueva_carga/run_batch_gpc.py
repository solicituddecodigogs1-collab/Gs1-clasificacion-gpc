#!/usr/bin/env python3
"""
Orquestador de clasificación GPC (GS1 Venezuela) con la Batch API de Anthropic.

Flujo (subcomandos, cada uno reanudable):

    python run_batch_gpc.py prepare            # 1-3: ingesta, desduplicación y .jsonl por lotes
    python run_batch_gpc.py submit             # envía los .jsonl a la Batch API
    python run_batch_gpc.py collect            # espera el fin de los lotes y descarga resultados
    python run_batch_gpc.py merge              # 6: fusiona con el maestro y exporta a ./output

    # Prueba de extremo a extremo SIN llamar a la API (resultados sintéticos):
    python run_batch_gpc.py prepare
    python run_batch_gpc.py merge --simulate

Requiere ANTHROPIC_API_KEY (o un perfil `ant auth login`) solo para submit/collect.

Notas de diseño
---------------
* custom_id = GTIN (normalizado). La Batch API exige ^[a-zA-Z0-9_-]{1,64}$ y
  custom_id únicos por lote; las filas que no cumplan se omiten y se reportan.
* Al desduplicar por (Descripción, Marca) solo se envía un GTIN "representante"
  por grupo. Por eso la fusión se hace en dos pasos:
    a) resultados --(GTIN)--> sub-dataframe desduplicado
    b) sub-dataframe --(Descripción, Marca)--> maestro completo
  Un merge directo por GTIN dejaría sin clasificar a todos los duplicados.
* Excel admite máx. 1.048.576 filas por hoja, así que el maestro (~1,18 M filas)
  se exporta como un .xlsx por archivo de origen (mismo formato que la entrada)
  y además como un CSV consolidado.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #
INPUT_DIR = Path("./input")
OUTPUT_DIR = Path("./output")
WORK_DIR = Path("./work")
BATCH_DIR = WORK_DIR / "batches"            # .jsonl de entrada
RESULTS_DIR = WORK_DIR / "results"          # resultados reales descargados
SIM_RESULTS_DIR = WORK_DIR / "results_sim"  # resultados simulados
STATE_FILE = WORK_DIR / "batch_state.json"

MODEL = "claude-sonnet-4-5"
BATCH_SIZE = 10_000
MAX_TOKENS = 700
POLL_SECONDS = 60
EXCEL_MAX_ROWS = 1_048_575  # 1 fila reservada para el encabezado

COL_GTIN = "GTIN"
COL_DESC = "Descripción"
COL_MARCA = "Marca"

# Columnas que se añaden al final del archivo exportado.
AI_COLS = ["razonamiento", "nivel_asignado", "gpc_code", "gpc_title", "confidence_score"]

# Columnas auxiliares internas (nunca se exportan).
_SRC = "__archivo_origen"
_KEY = "__gtin_key"

CUSTOM_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

LEVEL_DIGITS = {"BRICK": 8, "CLASE": 6, "FAMILIA": 4, "NO_MATCH": 0}

# --------------------------------------------------------------------------- #
# Prompt (escalamiento inverso) y esquema
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """\
Eres un clasificador experto en el GPC (Global Product Classification) de GS1.
Recibirás un producto como: "Marca: [Marca] | Descripción: [Descripción]".

JERARQUÍA GPC
  Segmento (2 dígitos) > Familia (4) > Clase (6) > Brick (8).

REGLA 1 DEL GPC — IDENTIDAD FÍSICA
Clasifica por lo que el producto ES físicamente (su naturaleza, composición y
forma), no por su marca, su público objetivo, su canal de venta ni su uso
comercial declarado. La marca solo sirve como pista para interpretar la
descripción; nunca define por sí sola la categoría.

PROHIBIDO ADIVINAR
No completes información que la descripción no contiene. No inventes códigos
GPC: si no conoces con certeza el código exacto y su título oficial en inglés
o español, NO lo devuelvas en ese nivel; retrocede al nivel superior.

ESCALAMIENTO INVERSO (de lo más específico a lo más general)
  1. BRICK (8 dígitos): solo si la identidad física del producto es inequívoca
     y conoces el código y título exactos.
  2. Si hay duda entre bricks o la descripción es ambigua -> CLASE (6 dígitos).
  3. Si hay duda entre clases -> FAMILIA (4 dígitos).
  4. Si ni la familia es determinable (descripción vacía, críptica, solo una
     marca, un código, o productos de naturaleza mixta) -> NO_MATCH.

FORMATO DE SALIDA
Responde ÚNICAMENTE llamando a la herramienta `clasificar_gpc`:
  - razonamiento: 1-3 frases sobre la identidad física y por qué se eligió
    (o por qué se retrocedió de) ese nivel.
  - nivel_asignado: BRICK | CLASE | FAMILIA | NO_MATCH
  - gpc_code: solo dígitos; 8, 6 o 4 según el nivel; "" si NO_MATCH.
  - gpc_title: título del nivel asignado; "" si NO_MATCH.
  - confidence_score: número entre 0 y 1. Debe reflejar tu certeza real y ser
    menor cuanto más general sea el nivel asignado.
"""

TOOL_NAME = "clasificar_gpc"
TOOL = {
    "name": TOOL_NAME,
    "description": "Registra la clasificación GPC del producto.",
    "input_schema": {
        "type": "object",
        # El orden importa: el razonamiento se genera antes que el código.
        "properties": {
            "razonamiento": {"type": "string"},
            "nivel_asignado": {"type": "string", "enum": list(LEVEL_DIGITS)},
            "gpc_code": {"type": "string", "pattern": "^([0-9]{4}|[0-9]{6}|[0-9]{8})?$"},
            "gpc_title": {"type": "string"},
            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": AI_COLS,
        "additionalProperties": False,
    },
}


def build_user_text(marca, desc) -> str:
    return f"Marca: {'' if pd.isna(marca) else marca} | Descripción: {'' if pd.isna(desc) else desc}"


# --------------------------------------------------------------------------- #
# 1. Ingesta intacta
# --------------------------------------------------------------------------- #
def norm_gtin(series: pd.Series) -> pd.Series:
    """GTIN como texto limpio (sin espacios ni sufijo '.0' típico de Excel)."""
    return series.astype("string").str.strip().str.replace(r"\.0+$", "", regex=True)


def ingest() -> pd.DataFrame:
    files = sorted(glob.glob(str(INPUT_DIR / "*.xlsx")))
    files = [f for f in files if not os.path.basename(f).startswith("~$")]
    if not files:
        sys.exit(f"No se encontraron .xlsx en {INPUT_DIR}/")

    frames = []
    for f in files:
        print(f"  leyendo {f} ...", flush=True)
        # GTIN como texto para no perder ceros a la izquierda; el resto de
        # columnas conserva el tipo que infiere pandas.
        df = pd.read_excel(f, dtype={COL_GTIN: str})
        missing = [c for c in (COL_GTIN, COL_DESC, COL_MARCA) if c not in df.columns]
        if missing:
            sys.exit(f"{f}: faltan columnas obligatorias {missing}")
        df[_SRC] = Path(f).stem
        frames.append(df)

    master = pd.concat(frames, ignore_index=True, sort=False)
    master[_KEY] = norm_gtin(master[COL_GTIN])
    print(f"Maestro: {len(master):,} filas, {len(master.columns) - 2} columnas originales")
    return master


# --------------------------------------------------------------------------- #
# 2. Desduplicación global
# --------------------------------------------------------------------------- #
def dedup(master: pd.DataFrame) -> pd.DataFrame:
    sub = master.loc[:, [_KEY, COL_DESC, COL_MARCA]].copy()

    sin_desc = sub[COL_DESC].isna() | (sub[COL_DESC].astype("string").str.strip() == "")
    sub = sub[~sin_desc]
    print(f"  filas sin descripción (no se envían): {int(sin_desc.sum()):,}")

    sub = sub.drop_duplicates(subset=[COL_DESC, COL_MARCA])
    print(f"  únicos por (Descripción, Marca): {len(sub):,}")

    # custom_id debe ser único y válido.
    valid = sub[_KEY].notna() & sub[_KEY].fillna("").str.match(CUSTOM_ID_RE)
    if (~valid).any():
        print(f"  AVISO: {int((~valid).sum()):,} filas con GTIN vacío/inválido para custom_id (omitidas)")
    sub = sub[valid]
    dup = sub.duplicated(subset=[_KEY], keep="first")
    if dup.any():
        print(f"  AVISO: {int(dup.sum()):,} GTIN repetidos con distinta Descripción/Marca "
              f"(se envía solo la primera aparición)")
    sub = sub[~dup].reset_index(drop=True)
    print(f"  a enviar a la API: {len(sub):,}")
    return sub


# --------------------------------------------------------------------------- #
# 3. Preparación de la Batch API
# --------------------------------------------------------------------------- #
def make_request(row) -> dict:
    return {
        "custom_id": row[_KEY],
        "params": {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "temperature": 0,
            "system": SYSTEM_PROMPT,
            "tools": [TOOL],
            "tool_choice": {"type": "tool", "name": TOOL_NAME},
            "messages": [{"role": "user", "content": build_user_text(row[COL_MARCA], row[COL_DESC])}],
        },
    }


def write_jsonl_batches(sub: pd.DataFrame) -> list[Path]:
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    for old in BATCH_DIR.glob("batch_*.jsonl"):
        old.unlink()
    paths = []
    for i, start in enumerate(range(0, len(sub), BATCH_SIZE), start=1):
        chunk = sub.iloc[start:start + BATCH_SIZE]
        path = BATCH_DIR / f"batch_{i:04d}.jsonl"
        with open(path, "w", encoding="utf-8") as fh:
            for row in chunk.to_dict("records"):
                fh.write(json.dumps(make_request(row), ensure_ascii=False) + "\n")
        paths.append(path)
        print(f"  {path}  ({len(chunk):,} solicitudes)")
    return paths


def cmd_prepare(_args) -> None:
    print("[1/3] Ingesta")
    master = ingest()
    print("[2/3] Desduplicación")
    sub = dedup(master)
    print("[3/3] Generando .jsonl")
    write_jsonl_batches(sub)
    if STATE_FILE.exists():
        STATE_FILE.unlink()  # lotes nuevos -> estado de envío anterior obsoleto


# --------------------------------------------------------------------------- #
# Envío y descarga (Batch API real)
# --------------------------------------------------------------------------- #
def load_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def save_state(state: dict) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def cmd_submit(_args) -> None:
    import anthropic

    client = anthropic.Anthropic()
    state = load_state()
    files = sorted(BATCH_DIR.glob("batch_*.jsonl"))
    if not files:
        sys.exit("No hay .jsonl; ejecuta primero `prepare`.")
    for path in files:
        if path.name in state:
            print(f"  {path.name}: ya enviado ({state[path.name]['batch_id']})")
            continue
        with open(path, encoding="utf-8") as fh:
            requests = [json.loads(line) for line in fh]
        batch = client.messages.batches.create(requests=requests)
        state[path.name] = {"batch_id": batch.id, "n": len(requests), "downloaded": False}
        save_state(state)  # persistir tras cada envío para poder reanudar
        print(f"  {path.name}: {batch.id} ({len(requests):,} solicitudes)")


def cmd_collect(_args) -> None:
    import anthropic

    client = anthropic.Anthropic()
    state = load_state()
    if not state:
        sys.exit("Sin lotes enviados; ejecuta primero `submit`.")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        pending = 0
        for name, info in state.items():
            if info["downloaded"]:
                continue
            batch = client.messages.batches.retrieve(info["batch_id"])
            c = batch.request_counts
            print(f"  {name} [{batch.processing_status}] ok={c.succeeded} err={c.errored} "
                  f"canc={c.canceled} exp={c.expired} proc={c.processing}")
            if batch.processing_status != "ended":
                pending += 1
                continue
            out = RESULTS_DIR / name.replace(".jsonl", "_results.jsonl")
            with open(out, "w", encoding="utf-8") as fh:
                # Los resultados llegan en cualquier orden: se indexan por custom_id.
                for res in client.messages.batches.results(info["batch_id"]):
                    fh.write(json.dumps(parse_result(res), ensure_ascii=False) + "\n")
            info["downloaded"] = True
            save_state(state)
        if not pending:
            break
        time.sleep(POLL_SECONDS)
    print("Descarga completa.")


def parse_result(res) -> dict:
    rec = {"gtin_key": res.custom_id, "status": res.result.type}
    if res.result.type != "succeeded":
        rec["error"] = str(getattr(res.result, "error", res.result.type))
        return rec
    msg = res.result.message
    tool = next((b for b in msg.content if b.type == "tool_use" and b.name == TOOL_NAME), None)
    if tool is None:
        rec["status"] = "no_tool_use"
        rec["error"] = f"stop_reason={msg.stop_reason}"
        return rec
    rec.update(tool.input)
    return rec


# --------------------------------------------------------------------------- #
# Resultados simulados (solo para probar la fusión sin gastar API)
# --------------------------------------------------------------------------- #
def simulate_results(sub: pd.DataFrame) -> None:
    import random

    rng = random.Random(0)
    SIM_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for old in SIM_RESULTS_DIR.glob("*.jsonl"):
        old.unlink()
    out = SIM_RESULTS_DIR / "simulado_results.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for gtin in sub[_KEY]:
            lvl = rng.choice(list(LEVEL_DIGITS))
            n = LEVEL_DIGITS[lvl]
            code = "".join(rng.choice("0123456789") for _ in range(n))
            rec = {"gtin_key": gtin, "status": "succeeded", "razonamiento": "simulado",
                   "nivel_asignado": lvl, "gpc_code": code,
                   "gpc_title": f"Título simulado {code}" if n else "",
                   "confidence_score": round(rng.random(), 2)}
            fh.write(json.dumps(rec) + "\n")
    print(f"  resultados simulados -> {out}")


# --------------------------------------------------------------------------- #
# 6. Fusión y exportación
# --------------------------------------------------------------------------- #
def load_results(results_dir: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(results_dir.glob("*.jsonl")):
        with open(path, encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh)
    if not rows:
        sys.exit(f"No hay resultados en {results_dir}/ (¿ejecutaste `collect`?)")
    res = pd.DataFrame(rows)
    for c in AI_COLS:
        if c not in res.columns:
            res[c] = pd.NA

    # Validación: el nivel debe coincidir con la longitud del código; si no,
    # se descarta la clasificación (mejor NO_MATCH que un código inventado).
    ok = res["status"].eq("succeeded")
    code = res["gpc_code"].fillna("").astype(str)
    expected = res["nivel_asignado"].map(LEVEL_DIGITS)
    bad = ok & (~code.str.fullmatch(r"\d*") | (code.str.len() != expected))
    if bad.any():
        print(f"  AVISO: {int(bad.sum()):,} respuestas inconsistentes -> NO_MATCH")
        res.loc[bad, ["nivel_asignado", "gpc_code", "gpc_title"]] = ["NO_MATCH", "", ""]
        res.loc[bad, "confidence_score"] = 0.0
    n_fail = int((~ok).sum())
    if n_fail:
        print(f"  AVISO: {n_fail:,} solicitudes sin resultado válido (quedarán vacías)")
    res = res[ok | bad]
    return res.drop_duplicates(subset="gtin_key", keep="last").rename(columns={"gtin_key": _KEY})[[_KEY, *AI_COLS]]


def write_xlsx(df: pd.DataFrame, path: Path) -> None:
    try:
        import xlsxwriter  # noqa: F401
        engine = "xlsxwriter"
    except ImportError:
        engine = "openpyxl"
    with pd.ExcelWriter(path, engine=engine) as xw:
        df.to_excel(xw, index=False)


def cmd_merge(args) -> None:
    print("[1/3] Reconstruyendo maestro y sub-dataframe")
    master = ingest()
    sub = dedup(master)

    if args.simulate:
        simulate_results(sub)
        results_dir = SIM_RESULTS_DIR
    else:
        results_dir = RESULTS_DIR
    results = load_results(results_dir)

    clash = [c for c in AI_COLS if c in master.columns]
    if clash:
        sys.exit(f"El maestro ya tiene columnas {clash}; renómbralas antes de fusionar.")

    print("[2/3] Fusión (how='left')")
    n0 = len(master)
    # a) resultados -> sub-dataframe, por GTIN
    sub = sub.merge(results, on=_KEY, how="left")
    # b) sub-dataframe -> maestro completo, por (Descripción, Marca): propaga el
    #    resultado de cada representante a todos sus duplicados.
    merged = master.merge(sub[[COL_DESC, COL_MARCA, *AI_COLS]], on=[COL_DESC, COL_MARCA], how="left")
    assert len(merged) == n0, "La fusión alteró el número de filas"
    cobertura = merged["nivel_asignado"].notna().mean()
    print(f"  filas con clasificación: {cobertura:.1%}")
    print(merged["nivel_asignado"].value_counts(dropna=False).to_string())

    print("[3/3] Exportando")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    original_cols = [c for c in master.columns if c not in (_SRC, _KEY)]
    final_cols = original_cols + AI_COLS  # columnas IA al final

    csv_path = OUTPUT_DIR / "gpc_consolidado.csv"
    merged[final_cols].to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  {csv_path}")

    for src, part in merged.groupby(_SRC, sort=False):
        part = part[final_cols]
        for i, start in enumerate(range(0, len(part), EXCEL_MAX_ROWS), start=1):
            suffix = "" if len(part) <= EXCEL_MAX_ROWS else f"_p{i}"
            path = OUTPUT_DIR / f"clasificado_{src}{suffix}.xlsx"
            write_xlsx(part.iloc[start:start + EXCEL_MAX_ROWS], path)
            print(f"  {path}")


# --------------------------------------------------------------------------- #
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare", help="ingesta + desduplicación + .jsonl").set_defaults(fn=cmd_prepare)
    sub.add_parser("submit", help="enviar lotes a la Batch API").set_defaults(fn=cmd_submit)
    sub.add_parser("collect", help="esperar y descargar resultados").set_defaults(fn=cmd_collect)
    m = sub.add_parser("merge", help="fusionar y exportar")
    m.add_argument("--simulate", action="store_true", help="usar resultados sintéticos (sin API)")
    m.set_defaults(fn=cmd_merge)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
