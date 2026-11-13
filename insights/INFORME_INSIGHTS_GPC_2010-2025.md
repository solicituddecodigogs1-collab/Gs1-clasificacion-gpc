# Informe de inteligencia de codificación GS1 Venezuela, 2010–2025

## Base y método
- **Fuente:** `insights/<año>/Final_AAAA.xlsx` y `NO_MATCH_AAAA_CLASIFICADO.xlsx`. Las filas `NO_MATCH` de cada Final se sustituyen por su versión clasificada.
- **Segmento, familia y clase:** se obtienen del catálogo oficial (`catalogo/gpc_catalogo_oficial.csv`) a partir del código GPC asignado.
- **Depuración:** se eliminaron los GTIN duplicados dentro del mismo año. **Esto cambia conclusiones del análisis anterior** (ver §1).
- **Resultado:** 922,770 GTIN únicos por año, 7,719 prefijos de empresa y 45 segmentos.
- **Tablas de apoyo:** `insights/_resumen/*.csv`.

## 1. Corrección importante: el pico de 2023 era duplicación
- El archivo 2023 tiene 94,525 filas, pero solo **47,382 GTIN únicos (−49.9%)**. Hay 93,254 filas duplicadas casi idénticas (99.9%), con el mismo GTIN, fecha y clasificación.
- En 2021, 2022, 2024 y 2025 la duplicación es de 0.2–1.4%. En 2010–2020 es nula.
- Con datos depurados, **2021–25 (249,629 GTIN) es −10.3% frente a 2016–20 (278,222)**. El informe anterior decía +7.2%, y eso estaba inflado por 2023.

| Período | GTIN únicos | Promedio anual |
|---|---|---|
| 2010–15 | 394,919 | 65,820 |
| 2016–20 | 278,222 | 55,644 |
| 2021–25 | 249,629 | 49,926 |

| Año | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| GTIN únicos | 41,101 | 40,940 | 41,627 | 47,382 | 51,341 | **68,339** |

**Lectura:** el mercado tocó fondo en 2020–22 (~41k por año). Se recupera de forma sostenida desde 2023, con +18.2% en 2024 y **+33.1% en 2025**.

## 2. Segmentos (GTIN únicos)

**Con mayor aceleración (2016–20 → 2021–25)**

| Segmento | 2016–20 | 2021–25 | Var. | Peso | 2025 |
|---|---|---|---|---|---|
| Arte/Artesanía/Costura | 2,419 | 6,166 | +155% | 0.9% → 2.5% | 1,498 |
| Fontanería/HVAC | 4,225 | 9,713 | +130% | 1.5% → 3.9% | 4,199 |
| Papelería/Artículos para celebraciones | 3,973 | 7,187 | +81% | 1.4% → 2.9% | 1,779 |
| Productos de construcción | 14,339 | 22,359 | +56% | 5.2% → 9.0% | 8,905 |
| Asistencia sanitaria | 12,237 | 19,083 | +56% | 4.4% → 7.6% | 4,778 |

**En contracción**

| Segmento | 2016–20 | 2021–25 | Var. |
|---|---|---|---|
| Hogar/Mobiliario | 11,997 | 5,600 | −53% |
| Limpieza/Higiene del hogar | 15,482 | 8,063 | −48% |
| Belleza/Cuidado personal | 32,234 | 17,215 | −47% |
| Herramientas | 5,234 | 2,738 | −48% |
| Automotriz | 12,891 | 9,786 | −24% |
| Alimentos/Bebidas | 66,760 | 60,346 | −10% |
| Prendas de vestir | 31,516 | 31,130 | −1% |

**Hallazgos dentro de los segmentos** (a nivel familia GPC)
- **Salud:** Medicamentos farmacéuticos pasó de 1,073 a 8,141 (+659%) y Dispositivos médicos de 291 a 3,726 (+1,180%). En cambio, Ayudas/tratamientos de salud cayó 31%.
- **Prendas de vestir:** Trajes de baño pasó de 926 a 8,895 (+861%). Ropa protectora (−54%) y Ropa interior (−49%) caen.
- **Construcción** y **Fontanería** crecen de forma homogénea, sin un sub-rubro dominante: +62% y +103%.

Alimentos/Bebidas alcanzó su máximo peso relativo en 2020 (33.9% del año), más por la caída de otros segmentos que por crecimiento propio: sus GTIN bajaron de 16,917 (2019) a 13,928 (2020).

