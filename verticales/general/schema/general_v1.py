"""
verticales/general/schema/general_v1.py

Schema base – Vertical General
Versión estructura: 1.0_general
"""

VERSION_SCHEMA_GENERAL = "1.0_general"

CAMPOS_OBLIGATORIOS = [
    "resumen_ejecutivo",
    "riesgos_detectados",
    "fortalezas_detectadas"
]


def validar_estructura_general(data: dict) -> bool:
    """
    Valida que el JSON generado por el modelo
    contenga los campos mínimos esperados.
    """

    if not isinstance(data, dict):
        return False

    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in data:
            return False

    return True