"""
Panel de Reportes PDF.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from database.db import get_session
from utils.ui_helpers import (
    COLORS, FONT_TITLE, FONT_NORMAL,
    center_window, error_dialog, info_dialog,
)


class ReportesFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ttk.Label(self, text="Reportes PDF", font=FONT_TITLE).pack(anchor="w", pady=(0, 20))

        cards = [
            ("📋  Padrón de Establecimientos",
             "Lista completa de establecimientos con datos y estado de trámite.",
             self._rpt_establecimientos),
            ("💰  Estado de Deudas",
             "Detalle de deudas por año, período y estado de pago.",
             self._rpt_deudas),
            ("🏪  Ficha de Establecimiento",
             "Ficha individual con todos los datos e historial de deudas.",
             self._rpt_ficha),
            ("🔍  Registro de Auditorías",
             "Listado completo de auditorías realizadas.",
             self._rpt_auditorias),
        ]

        for titulo, desc, cmd in cards:
            card = ttk.LabelFrame(self, text=titulo, padding=14)
            card.pack(fill="x", padx=4, pady=6)
            ttk.Label(card, text=desc, font=("Segoe UI", 11),
                      foreground=COLORS["text_light"]).pack(anchor="w", pady=(0, 8))
            ttk.Button(card, text="Generar PDF →", command=cmd).pack(anchor="w")

    def _ask_save_path(self, default_name: str) -> str | None:
        return filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            initialfile=default_name,
            title="Guardar reporte como...",
        )

    def _open_pdf(self, path: str):
        """Intenta abrir el PDF con el visor del sistema."""
        try:
            import subprocess, sys
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _rpt_establecimientos(self):
        from reports.pdf_reports import reporte_establecimientos

        var = tk.BooleanVar(value=True)
        win = tk.Toplevel(self)
        win.title("Opciones")
        win.resizable(False, False)
        center_window(win, 320, 140)
        win.grab_set()
        ttk.Label(win, text="¿Solo establecimientos activos?",
                  padding=14).pack()
        ttk.Checkbutton(win, text="Solo activos (excluir bajas)",
                        variable=var).pack()
        def generar():
            win.destroy()
            path = self._ask_save_path(
                f"padron_establecimientos_{datetime.now().strftime('%Y%m%d')}.pdf")
            if not path:
                return
            try:
                session = get_session()
                reporte_establecimientos(session, path, solo_activos=var.get())
                session.close()
                info_dialog(self, "Listo", f"PDF generado:\n{path}")
                self._open_pdf(path)
            except Exception as ex:
                error_dialog(self, "Error al generar PDF", str(ex))
        ttk.Button(win, text="Generar", style="Success.TButton",
                   command=generar, padding=6).pack(pady=10)

    def _rpt_deudas(self):
        from reports.pdf_reports import reporte_deudas

        win = tk.Toplevel(self)
        win.title("Opciones — Deudas")
        win.resizable(False, False)
        center_window(win, 320, 200)
        win.grab_set()
        f = ttk.Frame(win, padding=16)
        f.pack(fill="both")

        ttk.Label(f, text="Año (vacío = todos):").grid(row=0, column=0, sticky="w", pady=4)
        e_anio = ttk.Entry(f, width=8)
        e_anio.grid(row=0, column=1, sticky="w", pady=4)

        v_imp = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Solo deudas impagas", variable=v_imp).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=4)

        def generar():
            anio_s = e_anio.get().strip()
            anio   = int(anio_s) if anio_s.isdigit() else None
            win.destroy()
            path = self._ask_save_path(
                f"deudas_{anio or 'todos'}_{datetime.now().strftime('%Y%m%d')}.pdf")
            if not path:
                return
            try:
                session = get_session()
                reporte_deudas(session, path, anio=anio, solo_impagas=v_imp.get())
                session.close()
                info_dialog(self, "Listo", f"PDF generado:\n{path}")
                self._open_pdf(path)
            except Exception as ex:
                error_dialog(self, "Error al generar PDF", str(ex))

        ttk.Button(f, text="Generar", style="Success.TButton",
                   command=generar, padding=6).grid(row=2, column=0, columnspan=2, pady=12)

    def _rpt_ficha(self):
        from reports.pdf_reports import reporte_ficha_establecimiento
        from database.models import Establecimiento

        win = tk.Toplevel(self)
        win.title("Ficha de establecimiento")
        win.resizable(False, False)
        center_window(win, 400, 140)
        win.grab_set()
        f = ttk.Frame(win, padding=16)
        f.pack(fill="both")

        ttk.Label(f, text="Establecimiento:").grid(row=0, column=0, sticky="w", pady=6, padx=(0, 8))
        session = get_session()
        estabs = session.query(Establecimiento).order_by(
            Establecimiento.nombre_establecimiento).all()
        estab_map = {
            f"{e.codigo_establecimiento} — {(e.nombre_establecimiento or '').title()}": e.codigo_establecimiento
            for e in estabs}
        session.close()

        cb = ttk.Combobox(f, values=list(estab_map.keys()), width=36, state="readonly")
        cb.grid(row=0, column=1, sticky="ew", pady=6)

        def generar():
            key = cb.get()
            if not key:
                error_dialog(win, "Error", "Seleccioná un establecimiento.")
                return
            codigo = estab_map[key]
            win.destroy()
            path = self._ask_save_path(f"ficha_{codigo}_{datetime.now().strftime('%Y%m%d')}.pdf")
            if not path:
                return
            try:
                session = get_session()
                reporte_ficha_establecimiento(session, path, codigo)
                session.close()
                info_dialog(self, "Listo", f"PDF generado:\n{path}")
                self._open_pdf(path)
            except Exception as ex:
                error_dialog(self, "Error al generar PDF", str(ex))

        ttk.Button(f, text="Generar", style="Success.TButton",
                   command=generar, padding=6).grid(row=1, column=0, columnspan=2, pady=10)

    def _rpt_auditorias(self):
        from reports.pdf_reports import reporte_auditorias

        path = self._ask_save_path(
            f"auditorias_{datetime.now().strftime('%Y%m%d')}.pdf")
        if not path:
            return
        try:
            session = get_session()
            reporte_auditorias(session, path)
            session.close()
            info_dialog(self, "Listo", f"PDF generado:\n{path}")
            self._open_pdf(path)
        except Exception as ex:
            error_dialog(self, "Error al generar PDF", str(ex))