## 3. Anomalías explicadas por afiliado
Los picos se explican por pocas empresas que cargan catálogos grandes de golpe. En los años anteriores a 2018 los nombres vienen anonimizados (`gs1_afiliado_<RIF>_<id>`), así que aparecen por su id.

| Año | Anomalía | Causa identificada |
|---|---|---|
| 2011 | Total 99,774; Belleza 26,345 (×9.7) | Un solo afiliado (id 1274) aporta **38,748 GTIN (38.8% del año)**, 22,597 de ellos en Belleza |
| 2012 | Herramientas 8,916 (×5) | Un afiliado (id 3545) con 6,687 GTIN de herramientas |
| 2015 | Prendas 26,297 (+162%) | Afiliado id 4382 con 12,253 GTIN de prendas, más otro con 4,899 |
| 2016 | Comunicaciones 4,048 | Afiliado id 7767 con 3,975 |
| 2019 | Salud 4,834 (×2.5) | Avexim de Venezuela aporta 2,500 GTIN, todos de Salud |
| 2023 | Duplicación de filas | Ver §1. Los GTIN únicos crecieron un 13.8% real (41,627 → 47,382) |
| 2025 | Total +33% | **Textiles Gams** con 9,029 GTIN, concentrados en octubre (días 9, 13 y 14); **Distribuidora de Aluminio El Aluminiero** con 7,194; **Corporación Vettal** con 4,340, cargados en diciembre |

**Estacionalidad** (GTIN únicos, 2018–2025): mayo (9.9%), junio (9.6%) y octubre (10.8%) son los meses fuertes. Diciembre (6.0%) y enero (5.4%) son los más bajos.
- **Día de la semana:** el lunes concentra el 25.0% de los registros, y sábado y domingo suman menos del 1%.
- Considerando toda la serie, marzo destaca (12.5%), por el efecto de cargas puntuales en años anteriores a 2018.

## 4. Concentración

**Por segmento:** estable, sin diversificación estructural.

| Período | Segmentos que suman el 80% | Top 3 | HHI |
|---|---|---|---|
| 2010–15 | 12 | 49.0% | 989 |
| 2016–20 | 11 | 46.9% | 1,009 |
| 2021–25 | 11 | 45.6% | 1,029 |

**Por afiliado:** concentración muy alta.
- **117 prefijos (1.5% de 7,719) generan el 50% de todos los GTIN.** Los 10 mayores suman el 20.8% y el 1% superior suma el 44.4%.
- Los afiliados con más de 1,000 filas históricas son 140 y concentran cerca del 52% del volumen; los 2,926 con 10 o menos suman alrededor del 1.5% (cifras sobre filas, sin depurar duplicados).
- **El 25% de los GTIN de 2021–25 lo generan 10 empresas.** Entre ellas están Distribuidora Gimbo (calzado, 11,131), Coratex (prendas, 10,486), Textiles Gams (9,030), Distribuidora de Aluminio (7,194) y Crisvi (arte, 6,288).
- En 2025 el top 5 de afiliados sumó el 35.3% del año, frente a 15.4% en 2022.
- **Consecuencia:** un solo afiliado grande puede mover el total de un año o de un segmento. Por eso se justifica seguimiento de cuentas clave.

## 5. Captación y retención de afiliados

| Año | Afiliados activos | Nuevos | % de GTIN de afiliados nuevos |
|---|---|---|---|
| 2016 | 1,541 | 651 | 35% |
| 2020 | 1,305 | 456 | 29% |
| 2022 | 1,280 | 347 | 22% |
| 2024 | 1,349 | 371 | **14%** |
| 2025 | 1,245 | 310 | 35% |

- **Afiliados nuevos por año:** cayeron de 651 (2016) a 310 (2025), el valor más bajo de la serie. Los nuevos aportan cada vez menos GTIN, salvo en 2025, donde 310 empresas nuevas generan el 35% por el efecto de las grandes cargas.
- **Retención interanual:** entre 40% (2018) y 56% (2011), y 52–54% en 2022–25.
- **Vida corta:** el 51% de los prefijos registra actividad en un solo año. Solo 282 afiliados codifican en 10 años o más.
- **Nuevos afiliados 2021–25:** su segmento dominante es Alimentos/Bebidas en 1,188 casos, luego Salud (132), Limpieza (101) y Belleza (84). Hay base amplia de pequeños afiliados en alimentos, pero con pocos GTIN cada uno (19.7 GTIN por afiliado en 2024–25, frente a 231 en Prendas y 250 en Calzado).

