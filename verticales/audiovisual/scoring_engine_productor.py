"""
verticales/audiovisual/scoring_engine_productor.py
--------------------------------------------------
"""
"""
SCORING ENGINE AUDIOVISUAL v5.1
--------------------------------

MEJORAS CLAVE SOBRE 5.0:

1. Fallback inteligente:
   - si no hay dirección → prioriza ARTISTA

2. Heurística audiovisual mejorada

3. Corrector final basado en resumen ejecutivo:
   - alinea IA (texto) con scoring (números)

4. Evita simetría artificial (problema detectado)

PRINCIPIO:
La IA interpreta → Python valida y corrige
"""

from typing import Dict, List, Any, Tuple

ALGORITMO_SCORING_VERSION = "5.1_aud_direccional_corregido"

PESOS = {
    "baja": 1.0,
    "media": 3.0,
    "media-alta": 5.0,
    "alta": 7.0,
    "critica": 10.0,
}


# =========================================================
# NORMALIZADORES
# =========================================================

def _txt(x):
    return str(x or "").lower().strip()


def _sev(s):
    s = _txt(s)
    return {
        "baja": "baja",
        "media": "media",
        "media-alta": "media-alta",
        "media_alta": "media-alta",
        "alta": "alta",
        "critica": "critica",
        "crítica": "critica",
    }.get(s, "media")


def _rol(r):
    r = _txt(r)
    if "artista" in r:
        return "artista"
    if "productora" in r:
        return "productora"
    return "artista"


def _nivel(score):
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


# =========================================================
# EXTRACCIÓN
# =========================================================

def _riesgos(resultado):
    return resultado.get("analisis_sectorial", {}).get("riesgos_sectoriales", [])


# =========================================================
# DIRECCIÓN DEL RIESGO
# =========================================================

def _direccion_llm(r):
    d = _txt(r.get("afecta_principalmente_a"))
    if d in ["artista", "productora", "ambas"]:
        return d
    return None


def _direccion_heuristica(r):
    t = _txt(r.get("descripcion")) + " " + _txt(r.get("recomendacion"))

    # 🔥 patrones artista (FUERTE)
    if any(p in t for p in [
        "cesion", "derechos", "exclusiv",
        "regalia", "sin regal",
        "rescisi", "rescind",
        "seguro", "confidencialidad"
    ]):
        return "artista"

    # compartidos
    if any(p in t for p in [
        "jurisdic", "disputa", "cronograma"
    ]):
        return "ambas"

    return None


def _direccion_final(r):
    # 1. LLM
    d = _direccion_llm(r)
    if d:
        return d

    # 2. heurística
    d = _direccion_heuristica(r)
    if d:
        return d

    # 🔥 3. fallback FUERTE
    return "artista"


# =========================================================
# SCORE BASE
# =========================================================

def _peso(r):
    s = _sev(r.get("severidad"))
    base = PESOS.get(s, 3)
    extra = float(r.get("puntaje_agravante_relevante", 0) or 0)
    return base + extra


def _score_total(riesgos):
    return round(sum(_peso(r) for r in riesgos), 2)


# =========================================================
# REPARTO
# =========================================================

def _reparto(riesgos, rol):
    rol = _rol(rol)
    contraparte = "productora" if rol == "artista" else "artista"

    s_parte = 0
    s_contra = 0

    for r in riesgos:
        base = _peso(r)
        d = _direccion_final(r)

        if d == "ambas":
            s_parte += base * 0.7
            s_contra += base * 0.7

        elif d == rol:
            s_parte += base
            s_contra += base * 0.2

        elif d == contraparte:
            s_parte += base * 0.2
            s_contra += base

    return round(s_parte, 2), round(s_contra, 2)


# =========================================================
# 🔥 CORRECTOR FINAL (CLAVE)
# =========================================================

def _corregir_por_resumen(resultado, s_parte, s_contra, rol):
    try:
        texto = _txt(
            resultado["informe_cliente"]["resumen_ejecutivo"]["nivel_riesgo_global"]
        )
    except:
        return s_parte, s_contra

    if "artista" in texto and "productora" in texto:

        if "alto para el artista" in texto:
            if rol == "artista" and s_parte <= s_contra:
                return s_parte * 1.3, s_contra * 0.7

        if "alto para la productora" in texto:
            if rol == "productora" and s_parte <= s_contra:
                return s_parte * 1.3, s_contra * 0.7

    return s_parte, s_contra


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def calcular_scoring_productor(resultado: Dict[str, Any], rol_analizado="Artista"):

    riesgos = _riesgos(resultado)

    score_total = _score_total(riesgos)

    s_parte, s_contra = _reparto(riesgos, rol_analizado)

    # 🔥 ajuste final
    s_parte, s_contra = _corregir_por_resumen(
        resultado, s_parte, s_contra, _rol(rol_analizado)
    )

    resultado["scoring"] = {
        "severidad_contrato": {
            "score": score_total,
            "nivel": _nivel(score_total),
        },
        "riesgo_parte_analizada": {
            "score": round(s_parte, 2),
            "nivel": _nivel(s_parte),
        },
        "riesgo_contraparte": {
            "score": round(s_contra, 2),
            "nivel": _nivel(s_contra),
        },
        "score_total": score_total,
        "nivel_riesgo": _nivel(score_total),
        "version_scoring": ALGORITMO_SCORING_VERSION,
    }

    return resultado