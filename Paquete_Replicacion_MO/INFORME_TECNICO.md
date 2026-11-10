# Informe técnico — Clasificación automática GPC con IA
### GS1 Venezuela · Proyecto "Asignación GPC"

---

## 1. Resumen ejecutivo

Entre el **21 de octubre y el 10 de noviembre de 2026**, GS1 Venezuela construyó y ejecutó un
pipeline de clasificación automática de su catálogo histórico de productos bajo el estándar
**GPC (Global Product Classification)** de GS1, usando dos modelos de Claude (Anthropic) vía
la Batch API.

**Resultado final:** 1.428.900 productos procesados, correspondientes a **33 años** de catálogo
(1993–2025), con una **efectividad general de asignación del 86,47 %** y un costo real de
**$1.050 USD**.

Este documento describe qué se hizo, cuánto se hizo, cuándo se hizo y qué se aprendió, como
base para que otra oficina nacional de GS1 (Member Organization, "MO") pueda evaluar y
replicar el método con su propio catálogo. El **cómo** — el procedimiento paso a paso — está
en el documento separado `MANUAL_PROCEDIMIENTOS.md` de esta misma carpeta.

---

## 2. Contexto y objetivo

GS1 Venezuela mantiene un catálogo histórico de productos (código de barras, marca,
descripción, fechas, empresa) que nunca había sido clasificado de forma completa y
consistente bajo GPC. Clasificar manualmente 1,4 millones de registros no es viable. El
objetivo del proyecto fue:

1. Clasificar automáticamente cada producto contra el catálogo oficial GPC vigente.
2. Lograrlo sin heurísticas que inflen artificialmente el resultado (ver sección 6).
3. Hacerlo a un costo acotado y conocido.
4. Dejar el resultado organizado y auditable, año por año.

---

## 3. Línea de tiempo

El trabajo se hizo de forma incremental, año por año, generalmente desde el más reciente
hacia el más antiguo, refinando el método en el camino.

| Fecha | Hito |
|---|---|
| 21–23 oct 2026 | Arranque del proyecto: primeros años (2024–2025), diseño del prompt, primera versión de la pasada Haiku y la pasada de rescate Sonnet. |
| 27 oct – 2 nov 2026 | Ajustes puntuales, reprocesos dirigidos a casos difíciles detectados (ver sección 6.2). |
| 5–6 nov 2026 | Tramo más intensivo: procesamiento de la mayoría de los años restantes (2010–2023 y gran parte de 1993–2009), más de 100 commits en dos días. |
| 7 nov 2026 | Cierre de 2010–2025, reorganización completa del repositorio en carpetas, primer informe consolidado. |
| 9–10 nov 2026 | Eliminación de la heurística Marca→Segmento de los años que la tenían, compactación de archivos fragmentados en `Final_<año>.xlsx`, empaquetado para replicación. |

Duración total: **~3 semanas**, con 165 commits registrados en el repositorio.

---

## 4. Metodología (resumen)

1. **Catálogo oficial GPC** como única fuente de verdad — el mismo catálogo público y global
   de GS1, sin modificaciones.
2. **Preselección local de candidatos** por búsqueda léxica contra el catálogo (sin costo de
   API): para cada producto se seleccionan los 25 Bricks más afines más sus padres
   Class/Family/Segment.
3. **Pasada 1 — Claude Haiku 5.5**, vía Batch API: clasifica cada producto contra sus
   candidatos. Salida recortada a un JSON mínimo (`gpc_code`, `confidence_score`).
4. **Pasada 2 — Claude Sonnet 5.5**, vía Batch API: reintenta únicamente los productos que
   Haiku no pudo resolver (`NO_MATCH`), con el mismo esquema de candidatos y salida.
5. **Sin heurísticas de atajo**: en una primera versión del proyecto se usó una heurística
   Marca→Segmento para rellenar algunos `NO_MATCH` adicionales; se detectó que esto
   maquillaba la efectividad real y se **eliminó por completo** (sección 6.1). El resultado
   reportado aquí es 100 % decisión de los modelos.
6. **Organización del resultado**: un archivo `Final_<año>.xlsx` por año (1993–2025), y dos
   vistas derivadas — `Output_Asignados/` y `Output_NoMatch/` — también una por año.

El detalle técnico completo (prompts exactos, parámetros, estructura de columnas) está en
`MANUAL_PROCEDIMIENTOS.md`.

---

## 5. Resultados

### 5.1 Totales generales (1993–2025)

