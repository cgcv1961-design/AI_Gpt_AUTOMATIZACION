"""
AI_GPT_AUTOMATIZACION/core/nivelador.py

Determinador Global de Nivel de Riesgo

Este módulo define los umbrales oficiales del sistema.
Debe existir UN solo criterio de niveles para garantizar coherencia.

Si en el futuro se modifican umbrales,
debe hacerse aquí exclusivamente.
"""


def determinar_nivel(score: float) -> str:
    """
    Determina el nivel cualitativo del riesgo
    en función del score numérico total.

    :param score: Score numérico total.
    :return: Nivel cualitativo (bajo, medio, alto, critico).
    """

    if score < 20:
        return "bajo"
    elif score < 45:
        return "medio"
    elif score < 75:
        return "alto"
    else:
        return "critico"