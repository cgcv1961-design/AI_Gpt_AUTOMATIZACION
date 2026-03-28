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

import html
import os
import shutil
import traceback
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from services.pipeline_demo import procesar_contrato_desde_archivo


app = FastAPI(title="Analizador Contractual IA")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "demo_web" / "templates"
TEMP_UPLOADS_DIR = BASE_DIR / "temp_uploads"
OUTPUT_DIR = BASE_DIR / "output"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def html_debug_page(titulo: str, contenido: str) -> HTMLResponse:
    """
    Genera una página HTML simple para mostrar diagnósticos o errores
    sin depender de templates.
    """
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="utf-8">
            <title>{html.escape(titulo)}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 980px;
                    margin: 40px auto;
                    padding: 0 20px;
                    color: #222;
                    line-height: 1.5;
                }}
                h1 {{
                    color: #1f3b5c;
                }}
                .box {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 16px;
                    background: #fafafa;
                    margin-top: 20px;
                }}
                pre {{
                    white-space: pre-wrap;
                    word-break: break-word;
                    background: #111;
                    color: #f5f5f5;
                    padding: 12px;
                    border-radius: 6px;
                    overflow-x: auto;
                }}
                code {{
                    background: #f0f0f0;
                    padding: 2px 4px;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <h1>{html.escape(titulo)}</h1>
            <div class="box">
                {contenido}
            </div>
        </body>
        </html>
        """
    )


def obtener_tipo_contrato(salida: dict, resumen: dict) -> str:
    """
    Obtiene el tipo de contrato priorizando el JSON estructurado.
    Funciona tanto para GENERAL como para AUDIOVISUAL.
    """
    if not isinstance(salida, dict):
        return "-"

    nucleo = salida.get("nucleo_contractual", {}) or {}

    return (
        nucleo.get("tipo_contrato")
        or resumen.get("tipo_contrato")
        or "-"
    )


def obtener_cantidad_riesgos(salida: dict, resumen: dict) -> int:
    """
    Obtiene cantidad de riesgos desde scoring si existe.
    Si no, usa el resumen recibido.
    """
    if not isinstance(salida, dict):
        return resumen.get("cantidad_riesgos", 0)

    scoring = salida.get("scoring", {}) or {}
    metricas = scoring.get("metricas", {}) or {}

    return (
        metricas.get("cantidad_riesgos")
        or resumen.get("cantidad_riesgos")
        or 0
    )


def obtener_resumen_ejecutivo(salida: dict, resumen: dict) -> str:
    """
    Arma una interpretación ejecutiva útil para la UI.

    Prioridades:
    1. resumen.resumen_ejecutivo si ya viene plano
    2. informe_cliente.resumen_ejecutivo.vision_general
    3. informe_cliente.informe_detallado.conclusion_profesional
    """
    if isinstance(resumen, dict) and resumen.get("resumen_ejecutivo"):
        return resumen["resumen_ejecutivo"]

    if not isinstance(salida, dict):
        return "El análisis fue completado correctamente."

    informe_cliente = salida.get("informe_cliente", {}) or {}
    resumen_cliente = informe_cliente.get("resumen_ejecutivo", {}) or {}
    informe_detallado = informe_cliente.get("informe_detallado", {}) or {}

    return (
        resumen_cliente.get("vision_general")
        or informe_detallado.get("conclusion_profesional")
        or "El análisis fue completado correctamente."
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Pantalla inicial de la demo web.

    Si hay un problema con templates en Render, en lugar de devolver
    un 500 genérico, muestra una página de diagnóstico útil.
    """
    try:
        existe_templates = TEMPLATES_DIR.exists()
        existe_index = (TEMPLATES_DIR / "index.html").exists()
        existe_resultado = (TEMPLATES_DIR / "resultado.html").exists()

        if not existe_templates or not existe_index:
            return html_debug_page(
                "Diagnóstico de la demo web",
                f"""
                <p>No fue posible mostrar la pantalla inicial porque faltan archivos de plantilla.</p>
                <ul>
                    <li><b>BASE_DIR:</b> <code>{html.escape(str(BASE_DIR))}</code></li>
                    <li><b>TEMPLATES_DIR:</b> <code>{html.escape(str(TEMPLATES_DIR))}</code></li>
                    <li><b>Existe carpeta templates:</b> {existe_templates}</li>
                    <li><b>Existe index.html:</b> {existe_index}</li>
                    <li><b>Existe resultado.html:</b> {existe_resultado}</li>
                </ul>
                <p>Si esto aparece en Render, el problema está en la ruta efectiva del servidor o en el deploy del contenido estático.</p>
                """
            )

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={}
        )

    except Exception as e:
        return html_debug_page(
            "Error cargando la demo web",
            f"""
            <p>La ruta <code>/</code> falló al renderizar <code>index.html</code>.</p>
            <ul>
                <li><b>BASE_DIR:</b> <code>{html.escape(str(BASE_DIR))}</code></li>
                <li><b>TEMPLATES_DIR:</b> <code>{html.escape(str(TEMPLATES_DIR))}</code></li>
                <li><b>Existe carpeta templates:</b> {TEMPLATES_DIR.exists()}</li>
                <li><b>Existe index.html:</b> {(TEMPLATES_DIR / "index.html").exists()}</li>
                <li><b>Existe resultado.html:</b> {(TEMPLATES_DIR / "resultado.html").exists()}</li>
                <li><b>Error:</b> <code>{html.escape(str(e))}</code></li>
            </ul>
            <h3>Traceback</h3>
            <pre>{html.escape(traceback.format_exc())}</pre>
            """
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
        resumen = salida["resumen"]

        json_nombre = os.path.basename(salida["ruta_json_output"])
        word_nombre = os.path.basename(salida["ruta_word_output"])

        if not (TEMPLATES_DIR / "resultado.html").exists():
            return html_debug_page(
                "Análisis completado, pero falta la plantilla de resultado",
                f"""
                <p>El pipeline terminó, pero no se pudo renderizar <code>resultado.html</code>.</p>
                <ul>
                    <li><b>Vertical:</b> {html.escape(str(salida.get("vertical", "")))}</li>
                    <li><b>JSON:</b> <code>{html.escape(json_nombre)}</code></li>
                    <li><b>Word:</b> <code>{html.escape(word_nombre)}</code></li>
                </ul>
                <h3>Resumen</h3>
                <pre>{html.escape(str(resumen))}</pre>
                """
            )

        tipo_contrato = obtener_tipo_contrato(salida, resumen)
        cantidad_riesgos = obtener_cantidad_riesgos(salida, resumen)
        interpretacion_ejecutiva = obtener_resumen_ejecutivo(salida, resumen)

        return templates.TemplateResponse(
            request=request,
            name="resultado.html",
            context={
                "vertical": salida["vertical"],
                "resumen": resumen,
                "json_nombre": json_nombre,
                "word_nombre": word_nombre,
                "tipo_contrato": tipo_contrato,
                "cantidad_riesgos": cantidad_riesgos,
                "interpretacion_ejecutiva": interpretacion_ejecutiva,
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        return html_debug_page(
            "Error durante el análisis del contrato",
            f"""
            <p>La carga del archivo funcionó, pero el pipeline lanzó un error.</p>
            <ul>
                <li><b>Archivo recibido:</b> <code>{html.escape(nombre_seguro)}</code></li>
                <li><b>Ruta temporal:</b> <code>{html.escape(str(ruta_temporal))}</code></li>
                <li><b>TEMPLATES_DIR:</b> <code>{html.escape(str(TEMPLATES_DIR))}</code></li>
                <li><b>OUTPUT_DIR:</b> <code>{html.escape(str(OUTPUT_DIR))}</code></li>
                <li><b>Error:</b> <code>{html.escape(str(e))}</code></li>
            </ul>
            <h3>Traceback</h3>
            <pre>{html.escape(traceback.format_exc())}</pre>
            """
        )

    finally:
        if ruta_temporal.exists():
            ruta_temporal.unlink(missing_ok=True)


@app.get("/descargar/json/{nombre_archivo}")
def descargar_json(nombre_archivo: str):
    """
    Descarga el JSON final generado.
    """
    ruta = OUTPUT_DIR / nombre_archivo

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
    ruta = OUTPUT_DIR / nombre_archivo

    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Archivo Word no encontrado.")

    return FileResponse(
        path=str(ruta),
        filename=nombre_archivo,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )