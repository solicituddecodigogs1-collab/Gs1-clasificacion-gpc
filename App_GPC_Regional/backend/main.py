#!/usr/bin/env python3
"""API FastAPI para la app de clasificación GPC — GS1 LatAm.

La API key de Anthropic viaja en el header X-Api-Key de cada request que
la necesita y NUNCA se escribe a disco ni se registra en logs.
"""
from __future__ import annotations

import io
import secrets
import traceback

import anthropic
import pandas as pd
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import core
from .paises import ORDEN_PAISES, PAISES

app = FastAPI(title="Clasificación GPC — GS1 LatAm")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.exception_handler(Exception)
async def manejar_error_inesperado(request: Request, exc: Exception):
    """Red de seguridad: cualquier excepción que no se haya traducido ya a un
    HTTPException con mensaje claro llega aquí. Sin esto, FastAPI devuelve
    un "Internal Server Error" genérico sin ninguna pista — con esto, la
    persona que usa la app ve el tipo y mensaje real del error, y queda un
    traceback completo en logs/errores.log para poder diagnosticarlo."""
    traceback.print_exc()
    try:
        log_path = core.APP_DIR / "logs"
        log_path.mkdir(exist_ok=True)
        with (log_path / "errores.log").open("a", encoding="utf-8") as f:
            f.write(f"\n--- {request.method} {request.url.path} ---\n")
            f.write(traceback.format_exc())
    except Exception:
        pass
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error inesperado ({type(exc).__name__}): {exc}"},
    )


def client_de(api_key: str | None) -> anthropic.Anthropic:
    if not api_key:
        raise HTTPException(401, "Falta la API key (header X-Api-Key).")
    return anthropic.Anthropic(api_key=api_key)


