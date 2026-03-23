"""
AI_GPT_AUTOMATIZACION/utils/json_cleaner.py

Limpieza robusta de respuestas del modelo
para asegurar JSON válido.
"""

import re


def limpiar_respuesta_modelo(texto: str) -> str:
    """
    Elimina bloques markdown tipo ```json ... ```
    y devuelve únicamente el JSON interno.
    """

    if not texto:
        return ""

    texto = texto.strip()

    # Detectar bloque ```json ... ```
    patron = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(patron, texto, re.DOTALL)

    if match:
        return match.group(1).strip()

    return texto