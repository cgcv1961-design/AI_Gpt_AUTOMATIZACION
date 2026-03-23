"""
mapear_proyecto.py

Escanea todo el proyecto AI_Gpt_AUTOMATIZACION
y muestra la estructura real de carpetas y archivos.

Sirve para:
- detectar archivos duplicados
- verificar organización
- documentar el sistema
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def imprimir_arbol(ruta, nivel=0):

    elementos = sorted(os.listdir(ruta))

    for elemento in elementos:

        ruta_completa = os.path.join(ruta, elemento)

        indent = "│   " * nivel + "├── "

        if os.path.isdir(ruta_completa):

            print(f"{indent}{elemento}/")

            imprimir_arbol(ruta_completa, nivel + 1)

        else:

            print(f"{indent}{elemento}")


def main():

    print("")
    print("======================================")
    print("  MAPA DEL PROYECTO AI_GPT_AUTOMATIZACION")
    print("======================================")
    print("")

    imprimir_arbol(BASE_DIR)

    print("")
    print("✔ Escaneo finalizado")
    print("")


if __name__ == "__main__":
    main()