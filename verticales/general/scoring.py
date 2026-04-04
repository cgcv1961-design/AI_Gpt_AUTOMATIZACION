"""
verticales/general/scoring.py
-----------------------------

Motor de scoring v4.4
Severidad del contrato + compatibilidad con scoring dual.

OBJETIVO
--------
Calcular la SEVERIDAD DEL CONTRATO, es decir:
qué tan exigente, duro o litigioso es el contrato en sí mismo,
sin confundir ese valor con el riesgo específico para la parte analizada.

IMPORTANTE
----------
- Este módulo NO calcula el riesgo direccional por rol.
- Eso se agrega después en core/scoring_engine.py
- Este módulo mantiene aliases legacy para no romper la UI ni el Word.
"""

from typing import Dict


def calcular_scoring_general(resultado: Dict) -> Dict:
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

    for categoria in riesgos.values():
        for riesgo in categoria:
            sev = riesgo.get("severidad", "baja")
            if sev in conteo:
                conteo[sev] += 1

    total_riesgos = sum(conteo.values())

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
        if score_total >= 45:
            nivel = "alto"
        elif score_total >= 25:
            nivel = "medio-alto"
        elif score_total >= 15:
            nivel = "medio"
        else:
            nivel = "bajo"

    if nivel == "bajo" and total_riesgos >= 8:
        nivel = "medio"

    score_total = round(score_total, 2)

    return {
        "severidad_contrato": {
            "score": score_total,
            "nivel": nivel,
            "fundamento": "Mide la intensidad jurídica, económica y operativa del contrato en sí mismo."
        },

        # aliases legacy para no romper nada existente
        "score_total": score_total,
        "nivel_riesgo": nivel,

        "metricas": {
            "cantidad_riesgos": total_riesgos,
            "riesgos_criticos": conteo["critica"],
            "riesgos_altos": conteo["alta"],
            "riesgos_media_altos": conteo["media-alta"],
            "riesgos_medios": conteo["media"],
            "riesgos_bajos": conteo["baja"]
        },
        "version_scoring": "4.4_general_severidad_contrato"
    }