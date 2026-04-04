"""
verticales/general/service.py

Servicio de análisis para vertical GENERAL.
Arquitectura híbrida estable v4.1

Responsable de:
- Normalizar perfil
- Seleccionar modelo
- Construir prompt
- Ejecutar modelo
- Limpiar JSON
- Normalizar estructura (basico / tecnico)
- Recalcular severidad (determinístico)
- Guardar detalle auditable de reglas relevantes
- Calcular severidad del contrato

NOTA
----
El riesgo para la parte analizada ya NO se calcula acá.
Se enriquece después, en main.py, una vez que:
- ya se conoce la perspectiva
- ya se conocen los roles visibles
"""

import json

from utils.progreso import spinner

from typing import Dict
from openai import OpenAI
from config import CONFIG

from verticales.general.prompts.prompt_general import construir_prompt_general
from verticales.general.scoring import calcular_scoring_general
from utils.clasificador_severidad import analizar_severidad_detallada
from utils.json_cleaner import limpiar_respuesta_modelo

client = OpenAI()


def analizar_general(
    contrato: str,
    perfil: str,
    config: Dict
) -> Dict:

    if not perfil:
        raise ValueError("Perfil no informado.")

    perfil = perfil.strip().lower()

    alias = config.get("alias_perfiles", {})
    perfil_canonico = alias.get(perfil, perfil)

    modelos = config.get("modelos_por_perfil", {})
    modelo_nombre = modelos.get(perfil_canonico)

    if not modelo_nombre:
        raise ValueError(
            f"Perfil no soportado en vertical general: {perfil}"
        )

    prompt = construir_prompt_general(contrato, perfil_canonico)

    try:
        response = client.chat.completions.create(
            model=modelo_nombre,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
    except Exception as e:
        raise RuntimeError(f"Error al consultar el modelo: {str(e)}")

    resultado_texto = response.choices[0].message.content
    resultado_texto = limpiar_respuesta_modelo(resultado_texto)

    try:
        resultado = json.loads(resultado_texto)
    except json.JSONDecodeError:
        raise ValueError(
            "El modelo no devolvió un JSON válido.\n"
            f"Respuesta recibida:\n{resultado_texto[:800]}"
        )

    resultado = normalizar_estructura(resultado)

    riesgos = (
        resultado.get("analisis_profesional", {})
                 .get("riesgos_clasificados", {})
    )

    for categoria in riesgos.values():
        for riesgo in categoria:
            descripcion = riesgo.get("descripcion", "")

            analisis = analizar_severidad_detallada(descripcion)

            riesgo["severidad"] = analisis["severidad_final"]
            riesgo["severidad_base"] = analisis["severidad_base"]
            riesgo["familias_relevantes_detectadas"] = analisis["familias_detectadas"]
            riesgo["detalle_reglas_relevantes"] = analisis["detalle_reglas"]
            riesgo["severidad_minima_sugerida"] = analisis["severidad_minima_sugerida"]
            riesgo["puntaje_agravante_relevante"] = analisis["puntaje_agravante_total"]

    scoring = calcular_scoring_general(resultado)
    resultado["scoring"] = scoring

    resultado["metadata_sistema"] = {
        "vertical": "general",
        "perfil_original": perfil,
        "perfil_canonico": perfil_canonico,
        "modelo_utilizado": modelo_nombre,
        "version_servicio": "4.2_general_severidad_contrato_direccion_posterior"
    }

    return resultado


def normalizar_estructura(resultado: Dict) -> Dict:
    """
    Convierte cualquier salida (basico o tecnico)
    en estructura interna única:
    resultado["analisis_profesional"]["riesgos_clasificados"]
    """

    if (
        "analisis_profesional" in resultado and
        "riesgos_clasificados" in resultado["analisis_profesional"]
    ):
        return resultado

    riesgos_basico = resultado.get("riesgos_detectados", [])

    riesgos_normalizados = {
        "legal": [],
        "economico": [],
        "operativo": [],
        "reputacional": []
    }

    for riesgo in riesgos_basico:
        descripcion = riesgo.get("descripcion", "")
        impacto = riesgo.get("impacto", "legal")

        riesgo_normalizado = {
            "descripcion": descripcion,
            "impacto": impacto,
            "severidad": "baja"
        }

        if impacto == "financiero":
            riesgos_normalizados["economico"].append(riesgo_normalizado)
        elif impacto == "operativo":
            riesgos_normalizados["operativo"].append(riesgo_normalizado)
        elif impacto == "reputacional":
            riesgos_normalizados["reputacional"].append(riesgo_normalizado)
        else:
            riesgos_normalizados["legal"].append(riesgo_normalizado)

    resultado["analisis_profesional"] = {
        "riesgos_clasificados": riesgos_normalizados
    }
    return resultado


def ejecutar_analisis_general(data: dict):
    """
    Adaptador entre main.py y analizar_general()
    para ejecución desde el demo.
    """

    print("📑 Analizando contrato en vertical GENERAL...\n")

    texto = data.get("texto", "")
    perfil = "tecnico"

    with spinner("   ⏳ Ejecutando análisis IA general", "✔ Análisis completado"):
        resultado = analizar_general(
            contrato=texto,
            perfil=perfil,
            config=CONFIG
        )

    return resultado