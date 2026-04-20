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
7. Completa tipo_riesgo y afecta_principalmente_a si faltan.
8. Normaliza la salida final a un JSON único y rico.
9. Deja un scoring preliminar, pero NO definitivo.
10. El scoring final audiovisual se recalcula en main.py cuando
    ya está resuelta la perspectiva y el rol visible final.

PRINCIPIO DE DISEÑO
-------------------
JSON = fuente de verdad única

MEJORA DE ESTA VERSIÓN
----------------------
- Se elimina la dependencia del rol interno como fuente final del scoring.
- Se deja el scoring definitivo para main.py.
- Se agrega fallback determinista para `tipo_riesgo`.
- Se agrega fallback conservador para `afecta_principalmente_a`.
- Se corrige priorización de `terminacion` frente a `pago`
  en cláusulas de rescisión o resolución.
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


def _inferir_tipo_riesgo_desde_texto(descripcion: str, recomendacion: str = "", impacto: str = "") -> str:
    """
    Fallback conservador para completar `tipo_riesgo` si el LLM no lo devuelve.

    No reemplaza al motor determinista final. Solo mejora el insumo.

    IMPORTANTE:
    Se prioriza `terminacion` sobre `pago` cuando la cláusula gira
    principalmente sobre rescisión / resolución del vínculo.
    """
    texto = f"{descripcion} {recomendacion}".lower()

    # -----------------------------------------------------
    # PRIORIDAD 1: TERMINACIÓN / RESCISIÓN
    # -----------------------------------------------------
    if any(k in texto for k in [
        "rescisión",
        "rescision",
        "terminación",
        "terminacion",
        "resolver el contrato",
        "puede rescindir",
        "puede resolver",
        "rescisión anticipada",
        "rescision anticipada",
        "pagando solo lo devengado",
        "solo lo devengado",
    ]):
        return "terminacion"

    # -----------------------------------------------------
    # PRIORIDAD 2: CESIÓN / DERECHOS / IMAGEN
    # -----------------------------------------------------
    if any(k in texto for k in [
        "cesión",
        "cesion",
        "derechos",
        "imagen",
        "interpretación",
        "interpretacion",
        "todos los medios",
        "todos los territorios",
        "máximo plazo legal",
        "maximo plazo legal",
        "irrevocable",
        "perpetua",
    ]):
        return "cesion_derechos"

    # -----------------------------------------------------
    # PRIORIDAD 3: EXCLUSIVIDAD
    # -----------------------------------------------------
    if any(k in texto for k in [
        "exclusividad",
        "producciones competitivas",
        "no podrá participar",
        "no podra participar",
        "limita su participación",
        "limita su participacion",
    ]):
        return "exclusividad"

    # -----------------------------------------------------
    # PRIORIDAD 4: PENALIDAD
    # -----------------------------------------------------
    if any(k in texto for k in [
        "penalidad",
        "cláusula penal",
        "clausula penal",
        "multa",
        "daños y perjuicios",
    ]):
        return "penalidad"

    # -----------------------------------------------------
    # PRIORIDAD 5: PAGO / REGALÍAS / COMPENSACIÓN
    # -----------------------------------------------------
    if any(k in texto for k in [
        "regalías",
        "regalias",
        "pago",
        "precio",
        "remuneración",
        "remuneracion",
        "compensación",
        "compensacion",
        "ingresos futuros",
        "explotaciones secundarias",
    ]):
        return "pago"

    # -----------------------------------------------------
    # PRIORIDAD 6: CONTROL CREATIVO
    # -----------------------------------------------------
    if any(k in texto for k in [
        "control creativo",
        "editar",
        "adaptar",
        "modificar la interpretación",
        "modificar la interpretacion",
    ]):
        return "control_creativo"

    # -----------------------------------------------------
    # PRIORIDAD 7: SEGUROS
    # -----------------------------------------------------
    if any(k in texto for k in [
        "seguro",
        "cobertura",
        "coberturas",
        "rodaje",
    ]):
        return "seguros"

    # -----------------------------------------------------
    # PRIORIDAD 8: CONFIDENCIALIDAD
    # -----------------------------------------------------
    if any(k in texto for k in [
        "confidencialidad",
        "no divulgación",
        "no divulgacion",
        "reserva",
    ]):
        return "confidencialidad"

    # -----------------------------------------------------
    # PRIORIDAD 9: JURISDICCIÓN / CONFLICTOS
    # -----------------------------------------------------
    if any(k in texto for k in [
        "jurisdicción",
        "jurisdiccion",
        "tribunales",
        "arbitraje",
        "mediación",
        "mediacion",
    ]):
        return "jurisdiccion_conflictos"

    # -----------------------------------------------------
    # PRIORIDAD 10: DISTRIBUCIÓN / LICENCIA
    # -----------------------------------------------------
    if any(k in texto for k in [
        "distribución",
        "distribucion",
        "licencia",
        "plataformas",
        "territorios",
    ]):
        return "distribucion"

    # -----------------------------------------------------
    # PRIORIDAD 11: DISPONIBILIDAD ARTISTA
    # -----------------------------------------------------
    if any(k in texto for k in [
        "disponibilidad",
        "inasistencia",
        "asistencia",
        "presentarse",
    ]):
        return "disponibilidad_artista"

    # -----------------------------------------------------
    # PRIORIDAD 12: OBLIGACIONES OPERATIVAS
    # -----------------------------------------------------
    if any(k in texto for k in [
        "cronograma",
        "jornadas",
        "ensayos",
        "desplazamientos",
        "promoción",
        "promocion",
        "horarios",
    ]):
        return "obligaciones_operativas"

    if impacto == "reputacional":
        return "imagen_promocion"

    return "obligaciones_operativas"


