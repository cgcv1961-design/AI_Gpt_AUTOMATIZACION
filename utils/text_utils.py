"""
text_utils.py

Funciones auxiliares para procesamiento de texto.
No contienen lógica de negocio.
"""

import re


def limpiar_texto(texto: str) -> str:
    """
    Limpia espacios innecesarios y normaliza saltos de línea.
    No altera el contenido jurídico.
    """

    if not isinstance(texto, str):
        raise ValueError("El contrato debe ser un string.")

    # Elimina espacios al inicio y final
    texto = texto.strip()

    # Normaliza múltiples saltos de línea
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto