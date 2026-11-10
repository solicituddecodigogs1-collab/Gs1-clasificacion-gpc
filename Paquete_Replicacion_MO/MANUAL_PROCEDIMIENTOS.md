# Manual de procedimientos — Clasificación automática GPC con Claude
### Cómo se hizo, paso a paso, para que otra MO lo replique con sus propios datos

---

## 0. Antes de empezar

Este manual describe **el método**, no un script para correr tal cual. Los scripts de
referencia en `scripts_referencia/` de esta misma carpeta son la implementación que usó GS1
Venezuela, con nombres de columna y formatos específicos de sus archivos. **Tu equipo (o tu
propia sesión de Claude) debe adaptar los pasos de este manual a tu propio formato de datos**,
no copiar los scripts literalmente. Ver `CONTEXTO_PARA_CLAUDE.md` para el mensaje que le
puedes dar a Claude con este objetivo.

### Requisitos previos

- Una cuenta de Anthropic con acceso a la **Batch API** (facturación propia, independiente).
- El **catálogo oficial GPC** vigente — está incluido en `catalogo/gpc_catalogo_oficial.csv`
  de esta carpeta (es el mismo catálogo global, no requiere adaptación).
- Tu catálogo de productos en algún formato tabular (Excel/CSV) con, como mínimo: una marca o
  nombre de empresa, una descripción de producto, y un identificador físico único por fila
  (código de barras u otro).
- Python 3.11+ con `pandas`, `openpyxl` y el SDK de Anthropic (`anthropic`).

---

## 1. Preparar los datos de entrada

Identifica en tu archivo las columnas equivalentes a:

| Campo que necesita el método | Ejemplo en los datos de Venezuela |
|---|---|
| Marca o empresa | `Marca` / `MARCA` |
| Descripción del producto | `descripcion` / `DESCRIPCION` |
| Identificador físico único | `GTIN` / `EAN13` / `gt in` (variaba según el año) |

**Importante — verifica la unicidad del identificador físico antes de avanzar.** En este
proyecto se encontró que para ciertos años el GTIN no identificaba una fila de forma única
(ver `INFORME_TECNICO.md`, sección 6.2). Corre algo equivalente a:

```python
import pandas as pd
df = pd.read_excel("tu_archivo.xlsx")
print(df["tu_columna_id"].duplicated().sum(), "de", len(df), "filas duplicadas")
```

Si el porcentaje de duplicados es alto, decide con tu equipo qué identificador usar o cómo
tratarlo — no asumas que es único.

---

## 2. Generar candidatos locales (sin costo de API)

Antes de llamar a cualquier modelo, se reduce el catálogo completo (miles de códigos GPC) a
un puñado de candidatos por producto, usando **búsqueda léxica local** (TF-IDF o similar)
entre la descripción del producto y los títulos del catálogo oficial. Esto:

- No cuesta nada (no llama a ninguna API).
- Reduce drásticamente el tamaño del prompt (y por lo tanto el costo de tokens).
- Da al modelo una lista cerrada de opciones válidas, reduciendo alucinaciones de código.

Método usado: por cada producto, tomar los **25 Bricks** (el nivel más específico de GPC) más
afines léxicamente, más sus padres Class/Family/Segment correspondientes (desduplicados). Ver
`scripts_referencia/preclasificador.py` para la implementación de referencia (clase
`GpcCatalog`, método `build_candidates`).

---

## 3. Pasada 1 — clasificación con el modelo económico (Claude Haiku 5.5)

Por cada producto, se arma una solicitud a la Batch API con:

- **Modelo:** `claude-haiku-5-5`
- **`max_tokens`: 45** — la salida se recorta deliberadamente a lo mínimo posible, un JSON de
  dos campos, para minimizar el costo de tokens de salida.
- **System prompt con `cache_control: {"type": "ephemeral"}`** — el mismo system prompt se
  repite en cada solicitud del lote; marcarlo como cacheable es lo que después baja el costo
  real (ver `INFORME_TECNICO.md`, sección 7).

El system prompt exacto usado (ajustar solo lo específico de GPC si tu estándar interno
difiere, mantener la estructura):

