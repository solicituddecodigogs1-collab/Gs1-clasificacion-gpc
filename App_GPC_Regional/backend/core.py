#!/usr/bin/env python3
"""Lógica compartida del pipeline de clasificación GPC, sin interfaz.

Reutiliza lib/submit_batches.py del repo principal (GpcCatalog, el system
prompt, la construcción de prompts) en vez de reescribirla. Esta capa solo
orquesta: arma los requests del batch, estima costo, fusiona resultados.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
ROOT = APP_DIR.parent
PROYECTOS_DIR = APP_DIR / ".proyectos"
PROYECTOS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "lib"))
import submit_batches as sb  # noqa: E402

MODEL_HAIKU = sb.MODEL
MODEL_SONNET = "claude-sonnet-5-5"
MAX_TOKENS = sb.MAX_TOKENS

_catalog: sb.GpcCatalog | None = None


def get_catalog() -> sb.GpcCatalog:
    global _catalog
    if _catalog is None:
        _catalog = sb.GpcCatalog(ROOT / sb.CATALOG_FILE)
    return _catalog


def proyecto_dir(codigo: str) -> Path:
    d = PROYECTOS_DIR / codigo
    d.mkdir(parents=True, exist_ok=True)
    return d


def cargar_estado(codigo: str) -> dict:
    p = proyecto_dir(codigo) / "estado.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"paso": "subir", "pais": None, "notas_jerga": "", "mapeo": {}}


def guardar_estado(codigo: str, estado: dict) -> None:
    (proyecto_dir(codigo) / "estado.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2)
    )


def system_prompt_para(pais: str, notas_jerga: str) -> str:
    base = sb.SYSTEM_PROMPT.replace(
        "Eres un clasificador de productos bajo el estándar Global Product Classification (GPC) de GS1.",
        f"Eres un clasificador de productos bajo el estándar Global Product Classification (GPC) "
        f"de GS1, trabajando para GS1 {pais}.",
    )
    if notas_jerga.strip():
        base += (
            f"\n\nConvenciones locales de {pais} a tener en cuenta al leer las descripciones "
            f"de producto (abreviaturas, jerga, formato típico del catálogo de esta MO):\n"
            f"{notas_jerga.strip()}\n"
        )
    return base


def construir_requests(df: pd.DataFrame, marca_col: str, desc_col: str, model: str, system_prompt: str):
    """Arma los requests del batch (uno por producto único) y el mapa
    custom_id -> indices de df (para reaplicar el resultado a todas las
    filas que comparten esa combinación marca+descripción)."""
    catalog = get_catalog()
    vistos: dict[str, dict] = {}
    custom_id_a_indices: dict[str, list[int]] = {}
    for idx, row in df.iterrows():
        marca_val, desc_val = row[marca_col], row[desc_col]
        cid = sb.make_custom_id(marca_val, desc_val)
        custom_id_a_indices.setdefault(cid, []).append(int(idx))
        if cid in vistos:
            continue
        q = sb.query_text(marca_val, desc_val, None, None)
        candidates = catalog.build_candidates(q)
        user_content = sb.build_user_content(marca_val, desc_val, candidates)
        vistos[cid] = {
            "custom_id": cid,
            "params": {
                "model": model,
                "max_tokens": MAX_TOKENS,
                "system": [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                "messages": [{"role": "user", "content": user_content}],
            },
        }
    return list(vistos.values()), custom_id_a_indices


def estimar_costo(n_unicos: int, n_total: int, model: str) -> dict:
    precios = {
        MODEL_HAIKU: (0.50, 2.50),
        MODEL_SONNET: (1.50, 7.50),
    }
    in_price, out_price = precios.get(model, (0.50, 2.50))
    avg_in_tokens = 1150  # medido empíricamente (ver Paquete_Replicacion_MO/INFORME_TECNICO.md)
    out_tokens = 12
    total_in = n_unicos * avg_in_tokens
    total_out = n_unicos * out_tokens
    costo = total_in / 1e6 * in_price + total_out / 1e6 * out_price
    return {"n_total": n_total, "n_unicos": n_unicos, "costo_estimado_usd": round(costo, 2)}


def fusionar_resultados(df: pd.DataFrame, mapa: dict[str, list[int]], resultados: dict[str, dict]) -> pd.DataFrame:
    """Aplica los resultados del batch (custom_id -> {gpc_code, confidence_score})
    sobre las filas correspondientes de df. Candado ground-truth: un código
    que no está en el catálogo oficial nunca se acepta."""
    catalog = get_catalog()
    for cid, indices in mapa.items():
        r = resultados.get(cid)
        if not r or str(r.get("gpc_code")) == "NO_MATCH":
            continue
        code = str(r["gpc_code"])
        info = catalog.by_code.get(code)
        if not info:
            continue
        for idx in indices:
            df.at[idx, "gpc_code"] = code
            df.at[idx, "nivel_asignado"] = info["nivel"]
            df.at[idx, "gpc_description"] = info["titulo"]
            df.at[idx, "confidence_score"] = r.get("confidence_score")
    return df


def parse_batch_results(client, batch_id: str) -> dict[str, dict]:
    resultados: dict[str, dict] = {}
    for entry in client.messages.batches.results(batch_id):
        if entry.result.type == "succeeded":
            text = next((b.text for b in entry.result.message.content if b.type == "text"), None)
            try:
                resultados[entry.custom_id] = json.loads(text)
            except Exception:
                resultados[entry.custom_id] = {"gpc_code": "NO_MATCH", "confidence_score": 0}
        else:
            resultados[entry.custom_id] = {"gpc_code": "NO_MATCH", "confidence_score": 0}
    return resultados
