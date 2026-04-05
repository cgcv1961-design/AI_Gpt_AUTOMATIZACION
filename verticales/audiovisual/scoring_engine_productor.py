"""
verticales/audiovisual/scoring_engine_productor.py
--------------------------------------------------

Motor de scoring para la vertical AUDIOVISUAL.

OBJETIVO DE ESTA VERSIÓN
------------------------
Alinear la vertical audiovisual con la nueva arquitectura general del sistema:

1. Severidad del contrato
2. Riesgo para la parte analizada
3. Riesgo para la contraparte

IMPORTANTE
----------
Este módulo ya no debe quedarse como un scoring aislado o paralelo.
Ahora actúa como adaptador audiovisual del motor dual.

ENTRADA ESPERADA
----------------
resultado : dict
    JSON ya normalizado del análisis audiovisual.
rol_analizado : str
    Rol contractual detectado para la parte analizada
    (por ejemplo: "Artista", "Productora", "Productor").

SALIDA
------
resultado : dict
    El mismo JSON, con el bloque `scoring` enriquecido.

PRINCIPIO
---------
- Primero se calcula una severidad contractual audiovisual coherente.
- Luego se usa el motor dual común del sistema para construir la salida final.
"""

from __future__ import annotations

from typing import Dict, List, Any

from core.scoring_engine import enriquecer_scoring_dual


# =========================================================
# CONFIGURACIÓN
# =========================================================

ALGORITMO_SCORING_VERSION = "4.0_aud_dual_alineado"

# Pesos por severidad para la vertical audiovisual.
# Mantienen la lógica más expresiva del sector audiovisual,
# pero ya compatibles con la escala ampliada.
PESOS_SEVERIDAD_AUD = {
    "baja": 1.0,
    "media": 3.0,
    "media-alta": 5.0,
    "alta": 7.0,
    "critica": 10.0,
}


# =========================================================
# HELPERS
# =========================================================

def _texto(valor: Any) -> str:
    if valor in (None, "", [], {}):
        return ""
    return str(valor).strip()


def _normalizar_severidad(severidad: str) -> str:
    valor = _texto(severidad).lower()

    equivalencias = {
        "baja": "baja",
        "media": "media",
        "media-alta": "media-alta",
        "media_alta": "media-alta",
        "alta": "alta",
        "critica": "critica",
        "crítica": "critica",
    }

    return equivalencias.get(valor, "media")


def _determinar_nivel_audiovisual(score: float) -> str:
    """
    Determinación cualitativa de severidad contractual audiovisual.

    Mantiene una calibración sectorial simple:
    - score bajo: contrato relativamente contenido
    - score medio: contrato con exigencias relevantes
    - score alto: contrato duro / agresivo
    - score crítico: contrato especialmente severo
    """
    if score < 15:
        return "bajo"
    elif score < 35:
        return "medio"
    elif score < 60:
        return "alto"
    else:
        return "critico"


def _extraer_riesgos_audiovisuales(resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
    riesgos = (
        resultado.get("analisis_sectorial", {})
                .get("riesgos_sectoriales", [])
    )

    if not isinstance(riesgos, list):
        return []

    salida = []
    for riesgo in riesgos:
        if isinstance(riesgo, dict):
            salida.append(riesgo)

    return salida


def _contar_metricas(riesgos: List[Dict[str, Any]]) -> Dict[str, int]:
    severidades = [_normalizar_severidad(r.get("severidad", "media")) for r in riesgos]

    return {
        "cantidad_riesgos": len(riesgos),
        "riesgos_criticos": severidades.count("critica"),
        "riesgos_altos": severidades.count("alta"),
        "riesgos_media_altos": severidades.count("media-alta"),
        "riesgos_medios": severidades.count("media"),
        "riesgos_bajos": severidades.count("baja"),
    }


def _calcular_score_base_audiovisual(riesgos: List[Dict[str, Any]]) -> float:
    """
    Score base audiovisual.

    Regla:
    - usa la severidad ya recalculada por el clasificador determinista
    - suma el puntaje agravante relevante cuando existe
    """
    score = 0.0

    for riesgo in riesgos:
        severidad = _normalizar_severidad(riesgo.get("severidad", "media"))
        peso = PESOS_SEVERIDAD_AUD.get(severidad, 3.0)
        agravante = float(riesgo.get("puntaje_agravante_relevante", 0.0) or 0.0)

        score += peso + agravante

    return round(score, 2)


def _obtener_resumen_equilibrio(resultado: Dict[str, Any]) -> str:
    return _texto(
        resultado.get("analisis_profesional", {}).get("evaluacion_equilibrio_contractual")
        or resultado.get("analisis_sectorial", {}).get("evaluacion_equilibrio_contractual")
        or resultado.get("informe_cliente", {}).get("resumen_ejecutivo", {}).get("nivel_riesgo_global")
    )


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def calcular_scoring_productor(resultado: Dict[str, Any], rol_analizado: str = "Artista") -> Dict[str, Any]:
    """
    Aplica scoring audiovisual alineado con el motor dual.

    Paso 1:
        calcula la severidad del contrato en clave audiovisual

    Paso 2:
        deja ese resultado en `resultado["scoring"]`

    Paso 3:
        delega en `enriquecer_scoring_dual(...)` para completar:
        - riesgo para la parte analizada
        - riesgo para la contraparte

    Parámetros
    ----------
    resultado : dict
        JSON audiovisual normalizado.
    rol_analizado : str
        Rol contractual detectado para la parte analizada.

    Retorna
    -------
    dict
        JSON con scoring enriquecido.
    """
    if not isinstance(resultado, dict):
        return resultado

    riesgos = _extraer_riesgos_audiovisuales(resultado)

    score_total = _calcular_score_base_audiovisual(riesgos)
    nivel = _determinar_nivel_audiovisual(score_total)
    metricas = _contar_metricas(riesgos)

    resumen_equilibrio = _obtener_resumen_equilibrio(resultado)

    # -----------------------------------------------------
    # 1) BLOQUE BASE DE SEVERIDAD CONTRACTUAL
    # -----------------------------------------------------
    resultado["scoring"] = {
        "severidad_contrato": {
            "score": score_total,
            "nivel": nivel,
            "fundamento": (
                "Mide la intensidad jurídica, económica y operativa del contrato audiovisual en sí mismo."
            )
        },

        # aliases legacy
        "score_total": score_total,
        "nivel_riesgo": nivel,

        "metricas": metricas,
        "version_scoring": ALGORITMO_SCORING_VERSION,
    }

    # -----------------------------------------------------
    # 2) APOYO DE CONTEXTO PARA EL MOTOR DUAL
    # -----------------------------------------------------
    # Si todavía no existe metadata_sistema, la creamos.
    resultado.setdefault("metadata_sistema", {})
    resultado["metadata_sistema"].setdefault("metadata_presentacion", {})

    # Forzamos el rol detectado para ayudar a enriquecer la salida dual,
    # especialmente antes de que main.py complete metadata más rica.
    if rol_analizado:
        resultado["metadata_sistema"]["metadata_presentacion"]["rol_contractual_detectado"] = rol_analizado

    # Si hay resumen de equilibrio contractual, es útil conservarlo
    # porque puede reforzar la lectura direccional en capas posteriores.
    if resumen_equilibrio:
        resultado["metadata_sistema"]["resumen_equilibrio_contractual"] = resumen_equilibrio

    # -----------------------------------------------------
    # 3) ENRIQUECIMIENTO DUAL
    # -----------------------------------------------------
    resultado = enriquecer_scoring_dual(resultado)

    return resultado