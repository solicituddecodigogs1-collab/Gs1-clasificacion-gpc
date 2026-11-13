#!/usr/bin/env python3
"""App de clasificación GPC para las MO de GS1 en América Latina.

Cada MO usa su propia API key de Anthropic (nunca se guarda en disco,
solo vive en memoria durante la sesión del navegador). El resto del
estado del proyecto (país, mapeo de columnas, catálogo subido, ids de
los batches) se guarda en .proyectos/<codigo>/ para poder cerrar el
navegador y volver más tarde -- los batches de la API pueden tardar
horas.

Reutiliza la logica ya probada de lib/submit_batches.py (GpcCatalog,
el system prompt, la construccion del prompt de usuario) en vez de
reescribirla.
"""
from __future__ import annotations

import json
import secrets
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
PROYECTOS_DIR = APP_DIR / ".proyectos"
PROYECTOS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "lib"))
import submit_batches as sb  # noqa: E402

from paises import ORDEN_PAISES, PAISES  # noqa: E402

MODEL_HAIKU = sb.MODEL
MODEL_SONNET = "claude-sonnet-5-5"
MAX_TOKENS = sb.MAX_TOKENS

st.set_page_config(page_title="Clasificación GPC — GS1 LatAm", layout="wide")


# --------------------------------------------------------------- utilidades


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
    (proyecto_dir(codigo) / "estado.json").write_text(json.dumps(estado, ensure_ascii=False, indent=2))


@st.cache_resource
def get_catalog() -> sb.GpcCatalog:
    return sb.GpcCatalog(ROOT / sb.CATALOG_FILE)


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
    """A partir de un df con columnas marca/descripcion, arma los requests
    del batch (uno por producto único) y el mapa custom_id -> indices de df
    (para poder reaplicar el resultado a todas las filas que comparten esa
    combinacion marca+descripcion)."""
    catalog = get_catalog()
    vistos: dict[str, dict] = {}
    custom_id_a_indices: dict[str, list[int]] = {}
    for idx, row in df.iterrows():
        marca_val, desc_val = row[marca_col], row[desc_col]
        cid = sb.make_custom_id(marca_val, desc_val)
        custom_id_a_indices.setdefault(cid, []).append(idx)
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
        sb.MODEL: (0.50, 2.50),
        MODEL_SONNET: (1.50, 7.50),
    }
    in_price, out_price = precios.get(model, (0.50, 2.50))
    avg_in_tokens = 1150  # medido empíricamente sobre catálogos reales (ver Paquete_Replicacion_MO)
    out_tokens = 12
    total_in = n_unicos * avg_in_tokens
    total_out = n_unicos * out_tokens
    costo = total_in / 1e6 * in_price + total_out / 1e6 * out_price
    return {
        "n_total": n_total,
        "n_unicos": n_unicos,
        "costo_estimado_usd": round(costo, 2),
    }


# ------------------------------------------------------------------- UI


st.title("📦 Clasificación automática GPC")
st.caption("Construido por GS1 Venezuela — adaptado para las MO de la región. Cada MO usa su propia API key.")

with st.sidebar:
    st.header("1. Tu proyecto")
    codigo_input = st.text_input(
        "Código de proyecto (déjalo vacío para crear uno nuevo)",
        value=st.session_state.get("codigo", ""),
    )
    if st.button("Crear proyecto nuevo") or (not codigo_input and "codigo" not in st.session_state):
        if not codigo_input:
            codigo_input = secrets.token_hex(3).upper()
    if codigo_input:
        st.session_state["codigo"] = codigo_input
        st.success(f"Código de proyecto: **{codigo_input}** — guárdalo para volver más tarde.")

    st.divider()
    st.header("2. País")
    estado = cargar_estado(st.session_state.get("codigo", "")) if st.session_state.get("codigo") else {
        "paso": "subir", "pais": None, "notas_jerga": "", "mapeo": {}
    }
    pais = st.selectbox("Selecciona tu MO", ORDEN_PAISES, index=ORDEN_PAISES.index(estado["pais"]) if estado.get("pais") in ORDEN_PAISES else 0)
    info_pais = PAISES[pais]
    st.caption(
        f"Prefijo GS1 de referencia: **{info_pais.prefijo_gs1}**"
        f"{' (confirmado)' if info_pais.prefijo_verificado else ' (revisar contra gs1.org/prefixes)'}"
        f"  ·  Identificador fiscal: **{info_pais.id_fiscal}**"
    )
    notas_jerga = st.text_area(
        "Jerga / abreviaturas locales de tu catálogo (opcional, pero recomendado)",
        value=estado.get("notas_jerga", ""),
        placeholder="Ej.: CAB.=caballero, M/C=manga corta, PQ.=paquete...",
        height=100,
    )

    st.divider()
    st.header("3. Tu API key de Anthropic")
    api_key = st.text_input("API key (solo vive en esta sesión, nunca se guarda)", type="password")
    st.caption("Obtén una en console.anthropic.com. El costo lo factura Anthropic directo a tu cuenta.")

