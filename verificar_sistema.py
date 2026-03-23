"""
verificar_sistema.py

Script de diagnóstico del sistema completo.

Verifica:
- estructura de carpetas
- archivos críticos
- reglas JSON
- imports principales

Uso:
python verificar_sistema.py
"""

import os
import importlib

print("\n=========================================")
print("   VERIFICADOR DEL SISTEMA CONTRACTUAL")
print("=========================================\n")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------
# Carpetas críticas
# --------------------------------------------------

CARPETAS = [
    "api",
    "core",
    "services",
    "verticales",
    "utils",
    "reportes_generator",
    "tools",
    "input",
    "output",
    "demo",
    "demo_interface",
    "verticales",
]

# --------------------------------------------------
# Archivos críticos
# --------------------------------------------------

ARCHIVOS = [
    "config.py",
    "analizador.py",
    "services/router.py",
    "utils/clasificador_severidad.py",
    "utils/indicadores_severidad.json",
]

# --------------------------------------------------
# Verificar carpetas
# --------------------------------------------------

print("🔎 Verificando carpetas...\n")

for carpeta in CARPETAS:
    ruta = os.path.join(BASE_DIR, carpeta)

    if os.path.isdir(ruta):
        print(f"✔ carpeta OK → {carpeta}")
    else:
        print(f"❌ carpeta faltante → {carpeta}")

print("\n")

# --------------------------------------------------
# Verificar archivos
# --------------------------------------------------

print("🔎 Verificando archivos críticos...\n")

for archivo in ARCHIVOS:
    ruta = os.path.join(BASE_DIR, archivo)

    if os.path.isfile(ruta):
        print(f"✔ archivo OK → {archivo}")
    else:
        print(f"❌ archivo faltante → {archivo}")

print("\n")

# --------------------------------------------------
# Verificar imports principales
# --------------------------------------------------

print("🔎 Verificando imports...\n")

IMPORTS = [
    "services.router",
    "verticales.general.service",
    "utils.clasificador_severidad",
]

for modulo in IMPORTS:
    try:
        importlib.import_module(modulo)
        print(f"✔ import OK → {modulo}")

    except Exception as e:
        print(f"❌ error importando {modulo}")
        print(f"   {e}")

print("\n")

print("=========================================")
print("Diagnóstico finalizado")
print("=========================================\n")