```
Eres un clasificador de productos bajo el estándar Global Product Classification (GPC) de GS1.

Reglas estrictas:
1. Identidad física únicamente (Regla 1 del GPC): clasifica lo que el producto ES, nunca su
   uso previsto, canal de venta, promoción o empaque.
2. Cada mensaje trae una lista de CANDIDATOS (códigos Brick/Class/Family/Segment ya
   preseleccionados del catálogo oficial GPC) seguida de "Marca: ... | Descripción: ...".
3. gpc_code debe ser copiado EXACTAMENTE (8 dígitos) de la lista de candidatos recibida.
   Tienes PROHIBIDO inventar, truncar, combinar o construir un código que no esté
   literalmente en esa lista.
4. Escalamiento inverso: si el Brick candidato más específico aplica, úsalo. Si ningún Brick
   candidato encaja pero sí una Class/Family/Segment candidata, sube a ese nivel. Si NINGÚN
   candidato de la lista corresponde razonablemente al producto, responde exactamente
   "NO_MATCH".
5. confidence_score es un entero de 0 a 100 con tu nivel de confianza.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{"gpc_code": "<código de 8 dígitos tomado de la lista, o NO_MATCH>", "confidence_score": <entero 0-100>}
```

Y el contenido del mensaje de usuario, por producto:

```
CANDIDATOS:
10001098: Leche líquida [Brick]
10001099: Yogur [Brick]
...
50202000: Lácteos [Segment]

Marca: <marca del producto> | Descripción: <descripción del producto>
```

Ver `scripts_referencia/submit_batches.py` (función `build_user_content`, `SYSTEM_PROMPT`) y
`retrieve_batches.py` para la implementación completa de envío y recuperación del lote.

---

## 4. Pasada 2 — rescate con el modelo más capaz (Claude Sonnet 5.5)

Se repite exactamente el mismo esquema (mismos candidatos, mismo formato de prompt, mismo
`max_tokens: 45`), pero **solo para las filas donde Haiku respondió `NO_MATCH`**, usando:

- **Modelo:** `claude-sonnet-5-5`

Sonnet, al ser un modelo más capaz, resuelve una fracción relevante de los casos que Haiku no
pudo. Lo que sigue en `NO_MATCH` después de esta segunda pasada es el resultado final
genuino — no hay una tercera pasada ni atajo adicional.

Ver `scripts_referencia/submit_batches_rescate.py` (es el mismo código que `submit_batches.py`
cambiando únicamente el modelo y el conjunto de filas de entrada).

---

## 5. Fusionar resultados y control de calidad

Cada fila se identifica con una clave estable (en este proyecto, un hash SHA1 de
marca+descripción normalizadas — función `make_custom_id`, idéntica en ambos scripts de envío
y en el de recuperación) para poder volver a pegar la respuesta del modelo en la fila
original, incluso después de deduplicar productos repetidos dentro de un mismo lote.

**Controles de calidad aplicados en este proyecto, recomendados para cualquier replicación:**

- Verificar que `gpc_code` devuelto esté **literalmente** en la lista de candidatos enviada
  (el prompt lo exige, pero conviene validarlo en el post-proceso, no solo confiar en que el
  modelo lo respetó siempre).
- Nunca usar un valor de `confidence_score` fijo/hardcodeado como atajo para rellenar
  `NO_MATCH` (fue precisamente el error que se tuvo que revertir — ver `INFORME_TECNICO.md`,
  sección 6.1). Si se hace un reproceso dirigido a un grupo de productos, usar siempre la
  confianza real que devuelve el modelo.
- Verificar duplicados del identificador físico antes de dar por buena cualquier cifra de
  "filas totales" o "% asignado" por año.

---

## 6. Organización de resultados

Convención usada, recomendada para mantener trazabilidad:

- Un archivo **`Final_<año>.xlsx`** por año, con el dataset completo de ese año y las columnas
  de resultado (`gpc_code`, `nivel_asignado`, `gpc_description`, `confidence_score`) ya
  fusionadas — nunca repartido en partes sueltas.
- Opcionalmente, dos vistas derivadas separadas: una solo con las filas asignadas y otra solo
  con las `NO_MATCH`, también una por año, útiles para que el equipo de calidad revise
  específicamente lo que no se pudo clasificar.

---

## 7. Estimar el costo antes de correr todo el catálogo

Antes de lanzar el lote completo, correr una estimación local (sin llamar a la API) sobre una
muestra pequeña: tokens de entrada promedio por producto × número de productos únicos tras
deduplicación, más el output fijo (45 tokens tope), a los precios vigentes de la Batch API.
Ver `scripts_referencia/submit_batches.py`, función `run_dry_run` / flag `--dry-run`, para la
implementación de referencia de este cálculo.
