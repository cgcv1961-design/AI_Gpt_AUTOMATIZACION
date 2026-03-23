"""
AI_GPT_AUTOMATIZACION/config.py

Configuración oficial del sistema.
Separa:
- Semántica comercial (alias de perfiles)
- Infraestructura técnica (modelo por perfil canónico)
"""

CONFIG = {

    # -----------------------------------------
    # Alias de perfiles (normalización semántica)
    # -----------------------------------------
    "alias_perfiles": {
        "automatico": "basico",
        "asistido": "tecnico"
    },

    # -----------------------------------------
    # Modelos por perfil canónico
    # -----------------------------------------
    "modelos_por_perfil": {
        "basico": "gpt-4.1-mini",
        "tecnico": "gpt-4.1",
        "experto": "gpt-4.1"
    },

    # -----------------------------------------
    # Metadata del sistema
    # -----------------------------------------
    "sistema": {
        "version": "2.1",
        "nombre": "Analizador Contractual Multi-Vertical"
    }
}