"""
verticales/audiovisual/validador_respuesta.py
---------------------------------------------

Validador estructural para la respuesta audiovisual.

OBJETIVO
--------
Validar que la respuesta de la LLM tenga una forma mínima compatible
con la vertical audiovisual actual.

IMPORTANTE
----------
- NO exige severidad desde la LLM, porque la severidad se calcula
  externamente por lógica determinística.
- Sí valida:
  - estructura raíz
  - riesgos_sectoriales
  - impacto
  - tipo_riesgo (si viene)
  - afecta_principalmente_a (si viene)

USO
---
Se puede usar antes o después del normalizador, dependiendo del flujo.
"""

from typing import Dict, Any, List


IMPACTOS_VALIDOS = ["legal", "financiero", "operativo", "reputacional", "mixto"]

TIPOS_RIESGO_VALIDOS = [
    "cesion_derechos",
    "exclusividad",
    "penalidad",
    "plazo",
    "pago",
    "control_creativo",
    "distribucion",
    "obligaciones_operativas",
    "confidencialidad",
    "seguros",
    "terminacion",
    "jurisdiccion_conflictos",
    "imagen_promocion",
    "disponibilidad_artista",
]

AFECTA_VALIDOS = ["artista", "productora", "ambas"]


class ErrorEstructura(Exception):
    pass


def _validar_raiz(data: Dict[str, Any]) -> None:
    campos_raiz = ["nucleo_contractual", "analisis_sectorial", "informe_cliente"]
    for campo in campos_raiz:
        if campo not in data:
            raise ErrorEstructura(f"Falta campo obligatorio: {campo}")


def _validar_riesgos(riesgos: List[Dict[str, Any]]) -> None:
    if not isinstance(riesgos, list):
        raise ErrorEstructura("riesgos_sectoriales debe ser una lista.")

    for riesgo in riesgos:
        if not isinstance(riesgo, dict):
            raise ErrorEstructura("Cada riesgo debe ser un objeto JSON.")

        if "descripcion" not in riesgo or not str(riesgo.get("descripcion", "")).strip():
            raise ErrorEstructura("Cada riesgo debe incluir descripcion.")

        impacto = riesgo.get("impacto", "")
        if impacto not in IMPACTOS_VALIDOS:
            raise ErrorEstructura(f"Impacto inválido: {impacto}")

        # tipo_riesgo es recomendado/esperado.
        # Si viene, debe ser válido.
        tipo_riesgo = str(riesgo.get("tipo_riesgo", "") or "").strip()
        if tipo_riesgo and tipo_riesgo not in TIPOS_RIESGO_VALIDOS:
            raise ErrorEstructura(f"tipo_riesgo inválido: {tipo_riesgo}")

        afecta = str(riesgo.get("afecta_principalmente_a", "") or "").strip()
        if afecta and afecta not in AFECTA_VALIDOS:
            raise ErrorEstructura(f"afecta_principalmente_a inválido: {afecta}")


def validar_respuesta_audiovisual(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ErrorEstructura("La respuesta no es un objeto JSON válido.")

    _validar_raiz(data)

    analisis_sectorial = data.get("analisis_sectorial")
    if not isinstance(analisis_sectorial, dict):
        raise ErrorEstructura("analisis_sectorial debe ser un objeto.")

    riesgos = analisis_sectorial.get("riesgos_sectoriales", [])
    _validar_riesgos(riesgos)

    return data