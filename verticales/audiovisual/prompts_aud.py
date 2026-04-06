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
2. Reducir repeticiones entre secciones.
3. Hacer el resumen ejecutivo realmente corto y orientado a la parte analizada.
4. Mantener la dirección del riesgo como ayuda para la capa determinística.
5. Evitar que el modelo genere hallazgos, implicancias, conclusión y recomendación
   diciendo lo mismo con palabras distintas.
"""

VERSION_PROMPT_AU = "4.3_audiovisual_json_rico_menos_redundante"


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
7. Evita repeticiones entre secciones. Cada bloque debe aportar algo distinto.
8. Escribe en tono profesional, claro y concreto.

ESTILO DE SALIDA
----------------
- Usar frases claras y breves.
- No sobre-explicar.
- No repetir literalmente los mismos conceptos en resumen, puntos críticos, hallazgos, recomendación y conclusión.
- Priorizar utilidad práctica para la toma de decisión.
- Escribir para un usuario no técnico.

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
Debe ser MUY breve.
Máximo 2 frases.
Debe responder:
- qué significa este contrato para la parte analizada
- cuál es el foco principal de riesgo o ventaja

NO repetir una lista completa de cláusulas.
NO copiar textualmente puntos críticos.
NO usar lenguaje genérico tipo "el contrato regula..." si no aporta valor.

D) NIVEL DE RIESGO GLOBAL
-------------------------
Debe ser una frase breve y clara.
Cuando sea posible, indicar la dirección del riesgo, por ejemplo:
- "medio-alto para el artista, bajo para la productora"
- "bajo para la productora, medio-alto para el artista"

E) PUNTOS CRÍTICOS PRINCIPALES
------------------------------
Lista breve.
Máximo 3 puntos.
Cada punto como frase corta.
No agregar explicación.
No repetir frases enteras del resumen ejecutivo.

F) HALLAZGOS PRINCIPALES
------------------------
Lista de observaciones relevantes.
Máximo 4.
No repetir literalmente los puntos críticos.
Usar esta sección para agregar contexto o matiz, no para repetir.
Si un hallazgo ya quedó claro en puntos críticos, no volver a escribirlo igual.

G) IMPLICANCIAS ESTRATÉGICAS
----------------------------
Máximo 2.
Consecuencias probables a mediano plazo.
Concretas y distintas de hallazgos.
No repetir las mismas palabras de hallazgos.

H) PREGUNTAS CLAVE ANTES DE FIRMAR
----------------------------------
Máximo 5.
Útiles y accionables.

I) CONCLUSIÓN PROFESIONAL
-------------------------
Máximo 1 párrafo breve.
Debe cerrar el análisis sin repetir toda la lista anterior.
Debe sintetizar el desequilibrio o la lógica general del contrato.

J) RECOMENDACIÓN PROFESIONAL
----------------------------
Máximo 1 párrafo corto.
Debe ser accionable y concreta.
No repetir literalmente la conclusión.
Debe centrarse en qué negociar o aclarar.

K) NIVEL DE CONFIANZA DEL ANÁLISIS
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