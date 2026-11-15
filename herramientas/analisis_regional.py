#!/usr/bin/env python3
"""Análisis regional de la codificación GS1 Venezuela.

Los archivos de codificación (insights/<año>/Final_*.xlsx y NO_MATCH_*_CLASIFICADO.xlsx)
no traen estado ni ciudad. Esta herramienta permite agregarlo a partir de una tabla
externa que relacione cada prefijo de empresa con su estado.

Uso:
  1) Generar la plantilla para completar (sin nombres de empresa):
       python3 herramientas/analisis_regional.py --plantilla plantilla_prefijo_estado.csv
  2) Completar la columna "estado" (los demás campos son solo orientativos).
  3) Calcular las métricas regionales:
       python3 herramientas/analisis_regional.py --tabla plantilla_prefijo_estado.csv

Salidas (en --salida, por defecto insights/_resumen/):
  regiones.csv          una fila por estado
  regiones_sector.csv   códigos 2023-2025 por estado y sector GPC
  regiones.json         lo mismo, para el boletín

Un código = un GTIN único por año. No se publican nombres de empresa.
"""
import argparse, csv, glob, json, os, collections
import openpyxl

COLS = {'prefijo': ['Prefijo', 'PREFIJO'], 'gtin': ['EAN13', 'GTIN'], 'fecha': ['fecha_creacion', 'FECHA CREACION'],
        'gpc_code': ['gpc_code'], 'nivel': ['nivel_asignado']}


def cargar(raiz, desde):
    cat = {r['codigo']: r for r in csv.DictReader(open(os.path.join(raiz, 'catalogo', 'gpc_catalogo_oficial.csv'), encoding='utf-8'))}
    vistos, filas = set(), []
    for f in sorted(glob.glob(os.path.join(raiz, 'insights', '*', '*.xlsx'))):
        anio = int(f.split(os.sep)[-2])
        if anio < desde:
            continue
        es_final = os.path.basename(f).startswith('Final')
        ws = openpyxl.load_workbook(f, read_only=True).active
        it = ws.iter_rows(values_only=True)
        h = list(next(it))
        idx = {k: next((h.index(c) for c in v if c in h), None) for k, v in COLS.items()}
        for r in it:
            g = r[idx['gpc_code']] if idx['gpc_code'] is not None else None
            g = str(g).strip().split('.')[0] if g is not None else ''
            if not g or g == 'NO_MATCH' and es_final:
                continue
            gtin = str(r[idx['gtin']]).split('.')[0] if r[idx['gtin']] is not None else ''
            pref = str(r[idx['prefijo']]).split('.')[0] if r[idx['prefijo']] is not None else ''
            clave = (gtin, anio)
            if not gtin or not pref or clave in vistos or g not in cat:
                continue
            vistos.add(clave)
            seg = cat[g]['segment_code']
            nivel = r[idx['nivel']]
            filas.append((anio, pref, cat[seg]['titulo'] if seg in cat else 'Sin segmento', len(gtin), nivel))
    return filas


def plantilla(filas, salida):
    por = collections.defaultdict(lambda: collections.Counter())
    cod = collections.Counter()
    for anio, pref, seg, _, _ in filas:
        if anio >= 2021:
            por[pref][seg] += 1
            if anio >= 2023:
                cod[pref] += 1
    with open(salida, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh)
        w.writerow(['prefijo', 'estado', 'sector_principal_2021_2025', 'codigos_2023_2025'])
        for pref, c in sorted(por.items(), key=lambda kv: -cod[kv[0]]):
            w.writerow([pref, '', c.most_common(1)[0][0], cod[pref]])
    print('Plantilla escrita:', salida, '-', len(por), 'prefijos')


def metricas(filas, tabla, salida):
    est = {}
    for r in csv.DictReader(open(tabla, encoding='utf-8-sig')):
        if r.get('estado', '').strip():
            est[r['prefijo'].strip()] = r['estado'].strip()
    if not est:
        raise SystemExit('La tabla no tiene ningún estado completado.')
    base = [(a, p, s, l, est[p]) for a, p, s, l, _ in filas if p in est and a >= 2023]
    sin = len({p for a, p, *_ in filas if a >= 2023 and p not in est})
    print('Prefijos 2023-2025 sin estado:', sin)
    total = len(base)
    por = collections.defaultdict(list)
    for fila in base:
        por[fila[4]].append(fila)
    out, sec = [], collections.defaultdict(collections.Counter)
    for e, fs in por.items():
        n = collections.Counter(a for a, *_ in fs)
        s25 = [f for f in fs if f[0] == 2025]
        emp25 = collections.Counter(p for _, p, *_ in s25)
        segs = collections.Counter(s for _, _, s, *_ in fs)
        for s, c in segs.items():
            sec[e][s] = c
        top = segs.most_common(1)[0]
        out.append({'estado': e, 'codigos_2023_2025': len(fs), 'pct_del_total': round(len(fs) / total * 100, 1),
                    'codigos_2024': n[2024], 'codigos_2025': n[2025],
                    'var_2025_vs_2024_pct': round((n[2025] / n[2024] - 1) * 100, 1) if n[2024] else '',
                    'empresas_2023_2025': len({p for _, p, *_ in fs}), 'empresas_2025': len(emp25),
                    'codigos_por_empresa_2025': round(n[2025] / len(emp25), 1) if emp25 else '',
                    'pct_mayor_empresa_2025': round(emp25.most_common(1)[0][1] / n[2025] * 100, 1) if emp25 else '',
                    'sector_dominante': top[0], 'pct_sector_dominante': round(top[1] / len(fs) * 100, 1),
                    'pct_gtin14': round(sum(1 for f in fs if f[3] == 14) / len(fs) * 100, 1)})
    out.sort(key=lambda d: -d['codigos_2023_2025'])
    os.makedirs(salida, exist_ok=True)
    with open(os.path.join(salida, 'regiones.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    with open(os.path.join(salida, 'regiones_sector.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh)
        w.writerow(['estado', 'sector', 'codigos_2023_2025'])
        for e, c in sec.items():
            for s, n in c.most_common():
                w.writerow([e, s, n])
    json.dump({'estados': out, 'sin_estado_prefijos': sin}, open(os.path.join(salida, 'regiones.json'), 'w'), ensure_ascii=False, indent=1)
    print('Listo:', salida, '-', len(out), 'estados')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--plantilla', help='Ruta del CSV de plantilla a generar')
    ap.add_argument('--tabla', help='CSV con columnas prefijo,estado ya completado')
    ap.add_argument('--salida', default=os.path.join('insights', '_resumen'))
    ap.add_argument('--raiz', default='.')
    ap.add_argument('--desde', type=int, default=2021, help='Primer año a leer (por defecto 2021)')
    a = ap.parse_args()
    if not a.plantilla and not a.tabla:
        ap.error('Indique --plantilla o --tabla')
    filas = cargar(a.raiz, a.desde)
    if a.plantilla:
        plantilla(filas, a.plantilla)
    if a.tabla:
        metricas(filas, a.tabla, a.salida)
