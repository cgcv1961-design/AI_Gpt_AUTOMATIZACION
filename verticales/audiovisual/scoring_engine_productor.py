"""
verticales/audiovisual/scoring_engine_productor.py
--------------------------------------------------

Motor de scoring para la vertical AUDIOVISUAL.

OBJETIVO DE ESTA VERSIÓN
------------------------
Resolver el problema principal detectado en las pruebas:

- la severidad contractual audiovisual era razonable
- pero el riesgo para la parte analizada y para la contraparte
  quedaba casi simétrico

Esta versión separa explícitamente:

1. Severidad del contrato
2. Riesgo para la parte analizada
3. Riesgo para la contraparte

PRINCIPIO DE DISEÑO
-------------------
En audiovisual no alcanza una lógica dual genérica.
Hace falta interpretar el sentido del riesgo según el sector.

Ejemplo:
- cesión global de derechos
- falta de regalías
- rescisión unilateral por la productora
- seguro limitado
- exclusividad amplia

Todo eso suele cargar principalmente sobre el ARTISTA,
aunque el contrato en sí pueda ser severo para ambas partes
en términos de litigiosidad o rigidez.

ENTRADA ESPERADA
----------------
resultado : dict
    JSON audiovisual ya normalizado.
rol_analizado : str
    Rol contractual detectado para la parte analizada.
    Ejemplos:
    - "Artista"
    - "Productora"
    - "Productor"

SALIDA
------
resultado : dict
    El mismo JSON con `resultado["scoring"]` enriquecido.

COMPATIBILIDAD
--------------
- Mantiene aliases legacy:
    score_total
    nivel_riesgo
- Mantiene metricas
- Mantiene version_scoring
"""

from __future__ import annotations

from typing import Dict, List, Any, Tuple


# =========================================================
# CONFIGURACIÓN
# =========================================================

