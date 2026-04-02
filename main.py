"""
AI_GPT_AUTOMATIZACION/main.py
-----------------------------

Motor principal de análisis contractual.

OBJETIVO DE ESTA VERSIÓN
------------------------
Normalizar correctamente:
- perspectiva de análisis
- país de referencia
- roles contractuales visibles
- nombres de partes para UI y Word

MEJORA PRINCIPAL
----------------
Evitar que en la salida final aparezcan diccionarios como texto y
mejorar la inferencia de roles visibles, especialmente en:
- NDA / confidencialidad
- arrendamientos
- audiovisual
"""

import sys
import json
import os
import time
from typing import Any, Dict, List, Tuple

from utils.generador_word_general import generar_word_general
from utils.generador_word_audiovisual import generar_word_audiovisual

from verticales.general.service import ejecutar_analisis_general

try:
    from verticales.audiovisual.service import ejecutar_analisis_audiovisual
except ImportError:
    ejecutar_analisis_audiovisual = None


def detectar_vertical(texto: str) -> str:
    texto = (texto or "").lower()

    palabras_audiovisual = [
        "productor",
        "productora",
        "rodaje",
        "derechos de imagen",
        "guion",
        "licencia audiovisual",
        "obra audiovisual",
        "artista",
        "interprete",
        "intérprete",
    ]

    for palabra in palabras_audiovisual:
        if palabra in texto:
            return "AUDIOVISUAL"

    return "GENERAL"


def cargar_contrato(ruta_json: str) -> dict:
    if not os.path.exists(ruta_json):
        raise FileNotFoundError("Archivo JSON no encontrado.")

    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


def mostrar_etapas_analisis():
    print("📄 Analizando estructura del contrato")
    time.sleep(0.5)

    print("⚖ Evaluando riesgos jurídicos")
    time.sleep(0.5)

    print("🧠 Ejecutando modelo de IA")
    time.sleep(0.5)

    print("📊 Calculando scoring")
    time.sleep(0.5)


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


def normalizar_pais_referencia(pais_referencia: str) -> str:
    valor = (pais_referencia or "").strip().lower()

    opciones_validas = {
        "argentina": "argentina",
        "uruguay": "uruguay",
        "italia": "italia",
        "espana": "espana",
        "internacional": "internacional",
    }

    return opciones_validas.get(valor, "internacional")


def construir_texto_desde_lista(lista: List[str], max_items: int = 3) -> str:
    items = [str(x).strip() for x in lista if str(x).strip()]
    if not items:
        return ""
    return "; ".join(items[:max_items])


def extraer_nombre_y_rol_desde_parte(parte: Any) -> Tuple[str, str]:
    if isinstance(parte, dict):
        nombre = texto_limpio(
            parte.get("nombre") or parte.get("parte") or parte.get("name"),
            default="-"
        )
        rol = texto_limpio(
            parte.get("rol") or parte.get("tipo") or parte.get("role"),
            default=""
        )
        return nombre, rol

    texto = texto_limpio(parte, default="-")
    if texto == "-":
        return "-", ""

    if "(" in texto and ")" in texto:
        base = texto.rsplit("(", 1)[0].strip()
        rol = texto.rsplit("(", 1)[1].replace(")", "").strip()
        return base, rol

    return texto, ""


def inferir_rol_por_tipo_y_posicion(tipo_contrato: str, posicion: int, total_partes: int) -> str:
    """
    Heurística cuando el JSON no trae rol explícito.
    posicion es 0-based.
    """
    tipo = (tipo_contrato or "").lower()

    if any(x in tipo for x in ["confidencialidad", "nda", "propiedad intelectual"]):
        if posicion == 0:
            return "Cliente"
        if posicion == 1:
            return "Proveedor"

    if any(x in tipo for x in ["arrendamiento", "locación", "locacion", "locazione"]):
        if posicion == 0:
            return "Arrendador / locatore"
        if posicion == 1:
            return "Arrendatario / conduttore"

    if any(x in tipo for x in ["audiovisual", "artístico", "artistico", "intérprete", "interprete"]):
        if posicion == 0:
            return "Productora"
        if posicion == 1:
            return "Artista"

    return ""


