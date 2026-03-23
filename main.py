"""
AI_GPT_AUTOMATIZACION/main.py
-----------------------------

Motor principal de análisis contractual.

Este script:

1) Recibe un contrato en formato JSON
2) Detecta el tipo de contrato
3) Selecciona la vertical jurídica correspondiente
4) Ejecuta el análisis
5) Genera el reporte final en JSON
6) Genera salida en Word usando un generador específico por vertical

Puede ejecutarse de dos formas:

Modo DEMO / CLI
    python main.py input/contrato.json

Modo API / WEB
    Utilizado por FastAPI / uvicorn a través de imports internos

Notas
-----
- Este archivo actúa como orquestador.
- La lógica jurídica vive en las verticales.
- La conversión PDF/TXT → JSON ocurre antes, en el convertidor.
"""

import sys
import json
import os
import time

from utils.generador_word_general import generar_word_general
from utils.generador_word_audiovisual import generar_word_audiovisual

from verticales.general.service import ejecutar_analisis_general

try:
    from verticales.audiovisual.service import ejecutar_analisis_audiovisual
except ImportError:
    ejecutar_analisis_audiovisual = None


# =========================================================
# DETECCIÓN DE VERTICAL
# =========================================================

def detectar_vertical(texto: str) -> str:
    """
    Detecta automáticamente la vertical jurídica del contrato.

    Parámetros
    ----------
    texto : str
        Texto completo del contrato.

    Retorna
    -------
    str
        "GENERAL" o "AUDIOVISUAL"
    """

    texto = texto.lower()

    palabras_audiovisual = [
        "productor",
        "rodaje",
        "derechos de imagen",
        "guion",
        "licencia audiovisual",
        "obra audiovisual"
    ]

    for palabra in palabras_audiovisual:
        if palabra in texto:
            return "AUDIOVISUAL"

    return "GENERAL"


# =========================================================
# CARGAR JSON
# =========================================================

def cargar_contrato(ruta_json: str) -> dict:
    """
    Carga el JSON de entrada del contrato.

    Parámetros
    ----------
    ruta_json : str
        Ruta al archivo JSON generado previamente.

    Retorna
    -------
    dict
        Contenido del contrato.
    """

    if not os.path.exists(ruta_json):
        raise FileNotFoundError("Archivo JSON no encontrado.")

    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


# =========================================================
# MENSAJES VISUALES DEL PROCESO
# =========================================================

def mostrar_etapas_analisis():
    """
    Muestra etapas visibles del análisis para evitar
    sensación de bloqueo durante la espera.
    """

    print("📄 Analizando estructura del contrato")
    time.sleep(0.5)

    print("⚖ Evaluando riesgos jurídicos")
    time.sleep(0.5)

    print("🧠 Ejecutando modelo de IA")
    time.sleep(0.5)

    print("📊 Calculando scoring")
    time.sleep(0.5)


# =========================================================
# GUARDAR JSON DE SALIDA
# =========================================================

def guardar_reporte_json(resultado: dict, ruta_json_entrada: str) -> str:
    """
    Guarda el resultado final en /output como JSON.

    Parámetros
    ----------
    resultado : dict
        Resultado final del análisis.
    ruta_json_entrada : str
        Ruta del JSON de entrada.

    Retorna
    -------
    str
        Ruta del JSON de salida.
    """

    os.makedirs("output", exist_ok=True)

    nombre_salida = os.path.basename(ruta_json_entrada).replace(".json", "_reporte.json")
    ruta_output = os.path.join("output", nombre_salida)

    with open(ruta_output, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    return ruta_output


# =========================================================
# GENERAR WORD SEGÚN VERTICAL
# =========================================================

def generar_reporte_word_por_vertical(vertical: str, resultado: dict, ruta_output_json: str) -> str:
    """
    Genera el reporte Word utilizando el generador específico
    de la vertical.

    Parámetros
    ----------
    vertical : str
        Vertical detectada.
    resultado : dict
        Resultado final del análisis.
    ruta_output_json : str
        Ruta del JSON final guardado en output.

    Retorna
    -------
    str
        Ruta del Word generado.
    """

    if vertical == "AUDIOVISUAL":
        return generar_word_audiovisual(resultado, ruta_output_json)

    return generar_word_general(resultado, ruta_output_json)


# =========================================================
# MOTOR PRINCIPAL
# =========================================================

def ejecutar_motor(ruta_json: str):
    """
    Orquesta el flujo principal del análisis contractual.

    Flujo
    -----
    1. Carga el contrato
    2. Detecta la vertical
    3. Ejecuta el análisis correspondiente
    4. Guarda el resultado en JSON
    5. Genera el Word de la vertical adecuada
    6. Devuelve datos útiles para reutilización desde API/Web
    """

    print("🔎 Detectando tipo de contrato...")

    data = cargar_contrato(ruta_json)

    texto = data.get("texto", "")

    if not texto:
        raise ValueError("El JSON no contiene el texto del contrato.")

    vertical = detectar_vertical(texto)

    print(f"✔ Vertical detectada: {vertical}")
    print("\n⚙ Ejecutando motor de análisis...\n")

    mostrar_etapas_analisis()

    # -----------------------------------------------------
    # GENERAL
    # -----------------------------------------------------

    if vertical == "GENERAL":
        resultado = ejecutar_analisis_general(data)

    # -----------------------------------------------------
    # AUDIOVISUAL
    # -----------------------------------------------------

    elif vertical == "AUDIOVISUAL":

        if ejecutar_analisis_audiovisual is None:
            print("⚠ Vertical audiovisual no disponible aún.")
            return None

        resultado = ejecutar_analisis_audiovisual(data)

    # -----------------------------------------------------
    # DESCONOCIDO
    # -----------------------------------------------------

    else:
        print("❌ No se pudo determinar la vertical.")
        return None

    # -----------------------------------------------------
    # GUARDAR JSON
    # -----------------------------------------------------

    ruta_output_json = guardar_reporte_json(resultado, ruta_json)
    print(f"\n📄 Reporte JSON guardado en: {ruta_output_json}")

    # -----------------------------------------------------
    # GENERAR WORD
    # -----------------------------------------------------

    ruta_word = generar_reporte_word_por_vertical(vertical, resultado, ruta_output_json)
    print(f"\n📄 Reporte Word guardado en: {ruta_word}")

    print("\n✔ Análisis finalizado")

    return {
        "vertical": vertical,
        "resultado": resultado,
        "ruta_json_output": ruta_output_json,
        "ruta_word_output": ruta_word,
    }


# =========================================================
# EJECUCIÓN DESDE CONSOLA
# =========================================================

if __name__ == "__main__":

    print("\n======================================")
    print("   SISTEMA DE ANALISIS CONTRACTUAL IA")
    print("======================================\n")

    if len(sys.argv) < 2:
        print("❌ Debe indicar un archivo JSON")
        print("\nEjemplo:")
        print("python main.py input/contrato.json")
        sys.exit()

    ruta_json = sys.argv[1]

    try:
        ejecutar_motor(ruta_json)

    except Exception as e:
        print("\n❌ Error durante el análisis")
        print(e)