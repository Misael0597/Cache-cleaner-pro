"""
app.py
Responsabilidad: Interfaz gráfica principal de CacheCleaner Pro.
Construida con CustomTkinter para una UI moderna en Windows.
"""
# pylint: disable=import-error, wrong-import-order, attribute-defined-outside-init, missing-class-docstring, unused-import, line-too-long, import-outside-toplevel, missing-final-newline


import customtkinter as ctk
import threading
from datetime import datetime

from core.scanner import escanear_dispositivo, formatear_tamano
from core.cleaner import ejecutar_limpieza
from core.config_manager import (
    inicializar, cargar_settings, guardar_settings, agregar_sesion
)
from core.scheduler import Scheduler


# ── Tema visual ──────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Configuración inicial
        inicializar()
        self.settings = cargar_settings()
        self.scheduler = Scheduler()
        self.scan_result = None

        # Ventana principal
        self.title("CacheCleaner Pro")
        self.geometry("700x600")
        self.resizable(False, False)

        self._construir_ui()
        self._iniciar_scheduler()

        # Escaneo automático al abrir
        self.after(500, self._escanear)

    # ── Construcción de la UI ─────────────────────────────────

    def _construir_ui(self):
        # Título
        ctk.CTkLabel(
            self,
            text="⚡ CacheCleaner Pro",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(pady=(30, 5))

        ctk.CTkLabel(
            self,
            text="Mantén tu PC rápida y libre de caché",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(pady=(0, 20))

        # ── Tarjeta de estado ──
        self.frame_estado = ctk.CTkFrame(self, corner_radius=16)
        self.frame_estado.pack(padx=40, fill="x")

        self.lbl_espacio = ctk.CTkLabel(
            self.frame_estado,
            text="Escaneando...",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        self.lbl_espacio.pack(pady=(20, 5))

        self.lbl_archivos = ctk.CTkLabel(
            self.frame_estado,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.lbl_archivos.pack(pady=(0, 20))

        # ── Barra de progreso ──
        self.barra_progreso = ctk.CTkProgressBar(self, width=500)
        self.barra_progreso.pack(pady=(25, 5))
        self.barra_progreso.set(0)

        self.lbl_progreso = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.lbl_progreso.pack()

        # ── Botón principal ──
        self.btn_limpiar = ctk.CTkButton(
            self,
            text="🧹  Limpiar Ahora",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=55,
            width=280,
            corner_radius=14,
            command=self._limpiar
        )
        self.btn_limpiar.pack(pady=25)

        # ── Pestañas ──
        self.tabs = ctk.CTkTabview(self, width=620, height=180)
        self.tabs.pack(padx=40, pady=(0, 20))

        self.tabs.add("Categorías")
        self.tabs.add("Automático")
        self.tabs.add("Historial")

        self._construir_tab_categorias()
        self._construir_tab_automatico()
        self._construir_tab_historial()

    def _construir_tab_categorias(self):
        tab = self.tabs.tab("Categorías")
        scroll = ctk.CTkScrollableFrame(tab, height=130)
        scroll.pack(fill="both", expand=True)

        self.switches_categorias = {}
        categorias = self.settings.get("categories", {})

        # Dos columnas
        col1 = ctk.CTkFrame(scroll, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True)
        col2 = ctk.CTkFrame(scroll, fg_color="transparent")
        col2.pack(side="left", fill="both", expand=True)

        items = list(categorias.items())
        for i, (key, config) in enumerate(items):
            var = ctk.BooleanVar(value=config.get("enabled", True))
            columna = col1 if i % 2 == 0 else col2

            sw = ctk.CTkSwitch(
                columna,
                text=config.get("label", key),
                variable=var,
                font=ctk.CTkFont(size=12),
                command=lambda k=key, v=var: self._toggle_categoria(k, v)
            )
            sw.pack(anchor="w", padx=10, pady=3)
            self.switches_categorias[key] = var

    def _construir_tab_automatico(self):
        tab = self.tabs.tab("Automático")

        fila1 = ctk.CTkFrame(tab, fg_color="transparent")
        fila1.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(fila1, text="Limpieza automática:", font=ctk.CTkFont(size=13)).pack(side="left")

        config_sch = self.settings.get("scheduler", {})
        self.var_auto = ctk.BooleanVar(value=config_sch.get("enabled", False))

        sw_auto = ctk.CTkSwitch(
            fila1,
            text="",
            variable=self.var_auto,
            command=self._toggle_scheduler
        )
        sw_auto.pack(side="left", padx=15)

        fila2 = ctk.CTkFrame(tab, fg_color="transparent")
        fila2.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(fila2, text="Cada:", font=ctk.CTkFont(size=13)).pack(side="left")

        self.opt_intervalo = ctk.CTkOptionMenu(
            fila2,
            values=["6 horas", "12 horas", "24 horas", "48 horas"],
            command=self._cambiar_intervalo,
            width=130
        )
        self.opt_intervalo.pack(side="left", padx=10)

        horas = config_sch.get("interval_hours", 24)
        self.opt_intervalo.set(f"{horas} horas")

        self.lbl_proxima = ctk.CTkLabel(
            tab,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.lbl_proxima.pack(pady=5)

    def _construir_tab_historial(self):
        tab = self.tabs.tab("Historial")
        self.scroll_historial = ctk.CTkScrollableFrame(tab, height=130)
        self.scroll_historial.pack(fill="both", expand=True)
        self._actualizar_historial_ui()

    # ── Lógica principal ──────────────────────────────────────

    def _escanear(self):
        """Escanea el dispositivo en un hilo separado."""
        def tarea():
            categorias = self.settings.get("categories", {})
            self.scan_result = escanear_dispositivo(categorias)
            self.after(0, self._actualizar_ui_escaneo)

        threading.Thread(target=tarea, daemon=True).start()

    def _actualizar_ui_escaneo(self):
        if not self.scan_result:
            return
        total = self.scan_result["total_bytes"]
        archivos = self.scan_result["total_files"]
        self.lbl_espacio.configure(text=formatear_tamano(total))
        self.lbl_archivos.configure(text=f"{archivos:,} archivos detectados")

    def _limpiar(self):
        """Ejecuta la limpieza en un hilo separado para no congelar la UI."""
        self.btn_limpiar.configure(state="disabled", text="Limpiando...")
        self.barra_progreso.set(0)

        def tarea():
            categorias = self.settings.get("categories", {})
            sesion = ejecutar_limpieza(categorias, callback=self._callback_progreso)
            agregar_sesion(sesion)
            self.after(0, lambda: self._finalizar_limpieza(sesion))

        threading.Thread(target=tarea, daemon=True).start()

    def _callback_progreso(self, progreso: float, label: str):
        """Actualiza la barra de progreso desde el hilo de limpieza."""
        self.after(0, lambda: self.barra_progreso.set(progreso))
        self.after(0, lambda: self.lbl_progreso.configure(text=label))

    def _finalizar_limpieza(self, sesion: dict):
        resultado = sesion["result"]
        liberado = formatear_tamano(resultado["total_bytes_freed"])
        archivos = resultado["total_files_deleted"]

        self.lbl_espacio.configure(text=liberado)
        self.lbl_archivos.configure(text=f"{archivos:,} archivos eliminados ✓")
        self.lbl_progreso.configure(text="Limpieza completada")
        self.barra_progreso.set(1)
        self.btn_limpiar.configure(state="normal", text="🧹  Limpiar Ahora")
        self._actualizar_historial_ui()

        # Re-escanear después de limpiar
        self.after(2000, self._escanear)

    def _toggle_categoria(self, key: str, var: ctk.BooleanVar):
        self.settings["categories"][key]["enabled"] = var.get()
        guardar_settings(self.settings)

    def _toggle_scheduler(self):
        self.settings["scheduler"]["enabled"] = self.var_auto.get()
        guardar_settings(self.settings)
        self._iniciar_scheduler()

    def _cambiar_intervalo(self, valor: str):
        horas = int(valor.split()[0])
        self.settings["scheduler"]["interval_hours"] = horas
        guardar_settings(self.settings)
        self._iniciar_scheduler()

    def _iniciar_scheduler(self):
        self.scheduler.detener()
        config_sch = self.settings.get("scheduler", {})
        if config_sch.get("enabled"):
            categorias = self.settings.get("categories", {})
            self.scheduler.iniciar(
                config_sch,
                lambda: ejecutar_limpieza(categorias)
            )
            proxima = self.scheduler.proxima_ejecucion()
            self.lbl_proxima.configure(text=f"Próxima limpieza: {proxima}")
        else:
            self.lbl_proxima.configure(text="Limpieza automática desactivada")

    def _actualizar_historial_ui(self):
        from core.config_manager import cargar_historial

        for widget in self.scroll_historial.winfo_children():
            widget.destroy()

        historial = cargar_historial()
        sesiones = historial.get("sessions", [])

        if not sesiones:
            ctk.CTkLabel(
                self.scroll_historial,
                text="Aún no hay limpiezas registradas.",
                text_color="gray"
            ).pack(pady=20)
            return

        for sesion in sesiones[:20]:
            fecha = sesion.get("timestamp", "")[:16].replace("T", " ")
            liberado = formatear_tamano(sesion["result"]["total_bytes_freed"])
            tipo = "Manual" if sesion.get("type") == "manual" else "Automática"

            ctk.CTkLabel(
                self.scroll_historial,
                text=f"🗓 {fecha}   💾 {liberado} liberados   🔧 {tipo}",
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(fill="x", padx=10, pady=2)