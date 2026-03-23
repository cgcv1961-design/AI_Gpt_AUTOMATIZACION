"""
verticales/general/prompts/prompt_general.py

Prompts oficiales para vertical GENERAL.
Versión determinística sin severidad generada por LLM.
"""

VERSION_PROMPT_GENERAL = "2.0_general_deterministico"


def construir_prompt_general(contrato: str, perfil: str) -> str:
    perfil = perfil.strip().lower()

    if perfil in ["automatico", "basico"]:
        return construir_prompt_basico(contrato)

    elif perfil in ["asistido", "tecnico"]:
        return construir_prompt_tecnico(contrato)

    else:
        raise ValueError(
            f"Perfil no soportado en vertical general: {perfil}"
        )


# --------------------------------------------------
# 🔹 MODO BASICO (Automático)
# --------------------------------------------------

def construir_prompt_basico(contrato: str) -> str:

    return f"""
El siguiente contrato puede estar redactado en cualquier idioma.

Analízalo jurídicamente.
Devuelve EXCLUSIVAMENTE un objeto JSON válido en español.

La clave "riesgos_detectados" debe ser una lista de objetos.

Cada objeto debe contener EXACTAMENTE:
- descripcion (string)
- impacto (legal|financiero|operativo|reputacional|mixto)

NO incluir severidad.
La severidad será calculada externamente.

No agregar texto fuera del JSON.
No usar markdown.
No usar ```json.
No explicar nada.

Formato exacto:

{{
  "tipo_contrato": "",
  "partes": [],
  "duracion_meses": null,
  "precio_mensual": null,
  "moneda": "",
  "riesgos_detectados": []
}}

Contrato:
{contrato}
"""


# --------------------------------------------------
# 🔹 MODO TECNICO (Asistido)
# --------------------------------------------------

def construir_prompt_tecnico(contrato: str) -> str:

    return f"""
El siguiente contrato puede estar redactado en cualquier idioma.

Analízalo con enfoque jurídico crítico.
Devuelve EXCLUSIVAMENTE un objeto JSON válido en español.

Dentro de "riesgos_clasificados", cada elemento debe contener EXACTAMENTE:
- descripcion (string)
- impacto (legal|financiero|operativo|reputacional|mixto)

NO incluir severidad.
La severidad será calculada externamente.

Formato exacto:

{{
  "nucleo_contractual": {{
    "tipo_contrato": "",
    "partes": [],
    "duracion_meses": null,
    "precio_mensual": null,
    "moneda": ""
  }},
  "analisis_profesional": {{
    "riesgos_clasificados": {{
      "legal": [],
      "economico": [],
      "operativo": [],
      "reputacional": []
    }},
    "evaluacion_equilibrio_contractual": "",
    "nivel_confianza_analisis": {{
      "general": "",
      "fundamento": ""
    }}
  }},
  "informe_cliente": {{
    "resumen_ejecutivo": {{
      "vision_general": "",
      "nivel_riesgo_global": "",
      "puntos_criticos": [],
      "recomendacion_estrategica_final": ""
    }},
    "informe_detallado": {{
      "hallazgos_principales": [],
      "implicancias_estrategicas_mediano_plazo": [],
      "preguntas_clave_antes_de_firmar": [],
      "conclusion_profesional": ""
    }}
  }}
}}

Contrato:
{contrato}
"""