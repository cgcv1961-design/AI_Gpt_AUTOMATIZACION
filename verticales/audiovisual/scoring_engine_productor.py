"""
verticales/audiovisual/scoring_engine_productor.py
--------------------------------------------------

Motor de scoring para la vertical AUDIOVISUAL.

VERSIÓN
-------
5.2_aud_direccional_simetrico

OBJETIVO DE ESTA VERSIÓN
------------------------
Corregir el problema detectado en pruebas reales:

1. La severidad contractual audiovisual era razonable.
2. El riesgo para el ARTISTA mejoró.
3. Pero el riesgo para la PRODUCTORA seguía quedando demasiado alto
   cuando el propio JSON narrativo indicaba que el mayor riesgo recaía
   sobre el artista.

Esta versión:
- mantiene la severidad del contrato,
- mejora la direccionalidad del riesgo,
- corrige de manera simétrica según el resumen ejecutivo,
- restaura `metricas` para Word y UI.

PRINCIPIO DE DISEÑO
-------------------
La IA interpreta y describe.
La lógica determinística:
- reparte el riesgo,
- valida consistencia,
- corrige asimetrías numéricas no deseadas.

IMPORTANTE
----------
En audiovisual:
- muchas cláusulas son severas en el contrato en sí,
- pero NO afectan igual a ambas partes.

Ejemplo:
- cesión amplia de derechos
- falta de regalías
- rescisión unilateral por la productora
- exclusividad
- seguro limitado

Todo eso suele cargar mucho más sobre el ARTISTA.

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
"""

from __future__ import annotations

from typing import Dict, List, Any, Tuple


# =========================================================
# CONFIGURACIÓN
# =========================================================

ALGORITMO_SCORING_VERSION = "5.2_aud_direccional_simetrico"

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
    Determinación cualitativa del nivel.

    Escala calibrada:
    - bajo
    - medio
    - medio-alto
    - alto
    - crítico
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
    Usa el campo pedido al prompt:
    - artista
    - productora
    - ambas

    Si no existe o viene vacío, devuelve string vacío.
    """
    direccion = _texto(riesgo.get("afecta_principalmente_a")).lower()

    if direccion in ("artista", "productora", "ambas"):
        return direccion

    return ""


def _inferir_direccion_heuristica(riesgo: Dict[str, Any]) -> str:
    """
    Heurística sectorial audiovisual.

    Devuelve:
    - artista
    - productora
    - ambas

    Reglas:
    - por defecto fuerte hacia ARTISTA si la cláusula le restringe ingresos,
      derechos, oportunidades o protección.
    - solo marca PRODUCTORA cuando realmente la expone a ella.
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
        "derechos exclusiva",
        "derechos exclusiva",
        "irrevocable",
        "máximo plazo legal",
        "maximo plazo legal",
        "todos los medios",
        "todos los territorios",
        "regalías",
        "regalias",
        "sin regalías",
        "sin regalias",
        "explotaciones secundarias",
        "remuneración fija",
        "remuneracion fija",
        "exclusividad",
        "producciones competitivas",
        "rescisión unilateral",
        "rescision unilateral",
        "rescindir",
        "pago solo de lo devengado",
        "seguro contratado por la productora",
        "sin detalle de coberturas",
        "confidencialidad",
        "vigencia posterior",
        "indefinida",
        "limita la participación del artista",
        "limitar la agenda y oportunidades del artista",
        "sin ingresos adicionales",
        "interpretación del artista",
        "interpretacion del artista",
    ]

    # -----------------------------------------------------
    # RIESGOS PRINCIPALMENTE DE LA PRODUCTORA
    # -----------------------------------------------------
    patrones_productora = [
        "incumplimiento del artista",
        "inasistencia del artista",
        "incumplimiento grave del artista",
        "disponibilidad del artista",
        "responsabilidad económica de la productora",
        "obligación de pago de la productora",
        "obligacion de pago de la productora",
        "costos adicionales de producción",
        "costos adicionales de produccion",
        "demoras imputables a la productora",
        "penalidades a la productora",
        "multa a la productora",
    ]

    # -----------------------------------------------------
    # RIESGOS COMPARTIDOS / ESTRUCTURALES
    # -----------------------------------------------------
    patrones_ambas = [
        "cronograma",
        "entregables",
        "penalidades por incumplimiento para ambas partes",
        "resolución de disputas",
        "resolucion de disputas",
        "jurisdicción",
        "jurisdiccion",
        "mediación",
        "mediacion",
        "ambas partes",
        "condiciones de trabajo",
        "obligaciones operativas específicas",
        "obligaciones operativas especificas",
    ]

    if any(p in texto for p in patrones_artista):
        return "artista"

    if any(p in texto for p in patrones_productora):
        return "productora"

    if any(p in texto for p in patrones_ambas):
        return "ambas"

    # fallback por impacto
    impacto = _texto(riesgo.get("impacto")).lower()

    if impacto in ("legal", "financiero", "operativo") and any(
        k in texto for k in [
            "cesión", "cesion", "regalías", "regalias",
            "exclusividad", "seguro", "rescisión", "rescision",
            "confidencialidad"
        ]
    ):
        return "artista"

    return "ambas"


def _obtener_direccion_riesgo(riesgo: Dict[str, Any]) -> str:
    """
    Prioridad:
    1. dirección explícita del prompt
    2. heurística audiovisual
    """
    direccion = _direccion_desde_prompt(riesgo)
    if direccion:
        return direccion

    return _inferir_direccion_heuristica(riesgo)


# =========================================================
# REPARTO BASE DEL SCORE
# =========================================================

