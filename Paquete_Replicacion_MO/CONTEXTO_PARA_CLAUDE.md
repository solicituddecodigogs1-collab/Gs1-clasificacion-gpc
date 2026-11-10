# Contexto para Claude — Replicar la clasificación automática GPC

> **Instrucciones de uso de este archivo:** esto está escrito para pegarse directamente como
> mensaje inicial (o como archivo de contexto, ej. `CLAUDE.md`) en una sesión de Claude Code
> nueva, en el repositorio de la MO que va a replicar este trabajo. Está escrito en segunda
> persona dirigido a Claude. Si lo estás leyendo como humano: este es el "briefing" completo
> que tu propia sesión de Claude necesita para empezar a trabajar; no necesitas editarlo salvo
> para corregir el nombre de la MO y, si ya los tienes a mano, los nombres reales de tus
> columnas en la sección "Lo que necesito que hagas primero".

---

## Qué es esto

GS1 Venezuela construyó un pipeline que clasifica automáticamente un catálogo de productos
bajo el estándar **GPC (Global Product Classification)** de GS1, usando dos modelos de Claude
vía la Batch API de Anthropic. Logró clasificar el 86,47 % de 1.428.900 productos (33 años de
catálogo histórico) por un costo real de $1.050 USD, sin ninguna heurística de atajo — el
resultado es 100 % decisión de los modelos.

Esta carpeta (`Paquete_Replicacion_MO/`) es el paquete completo que te entregan para que
ayudes a tu equipo a construir la misma capacidad, adaptada a los datos de esta MO. Contiene:

- `INFORME_TECNICO.md` — qué se hizo, cuánto, cuándo, y qué se aprendió (léelo para entender
  el resultado y las limitaciones ya conocidas).
- `MANUAL_PROCEDIMIENTOS.md` — el método paso a paso, con el system prompt exacto, los
  parámetros de la Batch API, y las reglas de control de calidad. **Este es tu documento de
  referencia principal — síguelo como especificación.**
- `catalogo/gpc_catalogo_oficial.csv` — el catálogo oficial GPC. Es global: úsalo tal cual,
  no lo regeneres.
- `scripts_referencia/` — el código real que usó GS1 Venezuela (`preclasificador.py`,
  `submit_batches.py`, `submit_batches_rescate.py`, `retrieve_batches.py`). **Es
  código de ejemplo, escrito para el formato de datos venezolano — tiene nombres de columna y
  rutas de archivo específicos de ese proyecto. No lo copies ni lo ejecutes tal cual: léelo
  para entender la lógica (sobre todo `build_candidates`, `SYSTEM_PROMPT`,
  `build_user_content`, `make_custom_id`) y reescribe tu propia versión adaptada a los datos
  reales de esta MO.**
- `ejemplos/` — un ejemplo completo de prompt de entrada y salida esperada, y de formato de
  fila antes/después de clasificar.

## Lo que necesito que hagas primero

1. Lee `MANUAL_PROCEDIMIENTOS.md` completo antes de escribir una sola línea de código.
2. Pregúntame (al humano que te está dando este contexto) o revisa los archivos del catálogo
   de esta MO para identificar: la columna de marca/empresa, la columna de descripción de
   producto, y qué columna sirve como identificador físico único por fila.
3. **Antes de asumir que ese identificador es único, verifícalo** (ver
   `MANUAL_PROCEDIMIENTOS.md`, sección 1 — este fue un problema real detectado en el proyecto
   original para ciertos años).
4. Confirma con el equipo qué cuenta de Anthropic / API key se va a usar para la Batch API (es
   facturación propia de esta MO, independiente de la de GS1 Venezuela).
5. Antes de lanzar el catálogo completo, corre una estimación de costo sobre una muestra
   pequeña (`MANUAL_PROCEDIMIENTOS.md`, sección 7) y compártela con el equipo antes de seguir.

## Reglas que no debes romper

- **No inventes ni copies una heurística de atajo** (como Marca→Segmento, descrita y
  eliminada en `INFORME_TECNICO.md` sección 6.1). Si en algún momento el resultado "mejora"
  de forma sospechosa, verifica si no se coló un atajo de este tipo — revisa si hay un
  `confidence_score` fijo repetido en vez de valores reales devueltos por el modelo.
- **No inventes códigos GPC.** El modelo solo puede usar códigos que vengan literalmente en
  la lista de candidatos que tú le mandas en el prompt — igual que hace el proyecto original.
- **No asumas que el formato de columnas de Venezuela aplica aquí.** Cada MO tiene su propio
  formato de exportación; tu trabajo es adaptar la lógica, no portar el código línea por
  línea.
- El catálogo GPC (`catalogo/gpc_catalogo_oficial.csv`) es la única pieza que **no** debe
  modificarse ni regenerarse — es el mismo catálogo global.

## Qué entregar al final

Siguiendo la convención del proyecto original (`MANUAL_PROCEDIMIENTOS.md`, sección 6): un
archivo `Final_<año>.xlsx` (o el periodo que corresponda) por cada corte de datos, con el
resultado ya fusionado — nunca repartido en archivos "por parte" sueltos.