def _normalizar_afecta_principalmente_a(valor: str, descripcion: str = "", tipo_riesgo: str = "") -> str:
    """
    Normaliza `afecta_principalmente_a`.

    Si el valor falta o es ambiguo, aplica un fallback conservador.
    """
    v = str(valor or "").strip().lower()

    if v in {"artista", "productora", "ambas"}:
        return v

    tipo = str(tipo_riesgo or "").strip().lower()
    texto = str(descripcion or "").lower()

    if tipo in {
        "cesion_derechos",
        "exclusividad",
        "pago",
        "control_creativo",
        "imagen_promocion",
        "disponibilidad_artista",
        "seguros",
        "confidencialidad",
        "terminacion",
    }:
        return "artista"

    if tipo in {"jurisdiccion_conflictos", "obligaciones_operativas", "plazo", "distribucion"}:
        return "ambas"

    if any(k in texto for k in [
        "cesión",
        "cesion",
        "derechos",
        "regalías",
        "regalias",
        "exclusividad",
        "sin detalle de coberturas",
        "rescisión",
        "rescision",
    ]):
        return "artista"

    return "ambas"


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
            recomendacion = riesgo.get("recomendacion", "")
            impacto = riesgo.get("impacto", "")

            # Severidad determinística por texto
            analisis = analizar_severidad_detallada(descripcion)

            riesgo["severidad"] = analisis["severidad_final"]
            riesgo["severidad_base"] = analisis["severidad_base"]
            riesgo["familias_relevantes_detectadas"] = analisis["familias_detectadas"]
            riesgo["detalle_reglas_relevantes"] = analisis["detalle_reglas"]
            riesgo["severidad_minima_sugerida"] = analisis["severidad_minima_sugerida"]
            riesgo["puntaje_agravante_relevante"] = analisis["puntaje_agravante_total"]

            # Completar tipo_riesgo si falta
            tipo_riesgo = riesgo.get("tipo_riesgo", "")
            if not str(tipo_riesgo).strip():
                tipo_riesgo = _inferir_tipo_riesgo_desde_texto(
                    descripcion=descripcion,
                    recomendacion=recomendacion,
                    impacto=impacto,
                )
            riesgo["tipo_riesgo"] = tipo_riesgo

            # Normalizar dirección
            riesgo["afecta_principalmente_a"] = _normalizar_afecta_principalmente_a(
                valor=riesgo.get("afecta_principalmente_a", ""),
                descripcion=descripcion,
                tipo_riesgo=tipo_riesgo,
            )

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
        "version_servicio": "4.7_audiovisual_terminacion_y_severidad_mejorada"
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