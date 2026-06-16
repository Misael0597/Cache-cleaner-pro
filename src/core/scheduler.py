"""
scheduler.py
Responsabilidad: Ejecutar la limpieza automática en segundo plano
según la configuración del usuario (intervalo o hora fija).
"""

import threading
import time
import schedule


class Scheduler:
    """
    Maneja la ejecución automática de la limpieza en segundo plano.
    Corre en un hilo separado para no bloquear la interfaz.
    """

    def __init__(self):
        self._hilo = None
        self._activo = False

    def iniciar(self, config_scheduler: dict, funcion_limpieza):
        """
        Inicia el scheduler según la configuración del usuario.
        - config_scheduler: sección 'scheduler' de settings.json
        - funcion_limpieza: función a ejecutar cuando toque limpiar
        """
        if not config_scheduler.get("enabled", False):
            return

        schedule.clear()

        modo = config_scheduler.get("mode", "interval")

        if modo == "interval":
            horas = config_scheduler.get("interval_hours", 24)
            schedule.every(horas).hours.do(funcion_limpieza)

        elif modo == "scheduled_time":
            hora = config_scheduler.get("scheduled_time", "03:00")
            schedule.every().day.at(hora).do(funcion_limpieza)

        self._activo = True
        self._hilo = threading.Thread(target=self._correr, daemon=True)
        self._hilo.start()

    def detener(self):
        """Detiene el scheduler y cancela todas las tareas programadas."""
        self._activo = False
        schedule.clear()

    def _correr(self):
        """Bucle interno que revisa cada minuto si hay tareas pendientes."""
        while self._activo:
            schedule.run_pending()
            time.sleep(60)

    def esta_activo(self) -> bool:
        """Retorna si el scheduler se encuentra corriendo actualmente."""
        return self._activo

    def proxima_ejecucion(self) -> str:
        """Retorna la fecha/hora de la próxima limpieza programada."""
        trabajos = schedule.get_jobs()
        if not trabajos:
            return "No programada"
        proxima = trabajos[0].next_run
        return proxima.strftime("%d/%m/%Y %H:%M")
