"""
Panel de inicio — dashboard con estadísticas rápidas.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from database.db import get_session
from database.models import Establecimiento, Inscripto, Deuda, Auditoria
from utils.ui_helpers import COLORS, FONT_TITLE, FONT_HEADER, FONT_NORMAL


class DashboardFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        # Encabezado
        header = tk.Frame(self, bg=COLORS["bg_sidebar"], height=90)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header,
                 text="Municipalidad de Fighiera",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORS["bg_sidebar"], fg="white").pack(pady=(16, 2))
        tk.Label(header,
                 text="Sistema de Gestión — Área de Alimentos",
                 font=("Segoe UI", 12),
                 bg=COLORS["bg_sidebar"], fg="#90cdf4").pack()

        # Tarjetas
        self.cards_frame = ttk.Frame(self, padding=20)
        self.cards_frame.pack(fill="x")

        # Alertas
        self.alerts_frame = ttk.LabelFrame(
            self, text="⚠  Deudas vencidas hoy o antes", padding=12)
        self.alerts_frame.pack(fill="x", padx=20, pady=(0, 16))

    def refresh(self):
        # Limpiar widgets anteriores
        for w in self.cards_frame.winfo_children():
            w.destroy()
        for w in self.alerts_frame.winfo_children():
            w.destroy()

        session = get_session()
        try:
            from sqlalchemy import func

            total_estab  = session.query(Establecimiento).filter_by(baja=False).count()
            total_bajas  = session.query(Establecimiento).filter_by(baja=True).count()
            total_inscr  = session.query(Inscripto).count()
            total_deudas = session.query(Deuda).filter_by(pago=False).count()
            total_audits = session.query(Auditoria).count()
            saldo_result = session.query(
                func.sum(Deuda.importe - Deuda.monto_abonado)
            ).filter(Deuda.pago == False).scalar() or 0.0

            # Deudas vencidas — extraer TODOS los datos necesarios
            # mientras la sesión está abierta para evitar DetachedInstanceError
            hoy = datetime.now()
            rows_vencidas = (
                session.query(Deuda)
                .filter(Deuda.pago == False, Deuda.vencimiento < hoy)
                .order_by(Deuda.vencimiento)
                .limit(8)
                .all()
            )

            # Serializar a dicts simples ANTES de cerrar la sesión
            vencidas = []
            for d in rows_vencidas:
                nombre = ""
                if d.establecimiento:
                    nombre = (d.establecimiento.nombre_establecimiento or "").title()
                vencidas.append({
                    "codigo": d.codigo_establecimiento or "",
                    "nombre": nombre,
                    "periodo": f"{d.periodo}/{d.anio}",
                    "vencimiento": d.vencimiento.strftime("%d/%m/%Y") if d.vencimiento else "—",
                    "saldo": d.saldo,
                })
        finally:
            session.close()

        # ── Tarjetas de estadísticas ─────────────────────────────────────────
        stats = [
            ("🏪", "Establecimientos activos",  str(total_estab),  COLORS["accent"]),
            ("👤", "Inscriptos / Titulares",     str(total_inscr),  "#6b46c1"),
            ("💰", "Deudas impagas",             str(total_deudas), COLORS["danger"]),
            ("🔍", "Auditorías registradas",      str(total_audits), COLORS["success"]),
            ("📉", "Establecimientos de baja",    str(total_bajas),  COLORS["text_light"]),
            ("💵", "Saldo adeudado total",        f"$ {saldo_result:,.2f}", COLORS["warning"]),
        ]

        for col, (icon, label, value, color) in enumerate(stats):
            row_idx = 0 if col < 3 else 1
            col_idx = col % 3
            card = tk.Frame(self.cards_frame, bg=COLORS["bg_panel"],
                            relief="flat", bd=0,
                            highlightbackground=COLORS["border"],
                            highlightthickness=1)
            card.grid(row=row_idx, column=col_idx,
                      padx=8, pady=8, sticky="nsew")
            self.cards_frame.columnconfigure(col_idx, weight=1)

            tk.Label(card, text=icon, font=("Segoe UI", 30),
                     bg=COLORS["bg_panel"]).pack(pady=(16, 4))
            tk.Label(card, text=value, font=("Segoe UI", 22, "bold"),
                     fg=color, bg=COLORS["bg_panel"]).pack()
            tk.Label(card, text=label, font=FONT_NORMAL,
                     fg=COLORS["text_light"], bg=COLORS["bg_panel"]).pack(pady=(2, 16))

        # ── Tabla de deudas vencidas ─────────────────────────────────────────
        if not vencidas:
            ttk.Label(self.alerts_frame,
                      text="Sin deudas vencidas pendientes. ✓",
                      foreground=COLORS["success"]).pack(anchor="w")
        else:
            cols   = ("estab", "nombre", "periodo", "vencimiento", "saldo")
            heads  = ("Código", "Establecimiento", "Período", "Vencimiento", "Saldo")
            widths = (90, 240, 90, 120, 120)
            tree = ttk.Treeview(self.alerts_frame, columns=cols,
                                show="headings",
                                height=min(len(vencidas), 6))
            for c, h, w in zip(cols, heads, widths):
                tree.heading(c, text=h, anchor="w")
                tree.column(c, width=w, anchor="w")
            for d in vencidas:
                tree.insert("", "end", tags=("vencido",), values=(
                    d["codigo"],
                    d["nombre"],
                    d["periodo"],
                    d["vencimiento"],
                    f"$ {d['saldo']:,.2f}",
                ))
            tree.tag_configure("vencido", background="#fff3cd",
                               foreground="#7c4f00")
            tree.pack(fill="x")

        ttk.Label(self.alerts_frame,
                  text=f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                  font=("Segoe UI", 10),
                  foreground=COLORS["text_light"]).pack(anchor="e")
