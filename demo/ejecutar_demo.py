"""
DEMO DEL SISTEMA DE ANALISIS CONTRACTUAL IA
--------------------------------------------

Flujo de ejecución:

1) Seleccionar contrato
2) Convertir documento a JSON
3) Ejecutar análisis contractual
4) Generar reporte

Diseñado para demostraciones con clientes.
"""

import os
import sys
import subprocess


# =====================================================
# CONFIGURAR PATH DEL PROYECTO
# =====================================================

# Obtiene carpeta raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agrega la raíz al path de Python
sys.path.append(BASE_DIR)


# =====================================================
# IMPORTS DEL SISTEMA
# =====================================================

from tools.convertidor_documentos import seleccionar_archivo, convertir_a_json


print("\n======================================")
print("   SISTEMA DE ANALISIS CONTRACTUAL IA")
print("======================================\n")

print("Cargando motor de análisis...")
print("Inicializando reglas jurídicas...\n")


# =====================================================
# 1️⃣ SELECCIONAR CONTRATO
# =====================================================

ruta_pdf = seleccionar_archivo()

if not ruta_pdf:

    print("❌ No se seleccionó archivo.")
    sys.exit()


print("\n📄 Archivo seleccionado:")
print(ruta_pdf)


# =====================================================
# 2️⃣ CONVERTIR A JSON
# =====================================================

print("\n1️⃣ Convirtiendo documento a JSON...\n")

try:

    ruta_json = convertir_a_json(ruta_pdf)

    print("✔ Documento convertido")
    print("JSON generado en:")
    print(ruta_json)

except Exception as e:

    print("\n❌ Error durante la conversión")
    print(e)
    sys.exit()


# =====================================================
# 3️⃣ EJECUTAR MOTOR DE ANALISIS
# =====================================================

print("\n2️⃣ Ejecutando análisis contractual...\n")

try:

    subprocess.run(["python", "main.py", ruta_json])

except Exception as e:

    print("\n❌ Error durante el análisis")
    print(e)