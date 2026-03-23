"""
utils/progreso.py
-----------------

Utilidades simples de progreso visual para consola.

Objetivo:
- evitar la sensación de "pausa muerta" durante llamadas largas
- no alterar la lógica del análisis
- ser reutilizable en GENERAL y AUDIOVISUAL
"""

import itertools
import sys
import threading
import time
from contextlib import contextmanager


class SpinnerConsola:
    """
    Spinner simple para procesos largos en consola.

    Uso:
        spinner = SpinnerConsola("⏳ Ejecutando análisis IA")
        spinner.start()
        try:
            ...
        finally:
            spinner.stop("✔ Análisis completado")
    """

    def __init__(self, mensaje: str = "Procesando", intervalo: float = 0.12):
        self.mensaje = mensaje
        self.intervalo = intervalo
        self._stop_event = threading.Event()
        self._thread = None

    def _run(self):
        for frame in itertools.cycle(["|", "/", "-", "\\"]):
            if self._stop_event.is_set():
                break

            sys.stdout.write(f"\r{self.mensaje} {frame}")
            sys.stdout.flush()
            time.sleep(self.intervalo)

        # Limpieza visual de la línea
        sys.stdout.write("\r" + " " * (len(self.mensaje) + 4) + "\r")
        sys.stdout.flush()

    def start(self):
        """
        Inicia el spinner.
        """
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, mensaje_final: str | None = None):
        """
        Detiene el spinner y opcionalmente imprime un mensaje final.
        """
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=1.0)

        if mensaje_final:
            print(mensaje_final)


@contextmanager
def spinner(mensaje: str, mensaje_final: str | None = None):
    """
    Context manager para usar el spinner de forma segura.

    Ejemplo:
        with spinner("⏳ Ejecutando análisis IA", "✔ Análisis completado"):
            respuesta = llamada_larga()
    """
    s = SpinnerConsola(mensaje)
    s.start()
    try:
        yield
    finally:
        s.stop(mensaje_final=mensaje_final)