"""
AI_GPT_AUTOMATIZACION/core/scoring_engine.py
--------------------------------------------

Motor determinista de scoring contractual.

OBJETIVO DE ESTA VERSIÓN
------------------------
1. Mantener el cálculo clásico por:
   - severidad
   - impacto

2. Agregar una capa determinista adicional que:
   - lea la descripción del riesgo
   - detecte familias de términos relevantes
   - sume agravantes
   - pueda imponer una severidad mínima

PROBLEMA QUE RESUELVE
---------------------
Antes, el scoring:
- NO inspeccionaba el texto de descripción del riesgo
- solo usaba severidad e impacto ya presentes

Eso hacía que cláusulas como:
- penalidad de USD 2.000.000
- cesión total/perpetua de IP

pudieran terminar con severidad baja si así llegaban desde capas previas.

Ahora:
- se mantiene la lógica anterior
- pero se agrega una corrección determinista auditable
  basada en reglas relevantes.

IMPORTANTE
----------
Este motor no reemplaza a la IA.
La complementa con reglas explícitas y verificables.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import math

from core.reglas_relevantes import (
    evaluar_reglas_relevantes,
    ORDEN_SEVERIDAD,
    SEVERIDAD_POR_ORDEN,
)

ALGORITMO_SCORING_VERSION = "3.0_core_reglas_relevantes"


# =========================================================
# CONFIGURACIÓN BASE
# =========================================================

PESOS_SEVERIDAD = {
    "baja": 1.0,
    "media": 2.0,
    "media-alta": 3.0,
    "alta": 4.0,
    "critica": 6.0,
}

MULTIPLICADORES_IMPACTO = {
    "legal": 1.0,
    "financiero": 1.3,
    "operativo": 1.1,
    "reputacional": 1.1,
    "mixto": 1.5,
}


# =========================================================
# HELPERS DE SEVERIDAD
# =========================================================

def normalizar_severidad(severidad: str) -> str:
    """
    Normaliza valores de severidad a los soportados por el motor.
    """
    valor = (severidad or "").strip().lower()

    equivalencias = {
        "baja": "baja",
        "media": "media",
        "media-alta": "media-alta",
        "media_alta": "media-alta",
        "alta": "alta",
        "critica": "critica",
        "crítica": "critica",
    }

    return equivalencias.get(valor, "media")


def severidad_mayor(a: str, b: str) -> str:
    """
    Devuelve la severidad más alta entre dos valores.
    """
    a_norm = normalizar_severidad(a)
    b_norm = normalizar_severidad(b)

    oa = ORDEN_SEVERIDAD.get(a_norm, 2)
    ob = ORDEN_SEVERIDAD.get(b_norm, 2)

    return a_norm if oa >= ob else b_norm


# =========================================================
# ENRIQUECIMIENTO DETERMINISTA DEL RIESGO
# =========================================================

def enriquecer_riesgo_con_reglas(riesgo: Dict) -> Dict:
    """
    Lee la descripción del riesgo y aplica reglas relevantes.

    Devuelve el riesgo enriquecido con:
    - severidad_ajustada
    - puntaje_agravante
    - detalle de reglas detectadas

    No destruye la severidad original.
    """
    descripcion = (riesgo.get("descripcion") or "").strip()
    severidad_original = normalizar_severidad(riesgo.get("severidad", "media"))

    resultado_reglas = evaluar_reglas_relevantes(descripcion)

    severidad_minima = resultado_reglas.get("severidad_minima_sugerida")
    severidad_ajustada = severidad_original

    if severidad_minima:
        severidad_ajustada = severidad_mayor(severidad_original, severidad_minima)

    riesgo_enriquecido = dict(riesgo)
    riesgo_enriquecido["severidad_original"] = severidad_original
    riesgo_enriquecido["severidad_ajustada"] = severidad_ajustada
    riesgo_enriquecido["puntaje_agravante"] = resultado_reglas.get("puntaje_agravante_total", 0.0)
    riesgo_enriquecido["familias_relevantes_detectadas"] = resultado_reglas.get("familias_detectadas", [])
    riesgo_enriquecido["detalle_reglas_relevantes"] = resultado_reglas.get("detalle_reglas", [])

    return riesgo_enriquecido


# =========================================================
# CÁLCULO DE SCORE
# =========================================================

def calcular_score(riesgos: List[Dict]) -> float:
    """
    Calcula score total basado en:
    - severidad ajustada
    - impacto
    - agravantes detectados por reglas relevantes

    Aplica además normalización logarítmica suave por volumen.
    """

    score_total = 0.0

    for riesgo in riesgos:
        severidad = normalizar_severidad(riesgo.get("severidad_ajustada", riesgo.get("severidad", "media")))
        impacto = (riesgo.get("impacto") or "").strip().lower()

        peso = PESOS_SEVERIDAD.get(severidad, 2.0)
        multiplicador = MULTIPLICADORES_IMPACTO.get(impacto, 1.0)
        agravante = float(riesgo.get("puntaje_agravante", 0.0))

        score_total += (peso * multiplicador) + agravante

    cantidad = len(riesgos)

    # Suavizado por volumen para evitar inflación excesiva por cantidad
    if cantidad > 0:
        score_total = score_total / (1 + math.log(cantidad + 1))

    return round(score_total, 2)


def determinar_nivel(score: float) -> str:
    """
    Determina nivel de riesgo global.
    """

    if score < 15:
        return "bajo"
    elif score < 30:
        return "medio"
    elif score < 50:
        return "alto"
    else:
        return "critico"


# =========================================================
# EXTRACCIÓN DE RIESGOS
# =========================================================

def extraer_riesgos_tecnico(data: dict) -> list:
    """
    Extrae todos los riesgos del modo técnico y los unifica
    en una lista plana para aplicar scoring.
    """

    riesgos_unificados = []

    clasificados = data.get("analisis_profesional", {}).get("riesgos_clasificados", {})

    for categoria in clasificados.values():
        if isinstance(categoria, list):
            riesgos_unificados.extend(categoria)

    return riesgos_unificados


def contar_metricas_por_severidad(riesgos: List[Dict]) -> Dict[str, int]:
    """
    Cuenta riesgos según severidad ajustada.
    """
    metricas = {
        "cantidad_riesgos": 0,
        "riesgos_altos": 0,
        "riesgos_media_altos": 0,
        "riesgos_medios": 0,
        "riesgos_bajos": 0,
    }

    for riesgo in riesgos:
        sev = normalizar_severidad(riesgo.get("severidad_ajustada", riesgo.get("severidad", "media")))

        metricas["cantidad_riesgos"] += 1

        if sev == "alta" or sev == "critica":
            metricas["riesgos_altos"] += 1
        elif sev == "media-alta":
            metricas["riesgos_media_altos"] += 1
        elif sev == "media":
            metricas["riesgos_medios"] += 1
        else:
            metricas["riesgos_bajos"] += 1

    return metricas


# =========================================================
# SCORING SOBRE RESULTADO TÉCNICO ACTUAL
# =========================================================

def aplicar_scoring_resultado_tecnico(resultado: Dict) -> Dict:
    """
    Inserta el bloque `scoring` en el resultado técnico actual.

    Además:
    - enriquece cada riesgo con reglas relevantes
    - ajusta severidades cuando corresponde
    - mantiene compatibilidad con la estructura actual del proyecto
    """

    if not isinstance(resultado, dict):
        return resultado

    riesgos = extraer_riesgos_tecnico(resultado)

    riesgos_enriquecidos = [enriquecer_riesgo_con_reglas(r) for r in riesgos]

    # Reinyecta severidad ajustada dentro de la estructura analisis_profesional
    clasificados = resultado.get("analisis_profesional", {}).get("riesgos_clasificados", {})
    nuevos_clasificados = {}

    idx_global = 0
    for categoria, lista_riesgos in clasificados.items():
        nueva_lista = []
        for _ in lista_riesgos:
            riesgo_enriquecido = riesgos_enriquecidos[idx_global]
            riesgo_final = dict(riesgo_enriquecido)

            # Para no romper el resto del sistema, la severidad visible queda ya ajustada
            riesgo_final["severidad"] = riesgo_enriquecido["severidad_ajustada"]

            nueva_lista.append(riesgo_final)
            idx_global += 1
        nuevos_clasificados[categoria] = nueva_lista

    if "analisis_profesional" not in resultado:
        resultado["analisis_profesional"] = {}

    resultado["analisis_profesional"]["riesgos_clasificados"] = nuevos_clasificados

    score = calcular_score(riesgos_enriquecidos)
    nivel = determinar_nivel(score)
    metricas = contar_metricas_por_severidad(riesgos_enriquecidos)

    resultado["scoring"] = {
        "score_total": score,
        "nivel_riesgo": nivel,
        "metricas": metricas,
        "version_scoring": ALGORITMO_SCORING_VERSION,
    }

    return resultado


# =========================================================
# COMPATIBILIDAD CON FLUJOS ANTIGUOS
# =========================================================

def aplicar_scoring_al_json(resultado: Dict) -> Dict:
    """
    Compatibilidad con estructuras antiguas que usan:
        resultado["riesgos_detectados"]

    Mantiene el comportamiento histórico, pero ahora también aplica
    reglas relevantes sobre la descripción del riesgo.
    """

    if not isinstance(resultado, dict):
        return resultado

    riesgos = resultado.get("riesgos_detectados", [])
    riesgos_enriquecidos = [enriquecer_riesgo_con_reglas(r) for r in riesgos]

    # Actualiza severidad visible para que refleje la corrección determinista
    nuevos_riesgos = []
    for r in riesgos_enriquecidos:
        r_final = dict(r)
        r_final["severidad"] = r["severidad_ajustada"]
        nuevos_riesgos.append(r_final)

    resultado["riesgos_detectados"] = nuevos_riesgos

    score = calcular_score(riesgos_enriquecidos)
    nivel = determinar_nivel(score)

    if "evaluacion_general" not in resultado:
        resultado["evaluacion_general"] = {}

    resultado["evaluacion_general"]["score_riesgo"] = {
        "nivel": nivel,
        "valor": score,
        "fundamento": (
            "Cálculo automático basado en metodología objetiva "
            f"(algoritmo {ALGORITMO_SCORING_VERSION})."
        )
    }

    return resultado