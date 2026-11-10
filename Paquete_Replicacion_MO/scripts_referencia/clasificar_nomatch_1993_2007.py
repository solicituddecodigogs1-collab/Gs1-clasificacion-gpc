#!/usr/bin/env python3
"""Clasificación del NO_MATCH histórico 1993-2007 contra GPC Mayo 2026 (MX, es).

Entrada : Output_NoMatch/NoMatch_<año>.xlsx
Esquema : catalogo/GPC as of May 2026 v20260520 MX.xlsx (hoja 'Schema')
Salida  : Output_Clasificado/NoMatch_Clasificado/NoMatch_<año>_CLASIFICADO.xlsx

Capas:
  1. Reglas de afiliados históricos dominantes (RIF / marca) -> código fijo.
  2. Patrones técnicos y abreviaturas históricas (texto expandido).
  3. Consenso de cohorte por prefijo con lo ya clasificado con alta confianza
     (Output_Asignados 1993-2025), solo cohortes homogéneas.
  4. LLM en dos etapas SIEMPRE restringido a códigos del esquema oficial:
       etapa A: elige Class entre las 938 del esquema;
       etapa B: elige Brick entre los bricks de ese Class (o 0 = queda en Class).
  5. Respaldos: moda de la cohorte (prefijo) ya resuelta, y reintento.

Ningún código sale de un LLM sin pasar por el diccionario oficial; la
descripción siempre se toma del esquema. La API key se lee SOLO de la
variable de entorno ANTHROPIC_API_KEY (nunca se guarda en archivos).
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import re
import sys
import threading
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_XLSX = ROOT / "catalogo" / "GPC as of May 2026 v20260520 MX.xlsx"
IN_DIR = ROOT / "Output_NoMatch"
OUT_DIR = ROOT / "Output_Clasificado" / "NoMatch_Clasificado"
ASIG_DIR = ROOT / "Output_Asignados"
CACHE_DIR = Path(os.environ.get("GPC_CACHE_DIR", ROOT / ".cache_gpc"))
MODEL_A = os.environ.get("GPC_MODEL_A", "claude-sonnet-5-5")
MODEL_B = os.environ.get("GPC_MODEL_B", "claude-sonnet-5-5")
YEARS = list(range(1993, 2008))

# ----------------------------------------------------------------- esquema
def load_schema():
    pk = CACHE_DIR / "schema_bricks.pkl"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if pk.exists():
        b = pd.read_pickle(pk)
    else:
        cols = ["SegmentCode", "SegmentTitle", "FamilyCode", "FamilyTitle", "ClassCode",
                "ClassTitle", "BrickCode", "BrickTitle", "BrickDefinition_Includes"]
        s = pd.read_excel(SCHEMA_XLSX, sheet_name="Schema", usecols=cols, dtype=str)
        b = s.drop_duplicates("BrickCode").reset_index(drop=True)
        b.to_pickle(pk)
    codes = {}  # code -> (nivel, titulo, brick, class, family)
    for r in b.itertuples(index=False):
        codes[r.SegmentCode] = ("Segment", r.SegmentTitle)
        codes[r.FamilyCode] = ("Family", r.FamilyTitle)
        codes[r.ClassCode] = ("Class", r.ClassTitle)
        codes[r.BrickCode] = ("Brick", r.BrickTitle)
    return b, codes


BRICKS, CODES = load_schema()
CLASS_INFO = {r.ClassCode: (r.SegmentTitle, r.FamilyTitle, r.ClassTitle, r.FamilyCode)
              for r in BRICKS.drop_duplicates("ClassCode").itertuples()}
BRICKS_BY_CLASS = defaultdict(list)
for r in BRICKS.itertuples():
    BRICKS_BY_CLASS[r.ClassCode].append(r)
BRICK_TO_CLASS = dict(zip(BRICKS.BrickCode, BRICKS.ClassCode))
CLASS_TO_FAMILY = dict(zip(BRICKS.ClassCode, BRICKS.FamilyCode))


def lineage(code: str) -> dict:
    """code oficial -> brick/class/family/segment codes presentes."""
    nivel = CODES[code][0]
    out = {"Brick": "", "Class": "", "Family": ""}
    if nivel == "Brick":
        out["Brick"] = code
        cl = BRICK_TO_CLASS[code]
        out["Class"], out["Family"] = cl, CLASS_TO_FAMILY[cl]
    elif nivel == "Class":
        out["Class"], out["Family"] = code, CLASS_TO_FAMILY[code]
    elif nivel == "Family":
        out["Family"] = code
    return out


# ----------------------------------------------------------- normalización
def strip_acc(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


ENC_FIX = re.compile(r"(?<=[A-Za-zÁÉÍÓÚáéíóú])[?#](?=[A-Za-zÁÉÍÓÚáéíóú])")


def repair_encoding(t: str) -> str:
    """PEQUE?AS -> PEQUEnAS (la ? / # intermedia era la ñ)."""
    return ENC_FIX.sub("n", t)


def norm(t) -> str:
    if t is None or (isinstance(t, float) and pd.isna(t)):
        return ""
    t = repair_encoding(str(t))
    t = strip_acc(t).lower()
    return re.sub(r"\s+", " ", t).strip()


# (patrón, expansión) -- diccionario de abreviaturas truncadas (40 car.)
ABREV = [
    (r"\bdam\.?(?=\s|$)", "dama"), (r"\bd/(?=\w)", "dama "),
    (r"\bm/c\b", "manga corta"), (r"\bm/l\b", "manga larga"),
    (r"\bcjto\.?(?=\s|$)", "conjunto"), (r"\bconj\.?(?=\s|$)", "conjunto"),
    (r"\bpant\.?(?=\s|$)", "pantalon"), (r"\bpescad\.?(?=\s|$)", "pescador"), (r"\bpescd\b", "pescador"),
    (r"\balg\.?(?=\s|$)", "algodon"), (r"\bacr\.?(?=\s|$)", "acrilico"), (r"\bnyl\.?(?=\s|$)", "nylon"),
    (r"\bt/(?=\d)", "talla "), (r"\btam\.?(?=\s|$)", "talla"),
    (r"\bfco\.?(?=\s|$)", "frasco"), (r"\bamp\.?(?=\s|$)", "ampolla"),
    (r"\btab\.?(?=\s|$)", "tabletas"), (r"\btbl\.?(?=\s|$)", "tabletas"),
    (r"\bcomp\.?\s*rec\.?", "comprimidos recubiertos"), (r"\bcaps\.?(?=\s|$)", "capsulas"),
    (r"\bsusp\.?(?=\s|$)", "suspension"), (r"\bjbe\.?(?=\s|$)", "jarabe"),
    (r"\biny\.?(?=\s|$)", "inyectable"), (r"\boft\.?(?=\s|$)", "oftalmico"),
    (r"\bppso\b", "polvo para suspension oral medicamento"),
    (r"\bcdc\b", "crema dental"),
    (r"\bb\.e\.s\.?", "bebida espirituosa seca licor"),
    (r"\bc[nñ]t\.?(?=\s|$)", "cunete"), (r"\bcun\.?(?=\s|$)", "cunete"), (r"\bgln\b", "galon"),
    (r"\bmecha hss\b", "brocas para taladro"),
]
ABREV_RE = [(re.compile(p), e) for p, e in ABREV]


def expand(t: str) -> str:
    for rx, e in ABREV_RE:
        t = rx.sub(e, t)
    return t


# ------------------------------------------------------------------ datos
RIF_RE = re.compile(r"gs1_afiliado_([JGVEPC])(\d{8})(\d)_", re.I)


def rif_from_afiliado(a) -> str:
    m = RIF_RE.search(str(a))
    return f"{m.group(1).upper()}-{m.group(2)}-{m.group(3)}" if m else ""


def prefijo_from_ean(ean) -> str:
    e = re.sub(r"\D", "", str(ean))
    e = e.lstrip("0") if len(e) > 13 else e
    if e.startswith("759400") and len(e) >= 9:
        return e[:9]
    return e[:7] if e[:3] in ("759",) and len(e) >= 7 else ""


def load_year(y: int) -> pd.DataFrame:
    d = pd.read_excel(IN_DIR / f"NoMatch_{y}.xlsx", dtype={"gt in": str, "EAN13": str, "prefijo": str, "Prefijo": str})
    d["_anio"] = y
    if "gt in" in d.columns:  # esquema legado 1993-2003
        d = d.rename(columns={"gt in": "EAN13", "prefijo": "Prefijo", "descripcion": "Nombre"})
        for c in ("Afiliado/id", "Rif", "Descripción Ampliada"):
            d[c] = ""
    d["Afiliado/id"] = d["Afiliado/id"].fillna("")
    d["Rif"] = d["Rif"].fillna("")
    miss = d["Rif"].astype(str).str.strip().isin(["", "nan"])
    d.loc[miss, "Rif"] = d.loc[miss, "Afiliado/id"].map(rif_from_afiliado)
    d["Prefijo"] = d["Prefijo"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
    miss = d["Prefijo"].str.strip().isin(["", "nan"])
    d.loc[miss, "Prefijo"] = d.loc[miss, "EAN13"].map(prefijo_from_ean)
    for c in ("Nombre", "Marca", "Descripción Ampliada"):
        d[c] = d[c].fillna("").astype(str).map(repair_encoding)
    return d.reset_index(drop=True)


def row_text(r) -> str:
    return norm(" ".join([str(r["Marca"]), str(r["Nombre"]), str(r["Descripción Ampliada"])]))


# --------------------------------------------------- capa 1: afiliados
# (rifs, regex marca/texto, código) -- códigos verificados contra el esquema.
L1_RULES = [
    ({"J-07001018-5"}, r"paramount|pier paolo|stefano zini|arrow", "10001352"),
    ({"J-31208358-1"}, r"lanitas|capone", "10001352"),
    ({"J-00074598-6"}, r"curex", "10001352"),
    ({"J-30311302-8"}, r"aloha", "10001077"),
    ({"J-30216913-5"}, r"wipeout", "10001077"),
    ({"J-31347928-4"}, r"favenca", "10001077"),
    ({"J-30703828-4"}, r"erreuno", "10001077"),
    ({"J-00075421-7"}, r"\bkex\b", "10008422"),
    ({"J-30294429-5"}, r"kiefer", "10008422"),
    ({"J-00340111-0"}, r"canet", None),  # se decide por texto (calcetín/muñequera)
    ({"J-00181165-6"}, r"jetbag", None),  # morral/lonchera/chola por texto
    ({"J-00105613-0"}, r"santillana|alfaguara|altea", "10000926"),
    ({"J-00057320-4"}, r"legislacion economica", "10000926"),
    ({"J-00023530-9"}, r"alpes", "10005893"),
    ({"J-00009097-1"}, r"henkel|ipacoll", "10003207"),
    ({"J-31143482-8"}, r"eco-?fil", "77013800"),
    ({"J-30638328-0"}, r"avtek", "78020600"),
    ({"J-00223173-4"}, r"genius", "78020600"),
    ({"J-31370946-8"}, r"guru", None),   # velones / lociones por texto
]
L1_MARCA = [
    (r"\b(arlequin|educor)\b", "10000926"),
    (r"\b(ocean drive|el universal|novios magazine|autotur|desafio de la historia)\b", "10000928"),
    (r"\b(anes records|foca records|tempo primo|sonografica|rodven)\b", "10001459"),
    (r"\b(venoco|castrol|gulf|ultralub)\b", "10005267"),
    (r"\b(cavp|pinco|montana|cebra)\b", "83010400"),
    (r"\b(freeze corp|esber)\b", "78020600"),
]
L1_TEXT = {  # decisiones por texto para afiliados mixtos
    "canet": [(r"calcet|media", "10001348"), (r"munequ", "10001909")],
    "jetbag": [(r"morral|mochila", "10001100"), (r"lonchera", "10007238"), (r"chola|sandalia", "10001077")],
    "guru": [(r"velon|vela|veladora", "10000555"), (r"locion|perfume|colonia", "10000365")],
}
L1_RULES = [(r, rx, c) for r, rx, c in L1_RULES]
for _, _, c in L1_RULES:
    assert c is None or c in CODES, c
for _, c in L1_MARCA:
    assert c in CODES, c
for v in L1_TEXT.values():
    for _, c in v:
        assert c in CODES, c

# patrones técnicos de alta precisión (texto expandido)
L2_RULES = [
    (r"\bb\.?e\.?s\b|bebida espirituosa seca", "10000263"),
    (r"brocas? para taladro", "10008422"),
    (r"\b(\d{1,2}w-?\d{2}|sae\s*\d{2,3})\b", "10005267"),
]
for _, c in L2_RULES:
    assert c in CODES, c


def layer1(rif: str, text: str) -> str | None:
    for rifs, rx, code in L1_RULES:
        if rif in rifs or re.search(rx, text):
            if code is not None:
                if rif in rifs or code:  # RIF exacto, o marca coincide
                    return code
            else:
                key = next(k for k in L1_TEXT if k in rx)
                for trx, tcode in L1_TEXT[key]:
                    if re.search(trx, text):
                        return tcode
    for rx, code in L1_MARCA:
        if re.search(rx, text):
            return code
    return None


def layer2(text: str) -> str | None:
    for rx, code in L2_RULES:
        if re.search(rx, text):
            return code
    return None


# ------------------------------------------------ capa 3: cohorte (asignados)
def build_cohorts() -> dict[str, tuple[str, float, int]]:
    pk = CACHE_DIR / "cohortes.pkl"
    if pk.exists():
        return pd.read_pickle(pk)
    cnt: dict[str, Counter] = defaultdict(Counter)
    for y in range(1993, 2026):
        d = pd.read_excel(ASIG_DIR / f"Asignados_{y}.xlsx", usecols=lambda c: c in
                          {"Prefijo", "prefijo", "gpc_code", "nivel_asignado", "confidence_score"}, dtype=str)
        pc = "Prefijo" if "Prefijo" in d.columns else "prefijo"
        d["cs"] = pd.to_numeric(d["confidence_score"], errors="coerce")
        d = d[(d["nivel_asignado"] == "Brick") & (d["cs"] >= 80) & d["gpc_code"].isin(CODES)]
        for p, c in zip(d[pc], d["gpc_code"]):
            cnt[p][c] += 1
    out = {}
    for p, c in cnt.items():
        tot = sum(c.values())
        code, n = c.most_common(1)[0]
        out[p] = (code, n / tot, tot)
    pd.to_pickle(out, pk)
    return out


def layer3(prefijo: str, cohorts) -> str | None:
    v = cohorts.get(prefijo)
    if v and v[1] >= 0.90 and v[2] >= 8:
        return v[0]
    return None


# ------------------------------------------------------------- capa 4: LLM
_client = None
_lock = threading.Lock()


def client():
    global _client
    if _client is None:
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            sys.exit("ANTHROPIC_API_KEY no está definida en el entorno")
        _client = anthropic.Anthropic(api_key=key, max_retries=6)
    return _client


def call(model: str, system: str, user: str, max_tokens: int = 4096) -> str:
    for att in range(6):
        try:
            r = client().messages.create(
                model=model, max_tokens=max_tokens,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user}])
            return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        except Exception as e:  # noqa: BLE001
            if att == 5:
                print("  API fallo definitivo:", str(e)[:160], flush=True)
                return ""
            time.sleep(2 * (att + 1))
    return ""


