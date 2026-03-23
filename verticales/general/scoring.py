"""
verticales/general/scoring.py

Motor de scoring v4.2
Calibración con masa crítica estructural.
"""

from typing import Dict


def calcular_scoring_general(resultado: Dict) -> Dict:

    riesgos = (
        resultado.get("analisis_profesional", {})
                 .get("riesgos_clasificados", {})
    )

    conteo = {
        "alta": 0,
        "media-alta": 0,
        "media": 0,
        "baja": 0
    }

    # ------------------------------------------------
    # 1️⃣ Conteo
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
    pesos = {
        "baja": 0.5,
        "media": 3,
        "media-alta": 6,
        "alta": 10
    }

    score_total = (
        conteo["baja"] * pesos["baja"] +
        conteo["media"] * pesos["media"] +
        conteo["media-alta"] * pesos["media-alta"] +
        conteo["alta"] * pesos["alta"]
    )

    # ------------------------------------------------
    # 3️⃣ Reglas estructurales (dominancia)
    # ------------------------------------------------

    if conteo["alta"] >= 2:
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
    # 5️⃣ Masa crítica estructural (NUEVO)
    # ------------------------------------------------
    if nivel == "bajo" and total_riesgos >= 8:
        nivel = "medio"

    return {
        "score_total": round(score_total, 2),
        "nivel_riesgo": nivel,
        "metricas": {
            "cantidad_riesgos": total_riesgos,
            "riesgos_altos": conteo["alta"],
            "riesgos_media_altos": conteo["media-alta"],
            "riesgos_medios": conteo["media"],
            "riesgos_bajos": conteo["baja"]
        },
        "version_scoring": "4.2_calibrado_masa_critica"
    }