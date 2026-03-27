"""
Proyecto: AI_Gpt_AUTOMATIZACION
Modulo: tools/convertidor_documentos.py
Version: 3.0

Descripcion
-----------
Convertidor universal de documentos a JSON.

Este módulo permite transformar contratos en diferentes formatos
a un JSON normalizado que luego será analizado por el sistema de IA.

Formatos soportados:
    • TXT
    • DOCX
    • ODT
    • PDF (texto)
    • PDF escaneado (OCR)

Flujo de funcionamiento
-----------------------
1. El usuario selecciona un archivo mediante ventana gráfica.
2. El sistema detecta el tipo de archivo.
3. Extrae el texto.
4. Si el PDF no tiene texto → aplica OCR.
5. Genera un JSON con el contenido del contrato.
6. El archivo JSON se guarda en la carpeta /input.

Estructura del JSON generado
----------------------------

{
    "texto": "contenido completo del contrato"
}

Este archivo luego será utilizado por el motor de análisis contractual.
"""

# ==========================================================
# IMPORTS
# ==========================================================

import json
import os
#  import tkinter as tk   se eliminaron para correr en Render
#  from tkinter import filedialog

from docx import Document
from odf.opendocument import load
from odf import text

from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import Image


# ==========================================================
# CONFIGURACIÓN OCR
# ==========================================================

# Ajustar si Tesseract está instalado en otra ruta
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ==========================================================
# SELECTOR DE ARCHIVO
# ==========================================================

def seleccionar_archivo():
    """
    Abre una ventana tipo explorador para seleccionar el contrato.

    Retorna
    -------
    str
        Ruta completa del archivo seleccionado.
    """

    root = tk.Tk()
    root.withdraw()

    return filedialog.askopenfilename(
        title="Seleccionar contrato a convertir",
        filetypes=[
            ("Archivos soportados", "*.txt *.docx *.odt *.pdf"),
            ("Todos los archivos", "*.*")
        ]
    )


# ==========================================================
# OCR PARA PDF ESCANEADO
# ==========================================================

def extraer_pdf_con_ocr(ruta_archivo):
    """
    Aplica OCR cuando el PDF no contiene texto.

    Parametros
    ----------
    ruta_archivo : str

    Retorna
    -------
    str
        Texto extraído mediante OCR.
    """

    print("⚠ PDF sin texto detectable. Aplicando OCR...")

    imagenes = convert_from_path(ruta_archivo)
    texto_total = []

    for i, img in enumerate(imagenes):

        print(f"Procesando página {i + 1}...")

        texto = pytesseract.image_to_string(img, lang="spa")

        texto_total.append(texto)

    return "\n".join(texto_total)


# ==========================================================
# EXTRACCIÓN DE TEXTO
# ==========================================================

def extraer_texto(ruta_archivo):
    """
    Detecta el tipo de archivo y extrae su texto.

    Parametros
    ----------
    ruta_archivo : str

    Retorna
    -------
    str
        Texto completo del documento.
    """

    extension = os.path.splitext(ruta_archivo)[1].lower()

    # ------------------------------------------------------
    # TXT
    # ------------------------------------------------------

    if extension == ".txt":

        with open(ruta_archivo, "r", encoding="utf-8") as f:
            return f.read()

    # ------------------------------------------------------
    # DOCX
    # ------------------------------------------------------

    elif extension == ".docx":

        doc = Document(ruta_archivo)

        return "\n".join(p.text for p in doc.paragraphs)

    # ------------------------------------------------------
    # ODT
    # ------------------------------------------------------

    elif extension == ".odt":

        doc = load(ruta_archivo)

        paragraphs = doc.getElementsByType(text.P)

        return "\n".join(
            p.firstChild.data if p.firstChild else ""
            for p in paragraphs
        )

    # ------------------------------------------------------
    # PDF
    # ------------------------------------------------------

    elif extension == ".pdf":

        reader = PdfReader(ruta_archivo)

        texto_paginas = []

        for page in reader.pages:

            texto = page.extract_text()

            if texto:
                texto_paginas.append(texto)

        texto_extraido = "\n".join(texto_paginas)

        # Si el texto es demasiado corto probablemente es escaneado
        if len(texto_extraido.strip()) < 50:

            return extraer_pdf_con_ocr(ruta_archivo)

        return texto_extraido

    # ------------------------------------------------------
    # FORMATO NO SOPORTADO
    # ------------------------------------------------------

    else:

        raise ValueError("Formato de archivo no soportado.")


# ==========================================================
# CONVERSIÓN A JSON
# ==========================================================

def convertir_a_json(ruta_archivo):
    """
    Convierte un documento a JSON.

    Parametros
    ----------
    ruta_archivo : str
        Ruta del documento original.

    Retorna
    -------
    str
        Ruta del JSON generado.
    """

    texto = extraer_texto(ruta_archivo)

    data = {
        "texto": texto
    }

    # ------------------------------------------------------
    # Crear carpeta /input si no existe
    # ------------------------------------------------------

    os.makedirs("input", exist_ok=True)

    nombre_archivo = os.path.basename(ruta_archivo)

    nombre_json = os.path.splitext(nombre_archivo)[0] + ".json"

    ruta_json = os.path.join("input", nombre_json)

    # ------------------------------------------------------
    # Guardar JSON
    # ------------------------------------------------------

    with open(ruta_json, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=2, ensure_ascii=False)

    return ruta_json


# ==========================================================
# EJECUCIÓN INTERACTIVA
# ==========================================================

if __name__ == "__main__":

    os.system("title Convertidor de Contratos a JSON")

    print("==========================================")
    print("  CONVERTIDOR DE CONTRATOS A JSON")
    print("==========================================\n")

    try:

        ruta = seleccionar_archivo()

        if ruta:

            archivo_generado = convertir_a_json(ruta)

            print("\n✅ Conversión exitosa.")
            print("Archivo generado en:")
            print(archivo_generado)

        else:

            print("No se seleccionó ningún archivo.")

    except Exception as e:

        print("\n❌ Ocurrió un error:")
        print(e)