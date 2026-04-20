"""
AI_GPT_AUTOMATIZACION/utils/clasificador_severidad.py
-----------------------------------------------------

Clasificador Determinístico v6.2

OBJETIVO
--------
Mantener compatibilidad con el clasificador actual,
pero agregar capas nuevas que detecten términos y combinaciones
jurídicamente sensibles.

MEJORAS DE ESTA VERSIÓN
-----------------------
1. Usa reglas relevantes ampliadas:
   - penalidades
   - cesión agresiva de IP
   - no competencia extensa
   - responsabilidad por terceros
   - alquileres
   - audiovisual

2. Mantiene compatibilidad con indicadores clásicos
   desde indicadores_severidad.json

3. Añade ajuste locativo conservador:
   - si una cláusula locativa sensible activa familias específicas,
     se evita que quede artificialmente en "baja"
   - este ajuste solo opera sobre familias locativas bien delimitadas,
     por lo que no afecta el comportamiento de NDA

4. Añade ajuste audiovisual conservador:
   - si una cláusula audiovisual crítica cae artificialmente en "baja",
     eleva el piso mínimo
   - esto corrige especialmente:
       * cesión total / exclusiva / irrevocable
       * rescisión unilateral
       * ausencia de regalías automáticas
       * exclusividad intensa
       * seguro ambiguo o débil
       * confidencialidad sin plazo
   - este ajuste no afecta alquileres ni NDA porque se activa
     sobre patrones sectoriales audiovisuales

5. Devuelve análisis detallado auditable.
"""

import json
import os
from typing import Dict, Optional, Set, List, Tuple

from core.reglas_relevantes import evaluar_reglas_relevantes, ORDEN_SEVERIDAD


# =========================================================
# CARGA DE INDICADORES CLÁSICOS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_REGLAS = os.path.join(BASE_DIR, "indicadores_severidad.json")


def cargar_indicadores() -> Dict:
    with open(RUTA_REGLAS, "r", encoding="utf-8") as f:
        return json.load(f)


INDICADORES = cargar_indicadores()


# =========================================================
# CONSTANTES DE CONTEXTO LOCATIVO
# =========================================================

FAMILIAS_LOCATIVAS_SENSIBLES: Set[str] = {
    "no_suspension_pagos_arrendatario",
    "deposito_condicionado_arrendatario",
    "pagos_iniciales_elevados_arrendatario",
    "acceso_inmueble_privacidad_arrendatario",
    "exoneracion_arrendador_amplia",
    "resolucion_inmediata_arrendatario",
    "reajuste_locativo_sin_tope",
    "venta_sin_indemnizacion_arrendatario",
    "abandono_bienes_a_favor_arrendador",
}


# =========================================================
# CONSTANTES DE CONTEXTO AUDIOVISUAL
# =========================================================

# Familias "semánticas" internas del ajuste audiovisual.
# No dependen obligatoriamente de core/reglas_relevantes.
# Se usan para elevar piso de severidad cuando una cláusula
# sectorial crítica queda artificialmente subclasificada.
FAMILIAS_AUDIOVISUALES_SENSIBLES: Set[str] = {
    "aud_cesion_derechos_agresiva",
    "aud_falta_regalias",
    "aud_exclusividad_intensa",
    "aud_rescision_unilateral_productora",
    "aud_seguro_ambiguo",
    "aud_confidencialidad_sin_plazo",
    "aud_pago_condicionado_hitos",
}


# =========================================================
# HELPERS
# =========================================================

def cumple_regla(texto: str, regla: dict) -> bool:
    if regla["tipo"] == "frase":
        return regla["contiene"] in texto

    if regla["tipo"] == "combinada":
        return all(palabra in texto for palabra in regla["contiene_todas"])

    return False


def _clasificar_severidad_base(descripcion: str) -> str:
    """
    Clasificación clásica basada en indicadores_severidad.json.
    """
    texto = (descripcion or "").lower()

    for regla in INDICADORES["alta"]["reglas"]:
        if cumple_regla(texto, regla):
            return "alta"

    for regla in INDICADORES["media-alta"]["reglas"]:
        if cumple_regla(texto, regla):
            return "media-alta"

    for regla in INDICADORES["media"]["reglas"]:
        if cumple_regla(texto, regla):
            return "media"

    return "baja"


def _severidad_mayor(a: Optional[str], b: Optional[str]) -> str:
    if not a and not b:
        return "baja"
    if not a:
        return b
    if not b:
        return a

    oa = ORDEN_SEVERIDAD.get(a, 1)
    ob = ORDEN_SEVERIDAD.get(b, 1)

    return a if oa >= ob else b


def _crear_detalle_regla_sectorial(
    familia: str,
    descripcion_regla: str,
    severidad_minima_sugerida: str,
    terminos_base_detectados: Optional[List[str]] = None,
    terminos_agravantes_detectados: Optional[List[str]] = None,
    puntaje_aplicado: float = 0.0,
) -> Dict:
    """
    Construye un detalle auditable compatible con el resto del sistema.
    """
    return {
        "familia": familia,
        "descripcion_regla": descripcion_regla,
        "terminos_base_detectados": terminos_base_detectados or [],
        "terminos_agravantes_detectados": terminos_agravantes_detectados or [],
        "moneda_detectada": None,
        "valor_detectado": None,
        "monto_relevante_detectado": False,
        "monto_alto_detectado": False,
        "severidad_minima_sugerida": severidad_minima_sugerida,
        "puntaje_aplicado": puntaje_aplicado,
        "origen": "ajuste_sectorial_interno",
    }


def _detectar_ajustes_audiovisuales(
    descripcion: str,
) -> Tuple[Set[str], Optional[str], float, List[Dict]]:
    """
    Detecta patrones audiovisuales sensibles directamente sobre el texto
    de la cláusula, sin depender exclusivamente de reglas_relevantes.

    Retorna:
    - familias audiovisuales detectadas
    - severidad mínima sugerida audiovisual
    - puntaje audiovisual adicional (trazable)
    - detalle de reglas audiovisuales aplicadas
    """
    texto = (descripcion or "").lower()

    familias_detectadas: Set[str] = set()
    detalles: List[Dict] = []
    severidad_minima: Optional[str] = None
    puntaje_total = 0.0

    def elevar(nueva: str) -> None:
        nonlocal severidad_minima
        severidad_minima = _severidad_mayor(severidad_minima, nueva)

    # -----------------------------------------------------
    # 1) CESIÓN AMPLIA / AGRESIVA DE DERECHOS
    # -----------------------------------------------------
    patrones_cesion_base = [
        "cesión",
        "cesion",
        "derechos",
    ]
    patrones_cesion_agravantes = [
        "exclusiva",
        "irrevocable",
        "máximo plazo legal",
        "maximo plazo legal",
        "todos los medios",
        "todos los territorios",
        "perpetua",
        "global",
    ]

    if any(p in texto for p in patrones_cesion_base) and any(p in texto for p in patrones_cesion_agravantes):
        familias_detectadas.add("aud_cesion_derechos_agresiva")
        elevar("media-alta")
        puntaje_total += 2.5
        detalles.append(
            _crear_detalle_regla_sectorial(
                familia="aud_cesion_derechos_agresiva",
                descripcion_regla="Cesión audiovisual especialmente amplia, exclusiva o de alcance excesivo.",
                severidad_minima_sugerida="media-alta",
                terminos_base_detectados=[p for p in patrones_cesion_base if p in texto],
                terminos_agravantes_detectados=[p for p in patrones_cesion_agravantes if p in texto],
                puntaje_aplicado=2.5,
            )
        )

    # -----------------------------------------------------
    # 2) FALTA DE REGALÍAS / INGRESOS FUTUROS INDEFINIDOS
    # -----------------------------------------------------
    patrones_regalias = [
        "sin regalías",
        "sin regalias",
        "no se prevén regalías",
        "no se preven regalías",
        "no se preven regalias",
        "explotaciones secundarias",
        "negociación futura",
        "negociacion futura",
        "compensación queda sujeta",
        "compensacion queda sujeta",
    ]

    if any(p in texto for p in patrones_regalias):
        familias_detectadas.add("aud_falta_regalias")
        elevar("media")
        puntaje_total += 1.6
        detalles.append(
            _crear_detalle_regla_sectorial(
                familia="aud_falta_regalias",
                descripcion_regla="Ausencia de regalías automáticas o compensación futura demasiado indeterminada.",
                severidad_minima_sugerida="media",
                terminos_base_detectados=[p for p in patrones_regalias if p in texto],
                puntaje_aplicado=1.6,
            )
        )

    # -----------------------------------------------------
    # 3) EXCLUSIVIDAD FUERTE
    # -----------------------------------------------------
    patrones_exclusividad = [
        "exclusividad",
        "producciones competitivas",
        "limita su participación",
        "limita su participacion",
        "participar en proyectos competitivos",
    ]

    if any(p in texto for p in patrones_exclusividad):
        familias_detectadas.add("aud_exclusividad_intensa")
        elevar("media")
        puntaje_total += 1.3
        detalles.append(
            _crear_detalle_regla_sectorial(
                familia="aud_exclusividad_intensa",
                descripcion_regla="Exclusividad audiovisual de alcance potencialmente restrictivo para el artista.",
                severidad_minima_sugerida="media",
                terminos_base_detectados=[p for p in patrones_exclusividad if p in texto],
                puntaje_aplicado=1.3,
            )
        )

    # -----------------------------------------------------
    # 4) RESCISIÓN UNILATERAL DE LA PRODUCTORA
    # -----------------------------------------------------
    patrones_rescision = [
        "rescinde",
        "rescindir",
        "rescisión",
        "rescision",
        "puede rescindir",
        "puede resolver",
        "pagando solo lo devengado",
        "solo lo devengado",
    ]

    if (
        any(p in texto for p in ["rescisión", "rescision", "rescindir", "resolver"])
        and any(p in texto for p in ["productora", "puede rescindir", "puede resolver", "solo lo devengado", "pagando solo lo devengado"])
    ):
        familias_detectadas.add("aud_rescision_unilateral_productora")
        elevar("media")
        puntaje_total += 1.8
        detalles.append(
            _crear_detalle_regla_sectorial(
                familia="aud_rescision_unilateral_productora",
                descripcion_regla="Facultad de rescisión o resolución unilateral especialmente favorable a la productora.",
                severidad_minima_sugerida="media",
                terminos_base_detectados=[p for p in patrones_rescision if p in texto],
                puntaje_aplicado=1.8,
            )
        )

    # -----------------------------------------------------
    # 5) SEGURO AMBIGUO / INSUFICIENTE
    # -----------------------------------------------------
    patrones_seguro = [
        "seguro",
        "coberturas",
        "sin especificar coberturas",
        "sin detallar coberturas",
        "razonable",
        "sin especificar montos",
        "sin especificar coberturas ni montos",
        "no se especifican coberturas",
    ]

    if "seguro" in texto and any(p in texto for p in [
        "razonable",
        "sin especificar coberturas",
        "sin detallar coberturas",
        "no se especifican coberturas",
        "no se especifican coberturas ni montos",
    ]):
        familias_detectadas.add("aud_seguro_ambiguo")
        elevar("media")
        puntaje_total += 1.2
        detalles.append(
            _crear_detalle_regla_sectorial(
                familia="aud_seguro_ambiguo",
                descripcion_regla="Cobertura de seguro audiovisual ambigua, incompleta o poco definida.",
                severidad_minima_sugerida="media",
                terminos_base_detectados=[p for p in patrones_seguro if p in texto],
                puntaje_aplicado=1.2,
            )
        )

    # -----------------------------------------------------
    # 6) CONFIDENCIALIDAD SIN PLAZO DEFINIDO
    # -----------------------------------------------------
    patrones_conf = [
        "confidencialidad",
        "sin plazo definido",
        "más allá de la vigencia",
        "mas alla de la vigencia",
        "sin plazo",
    ]

    if "confidencialidad" in texto and any(p in texto for p in [
        "sin plazo definido",
        "sin plazo",
        "más allá de la vigencia",
        "mas alla de la vigencia",
    ]):
        familias_detectadas.add("aud_confidencialidad_sin_plazo")
        elevar("media")
        puntaje_total += 1.0
        detalles.append(
            _crear_detalle_regla_sectorial(
                familia="aud_confidencialidad_sin_plazo",
                descripcion_regla="Confidencialidad postcontractual sin límite temporal razonable.",
                severidad_minima_sugerida="media",
                terminos_base_detectados=[p for p in patrones_conf if p in texto],
                puntaje_aplicado=1.0,
            )
        )

    # -----------------------------------------------------
    # 7) PAGO CONDICIONADO A HITOS O FINALIZACIÓN
    # -----------------------------------------------------
    patrones_pago = [
        "condicionado",
        "finalización de la participación",
        "finalizacion de la participacion",
        "hitos",
        "en dos partes",
        "60%",
    ]

    if any(p in texto for p in ["condicionado", "finalización de la participación", "finalizacion de la participacion", "hitos"]):
        familias_detectadas.add("aud_pago_condicionado_hitos")
        elevar("media")
        puntaje_total += 1.0
        detalles.append(
            _crear_detalle_regla_sectorial(
                familia="aud_pago_condicionado_hitos",
                descripcion_regla="Pago sujeto a hitos, participación o eventos que pueden generar incertidumbre de cobro.",
                severidad_minima_sugerida="media",
                terminos_base_detectados=[p for p in patrones_pago if p in texto],
                puntaje_aplicado=1.0,
            )
        )

    return familias_detectadas, severidad_minima, puntaje_total, detalles