def normalizar_rol_visible(rol: str, nombre: str = "", perspectiva: str = "proveedor") -> str:
    rol_txt = (rol or "").strip().lower()
    nombre_txt = (nombre or "").strip().lower()

    mapa_directo = {
        "cliente": "Cliente",
        "proveedor": "Proveedor",
        "proveedor/receptor": "Proveedor",
        "receptor": "Proveedor",
        "arrendador": "Arrendador / locatore",
        "arrendatario": "Arrendatario / conduttore",
        "arrendatarios": "Arrendatarios / conduttori",
        "locador": "Arrendador / locatore",
        "locatario": "Arrendatario / conduttore",
        "locatore": "Arrendador / locatore",
        "conduttore": "Arrendatario / conduttore",
        "productora": "Productora",
        "productor": "Productor",
        "artista": "Artista",
        "el artista": "Artista",
        "intérprete": "Artista / intérprete",
        "interprete": "Artista / intérprete",
        "prestador": "Prestador",
        "contratista": "Contratista",
        "licenciante": "Licenciante",
        "licenciatario": "Licenciatario",
    }

    if rol_txt in mapa_directo:
        return mapa_directo[rol_txt]

    if any(x in rol_txt for x in ["arrendador", "locador", "locatore", "propietario"]):
        return "Arrendador / locatore"
    if any(x in rol_txt for x in ["arrendatario", "arrendatarios", "inquilino", "locatario", "conduttore"]):
        return "Arrendatario / conduttore"
    if any(x in rol_txt for x in ["cliente", "customer"]):
        return "Cliente"
    if any(x in rol_txt for x in ["proveedor", "supplier", "receptor"]):
        return "Proveedor"
    if "productora" in rol_txt:
        return "Productora"
    if "productor" in rol_txt:
        return "Productor"
    if any(x in rol_txt for x in ["artista", "interprete", "intérprete"]):
        return "Artista"

    if any(x in nombre_txt for x in ["artista", "el artista", "intérprete", "interprete"]):
        return "Artista"
    if "productora" in nombre_txt:
        return "Productora"
    if "productor" in nombre_txt:
        return "Productor"
    if any(x in nombre_txt for x in ["arrendador", "locatore", "locador", "propietario"]):
        return "Arrendador / locatore"
    if any(x in nombre_txt for x in ["arrendatario", "arrendatarios", "conduttore", "locatario", "inquilino"]):
        return "Arrendatario / conduttore"
    if "cliente" in nombre_txt:
        return "Cliente"
    if "proveedor" in nombre_txt:
        return "Proveedor"

    if perspectiva == "proveedor":
        return "Parte receptora del contrato"

    return "Parte proponente del contrato"


def formatear_parte_visible(parte: Any, perspectiva: str = "proveedor", tipo_contrato: str = "", posicion: int = -1, total_partes: int = 0) -> str:
    nombre, rol = extraer_nombre_y_rol_desde_parte(parte)

    rol_fuente = rol
    if not rol_fuente:
        rol_fuente = inferir_rol_por_tipo_y_posicion(tipo_contrato, posicion, total_partes)

    rol_visible = normalizar_rol_visible(rol_fuente, nombre=nombre, perspectiva=perspectiva)

    if nombre == "-":
        return rol_visible

    if rol_visible and rol_visible not in ("Parte receptora del contrato", "Parte proponente del contrato"):
        return f"{nombre} ({rol_visible})"

    return nombre


def obtener_partes_normalizadas(resultado: Dict[str, Any]) -> List[Any]:
    nucleo = resultado.get("nucleo_contractual", {}) or {}
    partes = lista_desde_valor(nucleo.get("partes"))

    if partes:
        return partes

    candidatos = [
        nucleo.get("partes_involucradas"),
        nucleo.get("intervinientes"),
        nucleo.get("sujetos"),
    ]
    for candidato in candidatos:
        lista = lista_desde_valor(candidato)
        if lista:
            return lista

    return []


