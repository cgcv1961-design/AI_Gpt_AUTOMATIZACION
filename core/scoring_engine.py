"""
AI_GPT_AUTOMATIZACION/core/scoring_engine.py
--------------------------------------------

Capa de enriquecimiento dual del scoring.

SEPARA DOS CONCEPTOS:
---------------------
1. Severidad del contrato
   - qué tan duro, agresivo o litigioso es el contrato en sí

2. Riesgo para la parte analizada
   - qué tan expuesta queda la parte que está mirando el contrato

3. Riesgo para la contraparte
   - qué tan expuesta queda la otra parte

IMPORTANTE
----------
No reemplaza el scoring sectorial existente.
Lo toma como base y reorganiza la salida para hacerla más clara.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from utils.clasificador_severidad import clasificar_nivel


def _texto(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _normalizar_nivel(nivel: str) -> str:
    txt = _texto(nivel).lower()

    mapa = {
        "bajo": "bajo",
        "medio": "medio",
        "moderado": "medio",
        "medio-alto": "medio-alto",
        "alto": "alto",
        "muy alto": "alto",
        "critico": "critico",
        "crítico": "critico",
    }

    return mapa.get(txt, "medio")


def _factor_score_por_nivel(nivel: str) -> float:
    nivel = _normalizar_nivel(nivel)

    factores = {
        "bajo": 0.30,
        "medio": 0.60,
        "medio-alto": 0.80,
        "alto": 1.00,
        "critico": 1.15,
    }
    return factores.get(nivel, 0.60)


def _keywords_rol(rol: str) -> List[str]:
    rol_txt = _texto(rol).lower()

    if "cliente" in rol_txt:
        return ["cliente"]
    if "proveedor" in rol_txt:
        return ["proveedor"]
    if "arrendador" in rol_txt or "locatore" in rol_txt:
        return ["arrendador", "locatore"]
    if "arrendatario" in rol_txt or "conduttore" in rol_txt:
        return ["arrendatario", "conduttore", "arrendatarios", "conduttori"]
    if "artista" in rol_txt or "intérprete" in rol_txt or "interprete" in rol_txt:
        return ["artista", "intérprete", "interprete"]
    if "productora" in rol_txt:
        return ["productora"]
    if "productor" in rol_txt:
        return ["productor"]

    return [rol_txt] if rol_txt else []


def _extraer_nivel_para_rol(texto: str, rol: str) -> Optional[str]:
    """
    Busca expresiones como:
    - alto para el Proveedor
    - bajo para el Cliente
    - moderado para el arrendatario
    """
    texto_norm = _texto(texto).lower()
    if not texto_norm or not rol:
        return None

    keywords = _keywords_rol(rol)

    niveles = [
        "muy alto",
        "medio-alto",
        "alto",
        "moderado",
        "medio",
        "bajo",
        "crítico",
        "critico",
    ]

    for kw in keywords:
        for nivel in niveles:
            patron = rf"{re.escape(nivel)}[^.;,\n]*para el\s+{re.escape(kw)}"
            if re.search(patron, texto_norm):
                return _normalizar_nivel(nivel)

            patron2 = rf"{re.escape(nivel)}[^.;,\n]*para la\s+{re.escape(kw)}"
            if re.search(patron2, texto_norm):
                return _normalizar_nivel(nivel)

    return None


def _inferir_rol_contraparte(resultado: Dict[str, Any], rol_analizado: str) -> str:
    metadata_presentacion = (
        resultado.get("metadata_sistema", {})
                .get("metadata_presentacion", {})
        or {}
    )
    partes_con_rol = metadata_presentacion.get("partes_con_rol", []) or []

    rol_analizado_txt = _texto(rol_analizado).lower()

    for parte in partes_con_rol:
        parte_txt = _texto(parte)
        if "(" in parte_txt and ")" in parte_txt:
            rol_visible = parte_txt.rsplit("(", 1)[1].replace(")", "").strip()
            if rol_visible and rol_visible.lower() != rol_analizado_txt:
                return rol_visible

    mapa = {
        "cliente": "Proveedor",
        "proveedor": "Cliente",
        "arrendador / locatore": "Arrendatario / conduttore",
        "arrendatario / conduttore": "Arrendador / locatore",
        "arrendatarios / conduttori": "Arrendador / locatore",
        "artista": "Productora",
        "productora": "Artista",
        "productor": "Artista",
    }

    return mapa.get(rol_analizado, "Contraparte")


def _obtener_niveles_direccionales(
    resultado: Dict[str, Any],
    rol_analizado: str,
    rol_contraparte: str,
    nivel_default: str,
) -> Dict[str, str]:
    resumen = (
        resultado.get("informe_cliente", {})
                .get("resumen_ejecutivo", {})
        or {}
    )

    nivel_global_txt = _texto(resumen.get("nivel_riesgo_global"))

    # 1. Intento explícito por rol
    nivel_parte = _extraer_nivel_para_rol(nivel_global_txt, rol_analizado)
    nivel_contraparte = _extraer_nivel_para_rol(nivel_global_txt, rol_contraparte)

    # 2. Si no hay niveles explícitos, usamos el texto completo como referencia general
    if not nivel_parte and not nivel_contraparte:
        nivel_general = _normalizar_nivel(nivel_global_txt if nivel_global_txt else nivel_default)
        nivel_parte = nivel_general
        nivel_contraparte = nivel_general

    # 3. Si falta solo uno, completamos con el default
    if not nivel_parte:
        nivel_parte = _normalizar_nivel(nivel_default)
    if not nivel_contraparte:
        nivel_contraparte = _normalizar_nivel(nivel_default)

    return {
        "parte": nivel_parte,
        "contraparte": nivel_contraparte,
    }


def enriquecer_scoring_dual(resultado: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte el bloque scoring actual en una salida más clara:

    - severidad_contrato
    - riesgo_parte_analizada
    - riesgo_contraparte

    Mantiene también aliases legacy:
    - score_total
    - nivel_riesgo
    """
    if not isinstance(resultado, dict):
        return resultado

    scoring = resultado.get("scoring", {}) or {}
    metadata_presentacion = (
        resultado.get("metadata_sistema", {})
                .get("metadata_presentacion", {})
        or {}
    )

    rol_analizado = _texto(metadata_presentacion.get("rol_contractual_detectado")) or "Parte analizada"
    rol_contraparte = _inferir_rol_contraparte(resultado, rol_analizado)

    severidad_score = float(scoring.get("score_total", 0) or 0)
    severidad_nivel = _normalizar_nivel(scoring.get("nivel_riesgo", "medio"))

    niveles = _obtener_niveles_direccionales(
        resultado=resultado,
        rol_analizado=rol_analizado,
        rol_contraparte=rol_contraparte,
        nivel_default=severidad_nivel,
    )

    score_parte = round(severidad_score * _factor_score_por_nivel(niveles["parte"]), 2)
    score_contraparte = round(severidad_score * _factor_score_por_nivel(niveles["contraparte"]), 2)

    scoring["severidad_contrato"] = {
        "score": severidad_score,
        "nivel": severidad_nivel,
        "fundamento": "Mide qué tan exigente, severo o litigioso es el contrato en sí mismo."
    }

    scoring["riesgo_parte_analizada"] = {
        "score": score_parte,
        "nivel": niveles["parte"],
        "rol": rol_analizado,
        "fundamento": "Mide qué tan expuesta queda la parte analizada según el contenido del contrato y la perspectiva seleccionada."
    }

    scoring["riesgo_contraparte"] = {
        "score": score_contraparte,
        "nivel": niveles["contraparte"],
        "rol": rol_contraparte,
        "fundamento": "Mide qué tan expuesta queda la contraparte en relación con las mismas cláusulas."
    }

    # Aliases legacy: los mantenemos para no romper API, Word ni UI previos.
    scoring["score_total"] = severidad_score
    scoring["nivel_riesgo"] = severidad_nivel

    resultado["scoring"] = scoring
    return resultado