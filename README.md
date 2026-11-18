# GS1 Venezuela — Clasificación automática GPC (1993-2025)

Clasificación de ~33 años de productos del catálogo de GS1 Venezuela contra el
estándar GPC (Global Product Classification) usando Claude vía Batch API:
primera pasada con Haiku 5.5, rescate del `NO_MATCH` con Sonnet 5.5 y
heurística Marca→Segmento. Resultado global y costos: ver
`Paquete_Replicacion_MO/INFORME_TECNICO.md`.

## Mapa del repositorio

```
.
├── README.md
├── requirements.txt
├── batch_tracker.json        Estado de los lotes enviados a la Batch API (lo leen lib/ y herramientas/)
│
├── catalogo/                 Catálogo GPC oficial (CSV, Excel de esquema, lookup empresa→giro)
├── lib/                      Núcleo reutilizable: preclasificador, envío y recuperación de lotes
├── scripts/                  Drivers por año y procesos de rescate
│   ├── rescate_anticipado/       Un driver por año (1999-2014): Sonnet 5.5 + heurística Marca→Segmento
│   ├── clasificar_nomatch_1993_2007.py   Rescate en capas del NO_MATCH 1993-2007
│   └── construir_lookup_empresa.py
├── herramientas/             Utilidades de consolidación, extracción y reporte
│   └── reprocesos_puntuales/     Correcciones de una sola vez (jeans, footwear, kskin, ...)
│
├── datos/                    TODOS los datos, por etapa del pipeline (ver abajo)
├── docs/                     Informes, notas de lecciones aprendidas, presentaciones
│
├── App_GPC_Regional/         App web (FastAPI + HTML/JS) para otras MO de GS1 — autocontenida
└── Paquete_Replicacion_MO/   Kit para que otra MO replique el proyecto — autocontenido
```

### `datos/` — de la entrada al resultado

| Carpeta | Contenido | Archivos |
|---|---|---|
| `entrada/<año>/` | Archivos crudos de GS1 por año, en 5 partes (1993-2025) | 165 |
| `final/` | **Resultado final consolidado** `Final_<año>.xlsx` (1993-2025) | 33 |
| `asignados/` | Filas con GPC asignado `Asignados_<año>.xlsx` | 33 |
| `no_match/extraido/` | Filas sin GPC `NoMatch_<año>.xlsx` (1993-2025) | 33 |
| `no_match/historico/` | `NO_MATCH` tras la primera pasada, por año | 33 |
| `no_match/residual/` | `NO_MATCH` residual tras Sonnet 5.5 | 33 |
| `no_match/remanentes/` | Remanentes `NO_MATCH_<año>.xlsx` extraídos de `final/` (2005-2025) | 21 |
| `no_match/clasificado/` | `NO_MATCH` ya clasificado: `NoMatch_<año>_CLASIFICADO` (1993-2007), `NO_MATCH_<año>_CLASIFICADO` (2010-2025) y `auditoria_1993_2007.csv` | 32 |
| `salida/` | Salidas de los rescates por año: `no_match_<año>_rescate_sonnet.xlsx` y `..._reprocesado_haiku55.xlsx`. Es también el directorio de trabajo por defecto de `lib/` | 40 |
| `sin_heuristica/` | Reconstrucción sin la heurística Marca→Segmento + reportes de `NO_MATCH` | 28 |
| `piloto/` | Piloto inicial (5 archivos de prueba) | 11 |
| `final/_revisar/` | Archivo que difiere de su homólogo — ver nota abajo | 1 |

> **Pendiente de decisión** — `datos/final/_revisar/Final_2010_version_raiz.xlsx`: estaba suelto en la
> raíz y NO es idéntico a `datos/final/Final_2010.xlsx` (misma cantidad de filas, pero columnas
> descriptivas vaciadas y 35 `gpc_code` distintos). Se conservó para que alguien confirme cuál es
> la versión buena y borre la otra.

## Cómo se corre

Todos los scripts asumen que se ejecutan **desde la raíz del repo**:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...          # no persiste entre sesiones
python lib/submit_batches.py --dry-run
python herramientas/resumen_global.py
```

## Notas

- Los scripts de `scripts/rescate_anticipado/` y `herramientas/reprocesos_puntuales/` son
  **históricos** (un año / una corrección cada uno). Sus rutas fueron actualizadas a la nueva
  estructura, pero varios leen partes `clasificado_*_Parte_N.xlsx` que ya se compactaron en
  `datos/final/`; no están pensados para re-ejecutarse tal cual.
- `batch_tracker.json` conserva rutas antiguas (`input_<año>/`, `Output_Clasificado/...`) de lotes ya
  recuperados; es inocuo (ver `docs/MEJORAS_ANIOS_SIGUIENTES.md`, punto 6).
- `App_GPC_Regional/` y `Paquete_Replicacion_MO/` no se tocaron: cada uno lleva su propia copia del
  catálogo y de `lib/` a propósito, para poder copiarse sueltos.
- Rutas antiguas → nuevas: `docs/MAPA_RUTAS.md`.