def construir_partes_con_rol(resultado: Dict[str, Any], perspectiva: str) -> List[str]:
    partes = obtener_partes_normalizadas(resultado)
    if not partes:
        return []

    tipo_contrato = texto_limpio((resultado.get("nucleo_contractual", {}) or {}).get("tipo_contrato"), default="")
    total = len(partes)

    salida = []
    for i, parte in enumerate(partes):
        salida.append(
            formatear_parte_visible(
                parte,
                perspectiva=perspectiva,
                tipo_contrato=tipo_contrato,
                posicion=i,
                total_partes=total,
            )
        )

    return salida


def construir_metadata_presentacion(resultado: Dict[str, Any], perspectiva: str) -> Dict[str, Any]:
    partes = obtener_partes_normalizadas(resultado)
    partes_con_rol = construir_partes_con_rol(resultado, perspectiva=perspectiva)
    tipo_contrato = texto_limpio((resultado.get("nucleo_contractual", {}) or {}).get("tipo_contrato"), default="")

    parte_analizada_label = (
        "Parte receptora del contrato"
        if perspectiva == "proveedor"
        else "Parte proponente del contrato"
    )

    parte_analizada_raw = None
    parte_analizada_pos = 0

    if partes:
        if perspectiva == "proveedor":
            parte_analizada_pos = 1 if len(partes) >= 2 else 0
            parte_analizada_raw = partes[parte_analizada_pos]
        else:
            parte_analizada_pos = 0
            parte_analizada_raw = partes[0]

    nombre_parte_analizada = "-"
    rol_contractual_detectado = (
        "Parte receptora del contrato"
        if perspectiva == "proveedor"
        else "Parte proponente del contrato"
    )

    if parte_analizada_raw is not None:
        nombre, rol = extraer_nombre_y_rol_desde_parte(parte_analizada_raw)
        if not rol:
            rol = inferir_rol_por_tipo_y_posicion(tipo_contrato, parte_analizada_pos, len(partes))
        nombre_parte_analizada = nombre
        rol_contractual_detectado = normalizar_rol_visible(
            rol,
            nombre=nombre,
            perspectiva=perspectiva
        )

    return {
        "parte_analizada_label": parte_analizada_label,
        "rol_contractual_detectado": rol_contractual_detectado,
        "nombre_parte_analizada": nombre_parte_analizada,
        "partes_con_rol": partes_con_rol,
    }


