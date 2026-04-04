"""
verticales/general/scoring.py
-----------------------------

Motor de scoring v4.3
Calibración con masa crítica estructural
+ compatibilidad con severidad crítica
+ preparado para reglas relevantes integradas aguas arriba

OBJETIVO
--------
Calcular el score total y el nivel de riesgo global a partir de los
riesgos ya clasificados por severidad.

IMPORTANTE
----------
Este módulo NO detecta cláusulas por sí mismo.
La detección y recalibración semántica ocurre antes, en:
- utils/clasificador_severidad.py
- core/reglas_relevantes.py

Este módulo:
- cuenta severidades finales
- pondera
- aplica reglas estructurales
- devuelve el bloque scoring final
"""

from typing import Dict


def calcular_scoring_general(resultado: Dict) -> Dict:
    """
    Calcula el scoring general del contrato a partir de los riesgos
    ya clasificados en `analisis_profesional.riesgos_clasificados`.

    Parámetros
    ----------
    resultado : Dict
        JSON consolidado del análisis de la vertical GENERAL.

    Retorna
    -------
    Dict
        Bloque `scoring` con:
        - score_total
        - nivel_riesgo
        - métricas por severidad
        - versión del algoritmo
    """

    riesgos = (
        resultado.get("analisis_profesional", {})
                 .get("riesgos_clasificados", {})
    )

    conteo = {
        "critica": 0,
        "alta": 0,
        "media-alta": 0,
        "media": 0,
        "baja": 0
    }

    # ------------------------------------------------
    # 1️⃣ Conteo de severidades finales
    # ------------------------------------------------
    for categoria in riesgos.values():
        for riesgo in categoria:
            sev = riesgo.get("severidad", "baja")
            if sev in conteo:
                conteo[sev] += 1

    total_riesgos = sum(conteo.values())

    # ------------------------------------------------
    # 2️⃣ Ponderación calibrada
    # ------------------------------------------------
    # Nota:
    # - "critica" se reserva para casos realmente extremos
    # - mantenemos pesos previos y sumamos uno superior
    pesos = {
        "baja": 0.5,
        "media": 3,
        "media-alta": 6,
        "alta": 10,
        "critica": 14
    }

    score_total = (
        conteo["baja"] * pesos["baja"] +
        conteo["media"] * pesos["media"] +
        conteo["media-alta"] * pesos["media-alta"] +
        conteo["alta"] * pesos["alta"] +
        conteo["critica"] * pesos["critica"]
    )

    # ------------------------------------------------
    # 3️⃣ Reglas estructurales de dominancia
    # ------------------------------------------------
    if conteo["critica"] >= 1:
        nivel = "alto"

    elif conteo["alta"] >= 2:
        nivel = "alto"

    elif conteo["alta"] == 1 and conteo["media-alta"] >= 2:
        nivel = "alto"

    elif conteo["alta"] == 1:
        nivel = "medio-alto"

    elif conteo["media-alta"] >= 3:
        nivel = "medio-alto"

    else:
        # ------------------------------------------------
        # 4️⃣ Evaluación por score acumulado
        # ------------------------------------------------
        if score_total >= 45:
            nivel = "alto"
        elif score_total >= 25:
            nivel = "medio-alto"
        elif score_total >= 15:
            nivel = "medio"
        else:
            nivel = "bajo"

    # ------------------------------------------------
    # 5️⃣ Masa crítica estructural
    # ------------------------------------------------
    # Si hay muchos riesgos aunque todos sean leves, el sistema no
    # debería devolver "bajo" automáticamente.
    if nivel == "bajo" and total_riesgos >= 8:
        nivel = "medio"

    return {
        "score_total": round(score_total, 2),
        "nivel_riesgo": nivel,
        "metricas": {
            "cantidad_riesgos": total_riesgos,
            "riesgos_criticos": conteo["critica"],
            "riesgos_altos": conteo["alta"],
            "riesgos_media_altos": conteo["media-alta"],
            "riesgos_medios": conteo["media"],
            "riesgos_bajos": conteo["baja"]
        },
        "version_scoring": "4.3_general_reglas_relevantes"
    }