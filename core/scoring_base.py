"""
AI_GPT_AUTOMATIZACION/core/scoring_base.py

Motor Matemático Base de Scoring

Este módulo contiene exclusivamente lógica matemática neutral.
No contiene ninguna regla jurídica ni sectorial.

Su responsabilidad es:

- Sumar pesos según severidad
- Ser reutilizable por cualquier vertical

Este archivo NO debe modificarse al crear nuevas verticales.
"""

from typing import List, Dict


def sumar_pesos_por_severidad(
    riesgos: List[Dict],
    mapa_pesos: Dict[str, float]
) -> float:
    """
    Suma el score total en función de la severidad de cada riesgo.

    :param riesgos: Lista de riesgos detectados.
                    Cada riesgo debe contener una clave "severidad".
    :param mapa_pesos: Diccionario que define el peso numérico
                       para cada nivel de severidad.
    :return: Score numérico total.
    """

    score = 0.0

    if not isinstance(riesgos, list):
        return score

    for riesgo in riesgos:
        severidad = riesgo.get("severidad", "media")
        peso = mapa_pesos.get(severidad, 0)
        score += peso

    return score