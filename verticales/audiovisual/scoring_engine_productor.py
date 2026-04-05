"""
verticales/audiovisual/scoring_engine_productor.py
--------------------------------------------------

Motor de scoring para la vertical AUDIOVISUAL.

VERSIÓN
-------
5.3_aud_direccional_fuerte

OBJETIVO DE ESTA VERSIÓN
------------------------
Corregir el problema detectado en pruebas reales:

1. La severidad contractual audiovisual era razonable.
2. Pero el reparto del riesgo entre Artista y Productora seguía
   quedando demasiado simétrico.
3. Eso contradecía el propio contenido narrativo del JSON, que
   claramente muestra que la mayor carga suele recaer sobre el Artista.

CAMBIO CONCEPTUAL CLAVE
-----------------------
Se elimina la dependencia principal del "corrector final por resumen"
y se pasa a una direccionalidad fuerte por cláusula.

PRINCIPIO DE DISEÑO
-------------------
En audiovisual:
- el contrato puede ser severo en sí mismo,
- pero eso NO implica que ambas partes queden igual de expuestas.

Ejemplos típicos de riesgo para el Artista:
- cesión amplia de derechos
- falta de regalías
- exclusividad
- rescisión unilateral por la productora
- seguro limitado
- confidencialidad extensa

Estos riesgos NO deben repartirse simétricamente.

ENTRADA ESPERADA
----------------
resultado : dict
    JSON audiovisual ya normalizado.
rol_analizado : str
    Rol detectado para la parte analizada.
    Ejemplos:
    - "Artista"
    - "Productora"
    - "Productor"

SALIDA
------
resultado : dict
    El mismo JSON con:
    resultado["scoring"] enriquecido.

COMPATIBILIDAD
--------------
Mantiene:
- score_total
- nivel_riesgo
- metricas
- version_scoring
"""

from __future__ import annotations

from typing import Dict, List, Any


# =========================================================
# CONFIGURACIÓN
# =========================================================

ALGORITMO_SCORING_VERSION = "5.3_aud_direccional_fuerte"

PESOS_SEVERIDAD_AUD = {
    "baja": 1.0,
    "media": 3.0,
    "media-alta": 5.0,
    "alta": 7.0,
    "critica": 10.0,
}


# =========================================================
# HELPERS GENERALES
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


def _normalizar_rol(rol: str) -> str:
    valor = _texto(rol).lower()

    if "artista" in valor or "intérprete" in valor or "interprete" in valor:
        return "artista"

    if "productora" in valor:
        return "productora"

    if "productor" in valor:
        return "productor"

    return valor or "artista"


def _rol_contraparte(rol_analizado: str) -> str:
    rol = _normalizar_rol(rol_analizado)

    if rol == "artista":
        return "productora"
    if rol in ("productora", "productor"):
        return "artista"

    return "contraparte"


def _etiqueta_rol(rol: str) -> str:
    rol_norm = _normalizar_rol(rol)

    if rol_norm == "artista":
        return "Artista"
    if rol_norm == "productora":
        return "Productora"
    if rol_norm == "productor":
        return "Productor"

    return _texto(rol) if _texto(rol) else "Contraparte"


def _determinar_nivel_audiovisual(score: float) -> str:
    """
    Escala cualitativa audiovisual.
    """
    if score < 10:
        return "bajo"
    elif score < 20:
        return "medio"
    elif score < 35:
        return "medio-alto"
    elif score < 55:
        return "alto"
    else:
        return "critico"


# =========================================================
# EXTRACCIÓN DE RIESGOS
# =========================================================

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


# =========================================================
# SCORE BASE DEL CONTRATO
# =========================================================

def _peso_base_riesgo(riesgo: Dict[str, Any]) -> float:
    severidad = _normalizar_severidad(riesgo.get("severidad", "media"))
    peso = PESOS_SEVERIDAD_AUD.get(severidad, 3.0)
    agravante = float(riesgo.get("puntaje_agravante_relevante", 0.0) or 0.0)
    return peso + agravante


def _calcular_score_base_audiovisual(riesgos: List[Dict[str, Any]]) -> float:
    score = 0.0

    for riesgo in riesgos:
        score += _peso_base_riesgo(riesgo)

    return round(score, 2)


