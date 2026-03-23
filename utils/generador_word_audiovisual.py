"""
AI_GPT_AUTOMATIZACION/utils/generador_word_audiovisual.py
---------------------------------------------------------

Generador de reporte Word para la vertical AUDIOVISUAL.

OBJETIVO
--------
Transformar el JSON final normalizado del análisis audiovisual en un
documento Word legible, claro y profesional.

PRINCIPIO
---------
El Word sale EXCLUSIVAMENTE del JSON.
No debe construir un segundo dictamen alternativo.

ESTRUCTURA ESPERADA DEL JSON
----------------------------
{
  "nucleo_contractual": {...},
  "analisis_sectorial": {
      "riesgos_sectoriales": [...],
      "nivel_confianza_analisis": {...}
  },
  "informe_cliente": {
      "resumen_ejecutivo": {...},
      "informe_detallado": {...},
      "recomendacion_profesional": "..."
  },
  "scoring": {...},
  "metadata_sistema": {...}
}
"""

import os
from typing import Any, Dict, List
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING


def generar_word_audiovisual(resultado: dict, ruta_json: str) -> str:
    """
    Genera el reporte Word para la vertical AUDIOVISUAL.

    Parámetros
    ----------
    resultado : dict
        JSON final normalizado del análisis audiovisual.
    ruta_json : str
        Ruta del JSON guardado. Se usa para derivar el nombre del .docx.

    Retorna
    -------
    str
        Ruta del archivo Word generado.
    """

    doc = Document()

    estilo_normal = doc.styles["Normal"]
    estilo_normal.font.name = "Calibri"
    estilo_normal.font.size = Pt(12)

    def compactar_parrafo(parrafo, indent=0):
        pf = parrafo.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        if indent:
            pf.left_indent = Pt(indent)

    def heading_compacto(texto, level=1):
        p = doc.add_heading(texto, level=level)
        compactar_parrafo(p)
        return p

    def parrafo_compacto(texto="", bold=False, indent=0):
        p = doc.add_paragraph()
        compactar_parrafo(p, indent=indent)
        run = p.add_run("" if texto is None else str(texto))
        run.bold = bold
        return p

    def parrafo_bulleted(texto="", indent=0):
        p = doc.add_paragraph(style="List Bullet")
        compactar_parrafo(p, indent=indent)
        p.add_run("" if texto is None else str(texto))
        return p

    def valor_no_vacio(*valores, default="-"):
        for v in valores:
            if v not in (None, "", [], {}):
                return v
        return default

    def texto_limpio(valor, default="-") -> str:
        if valor in (None, "", [], {}):
            return default
        return str(valor).strip()

    def lista_desde_valor(valor) -> List[str]:
        if valor in (None, "", [], {}):
            return []
        if isinstance(valor, list):
            return [str(x).strip() for x in valor if x not in (None, "", [], {})]
        if isinstance(valor, dict):
            return [f"{k}: {v}" for k, v in valor.items() if v not in (None, "", [], {})]
        return [str(valor).strip()]

    def formatear_duracion_audiovisual(nucleo: Dict[str, Any]) -> Dict[str, str]:
        """
        Devuelve:
        - breve
        - detalle
        """
        duracion_texto = texto_limpio(
            valor_no_vacio(
                nucleo.get("duracion_texto"),
                nucleo.get("plazo_texto"),
                default="-"
            ),
            default="-"
        )

        duracion_dias = valor_no_vacio(nucleo.get("duracion_dias"), default=None)
        unidad_duracion = texto_limpio(
            valor_no_vacio(
                nucleo.get("unidad_duracion"),
                nucleo.get("duracion_unidad"),
                default="-"
            ),
            default="-"
        )

        duracion_meses = valor_no_vacio(nucleo.get("duracion_meses"), default=None)
        duracion_generica = texto_limpio(nucleo.get("duracion"), default="-")

        if duracion_texto != "-":
            if duracion_dias not in (None, "", [], {}) and unidad_duracion != "-":
                return {"breve": f"{duracion_dias} {unidad_duracion}", "detalle": duracion_texto}
            if duracion_meses not in (None, "", [], {}):
                return {"breve": f"{duracion_meses} meses", "detalle": duracion_texto}
            return {"breve": "ver detalle abajo", "detalle": duracion_texto}

        if duracion_dias not in (None, "", [], {}) and unidad_duracion != "-":
            return {"breve": f"{duracion_dias} {unidad_duracion}", "detalle": ""}

        if duracion_meses not in (None, "", [], {}):
            return {"breve": f"{duracion_meses} meses", "detalle": ""}

        if duracion_generica != "-":
            return {"breve": duracion_generica, "detalle": ""}

        return {"breve": "-", "detalle": ""}

    def formatear_precio(nucleo: Dict[str, Any]) -> str:
        precio_total = texto_limpio(
            valor_no_vacio(
                nucleo.get("precio_total"),
                nucleo.get("precio"),
                nucleo.get("monto"),
                default="-"
            ),
            default="-"
        )

        moneda = texto_limpio(
            valor_no_vacio(
                nucleo.get("moneda"),
                nucleo.get("divisa"),
                default="-"
            ),
            default="-"
        )

        periodicidad = texto_limpio(
            valor_no_vacio(
                nucleo.get("periodicidad_precio"),
                nucleo.get("precio_periodicidad"),
                nucleo.get("unidad_precio"),
                default="-"
            ),
            default="-"
        )

        if precio_total == "-" and moneda == "-":
            return "-"

        if precio_total == "-":
            base = moneda
        elif moneda == "-":
            base = precio_total
        else:
            base = f"{precio_total} {moneda}"

        if periodicidad == "-":
            return base

        return f"{base} ({periodicidad})"

    def construir_distribucion_severidad(metricas: Dict[str, Any]) -> str:
        bloques = [
            ("altos", metricas.get("riesgos_altos", 0)),
            ("medio-altos", metricas.get("riesgos_media_altos", 0)),
            ("medios", metricas.get("riesgos_medios", 0)),
            ("bajos", metricas.get("riesgos_bajos", 0)),
        ]

        partes = []

        for nombre, valor in bloques:
            try:
                n = int(float(valor))
            except (TypeError, ValueError):
                continue
            if n > 0:
                partes.append(f"{nombre} {n}")

        return ", ".join(partes) if partes else "sin observaciones clasificadas"

    # =====================================================
    # DATOS
    # =====================================================

    nucleo = resultado.get("nucleo_contractual", {}) or {}
    analisis_sectorial = resultado.get("analisis_sectorial", {}) or {}
    informe_cliente = resultado.get("informe_cliente", {}) or {}
    metadata = resultado.get("metadata_sistema", {}) or {}
    scoring = resultado.get("scoring", {}) or {}

    resumen = informe_cliente.get("resumen_ejecutivo", {}) or {}
    detalle = informe_cliente.get("informe_detallado", {}) or {}
    confianza = analisis_sectorial.get("nivel_confianza_analisis", {}) or {}

    tipo_contrato = texto_limpio(
        valor_no_vacio(
            nucleo.get("tipo_contrato"),
            nucleo.get("clase_contrato"),
            nucleo.get("naturaleza_contrato"),
            default="-"
        ),
        default="-"
    )

    partes = lista_desde_valor(nucleo.get("partes"))
    duracion = formatear_duracion_audiovisual(nucleo)
    precio = formatear_precio(nucleo)

    riesgos = analisis_sectorial.get("riesgos_sectoriales", [])
    if not isinstance(riesgos, list):
        riesgos = []

    score_total = texto_limpio(scoring.get("score_total"), default="-")
    nivel_riesgo = texto_limpio(scoring.get("nivel_riesgo"), default="-")
    version_scoring = texto_limpio(scoring.get("version_scoring"), default="-")
    metricas = scoring.get("metricas", {}) or {}

    # =====================================================
    # TÍTULO
    # =====================================================

    heading_compacto("Reporte de Análisis Contractual Audiovisual", level=0)

    # =====================================================
    # INFORMACIÓN GENERAL
    # =====================================================

    heading_compacto("Información General", level=1)
    parrafo_compacto(f"Tipo de contrato: {tipo_contrato}")
    parrafo_compacto(f"Duración: {duracion['breve']}")
    if duracion["detalle"]:
        parrafo_compacto("Detalle del plazo:", bold=True)
        parrafo_compacto(duracion["detalle"], indent=18)
    parrafo_compacto(f"Precio total: {precio}")

    # =====================================================
    # PARTES
    # =====================================================

    heading_compacto("Partes del contrato", level=1)
    if not partes:
        parrafo_compacto("No se pudieron identificar las partes.")
    else:
        for parte in partes:
            parrafo_compacto(parte)

    # =====================================================
    # EVALUACIÓN GENERAL
    # =====================================================

    heading_compacto("Evaluación General del Contrato", level=1)
    parrafo_compacto(f"Score total: {score_total}")
    parrafo_compacto(f"Nivel de riesgo: {nivel_riesgo}")

    cantidad_riesgos = metricas.get("cantidad_riesgos", "-")
    if cantidad_riesgos != "-":
        parrafo_compacto(f"Cantidad de observaciones: {cantidad_riesgos}")

    parrafo_compacto(f"Distribución por severidad: {construir_distribucion_severidad(metricas)}")

    nivel_riesgo_global = texto_limpio(resumen.get("nivel_riesgo_global"), default="-")
    if nivel_riesgo_global != "-":
        parrafo_compacto(f"Nivel de riesgo global informado: {nivel_riesgo_global}")

    # =====================================================
    # RESUMEN EJECUTIVO
    # =====================================================

    heading_compacto("Resumen Ejecutivo para Cliente", level=1)
    vision_general = texto_limpio(resumen.get("vision_general"), default="-")
    if vision_general != "-":
        parrafo_compacto(vision_general)
    else:
        parrafo_compacto("No se generó resumen ejecutivo.")

    # =====================================================
    # PUNTOS CRÍTICOS
    # =====================================================

    heading_compacto("Puntos Críticos Principales", level=1)
    puntos_criticos = lista_desde_valor(resumen.get("puntos_criticos"))
    if puntos_criticos:
        for punto in puntos_criticos:
            parrafo_bulleted(punto)
    else:
        parrafo_compacto("No se reportaron puntos críticos principales.")

    # =====================================================
    # HALLAZGOS
    # =====================================================

    heading_compacto("Hallazgos Principales", level=1)
    hallazgos = lista_desde_valor(detalle.get("hallazgos_principales"))
    if hallazgos:
        for hallazgo in hallazgos:
            parrafo_bulleted(hallazgo)
    else:
        parrafo_compacto("No se reportaron hallazgos principales.")

    # =====================================================
    # IMPLICANCIAS
    # =====================================================

    heading_compacto("Implicancias Estratégicas a Mediano Plazo", level=1)
    implicancias = lista_desde_valor(detalle.get("implicancias_estrategicas_mediano_plazo"))
    if implicancias:
        for item in implicancias:
            parrafo_bulleted(item)
    else:
        parrafo_compacto("No se reportaron implicancias estratégicas específicas.")

    # =====================================================
    # RECOMENDACIÓN
    # =====================================================

    heading_compacto("Recomendación Profesional", level=1)
    recomendacion = texto_limpio(informe_cliente.get("recomendacion_profesional"), default="-")
    if recomendacion != "-":
        parrafo_compacto(recomendacion)
    else:
        parrafo_compacto("No se generó recomendación profesional.")

    # =====================================================
    # PREGUNTAS
    # =====================================================

    heading_compacto("Preguntas Clave Antes de Firmar", level=1)
    preguntas = lista_desde_valor(detalle.get("preguntas_clave_antes_de_firmar"))
    if preguntas:
        for pregunta in preguntas:
            parrafo_bulleted(pregunta)
    else:
        parrafo_compacto("No se reportaron preguntas clave antes de firmar.")

    # =====================================================
    # CONCLUSIÓN
    # =====================================================

    heading_compacto("Conclusión Profesional", level=1)
    conclusion = texto_limpio(detalle.get("conclusion_profesional"), default="-")
    if conclusion != "-":
        parrafo_compacto(conclusion)
    else:
        parrafo_compacto("No se reportó conclusión profesional.")

    # =====================================================
    # NIVEL DE CONFIANZA
    # =====================================================

    heading_compacto("Nivel de Confianza del Análisis", level=1)
    parrafo_compacto(f"Nivel general: {texto_limpio(confianza.get('general'), default='-')}")
    fundamento_confianza = texto_limpio(confianza.get("fundamento"), default="-")
    if fundamento_confianza != "-":
        parrafo_compacto("Fundamento:", bold=True)
        parrafo_compacto(fundamento_confianza, indent=18)

    # =====================================================
    # SISTEMA
    # =====================================================

    heading_compacto("Sistema de Análisis Utilizado", level=1)
    parrafo_compacto("Motor de Inteligencia Artificial", bold=True)
    parrafo_compacto(f"Modelo utilizado: {texto_limpio(metadata.get('modelo_utilizado'), default='-')}")
    parrafo_compacto(f"Perfil de análisis: {texto_limpio(metadata.get('perfil_canonico'), default='-')}")

    parrafo_compacto("Motor Jurídico-Contractual", bold=True)
    parrafo_compacto(f"Versión del motor: {texto_limpio(metadata.get('version_servicio'), default='-')}")
    parrafo_compacto(f"Versión del scoring: {version_scoring}")

    # =====================================================
    # SCORING
    # =====================================================

    heading_compacto("Resultados del Scoring", level=1)

    tabla_scoring = doc.add_table(rows=1, cols=2)
    tabla_scoring.style = "Table Grid"

    encabezado = tabla_scoring.rows[0].cells
    encabezado[0].text = "Indicador"
    encabezado[1].text = "Valor"

    filas = [
        ("Score total", str(score_total)),
        ("Nivel de riesgo", str(nivel_riesgo)),
        ("Cantidad de riesgos", str(metricas.get("cantidad_riesgos", "-"))),
    ]

    metricas_dinamicas = [
        ("Riesgos altos", metricas.get("riesgos_altos", 0)),
        ("Riesgos medio-altos", metricas.get("riesgos_media_altos", 0)),
        ("Riesgos medios", metricas.get("riesgos_medios", 0)),
        ("Riesgos bajos", metricas.get("riesgos_bajos", 0)),
    ]

    for nombre, valor in metricas_dinamicas:
        try:
            n = int(float(valor))
        except (TypeError, ValueError):
            continue
        if n > 0:
            filas.append((nombre, str(n)))

    for indicador, valor in filas:
        row = tabla_scoring.add_row().cells
        row[0].text = indicador
        row[1].text = valor

    # =====================================================
    # ANEXO DE RIESGOS
    # =====================================================

    heading_compacto("Anexo Técnico - Detalle Ampliado de Riesgos", level=1)

    if not riesgos:
        parrafo_compacto("No se detectaron riesgos sectoriales.")
    else:
        for i, r in enumerate(riesgos, start=1):
            severidad = texto_limpio(r.get("severidad"), default="-").capitalize()
            impacto = texto_limpio(r.get("impacto"), default="-")
            descripcion = texto_limpio(r.get("descripcion"), default="-")
            recomendacion_riesgo = texto_limpio(r.get("recomendacion"), default="-")

            parrafo_compacto(f"Riesgo {i}", bold=True)

            if severidad != "-":
                parrafo_compacto(f"Severidad: {severidad}")

            if impacto != "-":
                parrafo_compacto(f"Impacto: {impacto}")

            parrafo_compacto("Descripción:", bold=True)
            parrafo_compacto(descripcion, indent=18)

            if recomendacion_riesgo != "-":
                parrafo_compacto("Sugerencia / mitigación:", bold=True)
                parrafo_compacto(recomendacion_riesgo, indent=18)

    # =====================================================
    # CIERRE
    # =====================================================

    parrafo_compacto(
        "Este informe fue generado mediante un sistema automatizado de análisis contractual "
        "basado en inteligencia artificial y un motor de evaluación jurídica propietario."
    )

    # =====================================================
    # GUARDADO
    # =====================================================

    os.makedirs("output", exist_ok=True)
    nombre_docx = os.path.basename(ruta_json).replace(".json", ".docx")
    ruta_docx = os.path.join("output", nombre_docx)
    doc.save(ruta_docx)

    return ruta_docx