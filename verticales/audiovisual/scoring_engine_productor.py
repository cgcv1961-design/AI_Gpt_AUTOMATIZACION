"""
verticales/audiovisual/scoring_engine_productor.py
--------------------------------------------------

Motor de Scoring – Vertical Audiovisual – Perfil Productor

Este módulo aplica scoring sectorial especializado
utilizando el núcleo matemático común del sistema.

Arquitectura:
- Capa 1 → Score por riesgos individuales
- Capa 2 → Penalizaciones estructurales sectoriales
- Capa 3 → Detección de riesgo estructural combinado
- Capa 4 → Determinación de nivel (sectorial)

MEJORA DE ESTA VERSIÓN
----------------------
Se alinea el motor audiovisual con la escala ampliada de severidades:
- baja
- media
- media-alta
- alta
- critica

Además:
- se agregan métricas explícitas para riesgos críticos
- se mantiene intacta la lógica sectorial ya validada
- no se altera la arquitectura del bloque `evaluacion_general`
"""

from typing import Dict

from core.scoring_base import sumar_pesos_por_severidad
from core.utils_semanticos import (
    texto_indica_ausencia,
    texto_indica_ambiguedad
)

# =========================================================
# VERSIONADO DEL MOTOR
# =========================================================

ALGORITMO_SCORING_VERSION = "3.3_aud_productor_alineado_reglas_relevantes"

# =========================================================
# PESOS SECTORIALES
# =========================================================
# Alineados con la nueva escala de severidad.
# No se tocan umbrales de nivel cualitativo porque ya fueron
# calibrados sectorialmente en pruebas previas.
# =========================================================

PESOS_SEVERIDAD_AUD = {
    "baja": 1,
    "media": 3,
    "media-alta": 5,
    "alta": 6,
    "critica": 10
}


# =========================================================
# CAPA 2 — Penalizaciones estructurales sectoriales
# =========================================================

def calcular_penalizaciones_estructurales(data: Dict) -> float:
    """
    Aplica penalizaciones adicionales por debilidades estructurales
    específicas del sector audiovisual-productor.
    """

    penalizacion = 0.0

    estructura = data.get("estructura_derechos", {})
    cadena = data.get("cadena_titularidad", {})

    # Ausencia de garantías de autoría
    if texto_indica_ausencia(cadena.get("garantias_autoria", "")):
        penalizacion += 10

    # Ausencia de cláusula de indemnidad
    if texto_indica_ausencia(cadena.get("clausula_indemnidad", "")):
        penalizacion += 12

    # Ambigüedad en duración de derechos
    plazo = estructura.get("plazo_derechos", {})
    if texto_indica_ambiguedad(plazo.get("duracion", "")):
        penalizacion += 8

    # Territorio limitado regional
    territorio = estructura.get("territorio", {})
    texto_territorio = territorio.get("alcance", "").lower()
    if texto_territorio and "america latina" in texto_territorio:
        penalizacion += 4

    return penalizacion


# =========================================================
# CAPA 3 — Riesgo estructural combinado
# =========================================================

def detectar_riesgo_estructural(data: Dict) -> bool:
    """
    Riesgo estructural crítico solo si existen
    múltiples fallas combinadas relevantes.
    """

    estructura = data.get("estructura_derechos", {})
    cadena = data.get("cadena_titularidad", {})

    sin_garantias = texto_indica_ausencia(cadena.get("garantias_autoria", ""))
    sin_indemnidad = texto_indica_ausencia(cadena.get("clausula_indemnidad", ""))

    plazo = estructura.get("plazo_derechos", {})
    plazo_problematico = texto_indica_ambiguedad(plazo.get("duracion", ""))

    condiciones_criticas = sum([
        sin_garantias,
        sin_indemnidad,
        plazo_problematico
    ])

    return condiciones_criticas >= 3


# =========================================================
# CAPA 4 — NIVEL CUALITATIVO AUDIOVISUAL
# =========================================================

def determinar_nivel_audiovisual(score: float) -> str:
    """
    Determinación sectorial de nivel para audiovisual comercial.
    Ajusta los umbrales respecto al nivelador global.

    IMPORTANTE:
    Esta función ya fue calibrada con pruebas previas
    y no debe modificarse sin nueva validación.
    """

    if score < 25:
        return "bajo"
    elif score < 60:
        return "medio"
    elif score < 85:
        return "alto"
    else:
        return "critico"


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def aplicar_scoring_aud_productor(resultado: Dict) -> Dict:
    """
    Aplica scoring completo al resultado estructurado.

    Importante
    ----------
    - Mantiene intacto el bloque original `evaluacion_general`
      ya validado en pruebas.
    - Agrega además un bloque estandarizado `scoring`
      para compatibilidad con reportes, main.py y futuras verticales.
    """

    if not isinstance(resultado, dict):
        return resultado

    riesgos = (
        resultado
            .get("analisis_sectorial", {})
            .get("riesgos_sectoriales", [])
    )

    # -----------------------------------------------------
    # Capa 1 — Score base por severidad
    # -----------------------------------------------------

    score_riesgos = sumar_pesos_por_severidad(
        riesgos,
        PESOS_SEVERIDAD_AUD
    )

    # -----------------------------------------------------
    # Capa 2 — Penalización estructural
    # -----------------------------------------------------

    penalizacion = calcular_penalizaciones_estructurales(resultado)

    score_total = score_riesgos + penalizacion

    # -----------------------------------------------------
    # Capa 3 — Riesgo estructural crítico
    # -----------------------------------------------------

    riesgo_estructural = detectar_riesgo_estructural(resultado)

    if riesgo_estructural:
        score_total += 12

    # -----------------------------------------------------
    # Capa 4 — Nivel cualitativo audiovisual
    # -----------------------------------------------------

    nivel = determinar_nivel_audiovisual(score_total)
    score_total_redondeado = round(score_total, 2)

    # -----------------------------------------------------
    # BLOQUE ORIGINAL VALIDADO
    # -----------------------------------------------------

    if "evaluacion_general" not in resultado:
        resultado["evaluacion_general"] = {}

    resultado["evaluacion_general"]["score_riesgo"] = {
        "nivel": nivel,
        "valor": score_total_redondeado,
        "fundamento": (
            "Cálculo híbrido basado en riesgos individuales, "
            "penalizaciones estructurales y detección combinatoria "
            f"(motor {ALGORITMO_SCORING_VERSION})."
        )
    }

    resultado["evaluacion_general"]["riesgo_estructural_detectado"] = riesgo_estructural
    resultado["evaluacion_general"]["version_scoring"] = ALGORITMO_SCORING_VERSION

    # -----------------------------------------------------
    # BLOQUE ESTÁNDAR DEL SISTEMA
    # -----------------------------------------------------

    severidades = [str(r.get("severidad", "")).lower() for r in riesgos]

    metricas = {
        "cantidad_riesgos": len(riesgos),
        "riesgos_criticos": severidades.count("critica"),
        "riesgos_altos": severidades.count("alta"),
        "riesgos_media_altos": severidades.count("media-alta"),
        "riesgos_medios": severidades.count("media"),
        "riesgos_bajos": severidades.count("baja")
    }

    resultado["scoring"] = {
        "score_total": score_total_redondeado,
        "nivel_riesgo": nivel,
        "metricas": metricas,
        "version_scoring": ALGORITMO_SCORING_VERSION
    }

    return resultado