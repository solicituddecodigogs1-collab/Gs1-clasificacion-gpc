# Paquete de replicación — Clasificación automática GPC con Claude

Este es un paquete completo y autocontenido para que **otra oficina nacional de GS1 (MO)**
replique, con su propio catálogo y su propio equipo técnico, el proyecto de clasificación
automática GPC que construyó GS1 Venezuela.

No depende de nada fuera de esta carpeta: cópiala entera a donde la vayas a usar.

## Orden de uso recomendado

1. **`INFORME_TECNICO.md`** — léelo primero. Qué se hizo, cuánto, cuándo, los resultados
   reales (90,20 % de efectividad, $1.050 USD de costo) y las limitaciones ya conocidas.
   Incluye también (sección 8) un segundo método, complementario, de clasificación en capas
   usado para rescatar el `NO_MATCH` residual de 1993-2007 con 100 % de éxito.
2. **`CONTEXTO_PARA_CLAUDE.md`** — este es el archivo que le das directamente a tu propia
   sesión de Claude (pégalo como primer mensaje, o úsalo como `CLAUDE.md` del repositorio
   nuevo). Está escrito para que Claude lo lea y empiece a trabajar con tu equipo.
3. **`MANUAL_PROCEDIMIENTOS.md`** — el método paso a paso en detalle: el system prompt
   exacto, los parámetros de la Batch API, las reglas de control de calidad. Es la
   especificación que tu Claude debe seguir.
4. **`ejemplos/`** — un caso real completo (prompt + respuesta + fila antes/después) para
   que quede claro, sin ambigüedad, qué entra y qué sale del modelo.
5. **`catalogo/gpc_catalogo_oficial.csv`** — el catálogo oficial GPC. Úsalo tal cual, es
   global y no requiere adaptación.
6. **`scripts_referencia/`** — el código real de GS1 Venezuela. Es material de lectura para
   entender la lógica, **no un programa para ejecutar tal cual** — tiene nombres de columna y
   rutas específicas de los datos venezolanos. Tu Claude debe escribir su propia versión
   adaptada a tus datos, usando esto como referencia de la lógica (candidatos,
   system prompt, fusión de resultados).

## Contenido de la carpeta

```
Paquete_Replicacion_MO/
├── README.md                          (este archivo)
├── INFORME_TECNICO.md / .docx         (qué se hizo, resultados, costos, lecciones aprendidas)
├── MANUAL_PROCEDIMIENTOS.md / .docx   (el método, paso a paso, con el prompt exacto)
├── CONTEXTO_PARA_CLAUDE.md / .docx    (el mensaje para darle a tu propia sesión de Claude)
├── catalogo/
│   └── gpc_catalogo_oficial.csv       (catálogo oficial GPC — global, sin adaptar)
├── ejemplos/
│   ├── ejemplo_prompt_real.md         (caso real: prompt + respuesta + fila antes/después)
│   ├── ejemplo_candidatos_completo.txt (el bloque de candidatos completo de ese caso)
│   └── auditoria_1993_2007.csv        (resultado real del rescate en capas, 100% resuelto)
└── scripts_referencia/                (código real de GS1 Venezuela, como referencia de lectura)
    ├── preclasificador.py             (catálogo + búsqueda léxica de candidatos)
    ├── submit_batches.py              (pasada 1 — Claude Haiku 5.5)
    ├── submit_batches_rescate.py      (pasada 2 — Claude Sonnet 5.5, rescate de NO_MATCH)
    ├── retrieve_batches.py            (recuperación y fusión de resultados del lote)
    └── clasificar_nomatch_plantilla_argentina.py (procedimiento complementario de 5 capas,
                                          sección 8 del manual — rescate del NO_MATCH residual.
                                          Ya adaptado: prefijo GS1 779/778 y CUIT en vez de
                                          759/RIF. Las reglas de negocio de la capa 1 son
                                          PLACEHOLDERS — reemplázalas por las tuyas antes de
                                          correrlo. El original real de GS1 Venezuela, con sus
                                          datos de afiliados, se queda en la rama principal del
                                          repo, no en este paquete)
```