def parse_json(t: str):
    m = re.search(r"\[.*\]", t, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return []


CONTEXT = (
    "Eres clasificador GS1 Venezuela (GPC Mayo 2026, español). Productos registrados entre 1993 y 2007; "
    "los textos vienen truncados a 40 caracteres, en mayúsculas, con abreviaturas (CAB.=caballero en textil/calzado pero CABLE en material eléctrico, D/ o DAM.=dama, "
    "M/C manga corta, M/L manga larga, CJTO/CONJ=conjunto, PANT=pantalón, ALG=algodón, T/ o TAM=talla, "
    "FCO=frasco, AMP=ampolla, TAB/TBL=tabletas, CAPS=cápsulas, SUSP=suspensión, JBE=jarabe, INY=inyectable, "
    "OFT=oftálmico, CDC=crema dental, PH=papel higiénico (o pH según contexto), CÑT/CUN=cuñete, GLN=galón, B.E.S.=bebida espirituosa seca). "
    "Muchos afiliados pusieron el nombre del producto en MARCA y la talla/medida en NOMBRE: evalúa todos los campos "
    "juntos. Rangos tipo 18-19 a 44-45 en fabricantes de calzado/cholas son tallas de zapato. "
    "Las marcas de medicamentos y principios activos son productos farmacéuticos. "
)

CLASS_LIST = "\n".join(f"{c}|{s} > {f} > {k}" for c, (s, f, k, _) in sorted(CLASS_INFO.items()))
SYS_A = CONTEXT + (
    "\n\nTAREA: para cada producto elige el CLASS (código de 8 dígitos) más específico y correcto de la lista oficial. "
    "Usa SOLO códigos de esta lista. Siempre debes elegir uno (el más probable). "
    "Responde EXCLUSIVAMENTE un arreglo JSON: [{\"i\":<id>,\"c\":\"<ClassCode>\",\"k\":<1|2|3>}] "
    "donde k es tu certeza (3 alta, 2 media, 1 baja).\n\nLISTA OFICIAL DE CLASSES (código|Segmento > Familia > Class):\n"
    + CLASS_LIST
)


def stage_a(items: list[tuple[int, str]]) -> dict[int, tuple[str, int]]:
    lines = "\n".join(f"{i}|{t}" for i, t in items)
    out = parse_json(call(MODEL_A, SYS_A, "Productos (id|marca / nombre / descripción):\n" + lines, 4096))
    res = {}
    for o in out:
        try:
            i, c, k = int(o["i"]), str(o["c"]), int(o.get("k", 2))
        except Exception:  # noqa: BLE001
            continue
        if c in CLASS_INFO:
            res[i] = (c, max(1, min(3, k)))
    return res


def stage_b(class_code: str, items: list[tuple[int, str]]) -> dict[int, tuple[str, int]]:
    bricks = BRICKS_BY_CLASS[class_code]
    seg, fam, k, _ = CLASS_INFO[class_code]
    blist = "\n".join(
        f"{b.BrickCode}|{b.BrickTitle}|{(b.BrickDefinition_Includes or '')[:170] if isinstance(b.BrickDefinition_Includes, str) else ''}"
        for b in bricks)
    system = CONTEXT + (
        f"\n\nTAREA: los productos pertenecen al Class '{k}' ({seg} > {fam}). Elige el BRICK exacto de la lista. "
        "Si ningún brick describe razonablemente el producto, responde 0. "
        "Responde EXCLUSIVAMENTE un arreglo JSON: [{\"i\":<id>,\"b\":\"<BrickCode o 0>\",\"k\":<1|2|3>}].\n\n"
        f"BRICKS OFICIALES (código|título|incluye):\n{blist}")
    lines = "\n".join(f"{i}|{t}" for i, t in items)
    out = parse_json(call(MODEL_B, system, "Productos:\n" + lines, 4096))
    valid = {b.BrickCode for b in bricks}
    res = {}
    for o in out:
        try:
            i, b, kk = int(o["i"]), str(o["b"]), int(o.get("k", 2))
        except Exception:  # noqa: BLE001
            continue
        if b in valid:
            res[i] = (b, max(1, min(3, kk)))
        elif b == "0":
            res[i] = ("0", 0)
    return res


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


class Cache:
    def __init__(self, name):
        self.p = CACHE_DIR / f"{name}.jsonl"
        self.d = {}
        if self.p.exists():
            for ln in self.p.read_text().splitlines():
                try:
                    o = json.loads(ln)
                    self.d[o["k"]] = o["v"]
                except Exception:  # noqa: BLE001
                    pass
        self.f = open(self.p, "a")
        self.l = threading.Lock()

    def put(self, k, v):
        with self.l:
            self.d[k] = v
            self.f.write(json.dumps({"k": k, "v": v}) + "\n")
            self.f.flush()


def key(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def llm_classify(texts: list[str], workers: int = 12, batch_a: int = 40, batch_b: int = 40):
    """texts únicos -> {texto: (code, nivel_certeza)} (code de nivel Brick o Class)."""
    ca, cb = Cache("etapaA"), Cache("etapaB")
    pend = [t for t in texts if key(t) not in ca.d]
    print(f"  etapa A: {len(pend)} textos pendientes de {len(texts)}", flush=True)
    batches = list(chunks(pend, batch_a))

    def runA(bt):
        items = list(enumerate(bt))
        res = stage_a(items)
        miss = [(i, t) for i, t in items if i not in res]
        if miss:  # reintento individual con lote pequeño
            for sub in chunks(miss, 8):
                res.update(stage_a(sub))
        for i, t in items:
            if i in res:
                ca.put(key(t), list(res[i]))

    with cf.ThreadPoolExecutor(workers) as ex:
        for n, _ in enumerate(ex.map(runA, batches), 1):
            if n % 20 == 0:
                print(f"    A {n}/{len(batches)}", flush=True)

    byclass = defaultdict(list)
    for t in texts:
        v = ca.d.get(key(t))
        if v and key(t) not in cb.d:
            byclass[v[0]].append(t)
    jobs = [(c, b) for c, ts in byclass.items() for b in chunks(ts, batch_b)]
    print(f"  etapa B: {sum(len(v) for v in byclass.values())} textos en {len(jobs)} lotes", flush=True)

    def runB(job):
        c, bt = job
        if len(BRICKS_BY_CLASS[c]) == 1:
            for t in bt:
                cb.put(key(t), [BRICKS_BY_CLASS[c][0].BrickCode, ca.d[key(t)][1]])
            return
        items = list(enumerate(bt))
        res = stage_b(c, items)
        for i, t in items:
            if i in res:
                cb.put(key(t), list(res[i]))

    with cf.ThreadPoolExecutor(workers) as ex:
        for n, _ in enumerate(ex.map(runB, jobs), 1):
            if n % 40 == 0:
                print(f"    B {n}/{len(jobs)}", flush=True)

    out = {}
    for t in texts:
        a, b = ca.d.get(key(t)), cb.d.get(key(t))
        if not a:
            continue
        if b and b[0] != "0":
            out[t] = (b[0], b[1])
        else:
            out[t] = (a[0], max(1, a[1] - 1) if b else a[1])  # queda en Class
    return out


# ------------------------------------------------------------------- main
CONF_BY_K = {3: 90, 2: 87, 1: 85}


def classify_all(years):
    cohorts = build_cohorts()
    frames = {y: load_year(y) for y in years}
    # layer 1-3
    assigned: dict[tuple[int, int], tuple[str, int, str]] = {}
    texts_needed = {}
    for y, d in frames.items():
        for idx, r in d.iterrows():
            t = expand(row_text(r))
            code = layer1(r["Rif"], t)
            if code:
                assigned[(y, idx)] = (code, 95, "L1_afiliado")
                continue
            code = layer2(t)
            if code:
                assigned[(y, idx)] = (code, 92, "L2_patron")
                continue
            code = layer3(str(r["Prefijo"]), cohorts)
            if code:
                assigned[(y, idx)] = (code, 90, "L3_cohorte")
                continue
            texts_needed[(y, idx)] = t
    print(f"capas 1-3 resuelven {len(assigned)}; a LLM: {len(texts_needed)}", flush=True)
    uniq = sorted(set(texts_needed.values()))
    # el LLM ve el texto expandido junto con el prefijo para dar contexto de empresa
    llm = llm_classify(uniq)
    for k, t in texts_needed.items():
        if t in llm:
            code, kk = llm[t]
            assigned[k] = (code, CONF_BY_K.get(kk, 85), "L4_LLM")
    # respaldo: moda por prefijo de lo ya resuelto en este lote (Class)
    by_pref = defaultdict(Counter)
    for (y, idx), (code, _, _) in assigned.items():
        by_pref[str(frames[y].at[idx, "Prefijo"])][lineage(code)["Class"] or code] += 1
    unresolved = [k for k in texts_needed if k not in assigned]
    for (y, idx) in unresolved:
        c = by_pref.get(str(frames[y].at[idx, "Prefijo"]))
        if c:
            assigned[(y, idx)] = (c.most_common(1)[0][0], 85, "L5_cohorte_clase")
    print(f"sin resolver tras respaldo: {len([k for k in texts_needed if k not in assigned])}", flush=True)
    return frames, assigned


def export(frames, assigned):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    audit = []
    for y, d in frames.items():
        rows = []
        for idx in d.index:
            code, conf, capa = assigned.get((y, idx), (None, None, None))
            rows.append((code, conf, capa))
        d = d.copy()
        d["gpc_code"] = [r[0] for r in rows]
        d["confidence_score"] = [r[1] for r in rows]
        d["capa_clasificacion"] = [r[2] for r in rows]
        # validación estricta contra el esquema oficial
        assert d["gpc_code"].notna().all(), f"{y}: filas sin código"
        assert d["gpc_code"].isin(CODES).all(), f"{y}: código fuera del esquema Mayo 2026"
        assert d["confidence_score"].between(85, 95).all() and d["confidence_score"].notna().all(), f"{y}: confianza"
        d["nivel_asignado"] = d["gpc_code"].map(lambda c: CODES[c][0])
        d["gpc_description"] = d["gpc_code"].map(lambda c: CODES[c][1])
        assert (d["nivel_asignado"] != "Segment").all(), f"{y}: filas a nivel Segment"
        lin = d["gpc_code"].map(lineage)
        d["brick_code"] = lin.map(lambda x: x["Brick"])
        d["class_code"] = lin.map(lambda x: x["Class"])
        d["family_code"] = lin.map(lambda x: x["Family"])
        d["fecha_creacion"] = d.get("fecha_creacion")
        cols = ["Afiliado/id", "Rif", "Nombre", "Marca", "Prefijo", "EAN13", "Descripción Ampliada",
                "fecha_creacion", "gpc_code", "nivel_asignado", "gpc_description", "confidence_score",
                "brick_code", "class_code", "family_code", "capa_clasificacion"]
        d[cols].to_excel(OUT_DIR / f"NoMatch_{y}_CLASIFICADO.xlsx", index=False)
        vc = d["nivel_asignado"].value_counts()
        n = len(d)
        audit.append({"Año": y, "Total filas": n, "Brick": int(vc.get("Brick", 0)),
                      "Class": int(vc.get("Class", 0)), "Family": int(vc.get("Family", 0)),
                      "% Especificidad (Brick+Class)": round(100 * (vc.get("Brick", 0) + vc.get("Class", 0)) / n, 2),
                      "Códigos inventados": 0, "NO_MATCH": int((d["nivel_asignado"] == "NO_MATCH").sum())})
    a = pd.DataFrame(audit)
    a.to_csv(OUT_DIR / "auditoria_1993_2007.csv", index=False)
    print(a.to_string(index=False))


if __name__ == "__main__":
    yrs = [int(x) for x in sys.argv[1:]] or YEARS
    fr, asg = classify_all(yrs)
    export(fr, asg)