def llamar_anthropic(fn, *args, **kwargs):
    """Ejecuta una llamada al SDK de Anthropic traduciendo los errores más
    comunes a un mensaje en español entendible, en vez de dejar que se
    conviertan en un "Internal Server Error" genérico sin detalle."""
    try:
        return fn(*args, **kwargs)
    except anthropic.AuthenticationError:
        raise HTTPException(401, "La API key no es válida. Revisa que la copiaste completa y sin espacios.")
    except anthropic.PermissionDeniedError:
        raise HTTPException(403, "La cuenta de Anthropic no tiene permiso para usar la Batch API con esta key.")
    except anthropic.RateLimitError:
        raise HTTPException(429, "Se alcanzó el límite de uso de la cuenta de Anthropic. Intenta de nuevo en unos minutos.")
    except anthropic.BadRequestError as e:
        raise HTTPException(400, f"Anthropic rechazó la solicitud: {e.message}")
    except anthropic.APIStatusError as e:
        if e.status_code == 400 and "credit balance" in str(e).lower():
            raise HTTPException(402, "La cuenta de Anthropic no tiene saldo suficiente. Agrega crédito en console.anthropic.com y vuelve a intentar.")
        raise HTTPException(e.status_code, f"Error de Anthropic: {e.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(503, "No se pudo conectar con Anthropic. Revisa tu conexión a internet e intenta de nuevo.")


def requiere_proyecto(codigo: str) -> dict:
    d = core.proyecto_dir(codigo)
    if not (d / "estado.json").exists():
        raise HTTPException(404, f"No existe el proyecto {codigo}.")
    return core.cargar_estado(codigo)


# ------------------------------------------------------------------ países
@app.get("/api/paises")
def listar_paises():
    return [
        {
            "nombre": p,
            "prefijo_gs1": PAISES[p].prefijo_gs1,
            "prefijo_verificado": PAISES[p].prefijo_verificado,
            "id_fiscal": PAISES[p].id_fiscal,
            "jerga_sugerida": PAISES[p].jerga_sugerida,
        }
        for p in ORDEN_PAISES
    ]


# --------------------------------------------------------------- proyectos
@app.post("/api/proyectos")
def crear_proyecto():
    codigo = secrets.token_hex(3).upper()
    core.guardar_estado(codigo, core.cargar_estado(codigo))
    return {"codigo": codigo}


@app.get("/api/proyectos/{codigo}")
def obtener_proyecto(codigo: str):
    estado = requiere_proyecto(codigo)
    catalogo_path = core.proyecto_dir(codigo) / "catalogo.parquet"
    if catalogo_path.exists():
        df = pd.read_parquet(catalogo_path)
        estado["columnas"] = list(df.columns)
        estado["preview"] = df.head(8).fillna("").astype(str).to_dict(orient="records")
    return estado


class PaisInput(BaseModel):
    pais: str
    notas_jerga: str = ""


@app.post("/api/proyectos/{codigo}/pais")
def guardar_pais(codigo: str, body: PaisInput):
    if body.pais not in PAISES:
        raise HTTPException(400, "País no reconocido.")
    estado = core.cargar_estado(codigo)
    estado["pais"] = body.pais
    estado["notas_jerga"] = body.notas_jerga
    estado["paso"] = "subir"
    core.guardar_estado(codigo, estado)
    return estado


@app.post("/api/proyectos/{codigo}/catalogo")
async def subir_catalogo(codigo: str, archivo: UploadFile = File(...)):
    estado = requiere_proyecto(codigo)
    contenido = await archivo.read()
    buf = io.BytesIO(contenido)
    df = pd.read_excel(buf) if archivo.filename.endswith(".xlsx") else pd.read_csv(buf)
    df = core.normalizar_columnas_texto(df)
    df.to_parquet(core.proyecto_dir(codigo) / "catalogo.parquet")
    estado["paso"] = "mapear"
    estado["n_filas"] = len(df)
    core.guardar_estado(codigo, estado)
    return {
        "columnas": list(df.columns),
        "n_filas": len(df),
        "preview": df.head(8).fillna("").astype(str).to_dict(orient="records"),
    }


class MapeoInput(BaseModel):
    marca: str
    descripcion: str
    identificador: str


@app.post("/api/proyectos/{codigo}/mapeo")
def guardar_mapeo(codigo: str, body: MapeoInput):
    estado = requiere_proyecto(codigo)
    df = pd.read_parquet(core.proyecto_dir(codigo) / "catalogo.parquet")
    estado["mapeo"] = {"marca": body.marca, "descripcion": body.descripcion, "id": body.identificador}
    n_unicos = df.apply(lambda r: core.sb.make_custom_id(r[body.marca], r[body.descripcion]), axis=1).nunique()
    est = core.estimar_costo(n_unicos, len(df), core.MODEL_HAIKU)
    estado["estimacion_haiku"] = est
    estado["paso"] = "estimar"
    core.guardar_estado(codigo, estado)
    return est


@app.post("/api/proyectos/{codigo}/batch/haiku")
def enviar_batch_haiku(codigo: str, x_api_key: str = Header(None)):
    client = client_de(x_api_key)
    estado = requiere_proyecto(codigo)
    pdir = core.proyecto_dir(codigo)
    df = pd.read_parquet(pdir / "catalogo.parquet")
    mapeo = estado["mapeo"]
    system_prompt = core.system_prompt_para(estado["pais"], estado.get("notas_jerga", ""))
    requests, mapa = core.construir_requests(df, mapeo["marca"], mapeo["descripcion"], core.MODEL_HAIKU, system_prompt)
    (pdir / "mapa_haiku.json").write_text(__import__("json").dumps(mapa, ensure_ascii=False), encoding="utf-8")
    (pdir / "system_prompt.txt").write_text(system_prompt, encoding="utf-8")
    batch = llamar_anthropic(client.messages.batches.create, requests=requests)
    estado["batch_haiku_id"] = batch.id
    estado["paso"] = "esperar_haiku"
    core.guardar_estado(codigo, estado)
    return {"batch_id": batch.id, "n_requests": len(requests)}


@app.get("/api/proyectos/{codigo}/batch/haiku/estado")
def estado_batch_haiku(codigo: str, x_api_key: str = Header(None)):
    client = client_de(x_api_key)
    estado = requiere_proyecto(codigo)
    batch = llamar_anthropic(client.messages.batches.retrieve, estado["batch_haiku_id"])
    return {
        "status": batch.processing_status,
        "counts": batch.request_counts.model_dump() if hasattr(batch, "request_counts") else {},
    }


@app.post("/api/proyectos/{codigo}/batch/haiku/procesar")
def procesar_batch_haiku(codigo: str, x_api_key: str = Header(None)):
    client = client_de(x_api_key)
    estado = requiere_proyecto(codigo)
    pdir = core.proyecto_dir(codigo)
    import json as _json

    df = pd.read_parquet(pdir / "catalogo.parquet")
    mapa = _json.loads((pdir / "mapa_haiku.json").read_text(encoding="utf-8"))
    resultados = llamar_anthropic(core.parse_batch_results, client, estado["batch_haiku_id"])

    df["gpc_code"] = "NO_MATCH"
    df["nivel_asignado"] = "NO_MATCH"
    df["gpc_description"] = "Sin coincidencia válida"
    df["confidence_score"] = pd.NA
    df = core.fusionar_resultados(df, mapa, resultados)
    df.to_parquet(pdir / "catalogo_post_haiku.parquet")

    n_nomatch = int((df["nivel_asignado"] == "NO_MATCH").sum())
    estado["n_nomatch_haiku"] = n_nomatch
    estado["n_asignados_haiku"] = len(df) - n_nomatch
    if n_nomatch > 0:
        estimacion = core.estimar_costo(n_nomatch, n_nomatch, core.MODEL_SONNET)
        estado["estimacion_sonnet"] = estimacion
        estado["paso"] = "ofrecer_rescate"
    else:
        estado["paso"] = "final"
    core.guardar_estado(codigo, estado)
    return estado


@app.post("/api/proyectos/{codigo}/batch/sonnet")
def enviar_batch_sonnet(codigo: str, x_api_key: str = Header(None)):
    client = client_de(x_api_key)
    estado = requiere_proyecto(codigo)
    pdir = core.proyecto_dir(codigo)
    df = pd.read_parquet(pdir / "catalogo_post_haiku.parquet")
    mapeo = estado["mapeo"]
    nomatch_df = df[df["nivel_asignado"] == "NO_MATCH"]
    system_prompt = (pdir / "system_prompt.txt").read_text(encoding="utf-8")
    requests, mapa = core.construir_requests(
        nomatch_df, mapeo["marca"], mapeo["descripcion"], core.MODEL_SONNET, system_prompt
    )
    (pdir / "mapa_sonnet.json").write_text(__import__("json").dumps(mapa, ensure_ascii=False), encoding="utf-8")
    batch = llamar_anthropic(client.messages.batches.create, requests=requests)
    estado["batch_sonnet_id"] = batch.id
    estado["paso"] = "esperar_sonnet"
    core.guardar_estado(codigo, estado)
    return {"batch_id": batch.id, "n_requests": len(requests)}


@app.post("/api/proyectos/{codigo}/saltar_rescate")
def saltar_rescate(codigo: str):
    estado = requiere_proyecto(codigo)
    estado["paso"] = "final"
    core.guardar_estado(codigo, estado)
    return estado


@app.get("/api/proyectos/{codigo}/batch/sonnet/estado")
def estado_batch_sonnet(codigo: str, x_api_key: str = Header(None)):
    client = client_de(x_api_key)
    estado = requiere_proyecto(codigo)
    batch = llamar_anthropic(client.messages.batches.retrieve, estado["batch_sonnet_id"])
    return {
        "status": batch.processing_status,
        "counts": batch.request_counts.model_dump() if hasattr(batch, "request_counts") else {},
    }


@app.post("/api/proyectos/{codigo}/batch/sonnet/procesar")
def procesar_batch_sonnet(codigo: str, x_api_key: str = Header(None)):
    client = client_de(x_api_key)
    estado = requiere_proyecto(codigo)
    pdir = core.proyecto_dir(codigo)
    import json as _json

    df = pd.read_parquet(pdir / "catalogo_post_haiku.parquet")
    mapa = _json.loads((pdir / "mapa_sonnet.json").read_text(encoding="utf-8"))
    resultados = llamar_anthropic(core.parse_batch_results, client, estado["batch_sonnet_id"])
    df = core.fusionar_resultados(df, mapa, resultados)
    df.to_parquet(pdir / "catalogo_final.parquet")
    estado["paso"] = "final"
    core.guardar_estado(codigo, estado)
    return estado


@app.get("/api/proyectos/{codigo}/resumen")
def resumen_final(codigo: str):
    estado = requiere_proyecto(codigo)
    pdir = core.proyecto_dir(codigo)
    final_path = pdir / "catalogo_final.parquet"
    if not final_path.exists():
        final_path = pdir / "catalogo_post_haiku.parquet"
    df = pd.read_parquet(final_path)
    nivel = df["nivel_asignado"].astype(str)
    n_asignados = int((nivel != "NO_MATCH").sum())
    n_nomatch = int((nivel == "NO_MATCH").sum())
    return {"total": len(df), "asignados": n_asignados, "no_match": n_nomatch}


@app.get("/api/proyectos/{codigo}/descargar/{tipo}")
def descargar(codigo: str, tipo: str):
    requiere_proyecto(codigo)
    pdir = core.proyecto_dir(codigo)
    final_path = pdir / "catalogo_final.parquet"
    if not final_path.exists():
        final_path = pdir / "catalogo_post_haiku.parquet"
    df = pd.read_parquet(final_path)
    nivel = df["nivel_asignado"].astype(str)
    if tipo == "completo":
        data, nombre = df, "Final_completo.xlsx"
    elif tipo == "asignados":
        data, nombre = df[nivel != "NO_MATCH"], "Asignados.xlsx"
    elif tipo == "nomatch":
        data, nombre = df[nivel == "NO_MATCH"], "NoMatch.xlsx"
    else:
        raise HTTPException(400, "Tipo inválido.")
    buf = io.BytesIO()
    data.to_excel(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


# ------------------------------------------------------------- frontend
app.mount("/", StaticFiles(directory=str(core.APP_DIR / "frontend"), html=True), name="frontend")
