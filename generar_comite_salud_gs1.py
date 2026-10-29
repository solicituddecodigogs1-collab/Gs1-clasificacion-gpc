"""Genera Comite_Salud_GS1_Venezuela_Nov2026.pptx (7 láminas, 16:9, Arial)."""
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

NAVY = RGBColor(0, 44, 108)
CYAN = RGBColor(0, 168, 225)
TEAL = RGBColor(0, 133, 122)
ORANGE = RGBColor(242, 99, 52)
TEXT = RGBColor(51, 65, 85)
CARD = RGBColor(240, 246, 252)
WHITE = RGBColor(255, 255, 255)
FONT = "Arial"
W, H = 13.333, 7.5
OUT = "Comite_Salud_GS1_Venezuela_Nov2026.pptx"


def check(bullets):
    assert len(bullets) <= 5, bullets
    for b in bullets:
        assert len(b.split()) <= 10, b


def rect(s, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    r = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    r.fill.solid()
    r.fill.fore_color.rgb = fill
    if line is None:
        r.line.fill.background()
    else:
        r.line.color.rgb = line
        r.line.width = Pt(0.75)
    r.shadow.inherit = False
    return r


def text(s, x, y, w, h, t, size, color, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, link=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = t
    r.font.name, r.font.size, r.font.bold = FONT, Pt(size), bold
    r.font.color.rgb = color
    if link:
        tb.click_action.hyperlink.address = link
    return tb


def bullets_box(s, x, y, w, h, items, size=14, color=TEXT):
    check(items)
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, b in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        r = p.add_run()
        r.text = "• " + b
        r.font.name, r.font.size = FONT, Pt(size)
        r.font.color.rgb = color


def new_slide(prs, title, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.6, 0.3, 6, 0.3, "COMITÉ SALUD GS1 VENEZUELA", 11, ORANGE, True)
    text(s, W - 1.6, 0.3, 1.0, 0.3, str(n), 11, TEXT, align=PP_ALIGN.RIGHT)
    text(s, 0.6, 0.6, W - 1.2, 0.95, title, 24, NAVY, True, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, 0.6, 1.6, W - 1.2, 0.04, TEAL)
    rect(s, 0.6, 1.66, W - 1.2, 0.02, ORANGE)
    return s


def box(s, x, y, w, h, title, items, accent=TEAL, size=14):
    rect(s, x, y, w, h, CARD, line=RGBColor(203, 213, 225))
    rect(s, x, y, 0.08, h, accent)
    text(s, x + 0.2, y + 0.1, w - 0.3, 0.5, title, 16, accent, True, anchor=MSO_ANCHOR.MIDDLE)
    bullets_box(s, x + 0.2, y + 0.7, w - 0.3, h - 0.8, items, size)


def kpi(s, x, y, w, h, value, label, sub, accent=TEAL):
    rect(s, x, y, w, h, CARD, line=RGBColor(203, 213, 225))
    rect(s, x, y, w, 0.08, accent)
    text(s, x + 0.1, y + 0.12, w - 0.2, 0.6, value, 32, accent, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    text(s, x + 0.1, y + 0.75, w - 0.2, 0.3, label, 15, NAVY, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    text(s, x + 0.1, y + 1.05, w - 0.2, 0.35, sub, 12, TEXT, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def table(s, x, y, w, h, headers, rows, col_w):
    gt = s.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    t = gt.table
    for i, cw in enumerate(col_w):
        t.columns[i].width = Inches(cw)
    for r in t.rows:
        r.height = Inches(h / (len(rows) + 1))

    def fill(cell, v, color, bg, bold, size):
        cell.fill.solid()
        cell.fill.fore_color.rgb = bg
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        run = tf.paragraphs[0].add_run()
        run.text = v
        run.font.name, run.font.size, run.font.bold = FONT, Pt(size), bold
        run.font.color.rgb = color

    for c, hd in enumerate(headers):
        fill(t.cell(0, c), hd, WHITE, NAVY, True, 14)
    for r, row in enumerate(rows, 1):
        for c, v in enumerate(row):
            fill(t.cell(r, c), v, ORANGE if c == 2 else TEXT, WHITE if r % 2 else CARD, c == 2, 15 if c == 2 else 14)


prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)

# 1. Portada
s = prs.slides.add_slide(prs.slide_layouts[6])
rect(s, 0, 0, W, H, NAVY)
rect(s, 0, 0, 0.35, H, ORANGE)
rect(s, 0.35, H - 0.3, W - 0.35, 0.3, CYAN)
text(s, 1.0, 0.7, 6, 0.4, "GS1 HEALTHCARE", 14, ORANGE, True)
text(s, 1.0, 1.9, 11.5, 1.2, "COMITÉ SALUD GS1 VENEZUELA", 40, WHITE, True, anchor=MSO_ANCHOR.BOTTOM)
rect(s, 1.05, 3.3, 1.5, 0.06, ORANGE)
text(s, 1.0, 3.5, 11.0, 1.3,
     "Rastreo Inteligente con IA, Seguridad del Paciente y Eficiencia en la Cadena de Suministro",
     22, WHITE)
text(s, 1.0, 5.4, 11.5, 1.0,
     "5 Noviembre, 2026 | 8:30 am - 10:00 am | Oficina GS1 Venezuela, Los Ruices, Edif. Quorum, Piso 1, Ofic. K",
     14, RGBColor(203, 213, 225))

# 2. Agenda
s = new_slide(prs, "El sector salud venezolano necesita un lenguaje común para transformar su cadena de suministro", 2)
agenda = [
    ("1", "Rastreo Inteligente: IA Aplicada a la Trazabilidad Médica",
     ["Catálogos fragmentados entre laboratorios, droguerías y clínicas", "IA para homologar y anticipar fallas"], TEAL),
    ("2", "Seguridad del paciente, eficiencia y trazabilidad de medicamentos",
     ["Control de caducidades y lotes en farmacias", "Combate a ilícitos y falsificación"], ORANGE),
    ("3", "GS1 News",
     ["Avances globales y locales de GS1 Venezuela", "Códigos 2D y clasificación GPC"], CYAN),
    ("4", "Ronda Abierta",
     ["Prioridades del comité para 2027", "Pilotos e interoperabilidad entre actores"], NAVY),
]
for i, (n, t, b, c) in enumerate(agenda):
    x, y = 0.6 + (i % 2) * 6.17, 1.95 + (i // 2) * 2.55
    rect(s, x, y, 5.95, 2.35, CARD, line=RGBColor(203, 213, 225))
    rect(s, x, y, 5.95, 0.08, c)
    o = rect(s, x + 0.2, y + 0.3, 0.6, 0.6, c, shape=MSO_SHAPE.OVAL)
    tf = o.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = n
    r.font.name, r.font.size, r.font.bold = FONT, Pt(20), True
    r.font.color.rgb = WHITE
    text(s, x + 1.0, y + 0.2, 4.8, 0.85, t, 16, NAVY, True, anchor=MSO_ANCHOR.MIDDLE)
    bullets_box(s, x + 1.0, y + 1.1, 4.8, 1.2, b, 15)

# 3. Punto 1
s = new_slide(prs, "La IA sobre GTIN, GLN y GPC automatiza la homologación de catálogos y anticipa fallas de abastecimiento", 3)
kpi(s, 0.6, 1.95, 3.9, 1.5, "3", "Estándares integrados", "GTIN · GLN · GPC", TEAL)
kpi(s, 4.72, 1.95, 3.9, 1.5, "1", "Maestro único de producto", "Catálogo común entre actores", ORANGE)
kpi(s, 8.83, 1.95, 3.9, 1.5, "24/7", "Monitoreo de lotes", "Alertas de vencimiento y frío", TEAL)
box(s, 0.6, 3.7, 6.0, 3.2, "Estandarización asistida por IA en bases de datos de SKUs farmacéuticos",
    ["Homologa descripciones entre laboratorios y droguerías", "Asigna GPC y valida GTIN automáticamente",
     "Detecta duplicados y atributos faltantes", "Alimenta un maestro común de productos"], TEAL, 17)
box(s, 6.73, 3.7, 6.0, 3.2, "Analítica predictiva de lotes y cadena de frío",
    ["Anticipa quiebres de stock por lote y GLN", "Alerta caducidades próximas antes del vencimiento",
     "Vigila desviaciones de temperatura en tránsito", "Prioriza redistribución entre sedes"], ORANGE, 17)

# 4. Punto 2
s = new_slide(prs, "GS1 DataMatrix en hospitales y farmacias venezolanas protege al paciente y ordena la cadena de suministro", 4)
for i, (k, v) in enumerate([("GTIN", "Producto"), ("LOTE", "Fabricación"), ("VENCIMIENTO", "Caducidad"), ("SERIAL", "Unidad")]):
    x = 0.6 + i * 3.1
    rect(s, x, 1.95, 2.95, 0.85, NAVY)
    text(s, x + 0.1, 1.97, 2.75, 0.5, k, 18, WHITE, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    text(s, x + 0.1, 2.4, 2.75, 0.35, v, 13, CYAN, False, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
pill = [
    ("Seguridad del Paciente", ["Verifica producto correcto antes de administrar", "Reduce errores de medicación en clínicas",
                                "Bloquea medicamentos vencidos en dispensación"], TEAL),
    ("Eficiencia Logística", ["Gestión FEFO en droguerías", "Mejora Fill Rate y OTIF",
                              "Inventarios precisos por lote"], ORANGE),
    ("Trazabilidad Unitaria", ["Identifica cada unidad con serial único", "Combate contrabando y falsificación",
                               "Agiliza retiros de lotes defectuosos"], CYAN),
]
for i, (t, b, c) in enumerate(pill):
    box(s, 0.6 + i * 4.15, 3.05, 3.95, 3.85, t, b, c, 17)

# 5. Caso de éxito
s = new_slide(prs, "NHS y ANMAT demuestran que la trazabilidad con estándares GS1 reduce riesgos y costos", 5)
table(s, 0.6, 1.95, 12.13, 2.4, ["Indicador", "Programa", "Resultado", "Lección para Venezuela"], [
    ["Retiro de lotes defectuosos", "Scan4Safety, NHS (Reino Unido)", "-76% en tiempo", "Retiros rápidos por lote y serial"],
    ["Inventario hospitalario", "Scan4Safety, NHS (Reino Unido)", "Millones de £ ahorrados", "Menos sobrestock y vencidos"],
    ["Medicamentos falsificados", "SNT, ANMAT (Argentina)", "0% en canal legal", "Verificación unitaria en el canal"],
], [3.0, 3.3, 2.5, 3.33])
text(s, 0.6, 4.5, 12, 0.4, "Modelo escalonado para replicar en Venezuela", 16, NAVY, True)
for i, (t, d, c) in enumerate([
    ("Fase 1 · Clínicas piloto", "GLN, GTIN y DataMatrix en puntos de uso", TEAL),
    ("Fase 2 · Droguerías", "FEFO, lotes y seriales en distribución", ORANGE),
    ("Fase 3 · Red nacional", "Interoperabilidad de maestros y verificación", CYAN)]):
    x = 0.6 + i * 4.15
    rect(s, x, 5.0, 3.95, 1.35, CARD, line=RGBColor(203, 213, 225))
    rect(s, x, 5.0, 3.95, 0.08, c)
    text(s, x + 0.15, 5.15, 3.65, 0.4, t, 15, c, True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.15, 5.6, 3.65, 0.7, d, 14, TEXT)
text(s, 0.6, 6.6, 12.1, 0.5,
     "Cifras de referencia de los programas citados; validar con fuentes oficiales NHS y ANMAT antes de difundir.",
     10, TEXT)

# 6. GS1 News
s = new_slide(prs, "GS1 Venezuela avanza hacia códigos 2D, catálogos clasificados con GPC y grupos técnicos de trabajo", 6)
box(s, 0.6, 1.95, 3.95, 4.95, "Transición a GS1 DataMatrix",
    ["Códigos 2D en empaques secundarios", "Adopción progresiva en empaques primarios",
     "Más datos por código: lote y vencimiento"], TEAL, 17)
box(s, 4.69, 1.95, 3.95, 4.95, "Clasificación masiva con GPC",
    ["Limpieza de catálogos del sector farmacéutico", "Clasificación bajo estándar GPC",
     "Base para homologar entre actores"], ORANGE, 17)
box(s, 8.78, 1.95, 3.95, 4.95, "Grupos de trabajo técnicos",
    ["Mesas con laboratorios y droguerías", "Participación de farmacias y clínicas",
     "Guías de implementación por sector"], CYAN, 17)

# 7. Ronda abierta
s = new_slide(prs, "Sus prioridades para 2027 definirán los pilotos de trazabilidad e interoperabilidad del sector", 7)
box(s, 0.6, 1.95, 7.2, 4.95, "Preguntas para el comité",
    ["¿Cuáles son las prioridades de su organización en 2027?",
     "¿Qué piloto de trazabilidad podríamos iniciar primero?",
     "¿Cómo interoperar maestros de productos entre actores?",
     "¿Qué barreras frenan hoy la adopción de DataMatrix?"], TEAL, 19)
box(s, 7.93, 1.95, 4.8, 2.5, "Próximos pasos",
    ["Consolidar prioridades del comité", "Definir piloto y responsables"], ORANGE, 17)
rect(s, 7.93, 4.65, 4.8, 2.25, NAVY)
text(s, 8.13, 4.8, 4.4, 0.4, "CONTACTO", 14, ORANGE, True)
text(s, 8.13, 5.3, 4.4, 0.5, "+58 414 2771877", 20, WHITE, True)
text(s, 8.13, 6.0, 4.4, 0.5, "www.gs1ve.org", 18, CYAN, True, link="https://www.gs1ve.org")

prs.save(OUT)
print("Generado", OUT)