if not st.session_state.get("codigo"):
    st.info("Crea o carga un código de proyecto en la barra lateral para empezar.")
    st.stop()

codigo = st.session_state["codigo"]
estado = cargar_estado(codigo)
estado["pais"] = pais
estado["notas_jerga"] = notas_jerga
guardar_estado(codigo, estado)
pdir = proyecto_dir(codigo)

st.header(f"Proyecto {codigo} — GS1 {pais}")

paso = estado.get("paso", "subir")

# ----------------------------------------------------------- paso: subir
if paso == "subir":
    st.subheader("Paso 1 — Sube tu catálogo")
    archivo = st.file_uploader("Archivo .xlsx o .csv con tu catálogo de productos", type=["xlsx", "csv"])
    if archivo is not None:
        df = pd.read_excel(archivo) if archivo.name.endswith(".xlsx") else pd.read_csv(archivo)
        st.write(f"{len(df)} filas, {len(df.columns)} columnas.")
        st.dataframe(df.head(10), use_container_width=True)

        cols = list(df.columns)
        c1, c2, c3 = st.columns(3)
        marca_col = c1.selectbox("Columna de marca/empresa", cols)
        desc_col = c2.selectbox("Columna de descripción de producto", cols, index=min(1, len(cols) - 1))
        id_col = c3.selectbox("Columna de identificador único (GTIN/EAN/código)", cols, index=min(2, len(cols) - 1))

        if st.button("Guardar mapeo y continuar →", type="primary"):
            df.to_parquet(pdir / "catalogo.parquet")
            estado["mapeo"] = {"marca": marca_col, "descripcion": desc_col, "id": id_col}
            estado["paso"] = "estimar"
            guardar_estado(codigo, estado)
            st.rerun()

# --------------------------------------------------------- paso: estimar
elif paso == "estimar":
    st.subheader("Paso 2 — Estimación de costo (pasada 1, Haiku)")
    df = pd.read_parquet(pdir / "catalogo.parquet")
    mapeo = estado["mapeo"]
    n_unicos = df.apply(lambda r: sb.make_custom_id(r[mapeo["marca"]], r[mapeo["descripcion"]]), axis=1).nunique()
    est = estimar_costo(n_unicos, len(df), MODEL_HAIKU)
    c1, c2, c3 = st.columns(3)
    c1.metric("Filas totales", est["n_total"])
    c2.metric("Productos únicos (tras deduplicar)", est["n_unicos"])
    c3.metric("Costo estimado pasada 1", f"${est['costo_estimado_usd']} USD")
    st.caption(
        "Estimación basada en tokens promedio medidos sobre catálogos reales (ver "
        "Paquete_Replicacion_MO/INFORME_TECNICO.md). El costo real puede ser menor por el "
        "descuento de caché del system prompt. La pasada 2 (rescate Sonnet) se estima aparte, "
        "después de ver cuántas filas quedan en NO_MATCH."
    )
    col_a, col_b = st.columns(2)
    if col_a.button("← Volver"):
        estado["paso"] = "subir"
        guardar_estado(codigo, estado)
        st.rerun()
    if col_b.button("Confirmar y enviar pasada 1 →", type="primary", disabled=not api_key):
        if not api_key:
            st.error("Pega tu API key en la barra lateral primero.")
        else:
            with st.spinner("Armando y enviando el lote a la Batch API..."):
                system_prompt = system_prompt_para(pais, notas_jerga)
                requests, mapa = construir_requests(df, mapeo["marca"], mapeo["descripcion"], MODEL_HAIKU, system_prompt)
                (pdir / "mapa_haiku.json").write_text(json.dumps(mapa, ensure_ascii=False))
                (pdir / "system_prompt.txt").write_text(system_prompt, encoding="utf-8")
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                batch = client.messages.batches.create(requests=requests)
                estado["batch_haiku_id"] = batch.id
                estado["paso"] = "esperar_haiku"
                guardar_estado(codigo, estado)
            st.rerun()