# =========================================================
# DIRECCIONALIDAD DEL RIESGO
# =========================================================

def _direccion_desde_prompt(riesgo: Dict[str, Any]) -> str:
    """
    Usa el campo opcional:
    - artista
    - productora
    - ambas

    Si no existe, devuelve string vacío.
    """
    direccion = _texto(riesgo.get("afecta_principalmente_a")).lower()

    if direccion in ("artista", "productora", "ambas"):
        return direccion

    return ""


def _inferir_direccion_heuristica(riesgo: Dict[str, Any]) -> str:
    """
    Heurística sectorial audiovisual FUERTE.

    Devuelve:
    - artista
    - productora
    - ambas

    Regla dominante:
    si la cláusula afecta derechos, ingresos, libertad profesional,
    estabilidad o protección del intérprete, se asigna a ARTISTA.
    """
    descripcion = _texto(riesgo.get("descripcion")).lower()
    recomendacion = _texto(riesgo.get("recomendacion")).lower()
    texto = f"{descripcion} {recomendacion}".strip()

    # -----------------------------------------------------
    # RIESGOS PRINCIPALMENTE DEL ARTISTA
    # -----------------------------------------------------
    patrones_artista = [
        "cesión",
        "cesion",
        "derechos",
        "irrevocable",
        "máximo plazo legal",
        "maximo plazo legal",
        "todos los medios",
        "todos los territorios",
        "regalías",
        "regalias",
        "sin regalías",
        "sin regalias",
        "remuneración fija",
        "remuneracion fija",
        "explotaciones secundarias",
        "compensación adicional",
        "compensacion adicional",
        "exclusividad",
        "producciones competitivas",
        "rescisión unilateral",
        "rescision unilateral",
        "rescisión anticipada",
        "rescision anticipada",
        "pago solo de lo devengado",
        "seguro contratado por la productora",
        "sin detalle de coberturas",
        "cobertura adecuada",
        "confidencialidad",
        "vigencia posterior",
        "sin plazo definido",
        "posterior al contrato",
        "limita la participación del artista",
        "oportunidades laborales",
        "ingresos futuros",
        "control sobre la obra",
        "control sobre la interpretación",
        "estabilidad laboral del artista",
    ]

    # -----------------------------------------------------
    # RIESGOS PRINCIPALMENTE DE LA PRODUCTORA
    # -----------------------------------------------------
    patrones_productora = [
        "incumplimiento grave del artista",
        "inasistencia del artista",
        "disponibilidad del artista",
        "costos adicionales de producción",
        "costos adicionales de produccion",
        "obligación de pago de la productora",
        "obligacion de pago de la productora",
        "responsabilidad de la productora por daños",
        "demoras imputables a la productora",
        "penalidades a la productora",
        "multa a la productora",
        "riesgo reputacional de la productora",
    ]

    # -----------------------------------------------------
    # RIESGOS COMPARTIDOS / ESTRUCTURALES
    # -----------------------------------------------------
    patrones_ambas = [
        "cronograma",
        "jornadas adicionales",
        "condiciones de trabajo",
        "obligaciones operativas específicas",
        "obligaciones operativas especificas",
        "resolución de disputas",
        "resolucion de disputas",
        "jurisdicción exclusiva",
        "jurisdiccion exclusiva",
        "tribunales de montevideo",
        "mediación",
        "mediacion",
        "ambas partes",
    ]

    if any(p in texto for p in patrones_artista):
        return "artista"

    if any(p in texto for p in patrones_productora):
        return "productora"

    if any(p in texto for p in patrones_ambas):
        return "ambas"

    # fallback fuerte audiovisual:
    # si no está claro y la cláusula toca el núcleo típico de asimetría,
    # la cargamos al ARTISTA.
    impacto = _texto(riesgo.get("impacto")).lower()

    if impacto in ("legal", "financiero", "operativo") and any(
        k in texto for k in [
            "cesión", "cesion", "derechos", "regalías", "regalias",
            "exclusividad", "seguro", "rescisión", "rescision",
            "confidencialidad", "compensación", "compensacion"
        ]
    ):
        return "artista"

    return "ambas"


