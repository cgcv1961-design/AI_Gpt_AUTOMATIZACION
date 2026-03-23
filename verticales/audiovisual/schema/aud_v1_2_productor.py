"""
verticales/audiovisual/schema/aud_v1_2_productor.py
---------------------------------------------------

Contrato de salida y normalización para la vertical AUDIOVISUAL.

OBJETIVO
--------
Definir una única estructura JSON autoritativa para AUDIOVISUAL.

PRINCIPIO
---------
JSON = fuente de verdad única

El Word NO debe reconstruir ni reinterpretar el análisis por fuera de este JSON.
Por lo tanto, toda la riqueza analítica que deba aparecer en el Word debe existir
aquí, dentro del JSON normalizado final.

ESTRUCTURA OBJETIVO
-------------------
{
  "nucleo_contractual": {...},
  "analisis_sectorial": {
      "riesgos_sectoriales": [...],
      "nivel_confianza_analisis": {
          "general": "...",
          "fundamento": "..."
      }
  },
  "informe_cliente": {
      "resumen_ejecutivo": {
          "vision_general": "...",
          "nivel_riesgo_global": "...",
          "puntos_criticos": [...]
      },
      "informe_detallado": {
          "hallazgos_principales": [...],
          "implicancias_estrategicas_mediano_plazo": [...],
          "preguntas_clave_antes_de_firmar": [...],
          "conclusion_profesional": "..."
      },
      "recomendacion_profesional": "..."
  },
  "scoring": {...},
  "metadata_sistema": {...}
}

NOTA
----
Este normalizador:
- conserva compatibilidad con salidas audiovisuales viejas
- enriquece campos faltantes a partir de los datos YA existentes
- reutiliza el texto contractual para mejorar el bloque de duración
- prioriza SIEMPRE lo que venga del modelo antes de usar fallbacks
"""

from __future__ import annotations

from typing import Any, Dict, List

from utils.duracion_audiovisual import enriquecer_duracion_audiovisual


def _valor_no_vacio(*valores, default="-"):
    """
    Devuelve el primer valor no vacío.

    Considera vacíos:
    None, "", [], {}
    """
    for v in valores:
        if v not in (None, "", [], {}):
            return v
    return default


def _texto(valor: Any, default: str = "-") -> str:
    """
    Convierte un valor en string legible.
    """
    if valor in (None, "", [], {}):
        return default
    return str(valor).strip()


def _lista(valor: Any) -> List[str]:
    """
    Normaliza cualquier valor a lista de strings.

    Reglas:
    - list -> lista de strings
    - dict -> lista 'clave: valor'
    - str -> lista de un elemento
    - vacío -> []
    """
    if valor in (None, "", [], {}):
        return []

    if isinstance(valor, list):
        salida = []
        for item in valor:
            if item in (None, "", [], {}):
                continue
            texto = str(item).strip()
            if texto:
                salida.append(texto)
        return salida

    if isinstance(valor, dict):
        salida = []
        for k, v in valor.items():
            if v not in (None, "", [], {}):
                salida.append(f"{k}: {v}")
        return salida

    texto = str(valor).strip()
    return [texto] if texto else []


