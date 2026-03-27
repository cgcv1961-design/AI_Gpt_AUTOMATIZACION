"""
Proyecto: AI_Gpt_AUTOMATIZACION
Modulo: tools/convertidor_documentos.py
Version: 4.0

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
    • PDF escaneado (OCR, si el entorno lo permite)

Flujo de funcionamiento
-----------------------
1. Opcionalmente el usuario selecciona un archivo mediante ventana gráfica.
2. El sistema detecta el tipo de archivo.
3. Extrae el texto.
4. Si el PDF no tiene texto, intenta OCR solo si las dependencias están disponibles.
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

from docx import Document
from odf.opendocument import load
from odf import text
from PyPDF2 import PdfReader

# ----------------------------------------------------------
# IMPORTS OPCIONALES PARA ENTORNOS LOCALES
# En Render/servidor pueden no estar disponibles.
# ----------------------------------------------------------

try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_DISPONIBLE = True
except Exception:
    tk = None
    filedialog = None
    TKINTER_DISPONIBLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_DISPONIBLE = True
except Exception:
    convert_from_path = None
    PDF2IMAGE_DISPONIBLE = False

try:
    import pytesseract
    PYTESSERACT_DISPONIBLE = True
except Exception:
    pytesseract = None
    PYTESSERACT_DISPONIBLE = False

try:
    from PIL import Image  # noqa: F401
    PIL_DISPONIBLE = True
except Exception:
    PIL_DISPONIBLE = False


# ==========================================================
# CONFIGURACIÓN OCR
# ==========================================================

def configurar_tesseract():
    """
    Configura la ruta de Tesseract solo si existe en Windows local.

    En servidores como Render normalmente no existirá, por lo que
    no se fuerza ninguna ruta para evitar errores.
    """
    if not PYTESSERACT_DISPONIBLE:
        return

    ruta_windows = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if os.path.exists(ruta_windows):
        pytesseract.pytesseract.tesseract_cmd = ruta_windows


configurar_tesseract()


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

    Lanza
    -----
    RuntimeError
        Si tkinter no está disponible en el entorno actual.
    """
    if not TKINTER_DISPONIBLE:
        raise RuntimeError(
            "La selección gráfica de archivos no está disponible en este entorno. "
            "Use una ruta de archivo directa o cargue el archivo mediante la API."
        )

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

def ocr_disponible():
    """
    Indica si el entorno tiene lo necesario para intentar OCR.
    """
    return PDF2IMAGE_DISPONIBLE and PYTESSERACT_DISPONIBLE and PIL_DISPONIBLE


def extraer_pdf_con_ocr(ruta_archivo):
    """
    Aplica OCR cuando el PDF no contiene texto, si el entorno lo permite.

    Parametros
    ----------
    ruta_archivo : str

    Retorna
    -------
    str
        Texto extraído mediante OCR.

    Lanza
    -----
    RuntimeError
        Si OCR no está disponible en el entorno actual.
    """
    if not ocr_disponible():
        raise RuntimeError(
            "El PDF parece ser escaneado, pero OCR no está disponible en este entorno. "
            "Faltan dependencias opcionales como pdf2image, pytesseract o PIL, "
            "o bien herramientas del sistema necesarias para OCR."
        )

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

def extraer_texto_txt(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        return f.read()


def extraer_texto_docx(ruta_archivo):
    doc = Document(ruta_archivo)
    return "\n".join(p.text for p in doc.paragraphs)


def extraer_texto_odt(ruta_archivo):
    doc = load(ruta_archivo)
    paragraphs = doc.getElementsByType(text.P)

    return "\n".join(
        p.firstChild.data if p.firstChild else ""
        for p in paragraphs
    )


def extraer_texto_pdf(ruta_archivo):
    """
    Extrae texto de un PDF.

    Si el PDF no tiene texto embebido, intenta OCR solamente si está disponible.
    Si OCR no está disponible, devuelve el texto detectado (aunque sea vacío o escaso)
    y deja trazabilidad por consola.
    """
    reader = PdfReader(ruta_archivo)
    texto_paginas = []

    for page in reader.pages:
        texto = page.extract_text()
        if texto:
            texto_paginas.append(texto)

    texto_extraido = "\n".join(texto_paginas).strip()

    # Si el texto es suficiente, se devuelve tal cual.
    if len(texto_extraido) >= 50:
        return texto_extraido

    # Si el texto es corto o casi vacío, podría ser un PDF escaneado.
    print("⚠ PDF con poco o ningún texto embebido detectado.")

    if ocr_disponible():
        try:
            return extraer_pdf_con_ocr(ruta_archivo)
        except Exception as e:
            print(f"⚠ No fue posible aplicar OCR: {e}")

    # En servidor, preferimos no romper toda la API por esto.
    # Devolvemos lo poco que se haya podido extraer.
    return texto_extraido

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

    if extension == ".txt":
        return extraer_texto_txt(ruta_archivo)

    elif extension == ".docx":
        return extraer_texto_docx(ruta_archivo)

    elif extension == ".odt":
        return extraer_texto_odt(ruta_archivo)

    elif extension == ".pdf":
        return extraer_texto_pdf(ruta_archivo)

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

    os.makedirs("input", exist_ok=True)

    nombre_archivo = os.path.basename(ruta_archivo)
    nombre_json = os.path.splitext(nombre_archivo)[0] + ".json"
    ruta_json = os.path.join("input", nombre_json)

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
