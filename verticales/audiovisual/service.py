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
7. Aplica scoring audiovisual alineado con el motor unificado.
8. Normaliza la salida final a un JSON único y rico.
9. Expone un adaptador estándar para integrarse con main.py,
   demo y API.

PRINCIPIO DE DISEÑO
-------------------
JSON = fuente de verdad única

Esto significa que:
- el dictamen final debe quedar consolidado en el JSON
- el Word debe salir exclusivamente de ese JSON
- no debe haber una segunda interpretación paralela en el generador Word

MEJORA DE ESTA VERSIÓN
----------------------
La vertical audiovisual deja de depender de una lógica de scoring aislada
y pasa a apoyarse en un motor alineado con la arquitectura nueva del sistema.

Esto permite:
- mayor consistencia entre vertical GENERAL y AUDIOVISUAL
- coherencia entre severidad del contrato y riesgo para la parte analizada
- menor duplicación de lógica
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
    """
    Intenta extraer el primer JSON válido desde un texto devuelto por el modelo.

    Casos soportados:
    - JSON limpio
    - bloque ```json ... ```
    - texto adicional antes o después del JSON

    Parámetros
    ----------
    texto : str
        Contenido textual devuelto por el modelo.

    Retorna
    -------
    Dict[str, Any]
        JSON parseado correctamente.

    Lanza
    -----
    ValueError
        Si no se puede extraer un JSON válido.
    """
    if not isinstance(texto, str):
        raise ValueError("La respuesta del modelo no es texto válido.")

    texto = texto.strip()

    # ------------------------------------------------
    # Caso 1: JSON limpio
    # ------------------------------------------------
    try:
        parsed = json.loads(texto)
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("El JSON devuelto no es un objeto.")
    except Exception:
        pass

    # ------------------------------------------------
    # Caso 2: bloques ```json ... ``` o ``` ... ```
    # ------------------------------------------------
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

    # ------------------------------------------------
    # Caso 3: buscar desde primer { hasta último }
    # ------------------------------------------------
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


def _detectar_rol_analizado_audiovisual(resultado: Dict[str, Any]) -> str:
    """
    Intenta inferir el rol analizado en audiovisual a partir de las partes.

    Regla práctica inicial:
    - si encuentra 'artista' en la segunda parte, devuelve 'Artista'
    - si encuentra 'productora' o 'productor', devuelve ese rol
    - por defecto devuelve 'Artista', porque en la mayoría de las pruebas
      actuales el análisis audiovisual se ha interpretado desde ese lado
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
    """
    Ejecuta el análisis audiovisual completo.

    Parámetros
    ----------
    contrato : str
        Texto completo del contrato.
    perfil : str
        Perfil de análisis solicitado.
    config : Dict
        Configuración central del sistema.

    Retorna
    -------
    Dict
        Resultado estructurado final del análisis audiovisual,
        ya normalizado como JSON autoritativo.
    """

    # ------------------------------------------------
    # 1) Validaciones básicas
    # ------------------------------------------------
    if not contrato or not str(contrato).strip():
        raise ValueError("No se recibió texto contractual para analizar.")

    if not perfil:
        raise ValueError("Perfil no informado.")

    # ------------------------------------------------
    # 2) Normalización de perfil
    # ------------------------------------------------
    perfil = perfil.strip().lower()

    alias = config.get("alias_perfiles", {})
    perfil_canonico = alias.get(perfil, perfil)

    modelos = config.get("modelos_por_perfil", {})
    modelo_nombre = modelos.get(perfil_canonico)

    if not modelo_nombre:
        raise ValueError(
            f"Perfil no soportado en vertical audiovisual: {perfil}"
        )

    # ------------------------------------------------
    # 3) Construcción del prompt
    # ------------------------------------------------
    prompt = construir_prompt_audiovisual(contrato)

    # ------------------------------------------------
    # 4) Llamada al modelo
    # ------------------------------------------------
    try:
        response = client.chat.completions.create(
            model=modelo_nombre,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
    except Exception as e:
        raise RuntimeError(f"Error al consultar el modelo: {str(e)}")

    resultado_texto = response.choices[0].message.content

    # ------------------------------------------------
    # 5) Parse robusto del JSON devuelto por el modelo
    # ------------------------------------------------
    resultado = _extraer_json_valido(resultado_texto)

    # ------------------------------------------------
    # 6) Clasificación determinística de severidad
    # ------------------------------------------------
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

    # ------------------------------------------------
    # 7) Normalización intermedia del JSON
    # ------------------------------------------------
    # La hacemos antes del scoring para disponer de una estructura
    # más uniforme y con partes claramente visibles.
    resultado = normalizar_respuesta_audiovisual(
        respuesta_modelo=resultado,
        texto_contrato=contrato
    )

    # ------------------------------------------------
    # 8) Detección del rol analizado
    # ------------------------------------------------
    rol_analizado = _detectar_rol_analizado_audiovisual(resultado)

    # ------------------------------------------------
    # 9) Scoring audiovisual alineado
    # ------------------------------------------------
    # Se delega en scoring_engine_productor.py, que ahora debe actuar
    # como wrapper/adaptador del motor unificado.
    resultado = calcular_scoring_productor(
        resultado=resultado,
        rol_analizado=rol_analizado
    )

    # ------------------------------------------------
    # 10) Metadata técnica
    # ------------------------------------------------
    resultado["metadata_sistema"] = {
        "vertical": "audiovisual",
        "perfil_original": perfil,
        "perfil_canonico": perfil_canonico,
        "modelo_utilizado": modelo_nombre,
        "rol_detectado_interno": rol_analizado,
        "version_servicio": "4.4_audiovisual_scoring_alineado"
    }

    return resultado


# =========================================================
# ADAPTADOR PARA EL MOTOR PRINCIPAL
# =========================================================

def ejecutar_analisis_audiovisual(data: dict) -> Dict:
    """
    Adaptador entre main.py y analizar_audiovisual().

    Este método permite que la vertical audiovisual funcione
    de forma homogénea con la vertical general, tanto en demo
    como en ejecución por API.

    Parámetros
    ----------
    data : dict
        JSON del contrato con el texto ya extraído.

    Retorna
    -------
    Dict
        Resultado final del análisis audiovisual, ya normalizado.
    """

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