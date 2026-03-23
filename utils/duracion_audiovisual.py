"""
utils/duracion_audiovisual.py
-----------------------------

Normalización segura de duración para la vertical AUDIOVISUAL.

Objetivo:
- preservar la duración textual original cuando exista
- calcular duración en días si se detectan fechas claras
- no romper compatibilidad con campos existentes
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional


MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def _texto_no_vacio(valor: Any) -> Optional[str]:
    if valor in (None, "", [], {}):
        return None
    texto = str(valor).strip()
    return texto or None


def _parsear_fecha_es(texto: str) -> Optional[datetime]:
    """
    Intenta parsear fechas del tipo:
    - 1 de Abril de 2026
    - 15 de junio de 2026
    """
    patron = re.compile(
        r"(\d{1,2})\s+de\s+([A-Za-záéíóúÁÉÍÓÚ]+)\s+de\s+(\d{4})",
        re.IGNORECASE
    )
    m = patron.search(texto)
    if not m:
        return None

    dia = int(m.group(1))
    mes_txt = m.group(2).strip().lower()
    anio = int(m.group(3))

    mes = MESES.get(mes_txt)
    if not mes:
        return None

    try:
        return datetime(anio, mes, dia)
    except ValueError:
        return None


def _extraer_fechas_del_texto(texto: str) -> list[datetime]:
    """
    Extrae todas las fechas en español presentes en un texto.
    """
    patron = re.compile(
        r"(\d{1,2}\s+de\s+[A-Za-záéíóúÁÉÍÓÚ]+\s+de\s+\d{4})",
        re.IGNORECASE
    )

    fechas = []
    for match in patron.finditer(texto):
        fecha = _parsear_fecha_es(match.group(1))
        if fecha:
            fechas.append(fecha)

    return fechas


def enriquecer_duracion_audiovisual(resultado: Dict[str, Any], texto_contrato: str) -> Dict[str, Any]:
    """
    Enriquece el bloque nucleo_contractual del resultado audiovisual
    con duración textual y, cuando sea posible, duración en días.

    Importante:
    - NO elimina duracion_meses
    - NO cambia nada en GENERAL
    - agrega campos nuevos para mejorar Word/JSON
    """
    if not isinstance(resultado, dict):
        return resultado

    nucleo = resultado.get("nucleo_contractual")
    if not isinstance(nucleo, dict):
        return resultado

    # 1) Buscar un plazo textual ya devuelto por IA si existe
    duracion_texto = _texto_no_vacio(
        nucleo.get("duracion_texto")
    ) or _texto_no_vacio(
        nucleo.get("plazo_texto")
    ) or _texto_no_vacio(
        nucleo.get("plazo")
    ) or _texto_no_vacio(
        nucleo.get("duracion")
    )

    # 2) Si no existe, intentar capturarlo del contrato
    #    Buscamos una cláusula que empiece con "SEGUNDA – Plazo" o similar.
    if not duracion_texto and texto_contrato:
        patron_plazo = re.compile(
            r"(SEGUNDA\s*[–\-]\s*Plazo.*?)(?=\n[A-ZÁÉÍÓÚÑ]+\s*[–\-]|$)",
            re.IGNORECASE | re.DOTALL
        )
        m = patron_plazo.search(texto_contrato)
        if m:
            duracion_texto = m.group(1).strip()

    # 3) Si encontramos texto de plazo, guardarlo
    if duracion_texto:
        nucleo["duracion_texto"] = duracion_texto

        fechas = _extraer_fechas_del_texto(duracion_texto)
        if len(fechas) >= 2:
            fecha_inicio = fechas[0]
            fecha_fin = fechas[1]

            dias = (fecha_fin - fecha_inicio).days
            if dias > 0:
                nucleo["duracion_dias"] = dias
                nucleo["unidad_duracion"] = "dias"

    return resultado