## 6. Calidad de clasificación
- **Mejora clara:** los GTIN clasificados a nivel Brick pasaron de 68.7% (2010) a 86.5% (2025), con un máximo de 92.1% en 2022. Los que quedan solo a nivel Segmento bajaron de 29.5% (2011) a 2.0% (2023–24).
- **Retroceso en 2025:** sube a 5.2% solo-segmento y a 17.8% con confianza menor a 70 (8.5% en 2023). Coincide con las cargas masivas de 2025.
- **Segmentos con peor clasificación:** Belleza (48.4% solo a nivel Segmento) y Salud (20.0%). Alimentos/Bebidas tiene 12.7% genérico.
- La confianza promedio es 72.5 en los datos Final y 94.4 en los NO_MATCH reclasificados.

## 7. Otros hallazgos
- **GTIN-14 (unidades logísticas):** representan entre el 28% y el 35% de los GTIN entre 2018 y 2024. En 2025 baja a 20.9%. En Fontanería/HVAC suben a 41% y en Salud a 36%. Conviene revisar si el cambio refleja un tipo de cargas distinto.
- **Origen del registro** (desde 2021): Sistema de Gestión y Sistema de Solicitud suman casi todo. En 2025 aparecen `Sistema Odoo` (1,821) y `App` (755).
- **Mercado exterior:** entre el 94.7% y el 100% de los registros comercializa en Venezuela. Solo el 1.9–5.3% declara otros países desde 2021.
- **Marcas:** 53,081 marcas distintas. La más grande es GIGETTO (48,111, la carga de 2011). Entre 2021 y 2025 destacan Ovejita (9,030), Crisvi (5,571), Only Uniform (5,119) y Kavak (5,099).
- **Estatus Retirado:** los datos de 2018–2020 sí lo registran (27.2%, 5.9% y 6.5%), pero desde 2021 es menor al 1%. No sirve para medir ciclo de vida porque depende del momento de la extracción.

## 8. Recomendaciones
1. **Gestión de cuentas clave (alto impacto).** 10 empresas generan el 25% de los GTIN de 2021–25. Asignar ejecutivo de cuenta, calendario de cargas y alertas si una cuenta deja de codificar. El objetivo es suavizar los picos y no depender de unos pocos clientes.
2. **Ofensiva comercial en Construcción, Ferretería/HVAC y Salud.** Son los segmentos que aceleran: +56% a +130% con clientes concentrados (Fontanería: el top 5 reúne el 77% de los GTIN de 2021–25). Se puede prospectar a fabricantes y distribuidores de ese ecosistema. Para Salud, capacitación en Medicamentos y Dispositivos médicos, que crecen mucho y requieren mejor clasificación.
3. **Recuperar la captación de nuevos afiliados.** La cohorte anual cayó de 651 a 310 y casi la mitad de los afiliados no vuelve al año siguiente. Un programa de onboarding en los primeros 12 meses puede mejorar la retención desde el 52–54% actual. La captación debería enfocarse en Alimentos/Bebidas (mayor número de nuevos) y Belleza/Limpieza, que perdieron cerca del 47–48%.
4. **Controles de calidad en la carga.** Detectar GTIN duplicados antes de publicar (la duplicación de 2023 duplicó el total anual) y revisar la clasificación a nivel Segmento en Belleza y Salud.

## 9. Limitaciones
- **GTIN duplicados:** 1,654 GTIN aparecen en más de un año. Cuentan una vez por año y no representan nuevos productos.
- **Identificación de afiliados:** en los años anteriores a 2018 el afiliado se identifica por el campo de prefijo, y los nombres vienen anonimizados.
- **Clasificación por algoritmo:** el segmento proviene de la asignación automática. Los GTIN clasificados solo a nivel Segmento son una aproximación y no distinguen entre familias.
- **Años sin país o estatus:** el país y el estatus solo existen en parte de los archivos (2018 en adelante), así que esos análisis no cubren toda la serie.
- **Causas:** las explicaciones de picos son por afiliado y son verificables. Las causas de negocio de cada carga (migración, regularización, lanzamiento) no pueden saberse con esta data.
