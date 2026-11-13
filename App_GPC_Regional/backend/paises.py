#!/usr/bin/env python3
"""Configuración por país para las 19 MO de GS1 en América Latina.

IMPORTANTE — los 19 prefijos GS1 se verificaron el 13-nov-2026 contra
https://en.wikipedia.org/wiki/List_of_GS1_country_codes (coincide con la
lista oficial de rangos de GS1; confirmar ahí mismo o en
https://www.gs1.org/standards/id-keys/company-prefix si se necesita para
validación estricta de GTIN). Esto no bloquea el uso de la app: aquí son
solo un dato de referencia que se le muestra al usuario, no se usan para
rechazar ni aceptar códigos de barra.

El identificador fiscal es solo una ETIQUETA de referencia (para que el
campo de la interfaz diga "CUIT" en vez de "RIF" según el país elegido),
no una validación de formato.

`jerga_sugerida` es un PUNTO DE PARTIDA editable, no un glosario exhaustivo
ni verificado contrato por contrato: reúne regionalismos de alimentos que
cambian de nombre entre países (confirmados por fuentes lingüísticas, ver
el regionalismo marcado) y abreviaturas de empaque de uso extendido en
catálogos de supermercado de la región (de conocimiento general, no
verificadas contra un catálogo real de cada país). El objetivo es ayudar
al modelo a no confundir, por ejemplo, "cambur" venezolano con otra cosa
que no sea "banana" — cada MO debe ajustarlo con los términos reales de
su propio catálogo antes de clasificar.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Pais:
    nombre: str
    prefijo_gs1: str
    prefijo_verificado: bool
    id_fiscal: str  # etiqueta de referencia, ej. "CUIT", "RFC"
    jerga_sugerida: str = ""  # punto de partida editable, ver docstring del módulo


PAISES: dict[str, Pais] = {
    "México": Pais(
        "México", "750", True, "RFC",
        "Regionalismos: frijol (no poroto/caraota), aguacate (no palta), "
        "elote=maíz tierno, refresco=gaseosa, despensa=abarrotes. "
        "Abreviaturas de empaque frecuentes: PZA=pieza, C/U=cada uno, "
        "PQ/PAQ=paquete, GDE=grande, CH=chico/chica, FCO=frasco, KG, GR, LT, ML.",
    ),
    "Guatemala": Pais(
        "Guatemala", "740", True, "NIT",
        "Regionalismos: frijol (negro, volteado), aguacate, gaseosa=refresco "
        "(ambos se usan), elote=maíz tierno. La libra sigue usándose como "
        "unidad de venta junto al kilo en mercados tradicionales. "
        "Abreviaturas: UND=unidad, PAQ=paquete, LB=libra, GDE/CH, DOC=docena.",
    ),
    "El Salvador": Pais(
        "El Salvador", "741", True, "NIT",
        "Regionalismos: frijol, aguacate, gaseosa, elote=maíz tierno, "
        "curtido (no es un producto GPC estándar, cuidado con confundirlo). "
        "La libra convive con el kilo como unidad de venta. "
        "Abreviaturas: UND=unidad, PAQ=paquete, LB=libra, GDE/CH.",
    ),
    "Honduras": Pais(
        "Honduras", "742", True, "RTN",
        "Regionalismos: frijol (rojo), aguacate, gaseosa, elote=maíz tierno, "
        "guineo=banano pequeño (distinto de plátano/plátano macho). "
        "Libra de uso común junto al kilo. "
        "Abreviaturas: UND=unidad, PAQ=paquete, LB=libra, GDE/CH.",
    ),
    "Nicaragua": Pais(
        "Nicaragua", "743", True, "RUC",
        "Regionalismos: frijol (rojo), aguacate, gaseosa, elote=maíz tierno, "
        "guineo=banano pequeño (distinto de plátano). "
        "Libra de uso común junto al kilo. "
        "Abreviaturas: UND=unidad, PAQ=paquete, LB=libra, GDE/CH.",
    ),
    "Costa Rica": Pais(
        "Costa Rica", "744", True, "Cédula Jurídica",
        "Regionalismos: frijol (negro), aguacate, gaseosa=refresco (ambos se "
        "usan), elote=maíz tierno, pipa=coco de agua. Libra de uso común "
        "junto al kilo. Abreviaturas: UND=unidad, PAQ=paquete, LB=libra, GDE/CH.",
    ),
    "Panamá": Pais(
        "Panamá", "745", True, "RUC",
        "Regionalismos: frijol, aguacate, gaseosa, guineo=banano pequeño "
        "(distinto de plátano). Los precios pueden venir en balboas o "
        "dólares (equivalencia 1:1), no es un producto distinto. "
        "Abreviaturas: UND=unidad, PAQ=paquete, LB=libra, GDE/CH.",
    ),
    "Cuba": Pais(
        "Cuba", "850", True, "NIT",
        "Regionalismos: frijoles (negros, colorados), aguacate, boniato=batata, "
        "refresco=gaseosa. El mercado combina circuitos estatal y privado "
        "(MIPYMES); las descripciones de catálogo pueden variar más que en "
        "otros países. Abreviaturas: UND=unidad, PAQ=paquete, LB=libra, KG.",
    ),
    "República Dominicana": Pais(
        "República Dominicana", "746", True, "RNC",
        "Regionalismos: habichuelas=frijoles (no \"frijol\" ni \"poroto\"), "
        "aguacate, guandules, refresco/gaseosa, guineo=banano (uso muy "
        "extendido, distinto de plátano). Abreviaturas: UND=unidad, "
        "PAQ=paquete, LB=libra, GDE/CH.",
    ),
    "Venezuela": Pais(
        "Venezuela", "759", True, "RIF",
        "Regionalismos: caraotas=frijoles negros (no \"frijol\" ni \"poroto\"), "
        "cambur=banano/banana (término exclusivo de Venezuela — no confundir "
        "con plátano), aguacate, refresco=gaseosa, harina de maíz precocida "
        "(harina P.A.N. y similares) ≠ harina de trigo. Abreviaturas: "
        "UND=unidad, PAQ=paquete, KG, GR, LT, ML, CARTÓN (ej. de huevos, 30 u.).",
    ),
    "Colombia": Pais(
        "Colombia", "770-771", True, "NIT",
        "Regionalismos: fríjol (no poroto/caraota), aguacate, gaseosa, "
        "mazorca/choclo=maíz tierno. La libra es unidad de venta muy común "
        "junto al kilo, sobre todo en plaza de mercado. Abreviaturas: "
        "UND=unidad, PAQ=paquete, LB=libra, BULTO (sacos de granos), GDE/CH.",
    ),
    "Ecuador": Pais(
        "Ecuador", "786", True, "RUC",
        "Regionalismos: fréjol/frijol, palta=aguacate (en sierra) / aguacate "
        "(en costa) — ambos conviven, choclo=maíz tierno, verde=plátano para "
        "cocinar (distinto de banano/guineo). Abreviaturas: UND=unidad, "
        "PAQ=paquete, LB=libra, GDE/CH.",
    ),
    "Perú": Pais(
        "Perú", "775", True, "RUC",
        "Regionalismos: frejol/frijol, palta=aguacate (término dominante en "
        "Perú), choclo=maíz tierno (distinto de cancha/maíz seco), camote. "
        "Abreviaturas: UND=unidad, PAQ=paquete, KG, GR, LT, ML.",
    ),
    "Bolivia": Pais(
        "Bolivia", "777", True, "NIT",
        "Regionalismos: palta=aguacate, choclo=maíz tierno, papa (gran "
        "variedad de nombres locales de papa nativa — tratarlas como la "
        "misma categoría GPC salvo que el catálogo distinga variedad "
        "comercial). Abreviaturas: UND=unidad, PAQ=paquete, KG, GR, LT.",
    ),
    "Chile": Pais(
        "Chile", "780", True, "RUT",
        "Regionalismos: palta=aguacate (no \"aguacate\" en el habla común), "
        "porotos=frijoles, bebida=gaseosa/refresco (ojo: en Chile \"bebida\" "
        "casi siempre significa gaseosa, no agua), zapallo=calabaza, "
        "choclo=maíz tierno. Abreviaturas: UN=unidad, PAQ=paquete, KG, GR, LT.",
    ),
    "Argentina": Pais(
        "Argentina", "778-779", True, "CUIT",
        "Regionalismos: poroto=frijol, palta=aguacate, gaseosa=refresco, "
        "choclo=maíz tierno, fiambre=embutido/charcutería. Abreviaturas: "
        "UN=unidad, PAQ=paquete, GDE=grande, CH=chico, X UN=por unidad, KG, GR, LT.",
    ),
    "Paraguay": Pais(
        "Paraguay", "784", True, "RUC",
        "Regionalismos: poroto=frijol, palta=aguacate, gaseosa=refresco, "
        "choclo=maíz tierno — fuerte influencia del guaraní en nombres de "
        "productos locales (ej. mandioca=yuca). Abreviaturas: UN=unidad, "
        "PAQ=paquete, KG, GR, LT.",
    ),
    "Uruguay": Pais(
        "Uruguay", "773", True, "RUT",
        "Regionalismos: poroto=frijol, palta=aguacate, gaseosa=refresco, "
        "choclo=maíz tierno. Abreviaturas: UN=unidad, PAQ=paquete, KG, GR, LT.",
    ),
    "Brasil": Pais(
        "Brasil", "789-790", True, "CNPJ",
        "Catálogo normalmente en portugués, no español — ajustar el modelo "
        "a eso. Términos: feijão=frijol, abacate=aguacate, refrigerante="
        "gaseosa, batata=papa, milho=maíz. Abreviaturas de empaque "
        "frecuentes: UN=unidade, CX=caixa, PCT=pacote, GDE=grande, PEQ=pequeno, "
        "KG, G, L, ML (confirmar contra el propio catálogo: no se verificaron "
        "contra una fuente oficial de etiquetado).",
    ),
}

ORDEN_PAISES = sorted(PAISES.keys())