def ajustar_resultado_a_perspectiva(resultado: Dict[str, Any], perspectiva: str) -> Dict[str, Any]:
    if not isinstance(resultado, dict):
        return resultado

    informe_cliente = resultado.get("informe_cliente", {}) or {}
    resumen = informe_cliente.get("resumen_ejecutivo", {}) or {}
    detalle = informe_cliente.get("informe_detallado", {}) or {}
    scoring = resultado.get("scoring", {}) or {}
    nucleo = resultado.get("nucleo_contractual", {}) or {}
    metadata = resultado.get("metadata_sistema", {}) or {}

    metadata_presentacion = metadata.get("metadata_presentacion", {}) or {}

    tipo_contrato = texto_limpio(nucleo.get("tipo_contrato"), default="contrato analizado")
    nivel_riesgo_global = texto_limpio(resumen.get("nivel_riesgo_global"), default="-")
    puntos_criticos = [texto_limpio(x, default="") for x in lista_desde_valor(resumen.get("puntos_criticos")) if texto_limpio(x, default="")]
    hallazgos = [texto_limpio(x, default="") for x in lista_desde_valor(detalle.get("hallazgos_principales")) if texto_limpio(x, default="")]
    score_total = texto_limpio(scoring.get("score_total"), default="-")
    nivel_scoring = texto_limpio(scoring.get("nivel_riesgo"), default="-")
    pais = texto_limpio(metadata.get("pais_referencia"), default="internacional")

    rol_detectado = texto_limpio(
        metadata_presentacion.get("rol_contractual_detectado"),
        default="Parte analizada"
    )

    puntos_txt = construir_texto_desde_lista(puntos_criticos, max_items=3)
    hallazgos_txt = construir_texto_desde_lista(hallazgos, max_items=2)

    if perspectiva == "proveedor":
        nueva_vision = (
            f"Este {tipo_contrato} se analiza desde la perspectiva de la parte analizada. "
            f"Rol contractual detectado: {rol_detectado}. "
            f"El nivel de riesgo global informado es {nivel_riesgo_global.lower() if nivel_riesgo_global != '-' else 'indeterminado'}. "
            f"Conviene revisar especialmente: {puntos_txt if puntos_txt else 'las cláusulas que concentran la mayor carga jurídica, económica u operativa'}."
        )

        nueva_recomendacion = (
            f"Se recomienda a la parte analizada revisar y negociar antes de firmar las cláusulas que puedan generar una exposición desproporcionada. "
            f"En este caso, el foco principal debería ponerse en: {puntos_txt if puntos_txt else 'las obligaciones más exigentes del contrato'}. "
            f"Contexto legal de referencia: {pais}."
        )

        nuevas_preguntas = [
            "¿La parte analizada comprende plenamente las obligaciones y restricciones que asumiría al firmar?",
            "¿Hay cláusulas que convenga negociar antes de avanzar por generar una exposición desproporcionada?",
            "¿La parte analizada puede cumplir en la práctica con las exigencias operativas, técnicas, económicas y de plazos del contrato?",
            "¿Existen mecanismos claros de revisión, renegociación o limitación de responsabilidad ante cambios relevantes?",
            "¿El beneficio real del contrato justifica el nivel de riesgo que asumiría la parte analizada?",
        ]

        nueva_conclusion = (
            f"Desde la perspectiva de la parte analizada ({rol_detectado}), el contrato requiere una revisión cuidadosa antes de la firma. "
            f"El scoring del sistema ubica el caso en nivel {nivel_scoring} con score total {score_total}. "
            f"{hallazgos_txt if hallazgos_txt else 'Las cláusulas más sensibles merecen revisión específica antes de avanzar.'}"
        )

    else:
        nueva_vision = (
            f"Este {tipo_contrato} se analiza desde la perspectiva de la parte analizada. "
            f"Rol contractual detectado: {rol_detectado}. "
            f"El nivel de riesgo global informado es {nivel_riesgo_global.lower() if nivel_riesgo_global != '-' else 'indeterminado'}. "
            f"El foco no está solo en proteger intereses, sino también en verificar que esa protección sea sólida, proporcionada y sostenible."
        )

        nueva_recomendacion = (
            f"Se recomienda a la parte analizada revisar si alguna cláusula resulta excesiva, difícil de ejecutar o potencialmente impugnable. "
            f"Conviene prestar especial atención a: {puntos_txt if puntos_txt else 'los puntos más sensibles del contrato'}. "
            f"Contexto legal de referencia: {pais}."
        )

        nuevas_preguntas = [
            "¿Las cláusulas más exigentes del contrato son realmente ejecutables y defendibles en la práctica?",
            "¿Existe algún punto que convenga moderar para reducir riesgo de litigio, nulidad parcial o resistencia de la contraparte?",
            "¿La estructura contractual protege adecuadamente a la parte analizada sin generar rigidez innecesaria?",
            "¿Hay aspectos operativos o económicos que podrían deteriorar el cumplimiento o la relación contractual?",
            "¿El equilibrio general del contrato favorece una relación sostenible además de jurídicamente protegida?",
        ]

        nueva_conclusion = (
            f"Desde la perspectiva de la parte analizada ({rol_detectado}), el contrato ofrece una base de protección relevante, "
            f"pero conviene validar que sus cláusulas más intensas sean proporcionadas y sostenibles. "
            f"El scoring del sistema ubica el caso en nivel {nivel_scoring} con score total {score_total}. "
            f"{hallazgos_txt if hallazgos_txt else 'Las alertas principales deben revisarse antes de avanzar.'}"
        )

    resumen["vision_general"] = nueva_vision
    resumen["recomendacion_estrategica_final"] = nueva_recomendacion
    detalle["preguntas_clave_antes_de_firmar"] = nuevas_preguntas
    detalle["conclusion_profesional"] = nueva_conclusion

    informe_cliente["resumen_ejecutivo"] = resumen
    informe_cliente["informe_detallado"] = detalle
    resultado["informe_cliente"] = informe_cliente

    return resultado


