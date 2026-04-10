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

MEJORAS DE ESTA VERSIÓN
-----------------------
1. Mantiene detección monetaria por moneda:
   - USD / US$ / dólares
   - EUR / € / euros
   - ARS / pesos argentinos
   - UYU / pesos uruguayos

2. Refuerza semántica locativa sin contaminar NDA:
   - no suspensión de pagos
   - depósito condicionado
   - pagos iniciales elevados
   - acceso al inmueble / visitas
   - cargas locativas desplazadas al arrendatario

3. Reduce falsos positivos inter-subdominios:
   - alquileres no debe disparar IP agresiva por la sola palabra "derechos"
   - alquileres no debe disparar rescisión audiovisual por la sola palabra "rescisión"
   - menciones genéricas a empleados ya no deben disparar por sí solas
     responsabilidad ampliada por terceros

4. Preserva la robustez de NDA y audiovisual.
"""

import re
from typing import Dict, List, Optional
from __future__ import annotations


# =========================================================
# JERARQUÍA DE SEVERIDAD
# =========================================================

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


# =========================================================
# UMBRALES MONETARIOS
# =========================================================

UMBRALES_MONETARIOS = {
    "USD": {"relevante": 25000, "alto": 100000},
    "EUR": {"relevante": 25000, "alto": 100000},
    "ARS": {"relevante": 10000000, "alto": 50000000},
    "UYU": {"relevante": 800000, "alto": 4000000},
}


# =========================================================
# FAMILIAS DE RIESGO RELEVANTE
# =========================================================

REGLAS_RELEVANTES = {
    # -----------------------------------------------------
    # CONTRATOS GENERALES / NDA / IP
    # -----------------------------------------------------
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
            "sin discusión previa",
            "sin discusion previa",
            "sin tope máximo",
            "sin tope maximo",
        ],
        "requiere_monto": True,
        "severidad_minima": "media-alta",
        "puntaje_base": 2.0,
        "puntaje_agravante": 2.0,
    },

    "cesion_ip_agresiva": {
        "descripcion": "Cesión amplia o especialmente gravosa de propiedad intelectual.",
        "terminos_base": [
            "propiedad intelectual",
            "propiedad industrial",
            "derechos de propiedad intelectual",
            "derechos de propiedad industrial",
            "derechos de autor",
            "copyright",
            "patente",
            "patentes",
            "know-how",
        ],
        "terminos_agravantes": [
            "cesión",
            "cesion",
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
            "máximo plazo legal",
            "maximo plazo legal",
            "todos los medios",
            "todos los territorios",
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
            "exclusividad",
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
            "sin plazo definido",
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
            "acto de terceros",
            "actos de terceros",
        ],
        "terminos_agravantes": [
            "cualquier tercero",
            "bajo su órbita",
            "bajo su orbita",
            "solidaria",
            "vinculados",
            "empleados",
            "socios",
            "contratistas",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.5,
        "puntaje_agravante": 1.0,
    },

    # -----------------------------------------------------
    # ALQUILERES / ARRENDAMIENTOS
    # -----------------------------------------------------
    "no_suspension_pagos_arrendatario": {
        "descripcion": "Renuncia o prohibición de suspender pagos por parte del arrendatario, incluso ante controversias o incumplimientos.",
        "terminos_base": [
            "suspender pagos",
            "suspensión del pago",
            "suspension del pago",
            "renuncia a suspender pagos",
            "prohibición de suspender pagos",
            "prohibicion de suspender pagos",
        ],
        "terminos_agravantes": [
            "por cualquier motivo",
            "incluso en caso de controversia",
            "incluso en caso de disputa",
            "incumplimientos del arrendador",
            "gastos accesorios",
            "alquiler",
        ],
        "requiere_monto": False,
        "severidad_minima": "media-alta",
        "puntaje_base": 1.8,
        "puntaje_agravante": 1.6,
    },

    "deposito_condicionado_arrendatario": {
        "descripcion": "Depósito de garantía sujeto a verificación amplia o a cumplimiento integral de obligaciones.",
        "terminos_base": [
            "depósito de garantía",
            "deposito de garantia",
            "depósito",
            "deposito",
        ],
        "terminos_agravantes": [
            "dos meses",
            "verificación del estado del inmueble",
            "verificacion del estado del inmueble",
            "cumplimiento de todas las obligaciones",
            "solo se devuelve",
            "se devuelve tras verificación",
            "se devuelve tras verificacion",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.4,
        "puntaje_agravante": 1.2,
    },

    "pagos_iniciales_elevados_arrendatario": {
        "descripcion": "Carga económica inicial exigente para el arrendatario, como mensualidades anticipadas, timbres o gastos de registro.",
        "terminos_base": [
            "mensualidades",
            "mensualidades anticipadas",
            "pago anticipadamente",
            "pagar anticipadamente",
            "gastos de registro",
            "timbres",
            "registro y timbre",
        ],
        "terminos_agravantes": [
            "tres primeras mensualidades",
            "tres mensualidades",
            "mitad de los costes de registro",
            "mitad de los costos de registro",
            "principalmente sobre el arrendatario",
            "recae principalmente sobre el arrendatario",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.3,
        "puntaje_agravante": 1.2,
    },

    "acceso_inmueble_privacidad_arrendatario": {
        "descripcion": "Acceso, visitas o ingreso al inmueble que puede afectar privacidad o uso pacífico del arrendatario.",
        "terminos_base": [
            "acceso al inmueble",
            "permitir el acceso",
            "debe permitir el acceso",
            "visitas en caso de venta",
            "facilitar visitas",
            "debe permitir visitas",
        ],
        "terminos_agravantes": [
            "privacidad",
            "bajo ciertas condiciones",
            "en caso de venta",
            "nueva renta",
            "puede afectar su privacidad",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.3,
        "puntaje_agravante": 1.1,
    },

    "exoneracion_arrendador_amplia": {
        "descripcion": "Exoneración amplia de responsabilidad del arrendador por daños, servicios o vicios.",
        "terminos_base": [
            "exonera expresamente al arrendador",
            "exoneración de responsabilidad del arrendador",
            "exoneracion de responsabilidad del arrendador",
            "el arrendador no será responsable",
            "el arrendador no sera responsable",
            "no será responsable por daños",
            "no sera responsable por daños",
        ],
        "terminos_agravantes": [
            "daños",
            "vicios",
            "servicios",
            "interrupciones",
            "defectos",
            "limitar reclamaciones",
            "limita reclamaciones",
            "no imputables",
        ],
        "requiere_monto": False,
        "severidad_minima": "media-alta",
        "puntaje_base": 1.8,
        "puntaje_agravante": 1.6,
    },

    "resolucion_inmediata_arrendatario": {
        "descripcion": "Resolución inmediata o automática frente a incumplimientos del arrendatario.",
        "terminos_base": [
            "resolución inmediata",
            "resolucion inmediata",
            "resuelto de pleno derecho",
            "condición resolutoria",
            "condicion resolutoria",
            "desalojo inmediato",
        ],
        "terminos_agravantes": [
            "automática",
            "automatica",
            "sin previo aviso",
            "sin intimación",
            "sin intimacion",
            "cualquier incumplimiento",
            "incumplimiento del arrendatario",
        ],
        "requiere_monto": False,
        "severidad_minima": "media-alta",
        "puntaje_base": 1.8,
        "puntaje_agravante": 1.6,
    },

    "reajuste_locativo_sin_tope": {
        "descripcion": "Reajuste locativo con amplitud relevante o sin tope claro.",
        "terminos_base": [
            "reajuste",
            "actualización del alquiler",
            "actualizacion del alquiler",
            "actualización de renta",
            "actualizacion de renta",
        ],
        "terminos_agravantes": [
            "sin tope",
            "ura",
            "ipc",
            "según mercado",
            "segun mercado",
            "anual",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.2,
        "puntaje_agravante": 1.2,
    },

    "venta_sin_indemnizacion_arrendatario": {
        "descripcion": "Facultad de vender el inmueble sin protección relevante para el arrendatario.",
        "terminos_base": [
            "venta del inmueble",
            "en caso de venta",
            "vender el inmueble",
            "venta o nueva renta",
            "nueva renta",
            "visitas en caso de venta",
        ],
        "terminos_agravantes": [
            "sin indemnización",
            "sin indemnizacion",
            "sin responsabilidad",
            "sin compensación",
            "sin compensacion",
            "debe permitir visitas",
            "acceso al inmueble",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.3,
        "puntaje_agravante": 1.2,
    },

    "abandono_bienes_a_favor_arrendador": {
        "descripcion": "Abandono de bienes muebles a favor del arrendador.",
        "terminos_base": ["abandono", "bienes muebles"],
        "terminos_agravantes": [
            "a favor del arrendador",
            "quedarán",
            "quedaran",
            "irrevocable",
            "lanzamiento",
        ],
        "requiere_monto": False,
        "severidad_minima": "media-alta",
        "puntaje_base": 1.7,
        "puntaje_agravante": 1.5,
    },

    # -----------------------------------------------------
    # AUDIOVISUAL
    # -----------------------------------------------------
    "rescision_unilateral_productora": {
        "descripcion": "Facultad amplia de rescisión unilateral por parte de la productora.",
        "terminos_base": [
            "por parte de la productora",
            "la productora podrá rescindir",
            "la productora podra rescindir",
            "facultad unilateral de rescisión por parte de la productora",
            "facultad unilateral de rescision por parte de la productora",
        ],
        "terminos_agravantes": [
            "rescisión unilateral",
            "rescision unilateral",
            "en cualquier momento",
            "razones artísticas",
            "razones artisticas",
            "razones técnicas",
            "razones tecnicas",
            "sin compensación",
            "sin compensacion",
            "sin indemnización",
            "sin indemnizacion",
        ],
        "requiere_monto": False,
        "severidad_minima": "media-alta",
        "puntaje_base": 1.8,
        "puntaje_agravante": 1.5,
    },

    "sin_regalias_automaticas": {
        "descripcion": "Ausencia de regalías automáticas o compensación clara por explotaciones secundarias.",
        "terminos_base": ["regalías", "regalias"],
        "terminos_agravantes": [
            "sin regalías",
            "sin regalias",
            "no se prevén",
            "no se preven",
            "explotaciones secundarias",
            "negociación futura",
            "negociacion futura",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.4,
        "puntaje_agravante": 1.3,
    },

    "seguro_ambiguo_o_limitado": {
        "descripcion": "Seguro ambiguo, limitado o sin especificación clara de coberturas.",
        "terminos_base": ["seguro"],
        "terminos_agravantes": [
            "razonable",
            "sin especificaciones",
            "sin especificacion",
            "no se especifican coberturas",
            "solo a las jornadas de rodaje",
            "no detalla coberturas",
        ],
        "requiere_monto": False,
        "severidad_minima": "media",
        "puntaje_base": 1.2,
        "puntaje_agravante": 1.2,
    },
}


# =========================================================
# HELPERS
# =========================================================

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


# =========================================================
# DETECCIÓN MONETARIA
# =========================================================

def extraer_numeros_candidatos(texto: str) -> List[float]:
    patrones = [
        r"\b\d{1,3}(?:[.,]\d{3})+\b",
        r"\b\d{5,}\b",
    ]

    encontrados = []
    for patron in patrones:
        encontrados.extend(re.findall(patron, texto))

    valores: List[float] = []
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


# =========================================================
# MOTOR PRINCIPAL
# =========================================================

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
        severidad_minima_global = severidad_mayor(severidad_minima_global, severidad_regla)

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
