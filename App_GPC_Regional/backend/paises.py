#!/usr/bin/env python3
"""Configuración por país para las 19 MO de GS1 en América Latina.

IMPORTANTE — verificar antes de confiar en esto para validación estricta:
los prefijos GS1 marcados "confirmado" se verificaron contra una búsqueda
en vivo el 13-nov-2026; los marcados "revisar" salen del conocimiento
general del modelo y DEBEN confirmarse contra la lista oficial
(https://www.gs1.org/standards/id-keys/company-prefix) antes de usarlos
para cualquier validación real de GTIN. Ninguno de los dos bloquea el uso
de la app: aquí son solo un dato de referencia que se le muestra al
usuario, no se usan para rechazar ni aceptar códigos de barra.

El identificador fiscal es solo una ETIQUETA de referencia (para que el
campo de la interfaz diga "CUIT" en vez de "RIF" según el país elegido),
no una validación de formato.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Pais:
    nombre: str
    prefijo_gs1: str
    prefijo_verificado: bool
    id_fiscal: str  # etiqueta de referencia, ej. "CUIT", "RFC"


PAISES: dict[str, Pais] = {
    "México": Pais("México", "750", False, "RFC"),
    "Guatemala": Pais("Guatemala", "740", False, "NIT"),
    "El Salvador": Pais("El Salvador", "741", False, "NIT"),
    "Honduras": Pais("Honduras", "742", False, "RTN"),
    "Nicaragua": Pais("Nicaragua", "743", False, "RUC"),
    "Costa Rica": Pais("Costa Rica", "744", False, "Cédula Jurídica"),
    "Panamá": Pais("Panamá", "745", False, "RUC"),
    "Cuba": Pais("Cuba", "850", False, "NIT"),
    "República Dominicana": Pais("República Dominicana", "746", False, "RNC"),
    "Venezuela": Pais("Venezuela", "759", True, "RIF"),
    "Colombia": Pais("Colombia", "770-771", True, "NIT"),
    "Ecuador": Pais("Ecuador", "786", True, "RUC"),
    "Perú": Pais("Perú", "775", True, "RUC"),
    "Bolivia": Pais("Bolivia", "777", True, "NIT"),
    "Chile": Pais("Chile", "780", True, "RUT"),
    "Argentina": Pais("Argentina", "778-779", True, "CUIT"),
    "Paraguay": Pais("Paraguay", "784", True, "RUC"),
    "Uruguay": Pais("Uruguay", "773", True, "RUT"),
    "Brasil": Pais("Brasil", "789-790", False, "CNPJ"),
}

ORDEN_PAISES = sorted(PAISES.keys())
