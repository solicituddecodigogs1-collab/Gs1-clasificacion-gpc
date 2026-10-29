---
description: Genera una presentación PPTX con la marca GS1 Healthcare (16:9, Arial) usando utils/gs1_healthcare_pptx.py
argument-hint: <tema o contenido de la presentación>
---

Crea una presentación PowerPoint de GS1 Healthcare sobre: $ARGUMENTS

## Procedimiento
1. Verifica `python-pptx` (`python3 -c "import pptx"`); si falta: `pip install python-pptx`.
2. Escribe un script Python (fuera de `utils/`) que importe desde `utils/gs1_healthcare_pptx.py`:
   `create_gs1_deck, add_gs1_cover, add_gs1_header, add_gs1_kpi_card, add_gs1_content_box, add_gs1_table` y las constantes de color.
3. Estructura: portada (`add_gs1_cover`) y láminas creadas con `prs.slides.add_slide(prs.slide_layouts[6])` (únicamente el layout en blanco), cada una con `add_gs1_header`.
4. Guarda el `.pptx` en `Output_Presentaciones/` y reporta la ruta.

## Reglas de diseño (obligatorias)
- Widescreen 16:9 (13.333 x 7.5 in); posicionamiento exacto con `Inches`. Área útil: x 0.6–12.73, y 1.9–7.0.
- Fuente `Arial`. Paleta: GS1_BLUE #002C6C, GS1_HC_TEAL #00857A, GS1_ORANGE #F26334, GS1_SKY #009CDE, GS1_TEXT #334155, GS1_BG_LIGHT #F0F4F8, GS1_BORDER #CBD5E1. No introduzcas otros colores.
- Action Titles: cada título es una oración completa con la conclusión o hallazgo principal.
- Máximo 5 viñetas por bloque y 10 palabras por viñeta (el módulo lanza `ValueError` si se excede).
- `word_wrap = True` en toda caja de texto y `MSO_ANCHOR.MIDDLE` en toda celda de tabla (ya aplicado por los helpers).
- Usa `highlight=True` en KPIs solo para la cifra clave de la lámina.
- Sin solapamientos: verifica que cada elemento quede dentro de la lámina y no se superponga.

## Helpers
- `add_gs1_cover(prs, title, subtitle, meta_info)`
- `add_gs1_header(slide, action_title, tracker="GS1 HEALTHCARE", slide_num=None)`
- `add_gs1_kpi_card(slide, left, top, width, height, value, label, sublabel="", highlight=False)`
- `add_gs1_content_box(slide, left, top, width, height, title, bullets, accent_color=GS1_HC_TEAL)`
- `add_gs1_table(slide, left, top, width, height, headers, rows, col_widths=None)`
