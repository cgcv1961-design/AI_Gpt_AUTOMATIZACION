"""
AI_GPT_AUTOMATIZACION/services/router.py

Punto único de entrada del sistema.
Recibe vertical y perfil.
Decide qué servicio sectorial ejecutar.
"""


from verticales.general.service import analizar_general
from verticales.audiovisual.service import analizar_audiovisual
from config import CONFIG


def analizar_contrato(
    contrato: str,
    vertical: str,
    perfil: str
) -> dict:

    vertical = vertical.strip().lower()

    if vertical == "general":
        return analizar_general(contrato, perfil, CONFIG)

    elif vertical == "audiovisual":
        return analizar_audiovisual(contrato, perfil, CONFIG)

    else:
        raise ValueError("Vertical no soportada.")