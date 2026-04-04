"""
AI_GPT_AUTOMATIZACION/utils/clasificador_severidad.py
-----------------------------------------------------

Clasificador Determinístico v5.0
- 4 niveles principales
- Indicadores externos en JSON
- Reglas combinadas
- Reglas relevantes auditables

OBJETIVO
--------
Mantener compatibilidad con el clasificador actual,
pero agregar una capa nueva que detecte términos y combinaciones
jurídicamente sensibles, por ejemplo:
- penalidades altas
- cesión agresiva de propiedad intelectual
- no competencia extensa
- responsabilidad ampliada por terceros

DISEÑO
------
1. Se calcula una severidad base desde indicadores clásicos.
2. Se evalúan reglas relevantes adicionales.
3. Se toma la severidad más alta entre:
   - severidad base
   - severidad mínima sugerida por reglas relevantes

Esto permite mejorar la detección sin romper la arquitectura actual.
"""

import json
import os
from typing import Dict, Optional

from core.reglas_relevantes import evaluar_reglas_relevantes, ORDEN_SEVERIDAD


# ------------------------------------------------
# 1️⃣ Carga externa de indicadores
# ------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_REGLAS = os.path.join(BASE_DIR, "indicadores_severidad.json")


def cargar_indicadores():
    with open(RUTA_REGLAS, "r", encoding="utf-8") as f:
        return json.load(f)


INDICADORES = cargar_indicadores()


# ------------------------------------------------
# 2️⃣ Evaluador de reglas clásicas
# ------------------------------------------------

def cumple_regla(texto: str, regla: dict) -> bool:

    if regla["tipo"] == "frase":
        return regla["contiene"] in texto

    if regla["tipo"] == "combinada":
        return all(palabra in texto for palabra in regla["contiene_todas"])

    return False


# ------------------------------------------------
# 3️⃣ Severidad base (clasificador clásico)
# ------------------------------------------------

def _clasificar_severidad_base(descripcion: str) -> str:
    """
    Clasificación jerárquica clásica basada en indicadores_severidad.json.
    """
    texto = (descripcion or "").lower()

    # 🔴 Alta
    for regla in INDICADORES["alta"]["reglas"]:
        if cumple_regla(texto, regla):
            return "alta"

    # 🟠 Media-Alta
    for regla in INDICADORES["media-alta"]["reglas"]:
        if cumple_regla(texto, regla):
            return "media-alta"

    # 🟡 Media
    for regla in INDICADORES["media"]["reglas"]:
        if cumple_regla(texto, regla):
            return "media"

    # 🟢 Baja
    return "baja"


def _severidad_mayor(a: Optional[str], b: Optional[str]) -> str:
    """
    Devuelve la severidad más alta entre dos valores.
    """
    if not a and not b:
        return "baja"
    if not a:
        return b
    if not b:
        return a

    oa = ORDEN_SEVERIDAD.get(a, 1)
    ob = ORDEN_SEVERIDAD.get(b, 1)

    return a if oa >= ob else b


# ------------------------------------------------
# 4️⃣ API DETALLADA NUEVA
# ------------------------------------------------

def analizar_severidad_detallada(descripcion: str) -> Dict:
    """
    Devuelve análisis completo de severidad:
    - severidad base
    - familias detectadas
    - detalle de reglas relevantes
    - severidad mínima sugerida
    - severidad final

    Esta función es la recomendada para nuevos flujos.
    """
    severidad_base = _clasificar_severidad_base(descripcion)
    reglas = evaluar_reglas_relevantes(descripcion)

    severidad_minima_sugerida = reglas.get("severidad_minima_sugerida")
    severidad_final = _severidad_mayor(severidad_base, severidad_minima_sugerida)

    return {
        "severidad_base": severidad_base,
        "severidad_minima_sugerida": severidad_minima_sugerida,
        "severidad_final": severidad_final,
        "familias_detectadas": reglas.get("familias_detectadas", []),
        "puntaje_agravante_total": reglas.get("puntaje_agravante_total", 0.0),
        "detalle_reglas": reglas.get("detalle_reglas", []),
    }


# ------------------------------------------------
# 5️⃣ API SIMPLE COMPATIBLE
# ------------------------------------------------

def clasificar_severidad(descripcion: str) -> str:
    """
    Compatibilidad con el sistema actual.

    Retorna solo la severidad final, pero internamente
    ya contempla reglas relevantes.
    """
    analisis = analizar_severidad_detallada(descripcion)
    return analisis["severidad_final"]