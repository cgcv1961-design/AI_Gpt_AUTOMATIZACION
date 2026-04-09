"""
AI_GPT_AUTOMATIZACION/core/scoring_engine.py
--------------------------------------------

Capa de enriquecimiento dual del scoring.

SEPARA TRES CONCEPTOS
---------------------
1. Severidad del contrato
   - qué tan duro, agresivo o litigioso es el contrato en sí

2. Riesgo para la parte analizada
   - qué tan expuesta queda la parte que está mirando el contrato

3. Riesgo para la contraparte
   - qué tan expuesta queda la otra parte

IMPORTANTE
----------
No reemplaza el scoring sectorial existente.
Lo toma como base y reorganiza la salida para hacerla más clara.

OBJETIVO DE ESTA VERSIÓN
------------------------
Corregir la direccionalidad en contratos locativos / arrendamientos
sin romper el funcionamiento de NDA y otros contratos generales.

PROBLEMA DETECTADO
------------------
En alquileres podían ocurrir dos cosas:

1. El resumen ejecutivo mencionaba solo un lado
   Ejemplo:
   - "moderado para el arrendatario"

   Antes:
   - el lado mencionado tomaba ese nivel
   - el lado faltante heredaba por defecto el nivel del contrato
   Resultado:
   - podía quedar más alto el arrendador que el arrendatario

2. El resumen ejecutivo no mencionaba ningún rol
   Ejemplo:
   - "moderado"

   Antes:
   - ambos lados heredaban el mismo nivel
   Resultado:
   - empate artificial

SOLUCIÓN DE ESTA VERSIÓN
------------------------
1. Si el resumen menciona explícitamente ambos roles:
   - se respeta tal cual (esto preserva NDA)

2. Si el resumen menciona solo uno:
   - se usa ese nivel para el rol mencionado
   - el otro se infiere con lógica contextual

3. Si el resumen no menciona ninguno:
   - se usa heurística direccional SOLO para contratos locativos
   - para el resto se conserva el comportamiento general

4. La heurística locativa NO toca la severidad del contrato.
   Solo mejora el reparto:
   - arrendatario / conduttore
   - arrendador / locatore
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from utils.clasificador_severidad import clasificar_nivel


# =========================================================
# HELPERS BÁSICOS
# =========================================================

def _texto(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _normalizar_nivel(nivel: str) -> str:
    txt = _texto(nivel).lower()

    mapa = {
        "bajo": "bajo",
        "medio": "medio",
        "moderado": "medio",
        "medio-alto": "medio-alto",
        "alto": "alto",
        "muy alto": "alto",
        "critico": "critico",
        "crítico": "critico",
    }

    return mapa.get(txt, "medio")


def _factor_score_por_nivel(nivel: str) -> float:
    nivel = _normalizar_nivel(nivel)

    factores = {
        "bajo": 0.30,
        "medio": 0.60,
        "medio-alto": 0.80,
        "alto": 1.00,
        "critico": 1.15,
    }
    return factores.get(nivel, 0.60)


def _keywords_rol(rol: str) -> List[str]:
    rol_txt = _texto(rol).lower()

    if "cliente" in rol_txt:
        return ["cliente"]
    if "proveedor" in rol_txt:
        return ["proveedor"]
    if "arrendador" in rol_txt or "locatore" in rol_txt:
        return ["arrendador", "locatore"]
    if "arrendatario" in rol_txt or "conduttore" in rol_txt:
        return ["arrendatario", "conduttore", "arrendatarios", "conduttori"]
    if "artista" in rol_txt or "intérprete" in rol_txt or "interprete" in rol_txt:
        return ["artista", "intérprete", "interprete"]
    if "productora" in rol_txt:
        return ["productora"]
    if "productor" in rol_txt:
        return ["productor"]

    return [rol_txt] if rol_txt else []


def _extraer_nivel_para_rol(texto: str, rol: str) -> Optional[str]:
    """
    Busca expresiones como:
    - alto para el Proveedor
    - bajo para el Cliente
    - moderado para el arrendatario
    """
    texto_norm = _texto(texto).lower()
    if not texto_norm or not rol:
        return None

    keywords = _keywords_rol(rol)

    niveles = [
        "muy alto",
        "medio-alto",
        "alto",
        "moderado",
        "medio",
        "bajo",
        "crítico",
        "critico",
    ]

    for kw in keywords:
        for nivel in niveles:
            patron = rf"{re.escape(nivel)}[^.;,\n]*para el\s+{re.escape(kw)}"
            if re.search(patron, texto_norm):
                return _normalizar_nivel(nivel)

            patron2 = rf"{re.escape(nivel)}[^.;,\n]*para la\s+{re.escape(kw)}"
            if re.search(patron2, texto_norm):
                return _normalizar_nivel(nivel)

    return None


def _inferir_rol_contraparte(resultado: Dict[str, Any], rol_analizado: str) -> str:
    metadata_presentacion = (
        resultado.get("metadata_sistema", {})
                .get("metadata_presentacion", {})
        or {}
    )
    partes_con_rol = metadata_presentacion.get("partes_con_rol", []) or []

    rol_analizado_txt = _texto(rol_analizado).lower()

    for parte in partes_con_rol:
        parte_txt = _texto(parte)
        if "(" in parte_txt and ")" in parte_txt:
            rol_visible = parte_txt.rsplit("(", 1)[1].replace(")", "").strip()
            if rol_visible and rol_visible.lower() != rol_analizado_txt:
                return rol_visible

    mapa = {
        "cliente": "Proveedor",
        "proveedor": "Cliente",
        "arrendador / locatore": "Arrendatario / conduttore",
        "arrendatario / conduttore": "Arrendador / locatore",
        "arrendatarios / conduttori": "Arrendador / locatore",
        "artista": "Productora",
        "productora": "Artista",
        "productor": "Artista",
    }

    return mapa.get(rol_analizado, "Contraparte")


# =========================================================
# HELPERS DE NIVELES
# =========================================================

ORDEN_NIVEL = {
    "bajo": 1,
    "medio": 2,
    "medio-alto": 3,
    "alto": 4,
    "critico": 5,
}

NIVEL_POR_ORDEN = {
    1: "bajo",
    2: "medio",
    3: "medio-alto",
    4: "alto",
    5: "critico",
}


def _subir_nivel(nivel: str, pasos: int = 1) -> str:
    base = ORDEN_NIVEL.get(_normalizar_nivel(nivel), 2)
    nuevo = min(5, base + pasos)
    return NIVEL_POR_ORDEN[nuevo]


def _bajar_nivel(nivel: str, pasos: int = 1) -> str:
    base = ORDEN_NIVEL.get(_normalizar_nivel(nivel), 2)
    nuevo = max(1, base - pasos)
    return NIVEL_POR_ORDEN[nuevo]


def _peso_severidad_riesgo(severidad: str) -> float:
    sev = _texto(severidad).lower()
    pesos = {
        "baja": 0.5,
        "media": 1.0,
        "media-alta": 1.6,
        "alta": 2.4,
        "critica": 3.2,
        "crítica": 3.2,
    }
    return pesos.get(sev, 1.0)


# =========================================================
# CONTEXTO LOCATIVO
# =========================================================

def _es_contexto_locativo(resultado: Dict[str, Any], rol_analizado: str, rol_contraparte: str) -> bool:
    tipo_contrato = _texto(
        (resultado.get("nucleo_contractual", {}) or {}).get("tipo_contrato", "")
    ).lower()

    texto_roles = f"{_texto(rol_analizado).lower()} {_texto(rol_contraparte).lower()}"

    palabras = [
        "arrendamiento",
        "arrendador",
        "arrendatario",
        "arrendatarios",
        "locazione",
        "locatore",
        "conduttore",
        "conduttori",
        "alquiler",
        "vivienda habitual",
    ]

    return any(p in tipo_contrato or p in texto_roles for p in palabras)


def _extraer_riesgos_clasificados(resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
    riesgos = (
        resultado.get("analisis_profesional", {})
                .get("riesgos_clasificados", {})
        or {}
    )

    salida: List[Dict[str, Any]] = []
    for categoria in riesgos.values():
        if not isinstance(categoria, list):
            continue
        for riesgo in categoria:
            if isinstance(riesgo, dict):
                salida.append(riesgo)

    return salida


def _inferir_direccion_locativa_desde_riesgo(descripcion: str) -> str:
    """
    Devuelve:
    - "arrendatario"
    - "arrendador"
    - "ambas"

    Heurística conservadora:
    se usa SOLO en contratos locativos y SOLO para mejorar reparto,
    no para cambiar la severidad contractual.
    """
    txt = _texto(descripcion).lower()

    patrones_arrendatario = [
        "no puede ser suspendido",
        "no puede ser suspendida",
        "no puede suspender",
        "prohibición de suspender pagos",
        "prohibicion de suspender pagos",
        "limita defensas ante incumplimientos del arrendador",
        "devolución está sujeta a verificación",
        "devolucion esta sujeta a verificacion",
        "depósito de garantía",
        "deposito de garantia",
        "gastos de registro",
        "gastos condominiales",
        "acceso al inmueble",
        "visitas en caso de venta",
        "nueva renta",
        "prórroga automática",
        "prorroga automatica",
        "seis meses de antelación",
        "seis meses de antelacion",
        "exonera expresamente al arrendador",
        "no será responsable",
        "no sera responsable",
        "interrupciones no imputables",
        "subarriendo",
        "comodato",
        "mantenimiento de sistemas térmicos",
        "mantenimiento de sistemas termicos",
        "recuperar el inmueble",
        "facultad del arrendador",
        "limitar reclamaciones",
        "limita reclamaciones",
    ]

    patrones_arrendador = [
        "derecho a indemnización",
        "derecho a indemnizacion",
        "restitución",
        "restitucion",
        "si no cumple con el uso declarado",
        "debe indemnizar",
        "obligación del arrendador",
        "obligacion del arrendador",
        "responsabilidad del arrendador",
    ]

    if any(p in txt for p in patrones_arrendatario):
        return "arrendatario"

    if any(p in txt for p in patrones_arrendador):
        return "arrendador"

    return "ambas"


def _inferir_niveles_locativos_por_clausulas(
    resultado: Dict[str, Any],
    rol_analizado: str,
    rol_contraparte: str,
    severidad_nivel_default: str,
) -> Optional[Dict[str, str]]:
    """
    Usa el contenido de riesgos clasificados para repartir exposición
    en contratos locativos cuando el resumen no alcanza.

    No se aplica a NDA ni a otros contratos generales.
    """
    if not _es_contexto_locativo(resultado, rol_analizado, rol_contraparte):
        return None

    riesgos = _extraer_riesgos_clasificados(resultado)
    if not riesgos:
        return None

    score_arrendatario = 0.0
    score_arrendador = 0.0

    for riesgo in riesgos:
        descripcion = _texto(riesgo.get("descripcion"))
        severidad = _texto(riesgo.get("severidad", "media"))
        peso = _peso_severidad_riesgo(severidad)

        direccion = _inferir_direccion_locativa_desde_riesgo(descripcion)

        if direccion == "arrendatario":
            score_arrendatario += peso * 1.0
            score_arrendador += peso * 0.15
        elif direccion == "arrendador":
            score_arrendador += peso * 1.0
            score_arrendatario += peso * 0.15
        else:
            score_arrendatario += peso * 0.45
            score_arrendador += peso * 0.45

    if score_arrendatario == 0 and score_arrendador == 0:
        return None

    rol_a = _texto(rol_analizado).lower()
    rol_c = _texto(rol_contraparte).lower()

    if "arrendat" in rol_a or "conduttor" in rol_a:
        score_parte = score_arrendatario
        score_contra = score_arrendador
    elif "arrendador" in rol_a or "locatore" in rol_a:
        score_parte = score_arrendador
        score_contra = score_arrendatario
    else:
        return None

    nivel_base = _normalizar_nivel(severidad_nivel_default)

    # Regla de reparto:
    # - si una parte supera claramente a la otra, se diferencia un escalón
    # - si la supera mucho, dos escalones
    # - si están cerca, se mantiene igual
    if score_parte >= score_contra * 1.8:
        nivel_parte = nivel_base
        nivel_contra = _bajar_nivel(nivel_base, 2)
    elif score_parte >= score_contra * 1.25:
        nivel_parte = nivel_base
        nivel_contra = _bajar_nivel(nivel_base, 1)
    elif score_contra >= score_parte * 1.8:
        nivel_contra = nivel_base
        nivel_parte = _bajar_nivel(nivel_base, 2)
    elif score_contra >= score_parte * 1.25:
        nivel_contra = nivel_base
        nivel_parte = _bajar_nivel(nivel_base, 1)
    else:
        nivel_parte = nivel_base
        nivel_contra = nivel_base

    return {
        "parte": nivel_parte,
        "contraparte": nivel_contra,
    }


# =========================================================
# OBTENCIÓN DE NIVELES DIRECCIONALES
# =========================================================

def _obtener_niveles_direccionales(
    resultado: Dict[str, Any],
    rol_analizado: str,
    rol_contraparte: str,
    nivel_default: str,
) -> Dict[str, str]:
    resumen = (
        resultado.get("informe_cliente", {})
                .get("resumen_ejecutivo", {})
        or {}
    )

    nivel_global_txt = _texto(resumen.get("nivel_riesgo_global"))

    # 1. Intento explícito por rol
    nivel_parte = _extraer_nivel_para_rol(nivel_global_txt, rol_analizado)
    nivel_contraparte = _extraer_nivel_para_rol(nivel_global_txt, rol_contraparte)

    # 2. Si el resumen trae ambos niveles explícitos, se respetan tal cual.
    #    Esto preserva NDA y otros casos ya correctos.
    if nivel_parte and nivel_contraparte:
        return {
            "parte": _normalizar_nivel(nivel_parte),
            "contraparte": _normalizar_nivel(nivel_contraparte),
        }

    # 3. Si es contrato locativo, intentamos inferencia por cláusulas.
    #    Esta capa corrige justamente los casos donde el resumen es:
    #    - genérico ("moderado")
    #    - o menciona solo un lado ("moderado para el arrendatario")
    niveles_locativos = _inferir_niveles_locativos_por_clausulas(
        resultado=resultado,
        rol_analizado=rol_analizado,
        rol_contraparte=rol_contraparte,
        severidad_nivel_default=nivel_default,
    )

    if niveles_locativos:
        # Si solo uno venía explícito, lo respetamos y completamos el otro con heurística.
        if nivel_parte and not nivel_contraparte:
            return {
                "parte": _normalizar_nivel(nivel_parte),
                "contraparte": niveles_locativos["contraparte"],
            }
        if nivel_contraparte and not nivel_parte:
            return {
                "parte": niveles_locativos["parte"],
                "contraparte": _normalizar_nivel(nivel_contraparte),
            }
        # Si ninguno venía explícito, usamos la heurística locativa completa.
        return niveles_locativos

    # 4. Si no es locativo y no hay niveles explícitos, mantenemos el comportamiento anterior.
    if not nivel_parte and not nivel_contraparte:
        nivel_general = _normalizar_nivel(nivel_global_txt if nivel_global_txt else nivel_default)
        nivel_parte = nivel_general
        nivel_contraparte = nivel_general

    # 5. Si falta solo uno y no es locativo:
    #    en vez de usar el nivel del contrato (que puede inflar artificialmente),
    #    bajamos un escalón desde el que sí vino explícito.
    if nivel_parte and not nivel_contraparte:
        nivel_contraparte = _bajar_nivel(_normalizar_nivel(nivel_parte), 1)
    elif nivel_contraparte and not nivel_parte:
        nivel_parte = _bajar_nivel(_normalizar_nivel(nivel_contraparte), 1)

    if not nivel_parte:
        nivel_parte = _normalizar_nivel(nivel_default)
    if not nivel_contraparte:
        nivel_contraparte = _normalizar_nivel(nivel_default)

    return {
        "parte": _normalizar_nivel(nivel_parte),
        "contraparte": _normalizar_nivel(nivel_contraparte),
    }


# =========================================================
# API PRINCIPAL
# =========================================================

def enriquecer_scoring_dual(resultado: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte el bloque scoring actual en una salida más clara:

    - severidad_contrato
    - riesgo_parte_analizada
    - riesgo_contraparte

    Mantiene también aliases legacy:
    - score_total
    - nivel_riesgo
    """
    if not isinstance(resultado, dict):
        return resultado

    scoring = resultado.get("scoring", {}) or {}
    metadata_presentacion = (
        resultado.get("metadata_sistema", {})
                .get("metadata_presentacion", {})
        or {}
    )

    rol_analizado = _texto(metadata_presentacion.get("rol_contractual_detectado")) or "Parte analizada"
    rol_contraparte = _inferir_rol_contraparte(resultado, rol_analizado)

    severidad_score = float(scoring.get("score_total", 0) or 0)
    severidad_nivel = _normalizar_nivel(scoring.get("nivel_riesgo", "medio"))

    niveles = _obtener_niveles_direccionales(
        resultado=resultado,
        rol_analizado=rol_analizado,
        rol_contraparte=rol_contraparte,
        nivel_default=severidad_nivel,
    )

    score_parte = round(severidad_score * _factor_score_por_nivel(niveles["parte"]), 2)
    score_contraparte = round(severidad_score * _factor_score_por_nivel(niveles["contraparte"]), 2)

    scoring["severidad_contrato"] = {
        "score": severidad_score,
        "nivel": severidad_nivel,
        "fundamento": "Mide qué tan exigente, severo o litigioso es el contrato en sí mismo."
    }

    scoring["riesgo_parte_analizada"] = {
        "score": score_parte,
        "nivel": niveles["parte"],
        "rol": rol_analizado,
        "fundamento": "Mide qué tan expuesta queda la parte analizada según el contenido del contrato y la perspectiva seleccionada."
    }

    scoring["riesgo_contraparte"] = {
        "score": score_contraparte,
        "nivel": niveles["contraparte"],
        "rol": rol_contraparte,
        "fundamento": "Mide qué tan expuesta queda la contraparte en relación con las mismas cláusulas."
    }

    # Aliases legacy: se mantienen para no romper API, Word ni UI previos.
    scoring["score_total"] = severidad_score
    scoring["nivel_riesgo"] = severidad_nivel

    resultado["scoring"] = scoring
    return resultado