ALGORITMO_SCORING_VERSION = "5.0_aud_direccional_por_rol"

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
    Nivel cualitativo audiovisual.

    Ajuste fino:
    - antes el score 31 salía "medio"
    - ahora queremos que contratos con varias cláusulas relevantes
      entren más fácilmente en medio-alto
    """
    if score < 12:
        return "bajo"
    elif score < 24:
        return "medio"
    elif score < 40:
        return "medio-alto"
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


# =========================================================
# SEVERIDAD CONTRACTUAL
# =========================================================

def _calcular_score_base_audiovisual(riesgos: List[Dict[str, Any]]) -> float:
    """
    Score base audiovisual = severidad del contrato.

    Usa:
    - severidad ya recalculada por el clasificador determinista
    - puntaje agravante relevante, cuando exista
    """
    score = 0.0

    for riesgo in riesgos:
        severidad = _normalizar_severidad(riesgo.get("severidad", "media"))
        peso = PESOS_SEVERIDAD_AUD.get(severidad, 3.0)
        agravante = float(riesgo.get("puntaje_agravante_relevante", 0.0) or 0.0)

        score += peso + agravante

    return round(score, 2)


# =========================================================
# DIRECCIONALIDAD AUDIOVISUAL
# =========================================================

def _direccion_desde_prompt(riesgo: Dict[str, Any]) -> str:
    """
    Usa el campo nuevo pedido al prompt:
    - artista
    - productora
    - ambas

    Si no existe, devuelve string vacío y caerá en heurística.
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
    """
    descripcion = _texto(riesgo.get("descripcion")).lower()
    recomendacion = _texto(riesgo.get("recomendacion")).lower()
    texto = f"{descripcion} {recomendacion}".strip()

    # Riesgos típicamente cargados sobre el artista
    patrones_artista = [
        "cesión de derechos",
        "cesion de derechos",
        "exclusiva",
        "irrevocable",
        "máximo plazo legal",
        "maximo plazo legal",
        "futuras posibilidades del artista",
        "sin regalías",
        "sin regalias",
        "explotaciones secundarias",
        "negociación futura",
        "negociacion futura",
        "participar en producciones competitivas",
        "exclusividad impide",
        "rescindir",
        "rescindido unilateralmente",
        "rescisión unilateral",
        "rescision unilateral",
        "sin compensación",
        "sin compensacion",
        "seguro contratado por la productora",
        "no cubre otras actividades",
        "confidencialidad se extiende",
        "restringir la comunicación profesional del artista",
    ]

    # Riesgos típicamente cargados sobre la productora
    patrones_productora = [
        "pago en dos etapas",
        "pago al inicio",
        "pago al finalizar",
        "incumplimiento grave del artista",
        "notificación formal del artista",
        "notificacion formal del artista",
        "riesgo reputacional por conducta del artista",
        "limitaciones de disponibilidad del artista",
    ]

    # Riesgos compartidos / estructurales
    patrones_ambas = [
        "resolución de disputas",
        "resolucion de disputas",
        "jurisdicción ordinaria",
        "jurisdiccion ordinaria",
        "mecanismos de resolución de disputas",
        "mecanismos de resolucion de disputas",
        "vacíos operativos",
        "vacios operativos",
        "cambios en el cronograma",
        "reprogramaciones",
    ]

    if any(p in texto for p in patrones_artista):
        return "artista"

    if any(p in texto for p in patrones_productora):
        return "productora"

    if any(p in texto for p in patrones_ambas):
        return "ambas"

    # Fallback por impacto + redacción
    impacto = _texto(riesgo.get("impacto")).lower()

    if "artista" in texto:
        return "artista"

    if "productora" in texto and "puede" in texto and "rescind" in texto:
        return "artista"

    if impacto in ("legal", "financiero", "operativo") and (
        "cesión" in texto or
        "cesion" in texto or
        "regalías" in texto or
        "regalias" in texto or
        "exclusividad" in texto or
        "seguro" in texto
    ):
        return "artista"

    return "ambas"


def _obtener_direccion_riesgo(riesgo: Dict[str, Any]) -> str:
    """
    Prioridad:
    1. campo explícito del prompt
    2. heurística audiovisual
    """
    direccion = _direccion_desde_prompt(riesgo)
    if direccion:
        return direccion

    return _inferir_direccion_heuristica(riesgo)


def _peso_base_riesgo(riesgo: Dict[str, Any]) -> float:
    severidad = _normalizar_severidad(riesgo.get("severidad", "media"))
    peso = PESOS_SEVERIDAD_AUD.get(severidad, 3.0)
    agravante = float(riesgo.get("puntaje_agravante_relevante", 0.0) or 0.0)
    return peso + agravante


def _repartir_score_por_rol(
    riesgos: List[Dict[str, Any]],
    rol_analizado: str
) -> Tuple[float, float]:
    """
    Reparte el score entre:
    - parte analizada
    - contraparte

    Regla:
    - si el riesgo afecta principalmente a la parte analizada, carga casi completo
    - si afecta a la contraparte, carga poco
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
            score_contraparte += base * 0.20
            continue

        if direccion == contraparte:
            score_parte += base * 0.20
            score_contraparte += base * 1.00
            continue

        # fallback muy conservador
        score_parte += base * 0.60
        score_contraparte += base * 0.60

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
        según orientación audiovisual específica

    Paso 3:
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

    nivel_parte = _determinar_nivel_audiovisual(score_parte)
    nivel_contraparte = _determinar_nivel_audiovisual(score_contraparte)

    metricas = _contar_metricas(riesgos)

    resultado["scoring"] = {
        "severidad_contrato": {
            "score": severidad_score,
            "nivel": severidad_nivel,
            "fundamento": "Mide la intensidad jurídica, económica y operativa del contrato audiovisual en sí mismo."
        },
        "riesgo_parte_analizada": {
            "score": score_parte,
            "nivel": nivel_parte,
            "rol": _etiqueta_rol(rol_norm),
            "fundamento": "Mide qué tan expuesta queda la parte analizada según las cláusulas audiovisuales del contrato."
        },
        "riesgo_contraparte": {
            "score": score_contraparte,
            "nivel": nivel_contraparte,
            "rol": _etiqueta_rol(rol_contraparte),
            "fundamento": "Mide qué tan expuesta queda la contraparte según las mismas cláusulas."
        },

        # aliases legacy
        "score_total": severidad_score,
        "nivel_riesgo": severidad_nivel,

        "metricas": metricas,
        "version_scoring": ALGORITMO_SCORING_VERSION,
    }

    # metadata de apoyo
    resultado.setdefault("metadata_sistema", {})
    resultado["metadata_sistema"].setdefault("metadata_presentacion", {})
    resultado["metadata_sistema"]["metadata_presentacion"]["rol_contractual_detectado"] = _etiqueta_rol(rol_norm)

    return resultado