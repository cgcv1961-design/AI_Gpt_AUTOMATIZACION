"""
AI_GPT_AUTOMATIZACION/api/api.py
--------------------------------

API y demo web mínima para análisis contractual autónomo.

Permite:
- abrir página web
- subir contrato
- ejecutar pipeline
- mostrar resumen
- descargar JSON y Word
"""

import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from services.pipeline_demo import procesar_contrato_desde_archivo

app = FastAPI(title="Analizador Contractual IA")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "demo_web" / "templates"
TEMP_UPLOADS_DIR = BASE_DIR / "temp_uploads"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)
os.makedirs(BASE_DIR / "output", exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Pantalla inicial de la demo web.
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.post("/analizar", response_class=HTMLResponse)
async def analizar(request: Request, archivo: UploadFile = File(...)):
    """
    Recibe el archivo subido, ejecuta el pipeline
    y muestra el resultado resumido.
    """

    if not archivo.filename:
        raise HTTPException(status_code=400, detail="No se recibió archivo.")

    nombre_seguro = os.path.basename(archivo.filename)
    ruta_temporal = TEMP_UPLOADS_DIR / nombre_seguro

    with open(ruta_temporal, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)

    try:
        salida = procesar_contrato_desde_archivo(str(ruta_temporal))
    finally:
        if ruta_temporal.exists():
            ruta_temporal.unlink(missing_ok=True)

    resumen = salida["resumen"]

    json_nombre = os.path.basename(salida["ruta_json_output"])
    word_nombre = os.path.basename(salida["ruta_word_output"])

    return templates.TemplateResponse(
        "resultado.html",
        {
            "request": request,
            "vertical": salida["vertical"],
            "resumen": resumen,
            "json_nombre": json_nombre,
            "word_nombre": word_nombre,
        }
    )


@app.get("/descargar/json/{nombre_archivo}")
def descargar_json(nombre_archivo: str):
    """
    Descarga el JSON final generado.
    """
    ruta = BASE_DIR / "output" / nombre_archivo

    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Archivo JSON no encontrado.")

    return FileResponse(
        path=str(ruta),
        filename=nombre_archivo,
        media_type="application/json"
    )


@app.get("/descargar/word/{nombre_archivo}")
def descargar_word(nombre_archivo: str):
    """
    Descarga el Word final generado.
    """
    ruta = BASE_DIR / "output" / nombre_archivo

    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Archivo Word no encontrado.")

    return FileResponse(
        path=str(ruta),
        filename=nombre_archivo,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )