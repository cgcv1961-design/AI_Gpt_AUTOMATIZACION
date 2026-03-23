# verticales/general/validador_respuesta.py

from typing import Dict, List

SEVERIDADES_VALIDAS = {"baja", "media", "alta", "critica"}
IMPACTOS_VALIDOS = {
    "legal",
    "financiero",
    "operativo",
    "reputacional",
    "mixto"
}



class ErrorEstructura(Exception):
    pass


# =========================
# VALIDADOR MODO BASICO
# =========================

def validar_respuesta_basica(data: Dict) -> Dict:

    claves_obligatorias = {
        "tipo_contrato",
        "partes",
        "duracion_meses",
        "precio_mensual",
        "moneda",
        "riesgos_detectados"
    }

    if set(data.keys()) != claves_obligatorias:
        raise ErrorEstructura("Estructura root inválida en modo básico")

    if not isinstance(data["partes"], list):
        raise ErrorEstructura("partes debe ser lista")

    if not isinstance(data["riesgos_detectados"], list):
        raise ErrorEstructura("riesgos_detectados debe ser lista")

    for riesgo in data["riesgos_detectados"]:
        _validar_riesgo(riesgo)

    return data


# =========================
# VALIDADOR MODO TECNICO
# =========================

def validar_respuesta_tecnica(data: Dict) -> Dict:

    if "nucleo_contractual" not in data:
        raise ErrorEstructura("Falta nucleo_contractual")

    if "analisis_profesional" not in data:
        raise ErrorEstructura("Falta analisis_profesional")

    if "informe_cliente" not in data:
        raise ErrorEstructura("Falta informe_cliente")

    riesgos = data["analisis_profesional"]["riesgos_clasificados"]

    for categoria in ["legal", "economico", "operativo", "reputacional"]:
        if categoria not in riesgos:
            raise ErrorEstructura(f"Falta categoria {categoria}")

        if not isinstance(riesgos[categoria], list):
            raise ErrorEstructura(f"{categoria} debe ser lista")

        for riesgo in riesgos[categoria]:
            _validar_riesgo(riesgo)

    return data


# =========================
# VALIDADOR DE RIESGO
# =========================

def _validar_riesgo(riesgo: Dict):

    claves = {"descripcion", "severidad", "impacto"}

    if set(riesgo.keys()) != claves:
        raise ErrorEstructura("Estructura de riesgo inválida")

    if riesgo["severidad"] not in SEVERIDADES_VALIDAS:
        raise ErrorEstructura("Severidad inválida")

    if riesgo["impacto"] not in IMPACTOS_VALIDOS:
        raise ErrorEstructura("Impacto inválido")