def guardar_reporte_json(resultado: dict, ruta_json_entrada: str) -> str:
    os.makedirs("output", exist_ok=True)

    nombre_salida = os.path.basename(ruta_json_entrada).replace(".json", "_reporte.json")
    ruta_output = os.path.join("output", nombre_salida)

    with open(ruta_output, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    return ruta_output


def generar_reporte_word_por_vertical(vertical: str, resultado: dict, ruta_output_json: str) -> str:
    if vertical == "AUDIOVISUAL":
        return generar_word_audiovisual(resultado, ruta_output_json)

    return generar_word_general(resultado, ruta_output_json)


def ejecutar_motor(
    ruta_json: str,
    perspectiva: str = "proveedor",
    pais_referencia: str = "internacional"
):
    print("🔎 Detectando tipo de contrato.")

    data = cargar_contrato(ruta_json)

    texto = data.get("texto", "")
    if not texto:
        raise ValueError("El JSON no contiene el texto del contrato.")

    if perspectiva not in ("proveedor", "cliente"):
        perspectiva = "proveedor"

    pais_referencia = normalizar_pais_referencia(pais_referencia)
    vertical = detectar_vertical(texto)

    print(f"✔ Vertical detectada: {vertical}")
    print(f"✔ Perspectiva de análisis: {perspectiva}")
    print(f"✔ País / contexto legal de referencia: {pais_referencia}")
    print("\n⚙ Ejecutando motor de análisis...\n")

    mostrar_etapas_analisis()

    if vertical == "GENERAL":
        resultado = ejecutar_analisis_general(data)
    elif vertical == "AUDIOVISUAL":
        if ejecutar_analisis_audiovisual is None:
            print("⚠ Vertical audiovisual no disponible aún.")
            return None
        resultado = ejecutar_analisis_audiovisual(data)
    else:
        print("❌ No se pudo determinar la vertical.")
        return None

    if not isinstance(resultado, dict):
        raise ValueError("El motor de análisis no devolvió un resultado válido.")

    resultado.setdefault("metadata_sistema", {})
    resultado["metadata_sistema"]["perspectiva_analisis"] = perspectiva
    resultado["metadata_sistema"]["pais_referencia"] = pais_referencia
    resultado["metadata_sistema"]["metadata_presentacion"] = construir_metadata_presentacion(
        resultado,
        perspectiva=perspectiva
    )

    if vertical == "GENERAL":
        resultado = ajustar_resultado_a_perspectiva(resultado, perspectiva=perspectiva)

    ruta_output_json = guardar_reporte_json(resultado, ruta_json)
    print(f"\n📄 Reporte JSON guardado en: {ruta_output_json}")

    ruta_word = generar_reporte_word_por_vertical(vertical, resultado, ruta_output_json)
    print(f"\n📄 Reporte Word guardado en: {ruta_word}")

    print("\n✔ Análisis finalizado")

    return {
        "vertical": vertical,
        "resultado": resultado,
        "ruta_json_output": ruta_output_json,
        "ruta_word_output": ruta_word,
        "perspectiva": perspectiva,
        "pais_referencia": pais_referencia,
    }


if __name__ == "__main__":
    print("\n======================================")
    print("   SISTEMA DE ANALISIS CONTRACTUAL IA")
    print("======================================\n")

    if len(sys.argv) < 2:
        print("❌ Debe indicar un archivo JSON")
        print("\nEjemplo:")
        print("python main.py input/contrato.json proveedor argentina")
        sys.exit()

    ruta_json = sys.argv[1]

    perspectiva = "proveedor"
    pais_referencia = "internacional"

    if len(sys.argv) >= 3:
        perspectiva = sys.argv[2]

    if len(sys.argv) >= 4:
        pais_referencia = sys.argv[3]

    try:
        ejecutar_motor(
            ruta_json,
            perspectiva=perspectiva,
            pais_referencia=pais_referencia
        )
    except Exception as e:
        print("\n❌ Error durante el análisis")
        print(e)