"""
AI_GPT_AUTOMATIZACION/api/api.py
--------------------------------

API y demo web mínima para análisis contractual autónomo.

OBJETIVO DE ESTA VERSIÓN
------------------------
Alinear la UI con la metadata de presentación generada por main.py,
evitando que lleguen a pantalla representaciones crudas de dicts.
"""

import html
import json
import os
import shutil
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Form
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


def cargar_json_generado(ruta_json_output: str) -> dict:
    try:
        with open(ruta_json_output, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def valor_no_vacio(*valores, default=None):
    for v in valores:
        if v not in (None, "", [], {}):
            return v
    return default


def texto_limpio(valor: Any, default: str = "-") -> str:
    if valor in (None, "", [], {}):
        return default
    return str(valor).strip()


def lista_desde_valor(valor: Any) -> List[Any]:
    if valor in (None, "", [], {}):
        return []

    if isinstance(valor, list):
        return [x for x in valor if x not in (None, "", [], {})]

    if isinstance(valor, dict):
        return [valor]

    return [valor]


def formatear_parte_visible(parte: Any) -> str:
    """
    Fallback defensivo para UI.
    Si llega un dict, lo convierte en texto visible.
    """
    if isinstance(parte, dict):
        nombre = texto_limpio(parte.get("nombre") or parte.get("parte") or parte.get("name"), default="-")
        rol = texto_limpio(parte.get("rol") or parte.get("tipo") or parte.get("role"), default="")
        if nombre != "-" and rol:
            return f"{nombre} ({rol})"
        if nombre != "-":
            return nombre
        return texto_limpio(rol, default="-")

    return texto_limpio(parte, default="-")


def normalizar_perspectiva_entrada(valor: str) -> str:
    texto = (valor or "").strip().lower()

    mapa = {
        "1": "proveedor",
        "2": "cliente",
        "proveedor": "proveedor",
        "cliente": "cliente",
    }

    return mapa.get(texto, "proveedor")


def normalizar_pais_entrada(valor: str) -> str:
    texto = (valor or "").strip().lower()

    mapa = {
        "1": "argentina",
        "2": "uruguay",
        "3": "italia",
        "4": "espana",
        "5": "internacional",
        "argentina": "argentina",
        "uruguay": "uruguay",
        "italia": "italia",
        "espana": "espana",
        "españa": "espana",
        "internacional": "internacional",
        "otro": "internacional",
        "internacional / otro": "internacional",
    }

    return mapa.get(texto, "internacional")


def obtener_tipo_contrato(data: dict, resumen: dict) -> str:
    nucleo = data.get("nucleo_contractual", {}) or {}
    return texto_limpio(nucleo.get("tipo_contrato") or resumen.get("tipo_contrato"), default="-")


def obtener_cantidad_riesgos(data: dict, resumen: dict) -> int:
    scoring = data.get("scoring", {}) or {}
    metricas = scoring.get("metricas", {}) or {}
    return metricas.get("cantidad_riesgos") or resumen.get("cantidad_riesgos") or 0


def obtener_interpretacion_ejecutiva(data: dict, resumen: dict) -> str:
    informe_cliente = data.get("informe_cliente", {}) or {}
    resumen_ejecutivo = informe_cliente.get("resumen_ejecutivo", {}) or {}
    informe_detallado = informe_cliente.get("informe_detallado", {}) or {}

    return (
        resumen.get("resumen_ejecutivo")
        or resumen_ejecutivo.get("vision_general")
        or informe_detallado.get("conclusion_profesional")
        or "El análisis fue completado correctamente."
    )


def obtener_score_total(data: dict, resumen: dict) -> float:
    scoring = data.get("scoring", {}) or {}
    valor = scoring.get("score_total") or resumen.get("score_total") or 0

    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def obtener_nivel_riesgo(data: dict, resumen: dict) -> str:
    scoring = data.get("scoring", {}) or {}
    return texto_limpio(scoring.get("nivel_riesgo") or resumen.get("nivel_riesgo"), default="-")


def obtener_pais_referencia(data: dict, resumen: dict) -> str:
    metadata = data.get("metadata_sistema", {}) or {}
    return texto_limpio(metadata.get("pais_referencia") or resumen.get("pais_referencia"), default="internacional")


def extraer_partes_desde_json(data: Dict[str, Any], resumen: Dict[str, Any]) -> List[str]:
    nucleo = data.get("nucleo_contractual", {}) or {}

    candidatos_lista = [
        data.get("partes"),
        resumen.get("partes"),
        nucleo.get("partes"),
        nucleo.get("partes_involucradas"),
        nucleo.get("intervinientes"),
        nucleo.get("sujetos"),
    ]

    for candidato in candidatos_lista:
        partes = lista_desde_valor(candidato)
        if partes:
            return [formatear_parte_visible(x) for x in partes]

    parte_a = valor_no_vacio(
        nucleo.get("parte_contratante"),
        nucleo.get("parte_1"),
        nucleo.get("locador"),
        nucleo.get("contratante"),
        resumen.get("parte_1"),
        default=None,
    )

    parte_b = valor_no_vacio(
        nucleo.get("parte_contraparte"),
        nucleo.get("parte_2"),
        nucleo.get("locatario"),
        nucleo.get("contratado"),
        resumen.get("parte_2"),
        default=None,
    )

    partes = []
    if parte_a:
        partes.append(formatear_parte_visible(parte_a))
    if parte_b:
        partes.append(formatear_parte_visible(parte_b))

    return partes


def obtener_roles_partes(partes: List[str]) -> Tuple[str, str]:
    parte_cliente = partes[0] if len(partes) > 0 else ""
    parte_proveedor = partes[1] if len(partes) > 1 else ""
    return parte_cliente, parte_proveedor


def interpretar_score_desde_nivel(nivel_riesgo: str) -> str:
    nivel = (nivel_riesgo or "").strip().lower()

    if nivel == "bajo":
        return "Riesgo bajo: el contrato presenta una exposición relativamente contenida, aunque igualmente conviene revisar sus cláusulas relevantes antes de firmar."
    elif nivel == "medio":
        return "Riesgo medio: existen cláusulas u obligaciones que requieren revisión antes de firmar."
    elif nivel == "medio-alto":
        return "Riesgo medio-alto: el contrato presenta una exposición importante y merece una revisión cuidadosa antes de su firma o negociación."
    elif nivel == "alto":
        return "Riesgo alto: el contrato puede resultar significativamente desfavorable y exige revisión prioritaria."

    return "El score es una medida numérica del riesgo total del contrato. Cuanto mayor es el valor, mayor es la exposición al riesgo."


def obtener_metadata_presentacion(data: Dict[str, Any]) -> Dict[str, Any]:
    metadata = data.get("metadata_sistema", {}) or {}
    presentacion = metadata.get("metadata_presentacion", {}) or {}

    partes_con_rol = presentacion.get("partes_con_rol", [])
    if not isinstance(partes_con_rol, list):
        partes_con_rol = []

    return {
        "parte_analizada_label": texto_limpio(
            presentacion.get("parte_analizada_label"),
            default="-"
        ),
        "rol_contractual_detectado": texto_limpio(
            presentacion.get("rol_contractual_detectado"),
            default="-"
        ),
        "nombre_parte_analizada": texto_limpio(
            presentacion.get("nombre_parte_analizada"),
            default="-"
        ),
        "partes_con_rol": [formatear_parte_visible(x) for x in partes_con_rol if formatear_parte_visible(x) != "-"],
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
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
                <li><b>Error:</b> <code>{html.escape(str(e))}</code></li>
            </ul>
            <h3>Traceback</h3>
            <pre>{html.escape(traceback.format_exc())}</pre>
            """
        )


@app.post("/analizar", response_class=HTMLResponse)
async def analizar(
    request: Request,
    archivo: UploadFile = File(...),
    perspectiva: str = Form("proveedor"),
    pais_referencia: str = Form("internacional")
):
    if not archivo.filename:
        raise HTTPException(status_code=400, detail="No se recibió archivo.")

    perspectiva_normalizada = normalizar_perspectiva_entrada(perspectiva)
    pais_referencia_normalizado = normalizar_pais_entrada(pais_referencia)

    nombre_seguro = os.path.basename(archivo.filename)
    ruta_temporal = TEMP_UPLOADS_DIR / nombre_seguro

    with open(ruta_temporal, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)

    try:
        salida = procesar_contrato_desde_archivo(
            str(ruta_temporal),
            perspectiva=perspectiva_normalizada,
            pais_referencia=pais_referencia_normalizado
        )
        resumen = salida.get("resumen", {}) or {}

        json_nombre = os.path.basename(salida["ruta_json_output"])
        word_nombre = os.path.basename(salida["ruta_word_output"])

        if not (TEMPLATES_DIR / "resultado.html").exists():
            return html_debug_page(
                "Análisis completado, pero falta la plantilla de resultado",
                f"""
                <p>El pipeline terminó, pero no se pudo renderizar <code>resultado.html</code>.</p>
                <ul>
                    <li><b>Perspectiva original recibida:</b> {html.escape(str(perspectiva))}</li>
                    <li><b>Perspectiva normalizada:</b> {html.escape(str(perspectiva_normalizada))}</li>
                    <li><b>País original recibido:</b> {html.escape(str(pais_referencia))}</li>
                    <li><b>País normalizado:</b> {html.escape(str(pais_referencia_normalizado))}</li>
                    <li><b>JSON:</b> <code>{html.escape(json_nombre)}</code></li>
                    <li><b>Word:</b> <code>{html.escape(word_nombre)}</code></li>
                </ul>
                """
            )

        data = cargar_json_generado(salida["ruta_json_output"])

        tipo_contrato = obtener_tipo_contrato(data, resumen)
        cantidad_riesgos = obtener_cantidad_riesgos(data, resumen)
        interpretacion_ejecutiva = obtener_interpretacion_ejecutiva(data, resumen)
        score_total = obtener_score_total(data, resumen)
        nivel_riesgo = obtener_nivel_riesgo(data, resumen)
        pais_referencia_final = obtener_pais_referencia(data, resumen)

        partes = extraer_partes_desde_json(data, resumen)
        parte_cliente, parte_proveedor = obtener_roles_partes(partes)

        interpretacion_score = interpretar_score_desde_nivel(nivel_riesgo)
        metadata_presentacion = obtener_metadata_presentacion(data)

        return templates.TemplateResponse(
            request=request,
            name="resultado.html",
            context={
                "json_nombre": json_nombre,
                "word_nombre": word_nombre,
                "tipo_contrato": tipo_contrato,
                "cantidad_riesgos": cantidad_riesgos,
                "interpretacion_ejecutiva": interpretacion_ejecutiva,
                "score_total": score_total,
                "nivel_riesgo": nivel_riesgo,
                "interpretacion_score": interpretacion_score,
                "partes": partes,
                "partes_con_rol": metadata_presentacion.get("partes_con_rol", []),
                "parte_cliente": parte_cliente,
                "parte_proveedor": parte_proveedor,
                "perspectiva": perspectiva_normalizada,
                "pais_referencia": pais_referencia_final,
                "parte_analizada_label": metadata_presentacion.get("parte_analizada_label", "-"),
                "rol_contractual_detectado": metadata_presentacion.get("rol_contractual_detectado", "-"),
                "nombre_parte_analizada": metadata_presentacion.get("nombre_parte_analizada", "-"),
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
                <li><b>Perspectiva original recibida:</b> <code>{html.escape(str(perspectiva))}</code></li>
                <li><b>Perspectiva normalizada:</b> <code>{html.escape(str(perspectiva_normalizada))}</code></li>
                <li><b>País original recibido:</b> <code>{html.escape(str(pais_referencia))}</code></li>
                <li><b>País normalizado:</b> <code>{html.escape(str(pais_referencia_normalizado))}</code></li>
                <li><b>Ruta temporal:</b> <code>{html.escape(str(ruta_temporal))}</code></li>
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
    ruta = OUTPUT_DIR / nombre_archivo

    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Archivo Word no encontrado.")

    return FileResponse(
        path=str(ruta),
        filename=nombre_archivo,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )