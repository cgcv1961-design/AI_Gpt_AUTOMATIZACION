"""
AI_GPT_AUTOMATIZACION/core/reglas_relevantes.py
------------------------------------------------

OBJETIVO
--------
Definir familias de términos y reglas agravantes para que el scoring
determinista pueda detectar cláusulas especialmente sensibles aunque
la severidad original venga baja desde capas anteriores.

PRINCIPIO
---------
La IA describe el riesgo.
La lógica determinista:
- detecta términos y combinaciones relevantes,
- suma agravantes,
- puede imponer una severidad mínima.

ESTO NO REEMPLAZA
-----------------
No reemplaza la severidad original.
La complementa de forma auditable y explícita.

USO ESPERADO
------------
Este módulo será consumido por:
    utils/clasificador_severidad.py

SALIDA PRINCIPAL
----------------
La función `evaluar_reglas_relevantes(texto)` devuelve un dict con:
- familias detectadas
- puntaje agravante adicional
- severidad mínima sugerida
- detalle auditable de coincidencias

MEJORA DE ESTA VERSIÓN
----------------------
Se amplía la detección monetaria para contemplar:
- USD / US$ / dólares
- EUR / € / euros
- ARS / pesos argentinos
- UYU / pesos uruguayos

Además:
- se distinguen montos "relevantes" de montos "altos"
- se aplican umbrales por moneda
- se mantiene trazabilidad completa de lo detectado
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


ORDEN_SEVERIDAD = {
    "baja": 1,
    "media": 2,
    "media-alta": 3,
    "alta": 4,
    "critica": 5,
}

SEVERIDAD_POR_ORDEN = {
    1: "baja",
    2: "media",
    3: "media-alta",
    4: "alta",
    5: "critica",
}


UMBRALES_MONETARIOS = {
    "USD": {
        "relevante": 25000,
        "alto": 100000,
    },
    "EUR": {
        "relevante": 25000,
        "alto": 100000,
    },
    "ARS": {
        "relevante": 10000000,
        "alto": 50000000,
    },
    "UYU": {
        "relevante": 800000,
        "alto": 4000000,
    },
}


REGLAS_RELEVANTES = {
    "penalidad_fuerte": {
        "descripcion": "Cláusulas penales, multas o penalidades de monto importante o aplicación amplia.",
        "terminos_base": [
            "penalidad",
            "cláusula penal",
            "clausula penal",
            "multa",
            "liquidated damages",
            "penalty",
        ],
        "terminos_agravantes": [
            "cualquier incumplimiento",
            "sin necesidad de interpelación",
            "sin necesidad de interpelacion",
            "daños adicionales",
            "daños y perjuicios",
            "acumulativa",
            "independiente de daños",
            "líquida",
            "liquida",
            "exigible sin discusión",
            "exigible sin discusion",
        ],
        "requiere_monto": True,
        "severidad_minima": "media-alta",
        "puntaje_base": 2.0,
        "puntaje_agravante": 2.0,
    },
    "cesion_ip_agresiva": {
        "descripcion": "Cesión amplia o especialmente gravosa de propiedad intelectual.",
        "terminos_base": [
            "cesión",
            "cesion",
            "propiedad intelectual",
            "derechos de propiedad intelectual",
            "derechos",
            "propiedad industrial",
        ],
        "terminos_agravantes": [
            "irrevocable",
            "automática",
            "automatica",
            "perpetua",
            "todos los derechos",
            "sin contraprestación",
            "sin contraprestacion",
            "sin compensación adicional",
            "sin compensacion adicional",
            "global",
            "mundial",
            "sin restricción temporal",
            "sin restriccion temporal",
            "sin restricción territorial",
            "sin restriccion territorial",
            "desarrollos futuros",
            "exclusivos",
            "exclusiva",
            "titularidad exclusiva",
        ],
        "requiere_monto": False,
        "severidad_minima": "alta",
        "puntaje_base": 2.5,
        "puntaje_agravante": 2.5,
    },
    "no_competencia_extensa": {
        "descripcion": "Restricciones postcontractuales extensas de confidencialidad o no competencia.",
        "terminos_base": [
            "no competencia",
            "confidencialidad",
            "no divulgación",
            "no divulgacion",
        ],
        "terminos_agravantes": [
            "10 años",
            "10 anos",
            "5 años",
            "5 anos",
            "después de finalizada la relación",
            "despues de finalizada la relacion",
            "subsisten",
            "postcontractual",
            "finalizada la relación",
            "finalizada la relacion",
            "larga duración",
            "larga duracion",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.5,
        "puntaje_agravante": 1.5,
    },
    "responsabilidad_terceros_ampliada": {
        "descripcion": "Responsabilidad amplia por empleados, socios, contratistas o terceros vinculados.",
        "terminos_base": [
            "responsabilidad solidaria",
            "responsabilidad por terceros",
            "terceros vinculados",
            "empleados",
            "socios",
            "contratistas",
        ],
        "terminos_agravantes": [
            "cualquier tercero",
            "bajo su órbita",
            "bajo su orbita",
            "solidaria",
            "vinculados",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.5,
        "puntaje_agravante": 1.0,
    },
}


def normalizar_texto(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def contiene_termino(texto: str, termino: str) -> bool:
    return termino.lower() in texto


def severidad_mayor(a: Optional[str], b: Optional[str]) -> Optional[str]:
    if not a:
        return b
    if not b:
        return a

    oa = ORDEN_SEVERIDAD.get(a, 1)
    ob = ORDEN_SEVERIDAD.get(b, 1)

    return a if oa >= ob else b


def extraer_numeros_candidatos(texto: str) -> List[float]:
    patrones = [
        r"\b\d{1,3}(?:[.,]\d{3})+\b",
        r"\b\d{5,}\b",
    ]

    encontrados = []
    for patron in patrones:
        encontrados.extend(re.findall(patron, texto))

    valores = []
    vistos = set()

    for valor in encontrados:
        limpio = valor.replace(".", "").replace(",", "")
        if limpio.isdigit():
            numero = float(limpio)
            if numero not in vistos:
                valores.append(numero)
                vistos.add(numero)

    return valores


def detectar_moneda(texto: str) -> Optional[str]:
    texto = normalizar_texto(texto)

    patrones_moneda = {
        "USD": ["usd", "us$", "dólares", "dolares", "dólar", "dolar"],
        "EUR": ["eur", "€", "euros", "euro"],
        "ARS": ["ars", "peso argentino", "pesos argentinos"],
        "UYU": ["uyu", "$u", "peso uruguayo", "pesos uruguayos"],
    }

    for moneda, alias in patrones_moneda.items():
        if any(a in texto for a in alias):
            return moneda

    return None


def clasificar_monto_por_moneda(texto: str) -> Dict:
    texto_norm = normalizar_texto(texto)
    moneda = detectar_moneda(texto_norm)
    numeros = extraer_numeros_candidatos(texto_norm)

    if not moneda or not numeros:
        return {
            "moneda_detectada": None,
            "valor_detectado": None,
            "es_relevante": False,
            "es_alto": False,
        }

    valor_max = max(numeros)
    umbrales = UMBRALES_MONETARIOS.get(moneda)

    if not umbrales:
        return {
            "moneda_detectada": moneda,
            "valor_detectado": valor_max,
            "es_relevante": False,
            "es_alto": False,
        }

    es_relevante = valor_max >= umbrales["relevante"]
    es_alto = valor_max >= umbrales["alto"]

    return {
        "moneda_detectada": moneda,
        "valor_detectado": valor_max,
        "es_relevante": es_relevante,
        "es_alto": es_alto,
    }


def evaluar_reglas_relevantes(texto: str) -> Dict:
    texto_norm = normalizar_texto(texto)

    familias_detectadas: List[str] = []
    detalle: List[Dict] = []
    puntaje_total = 0.0
    severidad_minima_global: Optional[str] = None

    info_monto = clasificar_monto_por_moneda(texto_norm)

    for nombre_familia, regla in REGLAS_RELEVANTES.items():
        bases_encontradas = [
            t for t in regla["terminos_base"]
            if contiene_termino(texto_norm, t)
        ]

        if not bases_encontradas:
            continue

        agravantes_encontrados = [
            t for t in regla["terminos_agravantes"]
            if contiene_termino(texto_norm, t)
        ]

        puntaje = regla["puntaje_base"]

        if agravantes_encontrados:
            puntaje += regla["puntaje_agravante"]

        if regla.get("requiere_monto", False):
            if info_monto["es_relevante"]:
                puntaje += 1.5
            if info_monto["es_alto"]:
                puntaje += 2.5

        severidad_regla = regla["severidad_minima"]

        if regla.get("requiere_monto", False) and info_monto["es_alto"]:
            severidad_regla = severidad_mayor(severidad_regla, "alta")

        familias_detectadas.append(nombre_familia)

        severidad_minima_global = severidad_mayor(
            severidad_minima_global,
            severidad_regla
        )

        detalle.append({
            "familia": nombre_familia,
            "descripcion_regla": regla["descripcion"],
            "terminos_base_detectados": bases_encontradas,
            "terminos_agravantes_detectados": agravantes_encontrados,
            "moneda_detectada": info_monto["moneda_detectada"],
            "valor_detectado": info_monto["valor_detectado"],
            "monto_relevante_detectado": info_monto["es_relevante"],
            "monto_alto_detectado": info_monto["es_alto"],
            "severidad_minima_sugerida": severidad_regla,
            "puntaje_aplicado": round(puntaje, 2),
        })

        puntaje_total += puntaje

    return {
        "familias_detectadas": familias_detectadas,
        "puntaje_agravante_total": round(puntaje_total, 2),
        "severidad_minima_sugerida": severidad_minima_global,
        "detalle_reglas": detalle,
    }