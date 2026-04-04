"""
verticales/audiovisual/scoring_engine_productor.py
--------------------------------------------------


Este módulo actúa como adaptador del sistema de scoring
para la vertical audiovisual.

IMPORTANTE:
- Usa el motor unificado (scoring_engine.py)
- Mantiene compatibilidad con el resto del sistema

OBJETIVO:
Evitar duplicación de lógica.
"""

from core.scoring_engine import calcular_scoring_dual


def calcular_scoring_productor(riesgos_clasificados, rol_analizado="artista"):
    """
    Wrapper para audiovisual.

    Entrada:
        riesgos_clasificados: dict
        rol_analizado: str (artista, productor, etc.)

    Salida:
        dict scoring unificado
    """

    return calcular_scoring_dual(
        riesgos_clasificados,
        rol_analizado=rol_analizado
    )