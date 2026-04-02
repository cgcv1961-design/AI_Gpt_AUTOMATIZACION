"""
verticales/general/prompts/prompt_general.py

Prompts oficiales para vertical GENERAL.
Versión determinística sin severidad generada por LLM.

OBJETIVO DE ESTA VERSIÓN
------------------------
Mejorar la calidad comunicacional de la salida:
- menos verborragia
- menos repetición
- más claridad para usuario final
- misma estructura JSON
- misma compatibilidad con lógica determinística externa

IMPORTANTE
----------
- La severidad NO debe ser generada por el LLM.
- La severidad será calculada externamente.
- El modelo debe devolver EXCLUSIVAMENTE JSON válido en español.
"""

VERSION_PROMPT_GENERAL = "2.2_general_deterministico_claridad_roles"


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
    """
    Prompt básico:
    - salida corta
    - estructura simple
    - sin severidad
    """

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
    """
    Prompt técnico:
    - salida rica
    - estructura completa
    - enfoque crítico profesional
    - estilo optimizado para prospectos reales
    """

    return f"""
El siguiente contrato puede estar redactado en cualquier idioma.

Analízalo con enfoque jurídico crítico.
Devuelve EXCLUSIVAMENTE un objeto JSON válido en español.

IMPORTANTE
----------
1. No agregues texto fuera del JSON.
2. No uses markdown.
3. No inventes datos no presentes en el contrato.
4. Si algo no puede inferirse con razonable seguridad, usa null, "" o [] según corresponda.
5. NO incluyas severidad.
   La severidad será calculada externamente por lógica determinística del sistema.

ESTILO DE SALIDA (OBLIGATORIO)
------------------------------
- Escribe con claridad profesional.
- Evita repeticiones entre secciones.
- Evita verborragia.
- Cada sección debe aportar información nueva.
- Usa frases cortas y directas.
- No repitas el tipo de contrato si ya quedó claro en el núcleo contractual.
- No repitas literalmente los mismos puntos en resumen, recomendación y conclusión.
- Cuando menciones roles, usa formulaciones claras y consistentes.
- Si el contrato deja claro quién se beneficia y quién queda más expuesto, exprésalo de forma directa.

REGLAS POR SECCIÓN
------------------

A) RESUMEN EJECUTIVO ("vision_general")
- Máximo 3 frases.
- Debe servir para lectura rápida.
- Debe incluir:
  • idea principal del contrato
  • nivel de riesgo global
  • 2 o 3 focos realmente críticos
- No repetir literalmente toda la lista de puntos críticos.
- No usar introducciones largas.

B) NIVEL DE RIESGO GLOBAL
- Debe ser una formulación simple y comprensible.
- Ejemplos válidos:
  • "moderado"
  • "alto para el Proveedor"
  • "alto para el Proveedor; bajo para el Cliente"
  • "equilibrado con focos sensibles"

C) PUNTOS CRÍTICOS
- Lista breve.
- Cada punto debe ser una frase corta.
- Sin explicación adicional.

D) RECOMENDACIÓN ESTRATÉGICA FINAL
- Máximo 1 párrafo corto.
- Debe ser accionable.
- No repetir toda la información del resumen.
- Debe decir qué conviene revisar, negociar o validar.

E) HALLAZGOS PRINCIPALES
- Lista concreta.
- Cada hallazgo debe aportar algo nuevo.
- No repetir literalmente los puntos críticos.

F) IMPLICANCIAS ESTRATÉGICAS A MEDIANO PLAZO
- Deben ser consecuencias probables reales.
- No usar frases abstractas vacías.
- No repetir hallazgos.

G) PREGUNTAS CLAVE ANTES DE FIRMAR
- Deben ser preguntas útiles, concretas y accionables.
- No usar preguntas demasiado genéricas si el contrato permite ser más específico.

H) CONCLUSIÓN PROFESIONAL
- Máximo 1 párrafo.
- Debe cerrar el análisis.
- Puede mencionar score una sola vez si aporta valor.
- No repetir todos los hallazgos otra vez.
- Debe sonar firme y profesional.

Dentro de "riesgos_clasificados", cada elemento debe contener EXACTAMENTE:
- descripcion (string)
- impacto (legal|financiero|operativo|reputacional|mixto)

NO incluir severidad.
La severidad será calculada externamente.

FORMATO EXACTO
--------------
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