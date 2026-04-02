"""
DEMO DEL SISTEMA DE ANALISIS CONTRACTUAL IA
--------------------------------------------

Flujo de ejecución:

1) Seleccionar contrato
2) Convertir documento a JSON
3) Configurar perspectiva y país de referencia
4) Ejecutar análisis contractual
5) Generar reporte

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
# 3️⃣ CONFIGURACIÓN DEL ANÁLISIS
# =====================================================

print("\n2️⃣ Configuración del análisis\n")

# -----------------------------
# Selección de perspectiva
# -----------------------------
print("Seleccionar perspectiva:")
print("1 - Proveedor (quien recibe el contrato)")
print("2 - Cliente (quien propone el contrato)")

opcion_perspectiva = input("Ingrese opción (1 o 2): ").strip()

if opcion_perspectiva == "2":
    perspectiva = "cliente"
else:
    perspectiva = "proveedor"

# -----------------------------
# Selección de país / contexto legal
# -----------------------------
print("\nSeleccionar país / contexto legal de referencia:")
print("1 - Argentina")
print("2 - Uruguay")
print("3 - Italia")
print("4 - España")
print("5 - Internacional / Otro")

opcion_pais = input("Ingrese opción (1 a 5): ").strip()

mapa_pais = {
    "1": "argentina",
    "2": "uruguay",
    "3": "italia",
    "4": "espana",
    "5": "internacional",
}

pais_referencia = mapa_pais.get(opcion_pais, "internacional")

print(f"\n✔ Perspectiva seleccionada: {perspectiva}")
print(f"✔ País / contexto legal seleccionado: {pais_referencia}")


# =====================================================
# 4️⃣ EJECUTAR MOTOR DE ANALISIS
# =====================================================

print("\n3️⃣ Ejecutando análisis contractual...\n")

try:
    subprocess.run(
        [
            "python",
            "main.py",
            ruta_json,
            perspectiva,
            pais_referencia,
        ],
        check=True
    )

except subprocess.CalledProcessError as e:
    print("\n❌ Error durante el análisis")
    print(f"El proceso terminó con código de error: {e.returncode}")

except Exception as e:
    print("\n❌ Error durante el análisis")
    print(e)