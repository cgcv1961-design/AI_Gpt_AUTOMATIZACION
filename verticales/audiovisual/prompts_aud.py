"""
verticales/audiovisual/prompts_aud.py
-------------------------------------

Prompts oficiales para la vertical AUDIOVISUAL.

OBJETIVO
--------
Definir el prompt base para contratos del sector audiovisual,
orientado a producir una salida JSON rica, consistente y útil
como fuente única de verdad del sistema.

PRINCIPIO DE DISEÑO
-------------------
JSON = fuente única de verdad

Esto significa que:
- el modelo debe devolver un JSON suficientemente rico
- el normalizador puede completar faltantes
- el Word NO debe inventar contenido fuera del JSON final

CRITERIO ESPECIAL
-----------------
La severidad NO debe ser generada por el LLM.
La severidad será calculada externamente por lógica determinística.

VERSIÓN
-------
Esta versión amplía la salida audiovisual para acercarla al nivel
de riqueza analítica de la vertical GENERAL, incorporando:

- resumen ejecutivo estructurado
- puntos críticos
- hallazgos principales
- implicancias estratégicas
- preguntas clave antes de firmar
- conclusión profesional
- nivel de confianza del análisis

NOTA
----
El modelo debe devolver EXCLUSIVAMENTE JSON válido en español.
No debe incluir texto fuera del JSON.
"""

VERSION_PROMPT_AU = "3.0_audiovisual_json_rico_deterministico"


def construir_prompt_audiovisual(contrato: str) -> str:
    """
    Construye el prompt para la vertical AUDIOVISUAL.

    Parámetros
    ----------
    contrato : str
        Texto completo del contrato a analizar.

    Retorna
    -------
    str
        Prompt final a enviar al modelo.
    """

    return f"""
El siguiente contrato pertenece al sector audiovisual.
Puede estar redactado en cualquier idioma.

Analízalo con enfoque especializado en:
- producción audiovisual
- interpretación artística
- cesión y explotación de derechos
- licencias
- distribución
- plataformas
- exclusividad
- seguros
- obligaciones operativas
- riesgos comerciales y reputacionales

IMPORTANTE
----------
1. Devuelve EXCLUSIVAMENTE un JSON válido en español.
2. No agregues explicación, comentario, introducción ni texto fuera del JSON.
3. No uses markdown.
4. No inventes datos no presentes en el contrato. Si un dato no puede inferirse, usa null o string vacío según corresponda.
5. NO incluyas severidad en los riesgos.
   La severidad será calculada externamente por el sistema.
6. El objetivo es producir un JSON suficientemente rico para que luego el Word
   salga exclusivamente de este JSON, sin reinterpretaciones paralelas.

INSTRUCCIONES DE ANÁLISIS
-------------------------
Analiza especialmente:

A) NÚCLEO CONTRACTUAL
- tipo de contrato
- partes
- duración
- precio / contraprestación
- moneda
- cualquier texto de plazo si es más expresivo que una simple duración en meses

B) RIESGOS SECTORIALES
Detecta riesgos relevantes del contrato audiovisual.
Cada riesgo debe describirse de forma concreta, clara y breve.

Cada elemento dentro de "riesgos_sectoriales" debe contener EXACTAMENTE:
- descripcion (string)
- impacto (legal|financiero|operativo|reputacional|mixto)
- recomendacion (string)

NO incluir severidad.
La severidad será calculada externamente.

C) RESUMEN EJECUTIVO PARA CLIENTE
Debe poder ser leído por un prospect o cliente no técnico.
Debe ser claro, profesional y útil para tomar decisiones.

D) PUNTOS CRÍTICOS PRINCIPALES
Lista breve de los puntos más delicados o negociables.

E) HALLAZGOS PRINCIPALES
Lista de observaciones relevantes que resumen el problema contractual.

F) IMPLICANCIAS ESTRATÉGICAS
Consecuencias probables a mediano plazo si el contrato se firma sin cambios.

G) PREGUNTAS CLAVE ANTES DE FIRMAR
Preguntas concretas que conviene resolver antes de firmar el contrato.

H) CONCLUSIÓN PROFESIONAL
Cierre técnico breve y claro.

I) NIVEL DE CONFIANZA DEL ANÁLISIS
Debe indicar:
- general: alto | medio | bajo
- fundamento: explicación breve de por qué el nivel de confianza es ese
  (por ejemplo: texto claro, información incompleta, cláusulas ambiguas, etc.)

FORMATO JSON EXACTO
-------------------
{{
  "nucleo_contractual": {{
    "tipo_contrato": "",
    "partes": [],
    "duracion_meses": null,
    "duracion_texto": "",
    "precio_total": null,
    "moneda": ""
  }},
  "analisis_sectorial": {{
    "riesgos_sectoriales": [
      {{
        "descripcion": "",
        "impacto": "legal",
        "recomendacion": ""
      }}
    ],
    "nivel_confianza_analisis": {{
      "general": "",
      "fundamento": ""
    }}
  }},
  "informe_cliente": {{
    "resumen_ejecutivo": {{
      "vision_general": "",
      "nivel_riesgo_global": "",
      "puntos_criticos": []
    }},
    "informe_detallado": {{
      "hallazgos_principales": [],
      "implicancias_estrategicas_mediano_plazo": [],
      "preguntas_clave_antes_de_firmar": [],
      "conclusion_profesional": ""
    }},
    "recomendacion_profesional": ""
  }}
}}

REGLAS ADICIONALES DE CALIDAD
-----------------------------
- "vision_general" debe ser breve, clara y profesional.
- "nivel_riesgo_global" debe ser una formulación textual simple para cliente.
- "puntos_criticos" debe ser una lista de frases cortas.
- "hallazgos_principales" debe ser una lista de observaciones relevantes.
- "implicancias_estrategicas_mediano_plazo" debe ser una lista concreta, no abstracta.
- "preguntas_clave_antes_de_firmar" debe contener preguntas reales, útiles y accionables.
- "conclusion_profesional" debe ser una síntesis técnica final.
- Si no hay precio claro, usar null en "precio_total".
- Si no hay duración clara en meses, usar null en "duracion_meses".
- Si el plazo está expresado de forma narrativa y eso aporta valor, completar también "duracion_texto".
- "partes" debe ser una lista simple de strings.

Contrato:
{contrato}
"""