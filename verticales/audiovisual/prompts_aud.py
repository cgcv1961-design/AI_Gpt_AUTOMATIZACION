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

OBJETIVO DE ESTA VERSIÓN
------------------------
Mejorar:
- claridad
- concisión
- utilidad comercial
- legibilidad para prospectos no técnicos
- DIRECCIONALIDAD DEL RIESGO en audiovisual

NOVEDAD CLAVE
-------------
Cada riesgo debe indicar a quién afecta principalmente:
- artista
- productora
- ambas

Esto no reemplaza el scoring.
Sirve para orientar correctamente el reparto del riesgo en la capa determinística.
"""

VERSION_PROMPT_AU = "4.0_audiovisual_json_rico_con_direccion"


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

ESTILO DE SALIDA (OBLIGATORIO)
------------------------------
- Evitar repeticiones.
- Usar frases claras y relativamente breves.
- No sobre-explicar.
- Cada sección debe aportar información distinta.
- No repetir literalmente los mismos conceptos en resumen, hallazgos, recomendación y conclusión.
- Priorizar utilidad práctica para toma de decisión.

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
- afecta_principalmente_a (artista|productora|ambas)

NO incluir severidad.
La severidad será calculada externamente.

MUY IMPORTANTE SOBRE "afecta_principalmente_a"
----------------------------------------------
Usa:
- "artista" cuando la cláusula carga principalmente sobre el intérprete / artista
- "productora" cuando la cláusula carga principalmente sobre la productora
- "ambas" cuando el riesgo sea verdaderamente compartido o estructural

Ejemplos orientativos:
- cesión amplia, exclusividad, falta de regalías, rescisión unilateral por la productora, seguro limitado -> normalmente "artista"
- vacíos de resolución de disputas, cronograma, ambigüedad operativa común -> normalmente "ambas"
- obligaciones especialmente gravosas de pago o ejecución sobre la productora -> "productora"

C) RESUMEN EJECUTIVO
- Máximo 3 frases.
- Debe ser claro, profesional y útil para lectura rápida.
- Debe incluir:
  • idea central del contrato
  • nivel de riesgo global
  • 2 o 3 focos críticos si corresponde
- No repetir literalmente toda la lista de puntos críticos.

D) PUNTOS CRÍTICOS PRINCIPALES
- Lista breve.
- Cada punto como frase corta.
- Sin explicación adicional.

E) HALLAZGOS PRINCIPALES
- Lista de observaciones relevantes.
- Deben aportar información nueva.
- No repetir exactamente los puntos críticos.

F) IMPLICANCIAS ESTRATÉGICAS
- Consecuencias probables a mediano plazo.
- Deben ser concretas, no abstractas.

G) PREGUNTAS CLAVE ANTES DE FIRMAR
- Preguntas concretas, útiles y accionables.
- Deben servir para negociación o validación previa.

H) CONCLUSIÓN PROFESIONAL
- Máximo 1 párrafo.
- Debe cerrar el análisis con claridad.
- No repetir todo lo anterior.

I) RECOMENDACIÓN PROFESIONAL
- Máximo 1 párrafo corto.
- Debe ser accionable.
- No repetir todos los hallazgos.

J) NIVEL DE CONFIANZA DEL ANÁLISIS
Debe indicar:
- general: alto | medio | bajo
- fundamento: explicación breve de por qué el nivel de confianza es ese

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
        "recomendacion": "",
        "afecta_principalmente_a": "artista"
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
- "nivel_riesgo_global" debe ser una formulación textual simple.
- "puntos_criticos" debe ser una lista de frases cortas.
- "hallazgos_principales" debe ser una lista de observaciones relevantes.
- "implicancias_estrategicas_mediano_plazo" debe ser concreta.
- "preguntas_clave_antes_de_firmar" debe contener preguntas reales y útiles.
- "conclusion_profesional" debe ser una síntesis técnica final.
- "recomendacion_profesional" debe ser corta, clara y accionable.
- Si no hay precio claro, usar null en "precio_total".
- Si no hay duración clara en meses, usar null en "duracion_meses".
- Si el plazo está expresado de forma narrativa y eso aporta valor, completar también "duracion_texto".
- "partes" debe ser una lista simple de strings.

Contrato:
{contrato}
"""