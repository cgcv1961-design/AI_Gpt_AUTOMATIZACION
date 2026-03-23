#scoring_engine.py

from typing import Dict, List
import math

ALGORITMO_SCORING_VERSION = "2.2_core"

PESOS_SEVERIDAD = {
    "baja": 1,
    "media": 2,
    "alta": 4,
    "critica": 6
}

MULTIPLICADORES_IMPACTO = {
    "legal": 1.0,
    "financiero": 1.3,
    "operativo": 1.1,
    "mixto": 1.5
}


def calcular_score(riesgos: List[Dict]) -> float:
    """
    Calcula score total basado en severidad e impacto.
    Aplica normalización logarítmica suave por volumen.
    """

    score_total = 0.0

    for riesgo in riesgos:
        severidad = riesgo["severidad"]
        impacto = riesgo["impacto"]

        peso = PESOS_SEVERIDAD.get(severidad, 2)
        multiplicador = MULTIPLICADORES_IMPACTO.get(impacto, 1.0)

        score_total += peso * multiplicador

    cantidad = len(riesgos)
    """
    cantidad = cantidad de riesgos
    log = logaritmo natural
    Si cantidad es pequeño → casi no afecta
    Si cantidad crece → empieza a suavizar
    """

    if cantidad > 0:
        score_total = score_total / (1 + math.log(cantidad + 1))

    return round(score_total, 2)

def extraer_riesgos_tecnico(data: dict) -> list:
    """
    Extrae todos los riesgos del modo técnico y los unifica
    en una lista plana para aplicar scoring.
    """

    riesgos_unificados = []

    clasificados = data["analisis_profesional"]["riesgos_clasificados"]

    for categoria in clasificados.values():
        riesgos_unificados.extend(categoria)

    return riesgos_unificados

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


def aplicar_scoring_al_json(resultado: Dict) -> Dict:
    """
    Inserta evaluacion_general.score_riesgo
    sin alterar estructura externa.
    """

    if not isinstance(resultado, dict):
        return resultado

    riesgos = resultado.get("riesgos_detectados", [])

    score = calcular_score(riesgos)
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