def _normalizar_riesgos_sectoriales(analisis_sectorial: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normaliza los riesgos sectoriales a una forma estable.

    Estructura resultante:
    [
        {
            "severidad": "...",
            "impacto": "...",
            "descripcion": "...",
            "recomendacion": "..."
        }
    ]
    """
    riesgos = analisis_sectorial.get("riesgos_sectoriales", [])
    if not isinstance(riesgos, list):
        return []

    salida = []

    for r in riesgos:
        if isinstance(r, dict):
            salida.append({
                "severidad": _texto(
                    _valor_no_vacio(
                        r.get("severidad"),
                        r.get("nivel"),
                        r.get("criticidad"),
                        default="-"
                    ),
                    default="-"
                ),
                "impacto": _texto(
                    _valor_no_vacio(
                        r.get("impacto"),
                        r.get("categoria"),
                        default="-"
                    ),
                    default="-"
                ),
                "descripcion": _texto(
                    _valor_no_vacio(
                        r.get("descripcion"),
                        r.get("detalle"),
                        r.get("riesgo"),
                        r.get("hallazgo"),
                        r.get("observacion"),
                        default="-"
                    ),
                    default="-"
                ),
                "recomendacion": _texto(
                    _valor_no_vacio(
                        r.get("recomendacion"),
                        r.get("mitigacion"),
                        default="-"
                    ),
                    default="-"
                ),
            })
        else:
            salida.append({
                "severidad": "-",
                "impacto": "-",
                "descripcion": _texto(r, default="-"),
                "recomendacion": "-",
            })

    return salida


def _normalizar_metricas_desde_riesgos(riesgos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Reconstruye métricas de scoring si no vinieran del servicio.
    """
    severidades = [str(r.get("severidad", "")).strip().lower() for r in riesgos]

    def count(*aliases: str) -> int:
        total = 0
        for sev in severidades:
            if sev in aliases:
                total += 1
        return total

    return {
        "cantidad_riesgos": len(riesgos),
        "riesgos_altos": count("alta", "alto"),
        "riesgos_media_altos": count("media-alta", "medio-alto", "media alta", "medio alto"),
        "riesgos_medios": count("media", "medio", "moderado"),
        "riesgos_bajos": count("baja", "bajo"),
    }


def _peso_severidad(severidad: str) -> int:
    """
    Devuelve un peso para ordenar de mayor a menor criticidad.
    """
    sev = str(severidad).strip().lower()
    mapa = {
        "alto": 4,
        "alta": 4,
        "medio-alto": 3,
        "media-alta": 3,
        "medio alto": 3,
        "media alta": 3,
        "medio": 2,
        "media": 2,
        "moderado": 2,
        "bajo": 1,
        "baja": 1,
    }
    return mapa.get(sev, 0)


def _top_descripciones(riesgos: List[Dict[str, Any]], maximo: int = 5) -> List[str]:
    """
    Extrae descripciones útiles para puntos críticos / hallazgos.
    Prioriza severidades más altas.
    """
    ordenados = sorted(
        riesgos,
        key=lambda r: _peso_severidad(str(r.get("severidad", "")).strip().lower()),
        reverse=True,
    )

    salida: List[str] = []
    usados = set()

    for r in ordenados:
        desc = _texto(r.get("descripcion"), default="-")
        if desc == "-" or desc in usados:
            continue
        salida.append(desc)
        usados.add(desc)
        if len(salida) >= maximo:
            break

    return salida


def _preguntas_desde_riesgos(riesgos: List[Dict[str, Any]], maximo: int = 5) -> List[str]:
    """
    Genera preguntas clave mínimas y determinísticas a partir de los riesgos.

    Esto sigue cumpliendo el principio de fuente única, porque estas preguntas
    pasan a formar parte del JSON final guardado.
    """
    preguntas = []

    for desc in _top_descripciones(riesgos, maximo=maximo):
        preguntas.append(f"¿Cómo se resuelve contractualmente el punto referido a: {desc}?")

    return preguntas


def normalizar_respuesta_audiovisual(
    respuesta_modelo: Dict[str, Any],
    texto_contrato: str = ""
) -> Dict[str, Any]:
    """
    Normaliza la salida audiovisual a un JSON único y rico.

    Parámetros
    ----------
    respuesta_modelo : dict
        Respuesta parseada del modelo o del pipeline audiovisual.
    texto_contrato : str
        Texto original del contrato, usado para enriquecer duración.

    Retorna
    -------
    dict
        JSON final normalizado, listo para:
        1) guardarse como output autoritativo
        2) alimentar el generador Word
    """
    raw = respuesta_modelo if isinstance(respuesta_modelo, dict) else {}

    nucleo = raw.get("nucleo_contractual", {}) or {}
    analisis_sectorial_raw = raw.get("analisis_sectorial", {}) or {}
    informe_cliente_raw = raw.get("informe_cliente", {}) or {}
    scoring_raw = raw.get("scoring", {}) or {}
    metadata_raw = raw.get("metadata_sistema", {}) or {}

    riesgos_sectoriales = _normalizar_riesgos_sectoriales(analisis_sectorial_raw)

    # -----------------------------------------------------
    # RESUMEN EJECUTIVO
    # -----------------------------------------------------
    resumen_raw = informe_cliente_raw.get("resumen_ejecutivo", {})
    if isinstance(resumen_raw, str):
        resumen_raw = {"vision_general": resumen_raw}
    elif not isinstance(resumen_raw, dict):
        resumen_raw = {}

    vision_general = _texto(
        _valor_no_vacio(
            resumen_raw.get("vision_general"),
            informe_cliente_raw.get("resumen_ejecutivo"),
            default="-"
        ),
        default="-"
    )

    nivel_riesgo_global = _texto(
        _valor_no_vacio(
            resumen_raw.get("nivel_riesgo_global"),
            raw.get("evaluacion_general", {}).get("score_riesgo", {}).get("nivel")
            if isinstance(raw.get("evaluacion_general"), dict) else None,
            scoring_raw.get("nivel_riesgo"),
            default="-"
        ),
        default="-"
    )

    puntos_criticos = _lista(
        _valor_no_vacio(
            resumen_raw.get("puntos_criticos"),
            resumen_raw.get("puntos_clave"),
            informe_cliente_raw.get("puntos_criticos"),
            default=[]
        )
    )
    if not puntos_criticos:
        puntos_criticos = _top_descripciones(riesgos_sectoriales, maximo=3)

    # -----------------------------------------------------
    # INFORME DETALLADO
    # -----------------------------------------------------
    detalle_raw = informe_cliente_raw.get("informe_detallado", {})
    if not isinstance(detalle_raw, dict):
        detalle_raw = {}

    # HALLAZGOS PRINCIPALES
    hallazgos_principales = _lista(
        _valor_no_vacio(
            detalle_raw.get("hallazgos_principales"),
            detalle_raw.get("hallazgos"),
            analisis_sectorial_raw.get("hallazgos"),
            default=[]
        )
    )
    if not hallazgos_principales:
        hallazgos_principales = _top_descripciones(riesgos_sectoriales, maximo=5)

    # IMPLICANCIAS ESTRATÉGICAS
    implicancias = _lista(
        _valor_no_vacio(
            detalle_raw.get("implicancias_estrategicas_mediano_plazo"),
            detalle_raw.get("implicancias"),
            informe_cliente_raw.get("implicancias"),
            default=[]
        )
    )

    # PREGUNTAS CLAVE
    preguntas = _lista(
        _valor_no_vacio(
            detalle_raw.get("preguntas_clave_antes_de_firmar"),
            detalle_raw.get("preguntas"),
            informe_cliente_raw.get("preguntas"),
            default=[]
        )
    )
    if not preguntas:
        preguntas = _preguntas_desde_riesgos(riesgos_sectoriales, maximo=5)

    # CONCLUSIÓN PROFESIONAL
    conclusion_profesional = _texto(
        _valor_no_vacio(
            detalle_raw.get("conclusion_profesional"),
            informe_cliente_raw.get("conclusion"),
            analisis_sectorial_raw.get("conclusion"),
            default="-"
        ),
        default="-"
    )

    # RECOMENDACIÓN PROFESIONAL
    recomendacion_profesional = _texto(
        _valor_no_vacio(
            informe_cliente_raw.get("recomendacion_profesional"),
            informe_cliente_raw.get("recomendacion_estrategica_final"),
            default="-"
        ),
        default="-"
    )

    # -----------------------------------------------------
    # NIVEL DE CONFIANZA
    # -----------------------------------------------------
    nivel_confianza_raw = analisis_sectorial_raw.get("nivel_confianza_analisis", {})
    if not isinstance(nivel_confianza_raw, dict):
        nivel_confianza_raw = {}

    nivel_confianza = {
        "general": _texto(
            _valor_no_vacio(
                nivel_confianza_raw.get("general"),
                default="-"
            ),
            default="-"
        ),
        "fundamento": _texto(
            _valor_no_vacio(
                nivel_confianza_raw.get("fundamento"),
                default="-"
            ),
            default="-"
        ),
    }

    # -----------------------------------------------------
    # SCORING
    # -----------------------------------------------------
    metricas_raw = scoring_raw.get("metricas", {}) or {}
    if not isinstance(metricas_raw, dict):
        metricas_raw = {}

    metricas = {
        "cantidad_riesgos": _valor_no_vacio(metricas_raw.get("cantidad_riesgos"), default=None),
        "riesgos_altos": _valor_no_vacio(metricas_raw.get("riesgos_altos"), default=None),
        "riesgos_media_altos": _valor_no_vacio(metricas_raw.get("riesgos_media_altos"), default=None),
        "riesgos_medios": _valor_no_vacio(metricas_raw.get("riesgos_medios"), default=None),
        "riesgos_bajos": _valor_no_vacio(metricas_raw.get("riesgos_bajos"), default=None),
    }

    if any(v is None for v in metricas.values()):
        metricas_reconstruidas = _normalizar_metricas_desde_riesgos(riesgos_sectoriales)
        for k, v in metricas.items():
            if v is None:
                metricas[k] = metricas_reconstruidas[k]

    scoring = {
        "score_total": _valor_no_vacio(
            scoring_raw.get("score_total"),
            raw.get("evaluacion_general", {}).get("score_riesgo", {}).get("valor")
            if isinstance(raw.get("evaluacion_general"), dict) else None,
            default="-"
        ),
        "nivel_riesgo": _valor_no_vacio(
            scoring_raw.get("nivel_riesgo"),
            raw.get("evaluacion_general", {}).get("score_riesgo", {}).get("nivel")
            if isinstance(raw.get("evaluacion_general"), dict) else None,
            default="-"
        ),
        "version_scoring": _valor_no_vacio(
            scoring_raw.get("version_scoring"),
            raw.get("evaluacion_general", {}).get("version_scoring")
            if isinstance(raw.get("evaluacion_general"), dict) else None,
            default="-"
        ),
        "metricas": metricas,
    }

    # -----------------------------------------------------
    # JSON FINAL
    # -----------------------------------------------------
    resultado = {
        "nucleo_contractual": nucleo,
        "analisis_sectorial": {
            "riesgos_sectoriales": riesgos_sectoriales,
            "nivel_confianza_analisis": nivel_confianza,
        },
        "informe_cliente": {
            "resumen_ejecutivo": {
                "vision_general": vision_general,
                "nivel_riesgo_global": nivel_riesgo_global,
                "puntos_criticos": puntos_criticos,
            },
            "informe_detallado": {
                "hallazgos_principales": hallazgos_principales,
                "implicancias_estrategicas_mediano_plazo": implicancias,
                "preguntas_clave_antes_de_firmar": preguntas,
                "conclusion_profesional": conclusion_profesional,
            },
            "recomendacion_profesional": recomendacion_profesional,
        },
        "scoring": scoring,
        "metadata_sistema": metadata_raw,
    }

    # Enriquecimiento de duración sobre el mismo JSON final
    resultado = enriquecer_duracion_audiovisual(resultado, texto_contrato)

    return resultado