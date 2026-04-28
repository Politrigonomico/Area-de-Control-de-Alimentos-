"""
Panel de Reportes — Alta Visibilidad con Tarjetas Azules.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from database.db import get_session
from utils.ui_helpers import (
    center_window, error_dialog, info_dialog,
)

# Configuración de accesibilidad local
F_GRANDE = ("Segoe UI", 14)
F_BOTON  = ("Segoe UI", 13, "bold")
F_TITULO = ("Segoe UI", 26, "bold")

COLOR_BG = "#FFFFFF"       # Fondo de la pantalla (Blanco)
COLOR_TXT = "#000000"      # Texto general (Negro)
CARD_BG = "#1a3a5c"        # Fondo de las tarjetas (Azul oscuro institucional)
CARD_FG = "#ffffff"        # Texto dentro de las tarjetas (Blanco)

class ReportesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG)
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(header, text="PANEL DE REPORTES", font=F_TITULO, 
                 bg=COLOR_BG, fg=COLOR_TXT).pack(anchor="w")
        
        tk.Label(header, text="Seleccioná un reporte para generar el documento PDF.", 
                 font=F_GRANDE, bg=COLOR_BG, fg="#333333").pack(anchor="w")

        grid_frame = tk.Frame(self, bg=COLOR_BG, padx=10, pady=10)
        grid_frame.pack(fill="both", expand=True)
        
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        cards = [
            ("📋  Padrón de Establecimientos",
             "Lista de todos los locales comerciales con sus datos.",
             self._rpt_establecimientos),
            ("💰  Estado de Deudas",
             "Resumen de pagos pendientes y realizados por año.",
             self._rpt_deudas),
            ("🏪  Ficha de Establecimiento",
             "Todos los datos y deudas de un local específico.",
             self._rpt_ficha),
            ("🔍  Registro de Auditorías",
             "Listado de inspecciones realizadas en un rango de fechas.",
             self._rpt_auditorias),
        ]

        for i, (titulo, desc, cmd) in enumerate(cards):
            row = i // 2
            col = i % 2
            
            # Tarjeta con fondo Azul Oscuro y letras Blancas
            card = tk.LabelFrame(grid_frame, text=f" {titulo} ", font=F_BOTON,
                                 bg=CARD_BG, fg=CARD_FG, bd=2, padx=20, pady=20)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
            tk.Label(card, text=desc, font=F_GRANDE, bg=CARD_BG, fg="#e2e8f0",
                     wraplength=400, justify="left").pack(anchor="w", pady=(0, 20))
            
            btn = tk.Button(card, text="GENERAR PDF AHORA", font=F_BOTON,
                            bg="#f7fafc", fg=CARD_BG, padx=25, pady=12,
                            relief="raised", cursor="hand2", command=cmd)
            btn.pack(anchor="w")

    def _ask_save_path(self, default_name: str) -> str | None:
        return filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            initialfile=default_name,
            title="Guardar reporte como...",
        )

    def _open_file(self, path: str):
        try:
            if os.name == 'nt': os.startfile(path)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", path])
        except: pass

    def _iniciar_carga(self):
        self.winfo_toplevel().config(cursor="wait")
        self.update()

    def _detener_carga(self):
        self.winfo_toplevel().config(cursor="")
        self.update()

    # --- Lógica de generación ---

    def _rpt_establecimientos(self):
        from reports.pdf_reports import reporte_establecimientos
        var = tk.BooleanVar(value=True)
        win = tk.Toplevel(self); win.title("Opciones"); win.grab_set()
        win.config(bg=COLOR_BG); center_window(win, 400, 180)
        
        tk.Label(win, text="¿Incluir solo locales activos?", font=F_GRANDE, bg=COLOR_BG).pack(pady=20)
        tk.Checkbutton(win, text="Sí, excluir bajas", variable=var, font=F_GRANDE, bg=COLOR_BG).pack()
        
        def generar():
            win.destroy()
            path = self._ask_save_path(f"padron_{datetime.now().strftime('%Y%m%d')}.pdf")
            if not path: return
            self._iniciar_carga()
            try:
                session = get_session()
                reporte_establecimientos(session, path, solo_activos=var.get())
                session.close(); self._detener_carga()
                self._open_file(path)
            except Exception as ex: self._detener_carga(); error_dialog(self, "Error", str(ex))
        tk.Button(win, text="GENERAR", font=F_BOTON, command=generar, bg="#CBD5E0").pack(pady=20)

    def _rpt_deudas(self):
        from reports.pdf_reports import reporte_deudas
        win = tk.Toplevel(self); win.title("Opciones Deuda"); win.grab_set()
        win.config(bg=COLOR_BG); center_window(win, 400, 250)
        
        f = tk.Frame(win, bg=COLOR_BG, padx=20, pady=20); f.pack()
        tk.Label(f, text="Año (vacio=todos):", font=F_GRANDE, bg=COLOR_BG).grid(row=0, column=0, pady=10)
        e_anio = tk.Entry(f, font=F_GRANDE, width=10); e_anio.grid(row=0, column=1)
        
        v_imp = tk.BooleanVar(value=False)
        tk.Checkbutton(f, text="Solo deudas impagas", variable=v_imp, font=F_GRANDE, bg=COLOR_BG).grid(row=1, column=0, columnspan=2, pady=10)
        
        def generar():
            anio = int(e_anio.get()) if e_anio.get().isdigit() else None
            win.destroy()
            path = self._ask_save_path(f"deudas_{anio or 'todas'}.pdf")
            if not path: return
            self._iniciar_carga()
            try:
                session = get_session()
                reporte_deudas(session, path, anio=anio, solo_impagas=v_imp.get())
                session.close(); self._detener_carga()
                self._open_file(path)
            except Exception as ex: self._detener_carga(); error_dialog(self, "Error", str(ex))
        tk.Button(win, text="GENERAR", font=F_BOTON, command=generar, bg="#CBD5E0").pack()

    def _rpt_ficha(self):
        from reports.pdf_reports import reporte_ficha_establecimiento
        from database.models import Establecimiento
        win = tk.Toplevel(self); win.title("Ficha Local"); win.grab_set()
        win.config(bg=COLOR_BG); center_window(win, 550, 200)
        
        tk.Label(win, text="Seleccioná el establecimiento:", font=F_GRANDE, bg=COLOR_BG).pack(pady=15)
        session = get_session()
        estabs = session.query(Establecimiento).order_by(Establecimiento.nombre_establecimiento).all()
        emap = {f"{e.codigo_establecimiento} - {e.nombre_establecimiento}": e.codigo_establecimiento for e in estabs}
        session.close()
        
        cb = ttk.Combobox(win, values=list(emap.keys()), width=50, font=("Segoe UI", 12), state="readonly")
        cb.pack(pady=10)
        
        def generar():
            if not cb.get(): return
            codigo = emap[cb.get()]; win.destroy()
            path = self._ask_save_path(f"ficha_{codigo}.pdf")
            if not path: return
            self._iniciar_carga()
            try:
                session = get_session()
                reporte_ficha_establecimiento(session, path, codigo)
                session.close(); self._detener_carga()
                self._open_file(path)
            except Exception as ex: self._detener_carga(); error_dialog(self, "Error", str(ex))
        tk.Button(win, text="GENERAR FICHA", font=F_BOTON, command=generar, bg="#CBD5E0").pack(pady=15)

    def _rpt_auditorias(self):
        from reports.pdf_reports import reporte_auditorias
        from utils.ui_helpers import parse_date_str
        win = tk.Toplevel(self); win.title("Filtro Auditorías"); win.grab_set()
        win.config(bg=COLOR_BG); center_window(win, 450, 250)
        
        f = tk.Frame(win, bg=COLOR_BG, padx=20, pady=20); f.pack()
        tk.Label(f, text="Desde (dd/mm/aaaa):", font=F_GRANDE, bg=COLOR_BG).grid(row=0, column=0, pady=10)
        e_desde = tk.Entry(f, font=F_GRANDE, width=15); e_desde.grid(row=0, column=1)
        
        tk.Label(f, text="Hasta (dd/mm/aaaa):", font=F_GRANDE, bg=COLOR_BG).grid(row=1, column=0, pady=10)
        e_hasta = tk.Entry(f, font=F_GRANDE, width=15); e_hasta.grid(row=1, column=1)
        
        def generar():
            d_str, h_str = e_desde.get().strip(), e_hasta.get().strip()
            f_desde = parse_date_str(d_str) if d_str else None
            f_hasta = parse_date_str(h_str) if h_str else None
            win.destroy()
            path = self._ask_save_path("auditorias_filtradas.pdf")
            if not path: return
            self._iniciar_carga()
            try:
                session = get_session()
                reporte_auditorias(session, path, fecha_desde=f_desde, fecha_hasta=f_hasta)
                session.close(); self._detener_carga()
                self._open_file(path)
            except Exception as ex: self._detener_carga(); error_dialog(self, "Error", str(ex))
        tk.Button(win, text="GENERAR AUDITORÍAS", font=F_BOTON, command=generar, bg="#CBD5E0").pack()