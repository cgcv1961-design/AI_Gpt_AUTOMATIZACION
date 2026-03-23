"""
audiovisual/validador_respuesta.py
"""
"""
Schema oficial Audiovisual Productor
Versión 1.2
"""
from typing import Dict
from verticales.audiovisual.schema.aud_v1_2_productor import (
    VERSION_SCHEMA,
    CAMPOS_OBLIGATORIOS,
    CAMPOS_METADATA_OBLIGATORIOS
)

SEVERIDADES_VALIDAS = ["baja", "media", "alta"]
IMPACTOS_VALIDOS = ["legal", "financiero", "operativo", "reputacional"]


class ErrorEstructura(Exception):
    pass


def validar_respuesta_aud_productor(data: Dict) -> Dict:

    if not isinstance(data, dict):
        raise ErrorEstructura("La respuesta no es un objeto JSON válido.")

    # 🔹 Validar campos raíz
    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in data:
            raise ErrorEstructura(f"Falta campo obligatorio: {campo}")

    # 🔹 Validar metadata
    metadata = data.get("metadata")

    if not isinstance(metadata, dict):
        raise ErrorEstructura("Metadata inválida.")

    for campo in CAMPOS_METADATA_OBLIGATORIOS:
        if campo not in metadata:
            raise ErrorEstructura(
                f"Falta campo obligatorio en metadata: {campo}"
            )

    if metadata.get("version") != VERSION_SCHEMA:
        raise ErrorEstructura(
            f"Versión incorrecta. Se esperaba {VERSION_SCHEMA}"
        )

    # 🔹 Validar riesgos_detectados
    riesgos = data.get("riesgos_detectados")

    if not isinstance(riesgos, list):
        raise ErrorEstructura("riesgos_detectados debe ser lista.")

    for riesgo in riesgos:

        if not isinstance(riesgo, dict):
            raise ErrorEstructura("Cada riesgo debe ser objeto.")

        if "descripcion" not in riesgo:
            raise ErrorEstructura("Riesgo sin descripcion.")

        severidad = riesgo.get("severidad")
        impacto = riesgo.get("impacto")

        if severidad not in SEVERIDADES_VALIDAS:
            raise ErrorEstructura("Severidad inválida.")

        if impacto not in IMPACTOS_VALIDOS:
            raise ErrorEstructura("Impacto inválido.")

    return data