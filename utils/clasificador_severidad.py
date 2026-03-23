"""
AI_GPT_AUTOMATIZACION/core/clasificador_severidad.py

Clasificador Determinístico v4.0
- 4 niveles
- Indicadores externos en JSON
- Reglas combinadas
"""

import json
import os


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
# 2️⃣ Evaluador de reglas
# ------------------------------------------------

def cumple_regla(texto: str, regla: dict) -> bool:

    if regla["tipo"] == "frase":
        return regla["contiene"] in texto

    if regla["tipo"] == "combinada":
        return all(palabra in texto for palabra in regla["contiene_todas"])

    return False


# ------------------------------------------------
# 3️⃣ Clasificación jerárquica
# ------------------------------------------------

def clasificar_severidad(descripcion: str) -> str:

    texto = descripcion.lower()

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