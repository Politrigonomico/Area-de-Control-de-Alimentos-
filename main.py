"""
Sistema de Gestión — Área de Alimentos — Municipalidad de Fighiera
Punto de entrada principal.
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db
from utils.ui_helpers import (
    COLORS, FONT_NORMAL,
    center_window, configure_treeview_style,
)


class App(tk.Tk):
    NAV_ITEMS = [
        ("🏠",  "Inicio",           "dashboard"),
        ("🏪",  "Establecimientos", "establecimientos"),
        ("👤",  "Inscriptos",       "inscriptos"),
        ("💰",  "Deudas y Pagos",   "deudas"),
        ("🔍",  "Auditorías",       "auditorias"),
        ("🧼",  "Sanidad",          "sanidad"),
        ("📋",  "Rubros / Emisión", "rubros"),
        # ("📄",  "Reportes PDF",     "reportes"),  # temporalmente deshabilitado
    ]

    def __init__(self):
        super().__init__()
        self.title("Sistema Área de Alimentos — Fighiera")
        self.configure(bg=COLORS["bg_sidebar"])
        center_window(self, 1280, 820)
        self.minsize(1000, 680)

        configure_treeview_style()
        init_db()

        self._frames = {}
        self._build_layout()
        self._navigate("dashboard")

    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=COLORS["bg_sidebar"], width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="🌽", font=("Segoe UI", 32),
                 bg=COLORS["bg_sidebar"], fg="white").pack(pady=(24, 4))
        tk.Label(self.sidebar, text="Área de\nAlimentos",
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["bg_sidebar"], fg="white",
                 justify="center").pack(pady=(0, 2))
        tk.Label(self.sidebar, text="Fighiera",
                 font=("Segoe UI", 9),
                 bg=COLORS["bg_sidebar"], fg="#90cdf4").pack(pady=(0, 16))
        ttk.Separator(self.sidebar).pack(fill="x", padx=12, pady=4)

        self._nav_buttons = {}
        for icon, label, key in self.NAV_ITEMS:
            btn = tk.Button(
                self.sidebar,
                text=f"  {icon}  {label}",
                font=FONT_NORMAL,
                anchor="w", bd=0, relief="flat",
                padx=16, pady=11,
                bg=COLORS["bg_sidebar"], fg="white",
                activebackground=COLORS["accent"],
                activeforeground="white",
                cursor="hand2",
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x")
            self._nav_buttons[key] = btn

        # Contenedor apilable — todos los frames van en la misma celda grid
        self.content = tk.Frame(self, bg=COLORS["bg_app"])
        self.content.pack(side="left", fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _navigate(self, key: str):
        # Actualizar botones sidebar
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(bg=COLORS["accent"],
                              font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=COLORS["bg_sidebar"],
                              font=FONT_NORMAL)

        # Crear frame la primera vez
        if key not in self._frames:
            frame = self._create_frame(key)
            # Todos se colocan en fila=0, col=0; tkraise los apila
            frame.grid(row=0, column=0, sticky="nsew",
                       padx=20, pady=20)
            self._frames[key] = frame

        # Traer al frente — confiable en Windows/Linux/Mac
        self._frames[key].tkraise()

        # Refrescar datos si el módulo lo soporta
        if hasattr(self._frames[key], "refresh"):
            self._frames[key].refresh()

    def _create_frame(self, key: str):
        parent = self.content

        if key == "dashboard":
            from ui.dashboard import DashboardFrame
            return DashboardFrame(parent)
        elif key == "establecimientos":
            from ui.establecimientos import EstablecimientosFrame
            return EstablecimientosFrame(parent)
        elif key == "inscriptos":
            from ui.inscriptos import InscriptosFrame
            return InscriptosFrame(parent)
        elif key == "deudas":
            from ui.deudas import DeudasFrame
            return DeudasFrame(parent)
        elif key == "auditorias":
            from ui.sanidad_auditorias import AuditoriasFrame
            return AuditoriasFrame(parent)
        elif key == "sanidad":
            from ui.sanidad_auditorias import SanidadFrame
            return SanidadFrame(parent)
        elif key == "rubros":
            from ui.rubros_emision import RubrosFrame
            return RubrosFrame(parent)
        elif key == "reportes":
            from ui.reportes import ReportesFrame
            return ReportesFrame(parent)
        else:
            f = ttk.Frame(parent)
            ttk.Label(f, text=f"Módulo '{key}' no implementado.").pack(pady=40)
            return f


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as exc:
        import traceback
        messagebox.showerror("Error fatal", traceback.format_exc())
        raise