def _repartir_score_por_rol(
    riesgos: List[Dict[str, Any]],
    rol_analizado: str
) -> Tuple[float, float]:
    """
    Reparte el score entre:
    - parte analizada
    - contraparte

    Reglas:
    - si el riesgo afecta principalmente a la parte analizada,
      carga casi completo sobre ella
    - si afecta a la contraparte,
      carga muy poco sobre la parte analizada
    - si afecta a ambas, se reparte
    """
    rol = _normalizar_rol(rol_analizado)
    contraparte = _rol_contraparte(rol)

    score_parte = 0.0
    score_contraparte = 0.0

    for riesgo in riesgos:
        base = _peso_base_riesgo(riesgo)
        direccion = _obtener_direccion_riesgo(riesgo)

        if direccion == "ambas":
            score_parte += base * 0.65
            score_contraparte += base * 0.65
            continue

        if direccion == rol:
            score_parte += base * 1.00
            score_contraparte += base * 0.15
            continue

        if direccion == contraparte:
            score_parte += base * 0.15
            score_contraparte += base * 1.00
            continue

        # fallback ultra conservador
        score_parte += base * 0.60
        score_contraparte += base * 0.60

    return round(score_parte, 2), round(score_contraparte, 2)


# =========================================================
# CORRECTOR POR RESUMEN EJECUTIVO
# =========================================================

def _texto_resumen(resultado: Dict[str, Any]) -> str:
    return _texto(
        resultado.get("informe_cliente", {})
                .get("resumen_ejecutivo", {})
                .get("nivel_riesgo_global", "")
    ).lower()


def _resumen_indica_artista_mas_expuesto(texto_resumen: str) -> bool:
    pistas = [
        "alto para el artista",
        "medio-alto para el artista",
        "riesgo para el artista",
        "moderado para el artista",
        "bajo para la productora",
    ]
    return any(p in texto_resumen for p in pistas)


def _resumen_indica_productora_mas_expuesta(texto_resumen: str) -> bool:
    pistas = [
        "alto para la productora",
        "medio-alto para la productora",
        "riesgo para la productora",
        "moderado para la productora",
        "bajo para el artista",
    ]
    return any(p in texto_resumen for p in pistas)


def _aplicar_corrector_simetrico(
    resultado: Dict[str, Any],
    score_parte: float,
    score_contraparte: float,
    rol_analizado: str
) -> Tuple[float, float]:
    """
    Corrector final basado en el resumen ejecutivo.

    REGLA CLAVE
    ----------
    Si el resumen ya dice claramente que el riesgo cae sobre una parte,
    el scoring no debe contradecirlo.

    Esto corrige especialmente el caso:
    - vista Productora / proponente
    donde antes quedaba demasiado cerca del Artista.
    """
    texto_resumen = _texto_resumen(resultado)
    rol = _normalizar_rol(rol_analizado)

    artista_mas_expuesto = _resumen_indica_artista_mas_expuesto(texto_resumen)
    productora_mas_expuesta = _resumen_indica_productora_mas_expuesta(texto_resumen)

    # Caso 1: el resumen dice que ARTISTA carga más riesgo
    if artista_mas_expuesto:
        if rol == "artista":
            # la parte analizada es artista -> debe quedar claramente por arriba
            if score_parte <= score_contraparte:
                score_parte *= 1.20
                score_contraparte *= 0.70
            else:
                score_parte *= 1.08
                score_contraparte *= 0.92
        else:
            # la parte analizada es productora -> debe quedar claramente por debajo
            if score_parte >= score_contraparte:
                score_parte *= 0.55
                score_contraparte *= 1.15
            else:
                score_parte *= 0.85
                score_contraparte *= 1.05

    # Caso 2: el resumen dice que PRODUCTORA carga más riesgo
    if productora_mas_expuesta:
        if rol in ("productora", "productor"):
            if score_parte <= score_contraparte:
                score_parte *= 1.20
                score_contraparte *= 0.70
            else:
                score_parte *= 1.08
                score_contraparte *= 0.92
        else:
            if score_parte >= score_contraparte:
                score_parte *= 0.55
                score_contraparte *= 1.15
            else:
                score_parte *= 0.85
                score_contraparte *= 1.05

    return round(score_parte, 2), round(score_contraparte, 2)


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def calcular_scoring_productor(resultado: Dict[str, Any], rol_analizado: str = "Artista") -> Dict[str, Any]:
    """
    Aplica scoring audiovisual con direccionalidad real por rol.

    Paso 1:
        calcula la severidad del contrato

    Paso 2:
        reparte el riesgo entre parte analizada y contraparte

    Paso 3:
        corrige según el resumen ejecutivo, si hace falta

    Paso 4:
        construye el bloque `scoring`
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

    score_parte, score_contraparte = _aplicar_corrector_simetrico(
        resultado=resultado,
        score_parte=score_parte,
        score_contraparte=score_contraparte,
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
            "fundamento": "Mide qué tan expuesta queda la parte analizada según el contenido del contrato y la perspectiva seleccionada."
        },
        "riesgo_contraparte": {
            "score": round(score_contraparte, 2),
            "nivel": nivel_contraparte,
            "rol": _etiqueta_rol(rol_contraparte),
            "fundamento": "Mide qué tan expuesta queda la contraparte en relación con las mismas cláusulas."
        },

        # aliases legacy
        "score_total": round(severidad_score, 2),
        "nivel_riesgo": severidad_nivel,

        # restauradas para Word / UI
        "metricas": metricas,

        "version_scoring": ALGORITMO_SCORING_VERSION,
    }

    resultado.setdefault("metadata_sistema", {})
    resultado["metadata_sistema"].setdefault("metadata_presentacion", {})
    resultado["metadata_sistema"]["metadata_presentacion"]["rol_contractual_detectado"] = _etiqueta_rol(rol_norm)

    return resultado