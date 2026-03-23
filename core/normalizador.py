from typing import Dict, List


SEVERIDADES_VALIDAS = {"baja", "media", "alta", "critica"}
IMPACTOS_VALIDOS = {"legal", "financiero", "operativo", "mixto"}


def normalizar_riesgos(resultado: Dict) -> Dict:
    """
    Garantiza que riesgos_detectados sea SIEMPRE
    una lista de dicts con estructura canónica:

    {
        "descripcion": str,
        "severidad": str,
        "impacto": str
    }
    """

    if not isinstance(resultado, dict):
        return resultado

    riesgos = resultado.get("riesgos_detectados", [])
    riesgos_normalizados: List[Dict] = []

    for r in riesgos:

        # Caso 1: el modelo devolvió string
        if isinstance(r, str):
            riesgos_normalizados.append({
                "descripcion": r.strip(),
                "severidad": "media",
                "impacto": "legal"
            })

        # Caso 2: el modelo devolvió dict
        elif isinstance(r, dict):

            descripcion = str(r.get("descripcion", "")).strip()

            severidad = str(r.get("severidad", "media")).lower()
            if severidad not in SEVERIDADES_VALIDAS:
                severidad = "media"

            impacto = str(r.get("impacto", "legal")).lower()
            if impacto not in IMPACTOS_VALIDOS:
                impacto = "legal"

            riesgos_normalizados.append({
                "descripcion": descripcion,
                "severidad": severidad,
                "impacto": impacto
            })

    resultado["riesgos_detectados"] = riesgos_normalizados

    return resultado