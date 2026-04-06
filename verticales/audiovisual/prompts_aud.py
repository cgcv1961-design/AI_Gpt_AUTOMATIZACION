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

CRITERIO ESPECIAL
-----------------
La severidad NO debe ser generada por el LLM.
La severidad será calculada externamente por lógica determinística.

OBJETIVO DE ESTA VERSIÓN
------------------------
1. Mejorar claridad y consistencia.
2. Intentar obtener dirección explícita del riesgo.
3. Pero sin romper el sistema si el modelo no devuelve ese campo.
"""

VERSION_PROMPT_AU = "4.1_audiovisual_json_rico_con_direccion_reforzada"


def construir_prompt_audiovisual(contrato: str) -> str:
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
5. NO incluyas severidad en los riesgos. La severidad será calculada externamente.
6. El objetivo es producir un JSON suficientemente rico para que luego el Word salga exclusivamente de este JSON.

ESTILO DE SALIDA
----------------
- Evitar repeticiones.
- Usar frases claras y breves.
- No sobre-explicar.
- Cada sección debe aportar información distinta.
- No repetir literalmente los mismos conceptos en resumen, hallazgos, recomendación y conclusión.

A) NÚCLEO CONTRACTUAL
---------------------
Incluye:
- tipo de contrato
- partes
- duración
- precio / contraprestación
- moneda
- duración textual si aporta valor

B) RIESGOS SECTORIALES
----------------------
Cada elemento dentro de "riesgos_sectoriales" debe contener:
- descripcion
- impacto
- recomendacion
- afecta_principalmente_a

Valores válidos de "afecta_principalmente_a":
- "artista"
- "productora"
- "ambas"

REGLA CRÍTICA
-------------
No omitir "afecta_principalmente_a".
Si no es perfectamente claro, estimarlo igual según la cláusula.

Ejemplos:
- cesión amplia, falta de regalías, exclusividad, rescisión unilateral por la productora, seguro limitado -> "artista"
- vacíos operativos o disputas estructurales -> "ambas"
- obligaciones o cargas claras de pago/ejecución sobre la productora -> "productora"

C) RESUMEN EJECUTIVO
--------------------
- máximo 3 frases
- claro y útil
- incluir idea central + nivel de riesgo global + focos críticos

D) PUNTOS CRÍTICOS PRINCIPALES
------------------------------
- lista breve
- frases cortas

E) HALLAZGOS PRINCIPALES
------------------------
- lista de observaciones relevantes
- sin repetir exactamente puntos críticos

F) IMPLICANCIAS ESTRATÉGICAS
----------------------------
- consecuencias probables a mediano plazo
- concretas

G) PREGUNTAS CLAVE ANTES DE FIRMAR
----------------------------------
- útiles y accionables

H) CONCLUSIÓN PROFESIONAL
-------------------------
- máximo 1 párrafo
- clara

I) RECOMENDACIÓN PROFESIONAL
----------------------------
- máximo 1 párrafo corto
- accionable

J) NIVEL DE CONFIANZA DEL ANÁLISIS
----------------------------------
Debe incluir:
- general: alto | medio | bajo
- fundamento: breve

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

Contrato:
{contrato}
"""