| Métrica | Valor |
|---|---|
| Años cubiertos | 33 (1993–2025) |
| Productos procesados | 1.428.900 |
| Asignados (con código GPC) | 1.235.558 |
| **Efectividad general** | **86,47 %** |
| Sin coincidencia (`NO_MATCH`) | 193.342 (13,53 %) |

### 5.2 Efectividad por periodo

| Periodo | Productos | % Asignado |
|---|---|---|
| 1993–1999 | 119.712 | 85,41 % |
| 2000–2009 | 337.691 | 82,84 % |
| 2010–2017 | 503.847 | 80,39 % |
| 2018–2025 | 467.650 | **95,92 %** |

La efectividad sube notablemente en los años recientes, principalmente porque los datos de
entrada (descripciones de producto) son de mejor calidad y más completos en los años más
nuevos del catálogo.

---

## 6. Lecciones aprendidas y limitaciones

### 6.1 La heurística Marca→Segmento (eliminada)

Una versión temprana del proyecto, para los años 2000–2025, incluía una heurística que
asignaba un Segment genérico basándose solo en la marca del producto cuando ambos modelos
fallaban. Esto subía artificialmente el porcentaje de "asignados" sin que el modelo hubiera
razonado realmente sobre el producto. Se identificó la firma exacta de esa heurística
(`confidence_score == 40` de forma fija, mientras que los reprocesos legítimos siempre traen
una confianza real devuelta por el modelo) y se revirtieron esas filas a `NO_MATCH`. **Los
números de este informe ya están limpios de esa heurística.**

**Recomendación para otra MO:** si se parte de cero, simplemente no implementar ningún atajo
de este tipo. Si se hereda un proceso con heurísticas similares, verificar si dejan una firma
de confianza fija y reconstruible, como en este caso.

### 6.2 Calidad del identificador físico de producto (GTIN)

Para los años 2018 y especialmente 2021–2025, se encontró que el campo GTIN (código de
barras) **no identifica de forma única una fila física** en una fracción relevante de los
casos: en 2023, el 98,6 % de las filas comparten GTIN con al menos otra fila (variantes de
descripción del mismo producto, reingresos, etc.). Se evaluó usar una clave alternativa
(hash de marca+descripción) pero resultó **peor**, no mejor. Se optó por usar GTIN como mejor
identificador disponible, con esta limitación documentada.

**Recomendación para otra MO:** verificar desde el inicio qué tan único es el identificador
físico disponible en los propios datos (GTIN, SKU interno, u otro) antes de asumir que
identifica una fila sin ambigüedad.

### 6.3 Reprocesos puntuales

Durante el proyecto surgieron varios casos de reproceso dirigido (ej. jeans en 2015, calzado
en 2021, sinónimos en 2020) donde un conjunto específico de productos se reclasificó aparte
tras detectar un patrón de error recurrente. Estos reprocesos usan siempre una confianza real
del modelo (nunca un valor fijo), lo que después permitió distinguirlos de la heurística
descrita en 6.1.

---

## 7. Costos

| Concepto | Valor |
|---|---|
| Modelo pasada 1 | Claude Haiku 5.5 — Batch API ($0,50 / $2,50 por MTok input/output) |
| Modelo pasada 2 (rescate) | Claude Sonnet 5.5 — Batch API ($1,50 / $7,50 por MTok input/output) |
| Productos en pasada 1 | 1.428.900 |
| Productos en pasada 2 (rescate) | 319.562 |
| **Costo real total** | **$1.050 USD** |

El costo real quedó por debajo de la proyección inicial basada en tokens promedio, gracias al
descuento de caché de Anthropic sobre el system prompt (que se repite en cada solicitud del
lote y se cobra a precio reducido a partir de la segunda vez que se usa dentro de la ventana
de caché).

---

## 8. Conclusión

El método — catálogo oficial como única fuente de verdad, preselección léxica local gratuita,
dos pasadas de modelos de Claude de capacidad creciente, sin heurísticas de atajo — logró
clasificar automáticamente el 86,47 % de 33 años de catálogo histórico por un costo total de
$1.050 USD. Es **replicable por cualquier otra oficina de GS1** sin más dependencia de los
datos venezolanos que el catálogo oficial GPC, que ya es global.

El resto de esta carpeta (`Paquete_Replicacion_MO/`) contiene todo lo necesario para que otra
MO, con su propio equipo técnico y su propia sesión de Claude, construya su propia versión
adaptada a su formato de datos. Ver `README.md` para el orden de uso.
