"""
verticales/audiovisual/scoring_engine_productor.py
--------------------------------------------------

Motor determinista de scoring para la vertical AUDIOVISUAL.

OBJETIVO
--------
Unificar la filosofía del proyecto también en audiovisual:

    contrato -> LLM -> motor determinista -> resultado

PRINCIPIO
---------
- La LLM describe cláusulas y riesgos sectoriales en JSON.
- Python recalcula la severidad contractual y la dirección del riesgo.
- El resultado final NO queda librado a una frase del resumen ejecutivo.

DIFERENCIA CON VERSIONES ANTERIORES
-----------------------------------
Esta versión deja de depender del resumen narrativo para repartir el riesgo.
La dirección se determina por cláusula usando:

1. `afecta_principalmente_a` si vino bien desde la LLM
2. una heurística determinista sectorial si ese campo falta o es ambiguo

NOVEDAD DE ESTA VERSIÓN
-----------------------
También incorpora `tipo_riesgo` como insumo real del scoring.
Esto permite que el motor "entienda" mejor la industria audiovisual.

SALIDA
------
Construye en `resultado["scoring"]`:
- severidad_contrato
- riesgo_parte_analizada
- riesgo_contraparte
- score_total / nivel_riesgo (aliases legacy)
- metricas

COMPATIBILIDAD
--------------
- Mantiene la estructura usada por Word y Render.
- Mantiene aliases legacy para no romper la UI existente.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


# =========================================================
# CONFIGURACIÓN
# =========================================================

ALGORITMO_SCORING_VERSION = "6.0_aud_determinista_por_clausula_y_tipo"

PESOS_SEVERIDAD_AUD = {
    "baja": 1.0,
    "media": 3.0,
    "media-alta": 5.0,
    "alta": 7.0,
    "critica": 10.0,
}

# Reglas reales de la industria audiovisual:
# estas ponderaciones no reemplazan la severidad;
# la complementan con lógica sectorial.
PESOS_TIPO_RIESGO = {
    "cesion_derechos": 4.0,
    "exclusividad": 3.0,
    "penalidad": 4.0,
    "plazo": 1.5,
    "pago": 2.5,
    "control_creativo": 3.0,
    "distribucion": 2.5,
    "obligaciones_operativas": 1.5,
    "confidencialidad": 1.5,
    "seguros": 2.0,
    "terminacion": 3.5,
    "jurisdiccion_conflictos": 1.5,
    "imagen_promocion": 2.5,
    "disponibilidad_artista": 2.0,
}

TIPOS_RIESGO_VALIDOS = set(PESOS_TIPO_RIESGO.keys())

# Lista explícita y documentada de reglas reales de industria.
# Esto sirve también como referencia de negocio para seguir calibrando.
REGLAS_REALES_INDUSTRIA = {
    "cesion_derechos": {
        "descripcion": "Cesión total o amplia de derechos, imagen, interpretación o explotación audiovisual.",
        "frases_clave": [
            "cesión",
            "cesion",
            "derechos",
            "todos los medios",
            "todos los territorios",
            "máximo plazo legal",
            "irrevocable",
            "perpetua",
            "global",
        ],
    },
    "exclusividad": {
        "descripcion": "Restricción a trabajar con terceros o en producciones competitivas.",
        "frases_clave": [
            "exclusividad",
            "producciones competitivas",
            "no podrá prestar servicios",
            "no podrá participar",
        ],
    },
    "penalidad": {
        "descripcion": "Multas, cláusulas penales o consecuencias económicas desproporcionadas.",
        "frases_clave": [
            "penalidad",
            "cláusula penal",
            "clausula penal",
            "multa",
            "daños y perjuicios",
        ],
    },
    "pago": {
        "descripcion": "Forma de pago, pago fijo, ausencia de regalías, compensaciones diferidas.",
        "frases_clave": [
            "remuneración fija",
            "remuneracion fija",
            "regalías",
            "regalias",
            "compensación",
            "compensacion",
            "pago",
            "precio",
        ],
    },
    "control_creativo": {
        "descripcion": "Control de interpretación, edición, aprobación o uso creativo concentrado en una parte.",
        "frases_clave": [
            "control creativo",
            "aprobación artística",
            "aprobacion artistica",
            "modificar la interpretación",
            "editar",
            "cortar",
            "adaptar",
        ],
    },
    "seguros": {
        "descripcion": "Coberturas limitadas, ambiguas o insuficientes para rodaje y actividades conexas.",
        "frases_clave": [
            "seguro",
            "coberturas",
            "jornadas de rodaje",
            "sin detalle de coberturas",
        ],
    },
    "terminacion": {
        "descripcion": "Rescisión, terminación o facultad unilateral de resolver el contrato.",
        "frases_clave": [
            "rescisión",
            "rescision",
            "terminación",
            "terminacion",
            "resolver el contrato",
            "rescindir",
        ],
    },
    "confidencialidad": {
        "descripcion": "Obligaciones de reserva, no divulgación o duración excesiva del deber de confidencialidad.",
        "frases_clave": [
            "confidencialidad",
            "no divulgación",
            "no divulgacion",
            "sin plazo definido",
        ],
    },
    "distribucion": {
        "descripcion": "Licencias, plataformas, territorios o modalidades de explotación.",
        "frases_clave": [
            "distribución",
            "distribucion",
            "plataformas",
            "licencia",
            "territorios",
            "ventanas de explotación",
            "ventanas de explotacion",
        ],
    },
    "obligaciones_operativas": {
        "descripcion": "Disponibilidad, cronograma, jornadas, ensayos, desplazamientos o tareas accesorias.",
        "frases_clave": [
            "cronograma",
            "jornadas",
            "horarios",
            "ensayos",
            "desplazamientos",
            "promoción",
            "promocion",
        ],
    },
    "jurisdiccion_conflictos": {
        "descripcion": "Jurisdicción, arbitraje, mediación o resolución de controversias.",
        "frases_clave": [
            "jurisdicción",
            "jurisdiccion",
            "arbitraje",
            "mediación",
            "mediacion",
            "tribunales",
        ],
    },
    "imagen_promocion": {
        "descripcion": "Uso promocional de imagen, nombre, voz o material derivado.",
        "frases_clave": [
            "imagen",
            "nombre",
            "voz",
            "promoción",
            "promocion",
            "material promocional",
        ],
    },
    "disponibilidad_artista": {
        "descripcion": "Disponibilidad rígida, reprogramaciones abiertas o exigencias de presencia.",
        "frases_clave": [
            "disponibilidad",
            "reprogramaciones",
            "presentarse",
            "asistencia",
            "inasistencia",
        ],
    },
}


# =========================================================
# HELPERS BÁSICOS
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


def _etiqueta_rol(rol: str) -> str:
    rol_norm = _normalizar_rol(rol)
    if rol_norm == "artista":
        return "Artista"
    if rol_norm == "productora":
        return "Productora"
    if rol_norm == "productor":
        return "Productor"
    return _texto(rol) if _texto(rol) else "Contraparte"


def _rol_contraparte(rol_analizado: str) -> str:
    rol = _normalizar_rol(rol_analizado)
    if rol == "artista":
        return "productora"
    if rol in ("productora", "productor"):
        return "artista"
    return "contraparte"


def _determinar_nivel_audiovisual(score: float) -> str:
    """
    Escala cualitativa audiovisual.

    Se mantiene la calibración que ya venía funcionando razonablemente
    en pruebas reales, pero asociada ahora a un reparto determinista
    por cláusula y también por tipo de riesgo.
    """
    if score < 10:
        return "bajo"
    if score < 20:
        return "medio"
    if score < 35:
        return "medio-alto"
    if score < 55:
        return "alto"
    return "critico"


# =========================================================
# TIPIFICACIÓN DE RIESGOS
# =========================================================

def _normalizar_tipo_riesgo(tipo: str) -> str:
    valor = _texto(tipo).lower().strip()
    equivalencias = {
        "cesion": "cesion_derechos",
        "cesión": "cesion_derechos",
        "cesion_derechos": "cesion_derechos",
        "exclusividad": "exclusividad",
        "penalidad": "penalidad",
        "plazo": "plazo",
        "pago": "pago",
        "control_creativo": "control_creativo",
        "distribucion": "distribucion",
        "distribución": "distribucion",
        "obligaciones_operativas": "obligaciones_operativas",
        "confidencialidad": "confidencialidad",
        "seguros": "seguros",
        "terminacion": "terminacion",
        "terminación": "terminacion",
        "jurisdiccion_conflictos": "jurisdiccion_conflictos",
        "jurisdicción_conflictos": "jurisdiccion_conflictos",
        "imagen_promocion": "imagen_promocion",
        "imagen_promoción": "imagen_promocion",
        "disponibilidad_artista": "disponibilidad_artista",
    }
    return equivalencias.get(valor, "")


def _inferir_tipo_riesgo_heuristico(riesgo: Dict[str, Any]) -> str:
    """
    Fallback determinista si el LLM no devolvió `tipo_riesgo`
    o lo devolvió ambiguo.

    Usa descripción + recomendación para tipificar con lógica
    del dominio audiovisual.
    """
    descripcion = _texto(riesgo.get("descripcion")).lower()
    recomendacion = _texto(riesgo.get("recomendacion")).lower()
    impacto = _texto(riesgo.get("impacto")).lower()
    texto = f"{descripcion} {recomendacion}".strip()

    for tipo_riesgo, config in REGLAS_REALES_INDUSTRIA.items():
        frases = config.get("frases_clave", [])
        if any(frase in texto for frase in frases):
            return tipo_riesgo

    # fallback muy conservador
    if impacto == "financiero":
        return "pago"
    if impacto == "legal":
        return "cesion_derechos"
    if impacto == "operativo":
        return "obligaciones_operativas"
    if impacto == "reputacional":
        return "imagen_promocion"

    return "obligaciones_operativas"


def _obtener_tipo_riesgo(riesgo: Dict[str, Any]) -> str:
    tipo_llm = _normalizar_tipo_riesgo(riesgo.get("tipo_riesgo", ""))
    if tipo_llm in TIPOS_RIESGO_VALIDOS:
        return tipo_llm
    return _inferir_tipo_riesgo_heuristico(riesgo)


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

    return [r for r in riesgos if isinstance(r, dict)]


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
# SCORE BASE CONTRACTUAL
# =========================================================

def _peso_base_riesgo(riesgo: Dict[str, Any]) -> float:
    """
    Peso contractual base por cláusula.

    Combina:
    - severidad recalculada determinísticamente
    - tipo_riesgo audiovisual
    - puntaje agravante relevante (si existe)

    Esto mejora mucho el dominio audiovisual sin romper la escala
    actual que ya te venía funcionando razonablemente.
    """
    severidad = _normalizar_severidad(riesgo.get("severidad", "media"))
    tipo_riesgo = _obtener_tipo_riesgo(riesgo)

    peso_severidad = PESOS_SEVERIDAD_AUD.get(severidad, 3.0)
    peso_tipo = PESOS_TIPO_RIESGO.get(tipo_riesgo, 1.5)
    agravante = float(riesgo.get("puntaje_agravante_relevante", 0.0) or 0.0)

    return peso_severidad + peso_tipo + agravante


def _calcular_score_base_audiovisual(riesgos: List[Dict[str, Any]]) -> float:
    score = 0.0
    for riesgo in riesgos:
        score += _peso_base_riesgo(riesgo)
    return round(score, 2)


# =========================================================
# DIRECCIONALIDAD DETERMINISTA
# =========================================================

def _direccion_desde_prompt(riesgo: Dict[str, Any]) -> str:
    """
    Usa el campo `afecta_principalmente_a` cuando la LLM lo devolvió bien.
    """
    direccion = _texto(riesgo.get("afecta_principalmente_a")).lower()
    if direccion in ("artista", "productora", "ambas"):
        return direccion
    return ""


def _inferir_direccion_heuristica(riesgo: Dict[str, Any]) -> str:
    """
    Fallback determinista sectorial.

    No depende del resumen ejecutivo. Toma descripción + recomendación
    y clasifica a quién afecta principalmente la cláusula.
    """
    descripcion = _texto(riesgo.get("descripcion")).lower()
    recomendacion = _texto(riesgo.get("recomendacion")).lower()
    impacto = _texto(riesgo.get("impacto")).lower()
    tipo_riesgo = _obtener_tipo_riesgo(riesgo)
    texto = f"{descripcion} {recomendacion}".strip()

    # Reglas por tipo de riesgo: prioridad alta
    if tipo_riesgo in {
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

    if tipo_riesgo in {"penalidad"}:
        if any(p in texto for p in ["penalidades a la productora", "multa a la productora", "obligación de pago de la productora", "obligacion de pago de la productora"]):
            return "productora"
        return "artista"

    if tipo_riesgo in {"jurisdiccion_conflictos", "obligaciones_operativas", "plazo", "distribucion"}:
        return "ambas"

    # Fallback por patrones de negocio
    patrones_artista = [
        "cesión", "cesion", "derechos", "irrevocable",
        "máximo plazo legal", "maximo plazo legal",
        "todos los medios", "todos los territorios",
        "regalías", "regalias", "sin regalías", "sin regalias",
        "remuneración fija", "remuneracion fija",
        "compensación adicional", "compensacion adicional",
        "explotaciones secundarias", "exclusividad",
        "producciones competitivas",
        "rescisión unilateral", "rescision unilateral",
        "rescisión anticipada", "rescision anticipada",
        "seguro contratado por la productora",
        "sin detalle de coberturas",
        "pago solo de lo devengado",
        "confidencialidad", "sin plazo definido",
        "oportunidades laborales", "ingresos futuros",
        "control sobre la interpretación", "control sobre la interpretacion",
        "estabilidad laboral",
    ]

    patrones_productora = [
        "incumplimiento grave del artista",
        "inasistencia del artista",
        "disponibilidad del artista",
        "costos adicionales de producción", "costos adicionales de produccion",
        "obligación de pago de la productora", "obligacion de pago de la productora",
        "demoras imputables a la productora",
        "penalidades a la productora", "multa a la productora",
    ]

    patrones_ambas = [
        "cronograma",
        "jornadas máximas", "jornadas maximas",
        "condiciones de trabajo",
        "obligaciones operativas específicas", "obligaciones operativas especificas",
        "jurisdicción exclusiva", "jurisdiccion exclusiva",
        "tribunales de montevideo",
        "resolución de disputas", "resolucion de disputas",
        "mediación", "mediacion",
        "partes extranjeras",
    ]

    if any(p in texto for p in patrones_artista):
        return "artista"
    if any(p in texto for p in patrones_productora):
        return "productora"
    if any(p in texto for p in patrones_ambas):
        return "ambas"

    # Fallback conservador
    if impacto in ("legal", "financiero", "operativo", "mixto") and any(
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
# REPARTO DETERMINISTA DEL RIESGO
# =========================================================

def _repartir_score_por_rol(riesgos: List[Dict[str, Any]], rol_analizado: str) -> Tuple[float, float]:
    """
    Reglas de reparto:
    - si afecta a la parte analizada: 100% / 5%
    - si afecta a la contraparte: 5% / 100%
    - si afecta a ambas: 55% / 55%

    Esto evita empates artificiales y, sobre todo, evita depender de la prosa
    del resumen ejecutivo para decidir la dirección final.
    """
    rol = _normalizar_rol(rol_analizado)
    contraparte = _rol_contraparte(rol)

    score_parte = 0.0
    score_contraparte = 0.0

    for riesgo in riesgos:
        base = _peso_base_riesgo(riesgo)
        direccion = _obtener_direccion_riesgo(riesgo)

        if direccion == "ambas":
            score_parte += base * 0.55
            score_contraparte += base * 0.55
            continue

        if direccion == rol:
            score_parte += base * 1.00
            score_contraparte += base * 0.05
            continue

        if direccion == contraparte:
            score_parte += base * 0.05
            score_contraparte += base * 1.00
            continue

        score_parte += base * 0.50
        score_contraparte += base * 0.50

    return round(score_parte, 2), round(score_contraparte, 2)


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def calcular_scoring_productor(resultado: Dict[str, Any], rol_analizado: str = "Artista") -> Dict[str, Any]:
    """
    Aplica scoring audiovisual completamente determinista por cláusula.

    Paso 1:
        calcula la severidad contractual audiovisual

    Paso 2:
        reparte el riesgo entre parte analizada y contraparte
        según la orientación de cada cláusula

    Paso 3:
        construye el bloque final compatible con Word y Render
    """
    if not isinstance(resultado, dict):
        return resultado

    riesgos = _extraer_riesgos_audiovisuales(resultado)
    rol_norm = _normalizar_rol(rol_analizado)
    rol_contraparte = _rol_contraparte(rol_norm)

    # Guardar tipo de riesgo inferido/normalizado en cada cláusula
    # para trazabilidad interna.
    for riesgo in riesgos:
        riesgo["tipo_riesgo_deterministico"] = _obtener_tipo_riesgo(riesgo)

    severidad_score = _calcular_score_base_audiovisual(riesgos)
    severidad_nivel = _determinar_nivel_audiovisual(severidad_score)

    score_parte, score_contraparte = _repartir_score_por_rol(
        riesgos=riesgos,
        rol_analizado=rol_norm,
    )

    nivel_parte = _determinar_nivel_audiovisual(score_parte)
    nivel_contraparte = _determinar_nivel_audiovisual(score_contraparte)
    metricas = _contar_metricas(riesgos)

    resultado["scoring"] = {
        "severidad_contrato": {
            "score": round(severidad_score, 2),
            "nivel": severidad_nivel,
            "fundamento": "Mide qué tan exigente, severo o litigioso es el contrato audiovisual en sí mismo.",
        },
        "riesgo_parte_analizada": {
            "score": round(score_parte, 2),
            "nivel": nivel_parte,
            "rol": _etiqueta_rol(rol_norm),
            "fundamento": "Mide qué tan expuesta queda la parte analizada según las cláusulas audiovisuales del contrato.",
        },
        "riesgo_contraparte": {
            "score": round(score_contraparte, 2),
            "nivel": nivel_contraparte,
            "rol": _etiqueta_rol(rol_contraparte),
            "fundamento": "Mide qué tan expuesta queda la contraparte según esas mismas cláusulas.",
        },
        # aliases legacy
        "score_total": round(severidad_score, 2),
        "nivel_riesgo": severidad_nivel,
        "metricas": metricas,
        "version_scoring": ALGORITMO_SCORING_VERSION,
    }

    # Se conserva la metadata de presentación para que Word/Render muestren
    # el rol visible correcto incluso después del recálculo final en main.py.
    resultado.setdefault("metadata_sistema", {})
    resultado["metadata_sistema"].setdefault("metadata_presentacion", {})
    resultado["metadata_sistema"]["metadata_presentacion"]["rol_contractual_detectado"] = _etiqueta_rol(rol_norm)

    return resultado