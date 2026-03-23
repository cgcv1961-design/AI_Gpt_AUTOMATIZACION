"""
AI_GPT_AUTOMATIZACION/utils/generador_word_general.py
-----------------------------------------------------

Generador de reporte Word para la vertical GENERAL.

OBJETIVO
--------
Transformar el JSON final del análisis contractual en un documento Word
legible, claro y profesional para prospects, clientes o uso interno.

PRINCIPIO
---------
JSON = fuente de verdad única

El Word debe salir EXCLUSIVAMENTE del JSON final.
No debe construir un segundo dictamen paralelo.

COMPATIBILIDAD
--------------
Soporta dos variantes principales:

1) ESQUEMA GENERAL BÁSICO VIEJO
   Claves típicas:
   - tipo_contrato
   - partes
   - duracion_meses
   - precio_mensual
   - moneda
   - riesgos_detectados
   - scoring
   - metadata_sistema

2) ESQUEMA GENERAL TÉCNICO NUEVO
   Claves típicas:
   - nucleo_contractual
   - analisis_profesional
   - informe_cliente
   - scoring
   - metadata_sistema

ESTRUCTURA DEL WORD
-------------------
- Título
- Información General
- Partes del contrato
- Evaluación General del Contrato
- Resumen Ejecutivo para Cliente
- Puntos Críticos Principales
- Hallazgos Principales
- Implicancias Estratégicas a Mediano Plazo
- Recomendación Estratégica Final
- Preguntas Clave Antes de Firmar
- Conclusión Profesional
- Nivel de Confianza del Análisis
- Sistema de Análisis Utilizado
- Resultados del Scoring
- Anexo Técnico - Detalle Ampliado de Riesgos
- Cierre institucional
"""

import os
from typing import Any, Dict, List
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING


def generar_word_general(resultado: dict, ruta_json: str) -> str:
    """
    Genera el reporte Word para la vertical GENERAL.

    Parámetros
    ----------
    resultado : dict
        Resultado final del análisis contractual.
    ruta_json : str
        Ruta del JSON final generado. Se usa para derivar el nombre del .docx.

    Retorna
    -------
    str
        Ruta del archivo Word generado.
    """

    # =====================================================
    # CREACIÓN DEL DOCUMENTO
    # =====================================================

    doc = Document()

    # =====================================================
    # CONFIGURACIÓN BASE
    # =====================================================

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

    # =====================================================
    # INFORMACIÓN GENERAL
    # =====================================================

    def extraer_partes_desde_nuevo_schema(nucleo: Dict[str, Any]) -> List[str]:
        candidatos = [
            nucleo.get("partes"),
            nucleo.get("partes_involucradas"),
            nucleo.get("intervinientes"),
            nucleo.get("sujetos"),
        ]

        for candidato in candidatos:
            partes = lista_desde_valor(candidato)
            if partes:
                return partes

        parte_a = valor_no_vacio(
            nucleo.get("parte_contratante"),
            nucleo.get("parte_1"),
            nucleo.get("locador"),
            nucleo.get("contratante"),
            default=None,
        )
        parte_b = valor_no_vacio(
            nucleo.get("parte_contraparte"),
            nucleo.get("parte_2"),
            nucleo.get("locatario"),
            nucleo.get("contratado"),
            default=None,
        )

        partes = []
        if parte_a is not None:
            partes.append(str(parte_a))
        if parte_b is not None:
            partes.append(str(parte_b))

        return partes

    def inferir_unidad_duracion(nucleo: Dict[str, Any], resultado_dict: Dict[str, Any]) -> str:
        unidad = valor_no_vacio(
            nucleo.get("unidad_duracion"),
            nucleo.get("duracion_unidad"),
            resultado_dict.get("unidad_duracion"),
            resultado_dict.get("duracion_unidad"),
            default=None,
        )

        if unidad not in (None, "", [], {}):
            return texto_limpio(unidad, default="-")

        duracion_en_meses = valor_no_vacio(
            resultado_dict.get("duracion_meses"),
            nucleo.get("duracion_meses"),
            default=None,
        )

        if duracion_en_meses not in (None, "", [], {}):
            return "meses"

        return "-"

    def inferir_periodicidad_precio(nucleo: Dict[str, Any], resultado_dict: Dict[str, Any]) -> str:
        periodicidad = valor_no_vacio(
            nucleo.get("periodicidad_precio"),
            nucleo.get("precio_periodicidad"),
            nucleo.get("unidad_precio"),
            resultado_dict.get("periodicidad_precio"),
            resultado_dict.get("precio_periodicidad"),
            resultado_dict.get("unidad_precio"),
            default=None,
        )

        if periodicidad not in (None, "", [], {}):
            return texto_limpio(periodicidad, default="-")

        precio_mensual = valor_no_vacio(
            resultado_dict.get("precio_mensual"),
            nucleo.get("precio_mensual"),
            default=None,
        )

        if precio_mensual not in (None, "", [], {}):
            return "mensual"

        return "-"

    def formatear_duracion_general(nucleo: Dict[str, Any], resultado_dict: Dict[str, Any]) -> Dict[str, str]:
        """
        Devuelve:
        - breve: versión corta de duración
        - detalle: texto de plazo si existiera
        """
        duracion_texto = texto_limpio(
            valor_no_vacio(
                nucleo.get("duracion_texto"),
                nucleo.get("plazo_texto"),
                default="-"
            ),
            default="-"
        )

        duracion_valor = valor_no_vacio(
            resultado_dict.get("duracion_meses"),
            resultado_dict.get("duracion"),
            nucleo.get("duracion_meses"),
            nucleo.get("plazo_meses"),
            nucleo.get("duracion"),
            nucleo.get("plazo"),
            default="-"
        )

        unidad_duracion = inferir_unidad_duracion(nucleo, resultado_dict)

        if duracion_texto != "-":
            breve = str(duracion_valor) if duracion_valor != "-" else "ver detalle abajo"
            if duracion_valor != "-" and unidad_duracion != "-":
                breve = f"{duracion_valor} {unidad_duracion}"
            return {"breve": breve, "detalle": duracion_texto}

        if duracion_valor == "-":
            return {"breve": "-", "detalle": ""}

        if unidad_duracion == "-":
            return {"breve": str(duracion_valor), "detalle": ""}

        return {"breve": f"{duracion_valor} {unidad_duracion}", "detalle": ""}

    def formatear_precio_general(nucleo: Dict[str, Any], resultado_dict: Dict[str, Any]) -> str:
        precio_valor = valor_no_vacio(
            resultado_dict.get("precio_mensual"),
            resultado_dict.get("precio"),
            nucleo.get("precio_mensual"),
            nucleo.get("monto_mensual"),
            nucleo.get("precio"),
            nucleo.get("monto"),
            default="-"
        )

        moneda = valor_no_vacio(
            resultado_dict.get("moneda"),
            nucleo.get("moneda"),
            nucleo.get("divisa"),
            default="-"
        )

        periodicidad = inferir_periodicidad_precio(nucleo, resultado_dict)

        valor_txt = texto_limpio(precio_valor, default="-")
        moneda_txt = texto_limpio(moneda, default="-")
        periodicidad_txt = texto_limpio(periodicidad, default="-")

        if valor_txt == "-" and moneda_txt == "-":
            return "-"

        if valor_txt == "-":
            base = moneda_txt
        elif moneda_txt == "-":
            base = valor_txt
        else:
            base = f"{valor_txt} {moneda_txt}"

        if periodicidad_txt == "-":
            return base

        return f"{base} ({periodicidad_txt})"

    def obtener_info_general(resultado_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        EXTRAE y normaliza la información general.
        Esta es la función que faltaba en tu archivo actual.
        """
        nucleo = resultado_dict.get("nucleo_contractual", {}) or {}

        tipo_contrato = valor_no_vacio(
            resultado_dict.get("tipo_contrato"),
            nucleo.get("tipo_contrato"),
            nucleo.get("clase_contrato"),
            nucleo.get("naturaleza_contrato"),
            default="-"
        )

        partes = resultado_dict.get("partes", [])
        if not partes:
            partes = extraer_partes_desde_nuevo_schema(nucleo)

        duracion_info = formatear_duracion_general(nucleo, resultado_dict)
        precio_texto = formatear_precio_general(nucleo, resultado_dict)

        return {
            "tipo_contrato": tipo_contrato,
            "duracion_info": duracion_info,
            "precio_texto": precio_texto,
            "partes": partes,
        }

    # =====================================================
    # RIESGOS
    # =====================================================

    def extraer_riesgos(resultado_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        riesgos_normalizados = []

        riesgos_viejos = resultado_dict.get("riesgos_detectados", [])
        if isinstance(riesgos_viejos, list) and riesgos_viejos:
            for r in riesgos_viejos:
                if isinstance(r, dict):
                    riesgos_normalizados.append({
                        "impacto": valor_no_vacio(r.get("impacto"), default="-"),
                        "severidad": valor_no_vacio(
                            r.get("severidad"),
                            r.get("nivel"),
                            r.get("criticidad"),
                            default="-"
                        ),
                        "descripcion": valor_no_vacio(
                            r.get("descripcion"),
                            r.get("riesgo"),
                            r.get("detalle"),
                            default="-"
                        ),
                        "categoria": valor_no_vacio(r.get("categoria"), default=""),
                        "clausula": valor_no_vacio(
                            r.get("clausula"),
                            r.get("clausula_observada"),
                            default=""
                        ),
                    })
            if riesgos_normalizados:
                return riesgos_normalizados

        analisis_prof = resultado_dict.get("analisis_profesional", {}) or {}
        informe_cliente = resultado_dict.get("informe_cliente", {}) or {}

        riesgos_clasificados = analisis_prof.get("riesgos_clasificados", {})
        if isinstance(riesgos_clasificados, dict) and riesgos_clasificados:
            for categoria, lista_riesgos in riesgos_clasificados.items():
                if not isinstance(lista_riesgos, list):
                    continue

                for r in lista_riesgos:
                    if isinstance(r, dict):
                        riesgos_normalizados.append({
                            "impacto": valor_no_vacio(r.get("impacto"), categoria, default="-"),
                            "severidad": valor_no_vacio(
                                r.get("severidad"),
                                r.get("nivel"),
                                r.get("criticidad"),
                                default="-"
                            ),
                            "descripcion": valor_no_vacio(
                                r.get("descripcion"),
                                r.get("detalle"),
                                r.get("hallazgo"),
                                r.get("riesgo"),
                                r.get("observacion"),
                                default="-"
                            ),
                            "categoria": valor_no_vacio(categoria, r.get("categoria"), r.get("tipo"), default=""),
                            "clausula": valor_no_vacio(r.get("clausula"), r.get("referencia"), default=""),
                        })
                    else:
                        texto = str(r).strip()
                        if texto:
                            riesgos_normalizados.append({
                                "impacto": categoria,
                                "severidad": "-",
                                "descripcion": texto,
                                "categoria": str(categoria),
                                "clausula": "",
                            })

            if riesgos_normalizados:
                return riesgos_normalizados

        candidatos = [
            analisis_prof.get("riesgos_detectados"),
            analisis_prof.get("riesgos"),
            analisis_prof.get("hallazgos"),
            analisis_prof.get("observaciones_criticas"),
            informe_cliente.get("riesgos_detectados"),
            informe_cliente.get("riesgos"),
            informe_cliente.get("alertas"),
        ]

        for candidato in candidatos:
            if isinstance(candidato, list) and candidato:
                for r in candidato:
                    if isinstance(r, dict):
                        riesgos_normalizados.append({
                            "impacto": valor_no_vacio(r.get("impacto"), default="-"),
                            "severidad": valor_no_vacio(
                                r.get("severidad"),
                                r.get("nivel"),
                                r.get("criticidad"),
                                default="-"
                            ),
                            "descripcion": valor_no_vacio(
                                r.get("descripcion"),
                                r.get("detalle"),
                                r.get("hallazgo"),
                                r.get("riesgo"),
                                r.get("observacion"),
                                default="-"
                            ),
                            "categoria": valor_no_vacio(r.get("categoria"), r.get("tipo"), default=""),
                            "clausula": valor_no_vacio(r.get("clausula"), r.get("referencia"), default=""),
                        })
                    else:
                        texto = str(r).strip()
                        if texto:
                            riesgos_normalizados.append({
                                "impacto": "-",
                                "severidad": "-",
                                "descripcion": texto,
                                "categoria": "",
                                "clausula": "",
                            })
                if riesgos_normalizados:
                    return riesgos_normalizados

        textos_candidatos = [
            analisis_prof.get("evaluacion_equilibrio_contractual"),
            informe_cliente.get("resumen_ejecutivo", {}).get("vision_general")
            if isinstance(informe_cliente.get("resumen_ejecutivo"), dict) else None,
            informe_cliente.get("informe_detallado", {}).get("conclusion_profesional")
            if isinstance(informe_cliente.get("informe_detallado"), dict) else None,
        ]

        for texto in textos_candidatos:
            if texto not in (None, "", [], {}):
                riesgos_normalizados.append({
                    "impacto": "contexto_general",
                    "severidad": "-",
                    "descripcion": str(texto),
                    "categoria": "contexto_general",
                    "clausula": "",
                })
                return riesgos_normalizados

        return riesgos_normalizados

    def normalizar_severidad(severidad: Any) -> str:
        texto = texto_limpio(severidad, default="-").lower()
        equivalencias = {
            "alta": "alto",
            "alto": "alto",
            "medio alto": "medio-alto",
            "media alta": "medio-alto",
            "media-alta": "medio-alto",
            "medio-alta": "medio-alto",
            "medio-alto": "medio-alto",
            "moderado": "medio",
            "media": "medio",
            "medio": "medio",
            "baja": "bajo",
            "bajo": "bajo",
        }
        return equivalencias.get(texto, texto)

    def peso_severidad(severidad: Any) -> int:
        sev = normalizar_severidad(severidad)
        mapa = {"alto": 4, "medio-alto": 3, "medio": 2, "bajo": 1, "-": 0}
        return mapa.get(sev, 0)

    def agrupar_riesgos_por_categoria(riesgos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grupos: Dict[str, List[Dict[str, Any]]] = {}
        for riesgo in riesgos:
            categoria = str(valor_no_vacio(riesgo.get("categoria"), default="sin_categoria")).strip().lower()
            grupos.setdefault(categoria, []).append(riesgo)
        return grupos

    def titulo_categoria(categoria: str) -> str:
        mapa = {
            "legal": "Riesgos Legales",
            "economico": "Riesgos Económicos",
            "económico": "Riesgos Económicos",
            "operativo": "Riesgos Operativos",
            "reputacional": "Riesgos Reputacionales",
            "contexto_general": "Observaciones Generales",
            "sin_categoria": "Otros Riesgos",
        }
        return mapa.get(categoria.lower(), f"Riesgos - {categoria.capitalize()}")

    def ordenar_riesgos_por_criticidad(riesgos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            riesgos,
            key=lambda r: (
                peso_severidad(r.get("severidad")),
                texto_limpio(r.get("categoria"), default=""),
                texto_limpio(r.get("descripcion"), default="")
            ),
            reverse=True
        )

    def seleccionar_riesgos_destacados(riesgos: List[Dict[str, Any]], puntos_criticos_json: List[str], maximo: int = 5):
        riesgos_ordenados = ordenar_riesgos_por_criticidad(riesgos)
        destacados = []
        descripciones_usadas = set()

        for riesgo in riesgos_ordenados:
            sev = normalizar_severidad(riesgo.get("severidad"))
            desc = texto_limpio(riesgo.get("descripcion"), default="-")
            if sev in ("alto", "medio-alto") and desc not in descripciones_usadas:
                destacados.append(riesgo)
                descripciones_usadas.add(desc)

        puntos_norm = [p.lower().strip() for p in puntos_criticos_json if str(p).strip()]
        if len(destacados) < maximo and puntos_norm:
            for riesgo in riesgos_ordenados:
                desc = texto_limpio(riesgo.get("descripcion"), default="-")
                desc_low = desc.lower()
                if desc in descripciones_usadas:
                    continue

                coincide = any(
                    punto in desc_low or desc_low[:50] in punto or any(token in desc_low for token in punto.split()[:4])
                    for punto in puntos_norm
                )
                if coincide:
                    destacados.append(riesgo)
                    descripciones_usadas.add(desc)
                    if len(destacados) >= maximo:
                        return destacados

        if len(destacados) < maximo:
            for riesgo in riesgos_ordenados:
                desc = texto_limpio(riesgo.get("descripcion"), default="-")
                if desc in descripciones_usadas:
                    continue
                destacados.append(riesgo)
                descripciones_usadas.add(desc)
                if len(destacados) >= maximo:
                    break

        return destacados

    # =====================================================
    # SCORING / METADATA / BLOQUES JSON
    # =====================================================

    def obtener_scoring(resultado_dict: Dict[str, Any]) -> Dict[str, Any]:
        scoring = resultado_dict.get("scoring", {}) or {}
        metricas = scoring.get("metricas", {}) or {}

        return {
            "score_total": valor_no_vacio(scoring.get("score_total"), scoring.get("score"), default="-"),
            "nivel_riesgo": valor_no_vacio(scoring.get("nivel_riesgo"), scoring.get("nivel"), default="-"),
            "version_scoring": valor_no_vacio(scoring.get("version_scoring"), default="-"),
            "metricas": {
                "cantidad_riesgos": valor_no_vacio(metricas.get("cantidad_riesgos"), metricas.get("total_riesgos"), default="-"),
                "riesgos_altos": valor_no_vacio(metricas.get("riesgos_altos"), metricas.get("altos"), default="-"),
                "riesgos_media_altos": valor_no_vacio(
                    metricas.get("riesgos_media_altos"),
                    metricas.get("riesgos_medio_altos"),
                    metricas.get("medio_altos"),
                    default="-"
                ),
                "riesgos_medios": valor_no_vacio(metricas.get("riesgos_medios"), metricas.get("medios"), default="-"),
                "riesgos_bajos": valor_no_vacio(metricas.get("riesgos_bajos"), metricas.get("bajos"), default="-"),
            }
        }

    def obtener_metadata(resultado_dict: Dict[str, Any]) -> Dict[str, Any]:
        metadata = resultado_dict.get("metadata_sistema", {}) or {}
        return {
            "modelo_utilizado": valor_no_vacio(metadata.get("modelo_utilizado"), metadata.get("modelo"), default="-"),
            "perfil_canonico": valor_no_vacio(metadata.get("perfil_canonico"), metadata.get("perfil"), default="-"),
            "version_servicio": valor_no_vacio(metadata.get("version_servicio"), metadata.get("version_motor"), default="-"),
        }

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

    def obtener_analisis_profesional(resultado_dict: Dict[str, Any]) -> Dict[str, Any]:
        analisis = resultado_dict.get("analisis_profesional", {}) or {}
        nivel_confianza = analisis.get("nivel_confianza_analisis", {}) or {}

        return {
            "evaluacion_equilibrio_contractual": texto_limpio(
                analisis.get("evaluacion_equilibrio_contractual"),
                default="-"
            ),
            "nivel_confianza_general": texto_limpio(
                nivel_confianza.get("general"),
                default="-"
            ),
            "nivel_confianza_fundamento": texto_limpio(
                nivel_confianza.get("fundamento"),
                default="-"
            ),
        }

    def obtener_informe_cliente(resultado_dict: Dict[str, Any]) -> Dict[str, Any]:
        informe = resultado_dict.get("informe_cliente", {}) or {}
        resumen = informe.get("resumen_ejecutivo", {}) or {}
        detalle = informe.get("informe_detallado", {}) or {}

        return {
            "vision_general": texto_limpio(resumen.get("vision_general"), default="-"),
            "nivel_riesgo_global": texto_limpio(resumen.get("nivel_riesgo_global"), default="-"),
            "puntos_criticos": lista_desde_valor(resumen.get("puntos_criticos")),
            "recomendacion_estrategica_final": texto_limpio(
                resumen.get("recomendacion_estrategica_final"),
                default="-"
            ),
            "hallazgos_principales": lista_desde_valor(detalle.get("hallazgos_principales")),
            "implicancias_estrategicas_mediano_plazo": lista_desde_valor(
                detalle.get("implicancias_estrategicas_mediano_plazo")
            ),
            "preguntas_clave_antes_de_firmar": lista_desde_valor(
                detalle.get("preguntas_clave_antes_de_firmar")
            ),
            "conclusion_profesional": texto_limpio(
                detalle.get("conclusion_profesional"),
                default="-"
            ),
        }

    def construir_resumen_ejecutivo(scoring: Dict[str, Any], informe_cliente: Dict[str, Any]) -> str:
        vision_general = texto_limpio(informe_cliente.get("vision_general"), default="-")
        nivel_riesgo_global = texto_limpio(informe_cliente.get("nivel_riesgo_global"), default="-")
        conclusion_profesional = texto_limpio(informe_cliente.get("conclusion_profesional"), default="-")
        nivel = texto_limpio(scoring.get("nivel_riesgo"), default="-").lower()
        metricas = scoring.get("metricas", {}) or {}
        distribucion = construir_distribucion_severidad(metricas)

        piezas = []

        if vision_general != "-":
            piezas.append(vision_general)

        if nivel_riesgo_global != "-":
            piezas.append(f"Nivel de riesgo global informado: {nivel_riesgo_global}.")

        piezas.append(
            f"Desde el scoring del sistema, el nivel global del caso se ubica en {nivel}, "
            f"con distribución por severidad: {distribucion}."
        )

        if conclusion_profesional != "-":
            piezas.append(conclusion_profesional)

        return " ".join(piezas)

    # =====================================================
    # DATOS
    # =====================================================

    info_nucleo = obtener_info_general(resultado)
    riesgos = extraer_riesgos(resultado)
    riesgos_ordenados = ordenar_riesgos_por_criticidad(riesgos)
    riesgos_agrupados = agrupar_riesgos_por_categoria(riesgos_ordenados)
    scoring = obtener_scoring(resultado)
    metadata = obtener_metadata(resultado)
    analisis_prof = obtener_analisis_profesional(resultado)
    informe_cliente = obtener_informe_cliente(resultado)
    riesgos_destacados = seleccionar_riesgos_destacados(
        riesgos_ordenados,
        informe_cliente.get("puntos_criticos", []),
        maximo=5
    )
    resumen_ejecutivo = construir_resumen_ejecutivo(scoring, informe_cliente)

    tipo_contrato = info_nucleo["tipo_contrato"]
    duracion = info_nucleo["duracion_info"]
    precio = info_nucleo["precio_texto"]
    partes = info_nucleo["partes"]

    score_total = scoring["score_total"]
    nivel_riesgo = scoring["nivel_riesgo"]
    version_scoring = scoring["version_scoring"]
    metricas = scoring["metricas"]

    # =====================================================
    # TÍTULO
    # =====================================================

    heading_compacto("Reporte de Análisis Contractual", level=0)

    # =====================================================
    # INFORMACIÓN GENERAL
    # =====================================================

    heading_compacto("Información General", level=1)
    parrafo_compacto(f"Tipo de contrato: {tipo_contrato}")
    parrafo_compacto(f"Duración: {duracion['breve']}")
    if duracion["detalle"]:
        parrafo_compacto("Detalle del plazo:", bold=True)
        parrafo_compacto(duracion["detalle"], indent=18)
    parrafo_compacto(f"Precio: {precio}")

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
    parrafo_compacto(f"Nivel de riesgo del scoring: {nivel_riesgo}")

    if metricas.get("cantidad_riesgos", "-") != "-":
        parrafo_compacto(f"Cantidad de observaciones: {metricas.get('cantidad_riesgos', '-')}")

    parrafo_compacto(f"Distribución por severidad: {construir_distribucion_severidad(metricas)}")

    if analisis_prof["evaluacion_equilibrio_contractual"] != "-":
        parrafo_compacto("Evaluación de equilibrio contractual:", bold=True)
        parrafo_compacto(analisis_prof["evaluacion_equilibrio_contractual"], indent=18)

    if informe_cliente["nivel_riesgo_global"] != "-":
        parrafo_compacto(f"Nivel de riesgo global informado: {informe_cliente['nivel_riesgo_global']}")

    # =====================================================
    # RESUMEN EJECUTIVO
    # =====================================================

    heading_compacto("Resumen Ejecutivo para Cliente", level=1)
    parrafo_compacto(resumen_ejecutivo)

    # =====================================================
    # PUNTOS CRÍTICOS
    # =====================================================

    heading_compacto("Puntos Críticos Principales", level=1)
    if informe_cliente["puntos_criticos"]:
        for punto in informe_cliente["puntos_criticos"]:
            parrafo_bulleted(punto)
    elif riesgos_destacados:
        for i, r in enumerate(riesgos_destacados, start=1):
            severidad = texto_limpio(r.get("severidad"), default="-").capitalize()
            categoria = texto_limpio(r.get("categoria"), default="Sin categoría")
            descripcion = texto_limpio(r.get("descripcion"), default="-")

            parrafo_compacto(f"Punto {i}", bold=True)
            parrafo_compacto(f"Categoría: {categoria}")
            parrafo_compacto(f"Severidad: {severidad}")
            parrafo_compacto("Descripción:", bold=True)
            parrafo_compacto(descripcion, indent=18)
    else:
        parrafo_compacto("No se identificaron puntos críticos relevantes para destacar.")

    # =====================================================
    # HALLAZGOS
    # =====================================================

    heading_compacto("Hallazgos Principales", level=1)
    hallazgos = informe_cliente["hallazgos_principales"]
    if hallazgos:
        for hallazgo in hallazgos:
            parrafo_bulleted(hallazgo)
    else:
        parrafo_compacto("No se reportaron hallazgos principales.")

    # =====================================================
    # IMPLICANCIAS
    # =====================================================

    heading_compacto("Implicancias Estratégicas a Mediano Plazo", level=1)
    implicancias = informe_cliente["implicancias_estrategicas_mediano_plazo"]
    if implicancias:
        for item in implicancias:
            parrafo_bulleted(item)
    else:
        parrafo_compacto("No se reportaron implicancias estratégicas específicas.")

    # =====================================================
    # RECOMENDACIÓN
    # =====================================================

    heading_compacto("Recomendación Estratégica Final", level=1)
    recomendacion = informe_cliente["recomendacion_estrategica_final"]
    if recomendacion != "-":
        parrafo_compacto(recomendacion)
    else:
        parrafo_compacto("No se reportó recomendación estratégica final.")

    # =====================================================
    # PREGUNTAS
    # =====================================================

    heading_compacto("Preguntas Clave Antes de Firmar", level=1)
    preguntas = informe_cliente["preguntas_clave_antes_de_firmar"]
    if preguntas:
        for pregunta in preguntas:
            parrafo_bulleted(pregunta)
    else:
        parrafo_compacto("No se reportaron preguntas clave antes de firmar.")

    # =====================================================
    # CONCLUSIÓN
    # =====================================================

    heading_compacto("Conclusión Profesional", level=1)
    conclusion = informe_cliente["conclusion_profesional"]
    if conclusion != "-":
        parrafo_compacto(conclusion)
    else:
        parrafo_compacto("No se reportó conclusión profesional.")

    # =====================================================
    # NIVEL DE CONFIANZA
    # =====================================================

    heading_compacto("Nivel de Confianza del Análisis", level=1)
    parrafo_compacto(f"Nivel general: {analisis_prof['nivel_confianza_general']}")
    if analisis_prof["nivel_confianza_fundamento"] != "-":
        parrafo_compacto("Fundamento:", bold=True)
        parrafo_compacto(analisis_prof["nivel_confianza_fundamento"], indent=18)

    # =====================================================
    # SISTEMA
    # =====================================================

    heading_compacto("Sistema de Análisis Utilizado", level=1)
    parrafo_compacto("Motor de Inteligencia Artificial", bold=True)
    parrafo_compacto(f"Modelo utilizado: {metadata['modelo_utilizado']}")
    parrafo_compacto(f"Perfil de análisis: {metadata['perfil_canonico']}")

    parrafo_compacto("Motor de Evaluación Jurídica", bold=True)
    parrafo_compacto(f"Versión del motor: {metadata['version_servicio']}")
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
    # ANEXO TÉCNICO
    # =====================================================

    heading_compacto("Anexo Técnico - Detalle Ampliado de Riesgos", level=1)

    if not riesgos_ordenados:
        parrafo_compacto("No se detectaron riesgos para ampliar.")
    else:
        categorias_ordenadas = [
            "legal",
            "economico",
            "económico",
            "operativo",
            "reputacional",
            "contexto_general",
            "sin_categoria",
        ]

        categorias_presentes = list(riesgos_agrupados.keys())
        categorias_finales = []

        for cat in categorias_ordenadas:
            if cat in riesgos_agrupados:
                categorias_finales.append(cat)

        for cat in categorias_presentes:
            if cat not in categorias_finales:
                categorias_finales.append(cat)

        for categoria in categorias_finales:
            lista_riesgos = riesgos_agrupados.get(categoria, [])
            if not lista_riesgos:
                continue

            heading_compacto(titulo_categoria(categoria), level=2)

            for i, r in enumerate(lista_riesgos, start=1):
                severidad = texto_limpio(r.get("severidad"), default="-").capitalize()
                impacto = texto_limpio(r.get("impacto"), default="-")
                descripcion = texto_limpio(r.get("descripcion"), default="-")
                clausula = texto_limpio(r.get("clausula"), default="-")

                parrafo_compacto(f"Riesgo {i}", bold=True)

                if severidad != "-":
                    parrafo_compacto(f"Severidad: {severidad}")

                if impacto != "-":
                    parrafo_compacto(f"Impacto: {impacto}")

                if clausula != "-":
                    parrafo_compacto(f"Cláusula / referencia: {clausula}")

                parrafo_compacto("Descripción:", bold=True)
                parrafo_compacto(descripcion, indent=18)

    # =====================================================
    # CIERRE
    # =====================================================

    parrafo_compacto(
        "Este informe fue generado mediante un sistema automatizado de análisis contractual "
        "basado en inteligencia artificial y un motor de evaluación jurídica propietario."
    )

    os.makedirs("output", exist_ok=True)
    nombre_docx = os.path.basename(ruta_json).replace(".json", ".docx")
    ruta_docx = os.path.join("output", nombre_docx)
    doc.save(ruta_docx)

    return ruta_docx