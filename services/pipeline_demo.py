"""
AI_GPT_AUTOMATIZACION/services/pipeline_demo.py
-----------------------------------------------

Pipeline unificado para demo web autónoma.

Responsabilidades
-----------------
1. Recibe un archivo subido por el usuario.
2. Lo convierte a JSON usando el convertidor existente.
3. Ejecuta el motor principal de análisis.
4. Devuelve rutas de salida y un resumen para mostrar en web.

Importante
----------
- Reutiliza el motor ya existente del sistema.
- No reemplaza la lógica jurídica.
- Sirve como puente entre la web y el motor.
"""

import os
import json
import shutil
from typing import Dict

from tools.convertidor_documentos import convertir_a_json
from main import ejecutar_motor


def procesar_contrato_desde_archivo(ruta_archivo: str) -> Dict:
    """
    Procesa un contrato desde archivo original hasta reporte final.

    Parámetros
    ----------
    ruta_archivo : str
        Ruta al archivo subido por el usuario.

    Retorna
    -------
    Dict
        Información útil para la interfaz web:
        - ruta_json_input
        - ruta_json_output
        - ruta_word_output
        - resumen
    """

    # -----------------------------------------------------
    # 1. Convertir a JSON de entrada
    # -----------------------------------------------------
    ruta_json_input = convertir_a_json(ruta_archivo)

    # -----------------------------------------------------
    # 2. Ejecutar motor principal
    #    ejecutar_motor debe generar JSON y Word en /output
    # -----------------------------------------------------
    resultado = ejecutar_motor(ruta_json_input)

    if not resultado:
        raise RuntimeError("El motor no devolvió resultado.")

    ruta_json_output = resultado.get("ruta_json_output")
    ruta_word_output = resultado.get("ruta_word_output")
    vertical = resultado.get("vertical", "-")

    # -----------------------------------------------------
    # 3. Leer JSON final para resumen
    # -----------------------------------------------------
    if not ruta_json_output or not os.path.exists(ruta_json_output):
        raise FileNotFoundError("No se encontró el JSON final de output.")

    with open(ruta_json_output, "r", encoding="utf-8") as f:
        data = json.load(f)

    resumen = construir_resumen_para_web(data)

    return {
        "ruta_json_input": ruta_json_input,
        "ruta_json_output": ruta_json_output,
        "ruta_word_output": ruta_word_output,
        "vertical": vertical,
        "resumen": resumen,
    }


def construir_resumen_para_web(data: dict) -> Dict:
    """
    Construye un resumen simple para mostrar en la web.
    Funciona para general y audiovisual.
    """

    metadata = data.get("metadata_sistema", {})
    vertical = metadata.get("vertical", "general").lower()

    if vertical == "audiovisual":
        nucleo = data.get("nucleo_contractual", {})
        scoring = data.get("scoring", {})
        riesgos = data.get("analisis_sectorial", {}).get("riesgos_sectoriales", [])

        return {
            "tipo_contrato": nucleo.get("tipo_contrato", "-"),
            "score_total": scoring.get("score_total", "-"),
            "nivel_riesgo": scoring.get("nivel_riesgo", "-"),
            "cantidad_riesgos": len(riesgos),
        }

    scoring = data.get("scoring", {})
    riesgos = data.get("riesgos_detectados", [])

    return {
        "tipo_contrato": data.get("tipo_contrato", "-"),
        "score_total": scoring.get("score_total", "-"),
        "nivel_riesgo": scoring.get("nivel_riesgo", "-"),
        "cantidad_riesgos": len(riesgos),
    }