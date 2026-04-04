"""
AI_GPT_AUTOMATIZACION/core/utils_semanticos.py

Utilidades Semánticas Reutilizables

Este módulo contiene funciones lingüísticas básicas
que permiten detectar:

- Ausencia real de cláusulas
- Ambigüedad o indefinición relevante

Estas funciones NO son sectoriales.
Son herramientas generales que pueden ser utilizadas
por cualquier vertical.
"""

from typing import Optional


PALABRAS_AUSENCIA = [
    "no existe",
    "no se incluye",
    "no se establece",
    "no se menciona",
    "ausencia",
    "no hay"
]


PALABRAS_AMBIGUEDAD = [
    "a definir",
    "pendiente",
    "indefinido",
    "sin especificar",
    "por acordar"
]


def texto_indica_ausencia(texto: Optional[str]) -> bool:
    """
    Detecta si un texto indica ausencia real de cláusula.

    :param texto: Texto a evaluar.
    :return: True si indica ausencia.
    """

    if not texto:
        return True

    texto = texto.lower()
    return any(palabra in texto for palabra in PALABRAS_AUSENCIA)


def texto_indica_ambiguedad(texto: Optional[str]) -> bool:
    """
    Detecta si un texto indica ambigüedad o indefinición relevante.

    :param texto: Texto a evaluar.
    :return: True si se detecta ambigüedad.
    """

    if not texto:
        return True

    texto = texto.lower()
    return any(palabra in texto for palabra in PALABRAS_AMBIGUEDAD)