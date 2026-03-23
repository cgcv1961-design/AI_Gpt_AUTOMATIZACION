"""
AI_Gpt_AUTOMATIZACION/analizar_contrato.py

Comando principal del sistema de análisis contractual.

Flujo completo:

1) Recibe un contrato
2) Lo convierte a JSON si es necesario
3) Ejecuta análisis IA
4) Aplica motor de scoring
5) Genera reporte Word

Pensado para uso en demo o producción.
"""

import os
import json

from services.file_processor import procesar_archivo
from analizador import analizar_contrato
from services.router import enrutar_analisis
from reportes_generator.generar_word import generar_reporte_word


# ======================================================
# CONFIG
# ======================================================

INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"


# ======================================================
# UTILIDAD
# ======================================================

def obtener_contrato():
    archivos = os.listdir(INPUT_FOLDER)

    if not archivos:
        raise Exception("No hay contratos en la carpeta input.")

    return os.path.join(INPUT_FOLDER, archivos[0])


# ======================================================
# MAIN
# ======================================================

def main():

    print("\n===================================")
    print(" MOTOR DE ANALISIS CONTRACTUAL")
    print("===================================\n")

    print("Cargando motor de análisis...")
    print("Inicializando reglas jurídicas...")
    print("Preparando sistema IA...\n")

    # 1️⃣ obtener contrato
    ruta_contrato = obtener_contrato()

    print(f"Contrato detectado: {ruta_contrato}\n")

    # 2️⃣ procesar archivo
    data = procesar_archivo(ruta_contrato)

    print("Contrato convertido a JSON correctamente\n")

    # 3️⃣ análisis IA
    print("Analizando contrato con IA...\n")

    resultado_ia = analizar_contrato(data)

    # 4️⃣ router vertical
    print("Aplicando motor de reglas jurídicas...\n")

    resultado_final = enrutar_analisis(resultado_ia)

    # 5️⃣ guardar JSON
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    ruta_json = os.path.join(OUTPUT_FOLDER, "resultado_analisis.json")

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, indent=2, ensure_ascii=False)

    print(f"Resultado JSON guardado en: {ruta_json}")

    # 6️⃣ generar reporte
    ruta_reporte = os.path.join(OUTPUT_FOLDER, "reporte_contrato.docx")

    generar_reporte_word(resultado_final, ruta_reporte)

    print(f"Reporte generado: {ruta_reporte}\n")

    print("Analisis completado correctamente.")


# ======================================================
# ENTRYPOINT
# ======================================================

if __name__ == "__main__":
    main()