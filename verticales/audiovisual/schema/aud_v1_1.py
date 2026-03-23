"""
schemas/aud_v1_1.py

Define el esquema oficial del
Analizador Contractual v1.1_aud
Vertical Audiovisual.

Este esquema representa el contrato formal
de salida del modo 'aud_tecnico'.

No debe modificarse sin versionar.
"""

VERSION_SCHEMA = "1.1_aud"


def obtener_estructura_base() -> dict:
    """
    Retorna la estructura base del JSON oficial.

    Se utiliza para:
    - Documentación
    - Validación futura
    - Pruebas
    - Control de integridad
    """

    return {
        "metadata": {
            "version": VERSION_SCHEMA,
            "tipo_contrato": "",
            "fecha_analisis": "",
            "idioma_detectado": ""
        },
        "resumen_ejecutivo": "",
        "evaluacion_general": {
            "score_riesgo": {
                "nivel": "",
                "valor": 0,
                "fundamento": ""
            }
        },
        "clausulas_clave": {
            "objeto": "",
            "plazo": "",
            "remuneracion": "",
            "territorio": {
                "alcance": "",
                "detalle": "",
                "observaciones": ""
            },
            "exclusividad": {
                "aplica": True,
                "detalle": ""
            },
            "cesion_derechos": {
                "nivel": "",
                "alcance": "",
                "observaciones": ""
            },
            "confidencialidad": "",
            "rescision": "",
            "jurisdiccion": ""
        },
        "riesgos_detectados": [],
        "fortalezas_detectadas": [],
        "puntos_a_revisar": []
    }
