"""
verticales/audiovisual/service.py
---------------------------------

Servicio de análisis para la vertical AUDIOVISUAL.

RESPONSABILIDADES
-----------------
Este módulo:

1. Normaliza el perfil de análisis.
2. Selecciona el modelo según la configuración central.
3. Construye el prompt especializado audiovisual.
4. Ejecuta el modelo de IA.
5. Extrae y parsea el JSON devuelto por el modelo.
6. Recalcula severidad de forma determinística.
7. Normaliza la salida final a un JSON único y rico.
8. Deja un scoring preliminar, pero NO definitivo.
9. El scoring final audiovisual se recalcula en main.py cuando
   ya está resuelta la perspectiva y el rol visible final.

PRINCIPIO DE DISEÑO
-------------------
JSON = fuente de verdad única

MEJORA DE ESTA VERSIÓN
----------------------
Se elimina la dependencia del rol interno como fuente final del scoring.
El scoring definitivo se deja para main.py, donde ya existe:
- perspectiva final
- metadata_presentacion
- rol_contractual_detectado final
"""

import json
from typing import Dict, Any

from openai import OpenAI

from config import CONFIG
from utils.clasificador_severidad import analizar_severidad_detallada
from utils.progreso import spinner
from verticales.audiovisual.prompts_aud import construir_prompt_audiovisual
from verticales.audiovisual.scoring_engine_productor import calcular_scoring_productor
from verticales.audiovisual.schema.aud_v1_2_productor import normalizar_respuesta_audiovisual


client = OpenAI()


def _extraer_json_valido(texto: str) -> Dict[str, Any]:
    if not isinstance(texto, str):
        raise ValueError("La respuesta del modelo no es texto válido.")

    texto = texto.strip()

    try:
        parsed = json.loads(texto)
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("El JSON devuelto no es un objeto.")
    except Exception:
        pass

    if "```" in texto:
        partes = texto.split("```")
        for parte in partes:
            candidato = parte.strip()

            if candidato.lower().startswith("json"):
                candidato = candidato[4:].strip()

            if candidato.startswith("{") and candidato.endswith("}"):
                try:
                    parsed = json.loads(candidato)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    continue

    inicio = texto.find("{")
    fin = texto.rfind("}")

    if inicio != -1 and fin != -1 and fin > inicio:
        candidato = texto[inicio:fin + 1]
        try:
            parsed = json.loads(candidato)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    raise ValueError(
        "No se pudo extraer JSON válido del modelo.\n"
        f"Respuesta:\n{texto[:500]}"
    )


def _detectar_rol_interno_audiovisual(resultado: Dict[str, Any]) -> str:
    """
    Detección preliminar del rol interno.

    IMPORTANTE:
    Este valor NO debe considerarse definitivo para scoring.
    El scoring final se recalcula en main.py cuando la perspectiva
    ya fue aplicada y el rol visible final está resuelto.
    """
    partes = (
        resultado.get("nucleo_contractual", {})
                .get("partes", [])
    )

    if isinstance(partes, list):
        for parte in partes:
            parte_txt = str(parte).lower()

            if "el artista" in parte_txt or "artista" in parte_txt or "intérprete" in parte_txt or "interprete" in parte_txt:
                return "Artista"

            if "la productora" in parte_txt or "productora" in parte_txt:
                return "Productora"

            if "productor" in parte_txt:
                return "Productor"

    return "Artista"


def analizar_audiovisual(
    contrato: str,
    perfil: str,
    config: Dict
) -> Dict:
    if not contrato or not str(contrato).strip():
        raise ValueError("No se recibió texto contractual para analizar.")

    if not perfil:
        raise ValueError("Perfil no informado.")

    perfil = perfil.strip().lower()

    alias = config.get("alias_perfiles", {})
    perfil_canonico = alias.get(perfil, perfil)

    modelos = config.get("modelos_por_perfil", {})
    modelo_nombre = modelos.get(perfil_canonico)

    if not modelo_nombre:
        raise ValueError(
            f"Perfil no soportado en vertical audiovisual: {perfil}"
        )

    prompt = construir_prompt_audiovisual(contrato)

    try:
        response = client.chat.completions.create(
            model=modelo_nombre,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
    except Exception as e:
        raise RuntimeError(f"Error al consultar el modelo: {str(e)}")

    resultado_texto = response.choices[0].message.content
    resultado = _extraer_json_valido(resultado_texto)

    riesgos = (
        resultado.get("analisis_sectorial", {})
                 .get("riesgos_sectoriales", [])
    )

    if isinstance(riesgos, list):
        for riesgo in riesgos:
            if not isinstance(riesgo, dict):
                continue

            descripcion = riesgo.get("descripcion", "")
            analisis = analizar_severidad_detallada(descripcion)

            riesgo["severidad"] = analisis["severidad_final"]
            riesgo["severidad_base"] = analisis["severidad_base"]
            riesgo["familias_relevantes_detectadas"] = analisis["familias_detectadas"]
            riesgo["detalle_reglas_relevantes"] = analisis["detalle_reglas"]
            riesgo["severidad_minima_sugerida"] = analisis["severidad_minima_sugerida"]
            riesgo["puntaje_agravante_relevante"] = analisis["puntaje_agravante_total"]

    resultado = normalizar_respuesta_audiovisual(
        respuesta_modelo=resultado,
        texto_contrato=contrato
    )

    rol_interno = _detectar_rol_interno_audiovisual(resultado)

    # Scoring preliminar.
    # El definitivo se recalcula en main.py con el rol visible final.
    resultado = calcular_scoring_productor(
        resultado=resultado,
        rol_analizado=rol_interno
    )

    metadata_sistema_existente = resultado.get("metadata_sistema", {}) or {}

    metadata_sistema_existente.update({
        "vertical": "audiovisual",
        "perfil_original": perfil,
        "perfil_canonico": perfil_canonico,
        "modelo_utilizado": modelo_nombre,
        "rol_detectado_interno": rol_interno,
        "version_servicio": "4.5_audiovisual_scoring_final_en_main"
    })

    resultado["metadata_sistema"] = metadata_sistema_existente

    return resultado


def ejecutar_analisis_audiovisual(data: dict) -> Dict:
    print("🎬 Analizando contrato en vertical AUDIOVISUAL...\n")

    texto = data.get("texto", "")

    if not texto:
        raise ValueError("No se encontró texto del contrato para analizar.")

    perfil = "tecnico"

    with spinner("   ⏳ Ejecutando análisis IA Audiovisual", "✔ Análisis completado"):
        resultado = analizar_audiovisual(
            contrato=texto,
            perfil=perfil,
            config=CONFIG
        )

    return resultado