def _ajuste_locativo_conservador(
    severidad_base: str,
    severidad_reglas: Optional[str],
    familias_detectadas: Set[str],
) -> str:
    """
    Ajuste final acotado a alquileres.

    Idea:
    - si ya hay una severidad por reglas >= media, no tocar nada
    - si la clasificación quedó en baja pero se detectó una familia locativa
      sensible, elevar el piso a media

    Esto evita subclasificar cláusulas como:
    - no suspender pagos
    - depósito condicionado
    - pagos iniciales fuertes
    - acceso al inmueble

    y no perjudica NDA porque solo opera sobre familias locativas.
    """
    if not (familias_detectadas & FAMILIAS_LOCATIVAS_SENSIBLES):
        return _severidad_mayor(severidad_base, severidad_reglas)

    severidad_actual = _severidad_mayor(severidad_base, severidad_reglas)

    if ORDEN_SEVERIDAD.get(severidad_actual, 1) < ORDEN_SEVERIDAD["media"]:
        return "media"

    return severidad_actual


def _ajuste_audiovisual_conservador(
    severidad_actual: str,
    familias_detectadas: Set[str],
    severidad_minima_audiovisual: Optional[str],
) -> str:
    """
    Ajuste final acotado a audiovisual.

    Idea:
    - si no hay familias audiovisuales sensibles, no hace nada
    - si una cláusula audiovisual crítica quedó en severidad baja,
      eleva el piso al mínimo sugerido audiovisual

    Esto corrige específicamente problemas observados en pruebas reales:
    - cesión total saliendo como baja
    - rescisión unilateral saliendo como baja
    - ausencia de regalías saliendo demasiado blanda
    """
    if not (familias_detectadas & FAMILIAS_AUDIOVISUALES_SENSIBLES):
        return severidad_actual

    return _severidad_mayor(severidad_actual, severidad_minima_audiovisual)