def _obtener_direccion_riesgo(riesgo: Dict[str, Any]) -> str:
    direccion = _direccion_desde_prompt(riesgo)
    if direccion:
        return direccion

    return _inferir_direccion_heuristica(riesgo)


# =========================================================
# REPARTO DEL SCORE POR ROL
# =========================================================

def _repartir_score_por_rol(
    riesgos: List[Dict[str, Any]],
    rol_analizado: str
) -> tuple[float, float]:
    """
    Reparte el score entre:
    - parte analizada
    - contraparte

    REGLA NUEVA 5.3
    --------------
    Mucho menos simétrica.

    Si el riesgo afecta a una parte:
    - esa parte recibe 100%
    - la otra solo 10%

    Si afecta a ambas:
    - 60% / 60%
    """
    rol = _normalizar_rol(rol_analizado)
    contraparte = _rol_contraparte(rol)

    score_parte = 0.0
    score_contraparte = 0.0

    for riesgo in riesgos:
        base = _peso_base_riesgo(riesgo)
        direccion = _obtener_direccion_riesgo(riesgo)

        if direccion == "ambas":
            score_parte += base * 0.60
            score_contraparte += base * 0.60
            continue

        if direccion == rol:
            score_parte += base * 1.00
            score_contraparte += base * 0.10
            continue

        if direccion == contraparte:
            score_parte += base * 0.10
            score_contraparte += base * 1.00
            continue

        # fallback ultra conservador, casi nunca debería ocurrir
        score_parte += base * 0.50
        score_contraparte += base * 0.50

    return round(score_parte, 2), round(score_contraparte, 2)


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def calcular_scoring_productor(resultado: Dict[str, Any], rol_analizado: str = "Artista") -> Dict[str, Any]:
    """
    Aplica scoring audiovisual con direccionalidad fuerte por rol.

    Paso 1:
        calcula la severidad del contrato

    Paso 2:
        reparte el riesgo entre parte analizada y contraparte
        según la orientación sectorial de cada cláusula

    Paso 3:
        construye el bloque scoring final
    """
    if not isinstance(resultado, dict):
        return resultado

    riesgos = _extraer_riesgos_audiovisuales(resultado)
    rol_norm = _normalizar_rol(rol_analizado)
    rol_contraparte = _rol_contraparte(rol_norm)

    severidad_score = _calcular_score_base_audiovisual(riesgos)
    severidad_nivel = _determinar_nivel_audiovisual(severidad_score)

    score_parte, score_contraparte = _repartir_score_por_rol(
        riesgos=riesgos,
        rol_analizado=rol_norm
    )

    nivel_parte = _determinar_nivel_audiovisual(score_parte)
    nivel_contraparte = _determinar_nivel_audiovisual(score_contraparte)

    metricas = _contar_metricas(riesgos)

    resultado["scoring"] = {
        "severidad_contrato": {
            "score": round(severidad_score, 2),
            "nivel": severidad_nivel,
            "fundamento": "Mide qué tan exigente, severo o litigioso es el contrato audiovisual en sí mismo."
        },
        "riesgo_parte_analizada": {
            "score": round(score_parte, 2),
            "nivel": nivel_parte,
            "rol": _etiqueta_rol(rol_norm),
            "fundamento": "Mide qué tan expuesta queda la parte analizada según las cláusulas audiovisuales del contrato."
        },
        "riesgo_contraparte": {
            "score": round(score_contraparte, 2),
            "nivel": nivel_contraparte,
            "rol": _etiqueta_rol(rol_contraparte),
            "fundamento": "Mide qué tan expuesta queda la contraparte según esas mismas cláusulas."
        },

        # aliases legacy
        "score_total": round(severidad_score, 2),
        "nivel_riesgo": severidad_nivel,

        # métricas restauradas para Word y UI
        "metricas": metricas,

        "version_scoring": ALGORITMO_SCORING_VERSION,
    }

    resultado.setdefault("metadata_sistema", {})
    resultado["metadata_sistema"].setdefault("metadata_presentacion", {})
    resultado["metadata_sistema"]["metadata_presentacion"]["rol_contractual_detectado"] = _etiqueta_rol(rol_norm)

    return resultado