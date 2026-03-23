# ==============================
# verticales/general/analizador.py
# Motor de análisis de contratos
# ==============================

# Cliente oficial de OpenAI
from openai import OpenAI

# Librería para manejar JSON
import json

# Creamos el cliente una sola vez
client = OpenAI()


def analizar_contrato(texto: str) -> dict:
    """
    Recibe el texto completo de un contrato
    y devuelve un diccionario Python con
    la estructura JSON solicitada.
    """

    # ----------------------------
    # Leer configuración externa
    # ----------------------------
    # Esto permite cambiar modelo sin tocar código
    with open("config.json", "r", encoding="utf-8") as cfg:
        config = json.load(cfg)

    modelo = config["modelo"]

    # ----------------------------
    # Construcción del prompt
    # ----------------------------
    prompt = f"""
El siguiente contrato está redactado en italiano.

Analízalo jurídicamente y devuelve EXCLUSIVAMENTE un objeto JSON válido en español.

No agregues texto antes ni después.
No expliques nada.
No uses markdown.
No uses ```json.

Los valores del JSON deben estar en español.

El formato debe ser exactamente:

{{
  "tipo_contrato": "",
  "partes": [],
  "duracion_meses": 0,
  "precio_mensual": 0,
  "moneda": "",
  "riesgos_detectados": []
}}

Contrato:
{texto}
"""

    # ----------------------------
    # Llamada al modelo
    # ----------------------------
    response = client.responses.create(
        model=modelo,
        input=prompt
    )

    # Extraemos texto limpio
    resultado_texto = response.output_text.strip()

    print("----- RESPUESTA CRUDA DEL MODELO -----")

    print("TIPO:", type(resultado_texto))
    print("CONTENIDO:")
    print(resultado_texto[:500])

    # Convertimos texto a diccionario Python
    return json.loads(resultado_texto)