def clasificar_nivel(score: float) -> str:
    """
    Clasificador simple de nivel a partir de score numérico.
    Se usa para la capa de scoring dual.
    """
    if score < 10:
        return "bajo"
    elif score < 25:
        return "medio"
    elif score < 40:
        return "medio-alto"
    elif score < 60:
        return "alto"
    else:
        return "critico"


# =========================================================
# API DETALLADA
# =========================================================

def analizar_severidad_detallada(descripcion: str) -> Dict:
    """
    Devuelve:
    - severidad_base
    - severidad_minima_sugerida
    - severidad_final
    - familias_detectadas
    - puntaje_agravante_total
    - detalle_reglas

    IMPORTANTE:
    -----------
    La severidad final se construye en capas:

    1) indicadores clásicos
    2) reglas relevantes generales / NDA / alquileres
    3) ajuste locativo conservador
    4) ajuste audiovisual conservador
    """
    severidad_base = _clasificar_severidad_base(descripcion)

    # Reglas relevantes generales
    reglas = evaluar_reglas_relevantes(descripcion)
    severidad_minima_reglas = reglas.get("severidad_minima_sugerida")
    familias_detectadas = set(reglas.get("familias_detectadas", []))
    puntaje_relevante = float(reglas.get("puntaje_agravante_total", 0.0) or 0.0)
    detalle_reglas = list(reglas.get("detalle_reglas", []))

    # Ajustes audiovisuales internos
    familias_aud, severidad_minima_aud, puntaje_aud, detalle_aud = _detectar_ajustes_audiovisuales(descripcion)

    familias_detectadas |= familias_aud
    detalle_reglas.extend(detalle_aud)

    # Se toma la mayor severidad sugerida entre reglas relevantes y audiovisual
    severidad_minima_total = _severidad_mayor(
        severidad_minima_reglas,
        severidad_minima_aud,
    )

    # Primero ajuste locativo
    severidad_post_locativo = _ajuste_locativo_conservador(
        severidad_base=severidad_base,
        severidad_reglas=severidad_minima_total,
        familias_detectadas=familias_detectadas,
    )

    # Luego ajuste audiovisual
    severidad_final = _ajuste_audiovisual_conservador(
        severidad_actual=severidad_post_locativo,
        familias_detectadas=familias_detectadas,
        severidad_minima_audiovisual=severidad_minima_aud,
    )

    return {
        "severidad_base": severidad_base,
        "severidad_minima_sugerida": severidad_minima_total,
        "severidad_final": severidad_final,
        "familias_detectadas": list(familias_detectadas),
        "puntaje_agravante_total": round(puntaje_relevante + puntaje_aud, 2),
        "detalle_reglas": detalle_reglas,
    }


# =========================================================
# API SIMPLE COMPATIBLE
# =========================================================

def clasificar_severidad(descripcion: str) -> str:
    """
    Compatibilidad con código existente.
    """
    analisis = analizar_severidad_detallada(descripcion)
    return analisis["severidad_final"]