# ---------------------------------------------------- paso: esperar_haiku
elif paso == "esperar_haiku":
    st.subheader("Paso 3 — Pasada 1 en curso (Claude Haiku)")
    st.code(estado["batch_haiku_id"], language=None)
    st.caption("Los batches pueden tardar desde minutos hasta 24 horas. Puedes cerrar esta pestaña y volver luego con tu código de proyecto.")
    if st.button("Verificar estado", type="primary", disabled=not api_key):
        if not api_key:
            st.error("Pega tu API key en la barra lateral para consultar el estado.")
        else:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            batch = client.messages.batches.retrieve(estado["batch_haiku_id"])
            st.write(f"Estado: **{batch.processing_status}**")
            st.json(batch.request_counts.model_dump() if hasattr(batch, "request_counts") else {})
            if batch.processing_status == "ended":
                estado["paso"] = "procesar_haiku"
                guardar_estado(codigo, estado)
                st.rerun()

# --------------------------------------------------- paso: procesar_haiku
elif paso == "procesar_haiku":
    st.subheader("Paso 4 — Procesando resultados de la pasada 1")
    if st.button("Descargar y fusionar resultados", type="primary", disabled=not api_key):
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        df = pd.read_parquet(pdir / "catalogo.parquet")
        mapeo = estado["mapeo"]
        mapa = json.loads((pdir / "mapa_haiku.json").read_text())

        resultados: dict[str, dict] = {}
        for entry in client.messages.batches.results(estado["batch_haiku_id"]):
            if entry.result.type == "succeeded":
                text = next((b.text for b in entry.result.message.content if b.type == "text"), None)
                try:
                    resultados[entry.custom_id] = json.loads(text)
                except Exception:
                    resultados[entry.custom_id] = {"gpc_code": "NO_MATCH", "confidence_score": 0}
            else:
                resultados[entry.custom_id] = {"gpc_code": "NO_MATCH", "confidence_score": 0}

        catalog = get_catalog()
        df["gpc_code"] = "NO_MATCH"
        df["nivel_asignado"] = "NO_MATCH"
        df["gpc_description"] = "Sin coincidencia válida"
        df["confidence_score"] = pd.NA
        for cid, indices in mapa.items():
            r = resultados.get(cid)
            if not r or str(r.get("gpc_code")) == "NO_MATCH":
                continue
            code = str(r["gpc_code"])
            info = catalog.by_code.get(code)
            if not info:
                continue  # candado ground-truth: nunca un codigo que no este en el catalogo
            for idx in indices:
                df.at[idx, "gpc_code"] = code
                df.at[idx, "nivel_asignado"] = info["nivel"]
                df.at[idx, "gpc_description"] = info["titulo"]
                df.at[idx, "confidence_score"] = r.get("confidence_score")

        df.to_parquet(pdir / "catalogo_post_haiku.parquet")
        n_nomatch = int((df["nivel_asignado"] == "NO_MATCH").sum())
        st.success(f"Pasada 1 fusionada. {len(df) - n_nomatch} asignados, {n_nomatch} siguen en NO_MATCH.")
        estado["n_nomatch_haiku"] = n_nomatch
        estado["paso"] = "ofrecer_rescate" if n_nomatch > 0 else "final"
        guardar_estado(codigo, estado)
        st.rerun()

