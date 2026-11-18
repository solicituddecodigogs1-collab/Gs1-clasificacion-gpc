# insights

Datos de codificación de GS1 Venezuela clasificados con GPC y los productos que se derivan de ellos.

## Estructura

```
insights/
├── <año>/                       1993 … 2025, una carpeta por año
│   ├── Final_<año>.xlsx             registro del año con su clasificación GPC
│   └── NO_MATCH_<año>_CLASIFICADO.xlsx   filas que la primera pasada no logró clasificar, ya reclasificadas
├── _resumen/                    tablas de apoyo (sin nombres de empresa)
│   ├── gtins_por_segmento_y_ano.csv
│   ├── metricas_por_segmento.csv
│   ├── variacion_segmentos_2016-20_vs_2021-25.csv
│   ├── captacion_afiliados_por_ano.csv
│   ├── calidad_clasificacion_por_ano.csv
│   └── INFORME_2010-2025_version_anterior.md
├── Boletin_insights_GS1_edicion_revista.pdf
└── _fuente_boletin/             HTML editable del boletín + render.js para regenerar el PDF (ver LEEME.md)
```

## Cómo se cuentan los códigos

- En cada `Final_<año>.xlsx`, las filas con `gpc_code = NO_MATCH` se sustituyen por su versión clasificada de `NO_MATCH_<año>_CLASIFICADO.xlsx`, para no contarlas dos veces.
- Un código es un GTIN único por año.
- El segmento se obtiene del catálogo oficial (`catalogo/gpc_catalogo_oficial.csv`) a partir del código GPC asignado.
- Para contar empresas se usa el prefijo de empresa; nunca se publican nombres de empresa ni marcas.
- Los archivos Final de 1993–2000 y los de 2001–2025 tienen columnas distintas; el boletín las unifica por nombre de campo.

## Límites conocidos

- No hay estado ni ciudad de las empresas: no se pueden hacer análisis regionales. `herramientas/analisis_regional.py` los calcula en cuanto exista una tabla prefijo → estado.
- La calidad de clasificación es menor en los años antiguos (más productos con solo marca y sin descripción).
- GTIN-14 solo se distingue desde 2018.
- No incluye datos de 2026.
