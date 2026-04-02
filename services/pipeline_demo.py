"""
AI_GPT_AUTOMATIZACION/services/pipeline_demo.py
-----------------------------------------------

Pipeline unificado para demo web autónoma.
"""

import os
import json
from typing import Dict

from tools.convertidor_documentos import convertir_a_json
from main import ejecutar_motor


def procesar_contrato_desde_archivo(
    ruta_archivo: str,
    perspectiva: str = "proveedor",
    pais_referencia: str = "internacional"
) -> Dict:
    """
    Procesa un contrato desde archivo original hasta reporte final.
    """

    ruta_json_input = convertir_a_json(ruta_archivo)

    resultado = ejecutar_motor(
        ruta_json_input,
        perspectiva=perspectiva,
        pais_referencia=pais_referencia
    )

    if not resultado:
        raise RuntimeError("El motor no devolvió resultado.")

    ruta_json_output = resultado.get("ruta_json_output")
    ruta_word_output = resultado.get("ruta_word_output")
    vertical = resultado.get("vertical", "-")

    if not ruta_json_output or not os.path.exists(ruta_json_output):
        raise FileNotFoundError("No se encontró el JSON final de output.")

    with open(ruta_json_output, "r", encoding="utf-8") as f:
        data = json.load(f)

    resumen = construir_resumen_para_web(data)
    resumen["perspectiva"] = perspectiva
    resumen["pais_referencia"] = pais_referencia

    return {
        "ruta_json_input": ruta_json_input,
        "ruta_json_output": ruta_json_output,
        "ruta_word_output": ruta_word_output,
        "vertical": vertical,
        "resumen": resumen,
        "perspectiva": perspectiva,
        "pais_referencia": pais_referencia,
    }


def construir_resumen_para_web(data: dict) -> Dict:
    """
    Construye un resumen simple para mostrar en la web.
    """

    metadata = data.get("metadata_sistema", {}) or {}
    vertical = metadata.get("vertical", "general").lower()

    if vertical == "audiovisual":
        nucleo = data.get("nucleo_contractual", {}) or {}
        scoring = data.get("scoring", {}) or {}
        riesgos = data.get("analisis_sectorial", {}).get("riesgos_sectoriales", [])
        if not isinstance(riesgos, list):
            riesgos = []

        return {
            "tipo_contrato": nucleo.get("tipo_contrato", "-"),
            "score_total": scoring.get("score_total", "-"),
            "nivel_riesgo": scoring.get("nivel_riesgo", "-"),
            "cantidad_riesgos": len(riesgos),
        }

    nucleo = data.get("nucleo_contractual", {}) or {}
    scoring = data.get("scoring", {}) or {}
    metricas = scoring.get("metricas", {}) or {}
    riesgos = data.get("riesgos_detectados", [])
    if not isinstance(riesgos, list):
        riesgos = []

    cantidad_riesgos = metricas.get("cantidad_riesgos")
    if cantidad_riesgos in (None, "", [], {}):
        cantidad_riesgos = len(riesgos)

    return {
        "tipo_contrato": nucleo.get("tipo_contrato", data.get("tipo_contrato", "-")),
        "score_total": scoring.get("score_total", "-"),
        "nivel_riesgo": scoring.get("nivel_riesgo", "-"),
        "cantidad_riesgos": cantidad_riesgos,
    }