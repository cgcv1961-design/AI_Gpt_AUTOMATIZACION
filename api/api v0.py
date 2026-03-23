"""
AI_GPT_AUTOMATIZACION/api.py

API principal del sistema de análisis contractual.
Arquitectura multi-vertical.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.router import analizar_contrato

app = FastAPI()


class ContratoRequest(BaseModel):
    contrato: str
    vertical: str
    perfil: str


@app.post("/analizar")
def analizar(request: ContratoRequest):
    """
    Endpoint principal.

    Recibe:
    - contrato
    - vertical (general, audiovisual, etc.)
    - perfil (basico, tecnico, experto)

    Devuelve:
    - JSON estructurado
    """

    try:
        resultado = analizar_contrato(
            contrato=request.contrato,
            vertical=request.vertical,
            perfil=request.perfil,
        )

        return resultado

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))