# -------------------------------------------------- paso: ofrecer_rescate
elif paso == "ofrecer_rescate":
    st.subheader("Paso 5 — Pasada 2: rescate con Claude Sonnet")
    n_nomatch = estado["n_nomatch_haiku"]
    est = estimar_costo(n_nomatch, n_nomatch, MODEL_SONNET)
    st.metric("Filas a reintentar con Sonnet", n_nomatch)
    st.metric("Costo estimado pasada 2", f"${est['costo_estimado_usd']} USD")
    col_a, col_b = st.columns(2)
    if col_a.button("Saltar rescate y terminar aquí"):
        estado["paso"] = "final"
        guardar_estado(codigo, estado)
        st.rerun()
    if col_b.button("Enviar pasada 2 (Sonnet) →", type="primary", disabled=not api_key):
        df = pd.read_parquet(pdir / "catalogo_post_haiku.parquet")
        mapeo = estado["mapeo"]
        nomatch_df = df[df["nivel_asignado"] == "NO_MATCH"]
        with st.spinner("Enviando lote de rescate..."):
            system_prompt = (pdir / "system_prompt.txt").read_text(encoding="utf-8")
            requests, mapa = construir_requests(nomatch_df, mapeo["marca"], mapeo["descripcion"], MODEL_SONNET, system_prompt)
            (pdir / "mapa_sonnet.json").write_text(json.dumps(mapa, ensure_ascii=False))
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            batch = client.messages.batches.create(requests=requests)
            estado["batch_sonnet_id"] = batch.id
            estado["paso"] = "esperar_sonnet"
            guardar_estado(codigo, estado)
        st.rerun()

# --------------------------------------------------- paso: esperar_sonnet
elif paso == "esperar_sonnet":
    st.subheader("Paso 6 — Pasada 2 en curso (Claude Sonnet)")
    st.code(estado["batch_sonnet_id"], language=None)
    if st.button("Verificar estado", type="primary", disabled=not api_key):
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        batch = client.messages.batches.retrieve(estado["batch_sonnet_id"])
        st.write(f"Estado: **{batch.processing_status}**")
        if batch.processing_status == "ended":
            estado["paso"] = "procesar_sonnet"
            guardar_estado(codigo, estado)
            st.rerun()

# --------------------------------------------------- paso: procesar_sonnet
elif paso == "procesar_sonnet":
    st.subheader("Paso 7 — Procesando resultados del rescate")
    if st.button("Descargar y fusionar", type="primary", disabled=not api_key):
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        df = pd.read_parquet(pdir / "catalogo_post_haiku.parquet")
        mapa = json.loads((pdir / "mapa_sonnet.json").read_text())
        catalog = get_catalog()

        resultados: dict[str, dict] = {}
        for entry in client.messages.batches.results(estado["batch_sonnet_id"]):
            if entry.result.type == "succeeded":
                text = next((b.text for b in entry.result.message.content if b.type == "text"), None)
                try:
                    resultados[entry.custom_id] = json.loads(text)
                except Exception:
                    resultados[entry.custom_id] = {"gpc_code": "NO_MATCH", "confidence_score": 0}
            else:
                resultados[entry.custom_id] = {"gpc_code": "NO_MATCH", "confidence_score": 0}

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

        df.to_parquet(pdir / "catalogo_final.parquet")
        estado["paso"] = "final"
        guardar_estado(codigo, estado)
        st.rerun()

# ------------------------------------------------------------- paso: final
if paso == "final":
    st.subheader("✅ Terminado")
    final_path = pdir / "catalogo_final.parquet"
    if not final_path.exists():
        final_path = pdir / "catalogo_post_haiku.parquet"
    df = pd.read_parquet(final_path)
    nivel = df["nivel_asignado"].astype(str)
    n_asignados = int((nivel != "NO_MATCH").sum())
    n_nomatch = int((nivel == "NO_MATCH").sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("Asignados", n_asignados, f"{100*n_asignados/len(df):.1f}%")
    c3.metric("NO_MATCH", n_nomatch, f"{100*n_nomatch/len(df):.1f}%")

    asignados = df[nivel != "NO_MATCH"]
    nomatch = df[nivel == "NO_MATCH"]

    import io
    for nombre, data in [("Final_completo.xlsx", df), ("Asignados.xlsx", asignados), ("NoMatch.xlsx", nomatch)]:
        buf = io.BytesIO()
        data.to_excel(buf, index=False)
        st.download_button(f"⬇️ Descargar {nombre}", buf.getvalue(), file_name=nombre)

    if st.button("Empezar un proyecto nuevo"):
        del st.session_state["codigo"]
        st.rerun()
