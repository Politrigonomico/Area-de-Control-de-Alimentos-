"""
Panel de inicio — dashboard con estadísticas rápidas y backup de DB.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import get_session
from database.models import Establecimiento, Inscripto, Deuda, Auditoria
from utils.ui_helpers import COLORS, FONT_TITLE, FONT_HEADER, FONT_NORMAL
from utils.backup import hacer_backup, listar_backups, BACKUP_DIR


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

        # ── Franja de backup ────────────────────────────────────────────────
        backup_bar = tk.Frame(self, bg=COLORS["bg_panel"],
                              highlightbackground=COLORS["border"],
                              highlightthickness=1)
        backup_bar.pack(fill="x", padx=0, pady=(0, 2))

        self.lbl_ultimo_backup = tk.Label(
            backup_bar,
            text="Último backup: calculando…",
            font=("Segoe UI", 10),
            bg=COLORS["bg_panel"],
            fg=COLORS["text_light"],
        )
        self.lbl_ultimo_backup.pack(side="left", padx=14, pady=6)

        tk.Button(
            backup_bar,
            text="💾  Hacer backup ahora",
            font=("Segoe UI", 10),
            bg=COLORS["accent"], fg="white",
            relief="flat", bd=0,
            padx=12, pady=4,
            cursor="hand2",
            activebackground="#1a5090",
            command=self._hacer_backup,
        ).pack(side="right", padx=10, pady=6)

        tk.Button(
            backup_bar,
            text="📂  Ver backups",
            font=("Segoe UI", 10),
            bg=COLORS["bg_panel"], fg=COLORS["accent"],
            relief="flat", bd=0,
            padx=8, pady=4,
            cursor="hand2",
            command=self._ver_backups,
        ).pack(side="right", padx=4, pady=6)

        # Tarjetas
        self.cards_frame = ttk.Frame(self, padding=20)
        self.cards_frame.pack(fill="x")

        # Alertas
        self.alerts_frame = ttk.LabelFrame(
            self, text="⚠  Deudas vencidas hoy o antes", padding=12)
        self.alerts_frame.pack(fill="x", padx=20, pady=(0, 16))

    def _hacer_backup(self):
        try:
            destino = hacer_backup()
            messagebox.showinfo(
                "Backup realizado",
                f"Base de datos respaldada correctamente.\n\n{destino}",
            )
            self._actualizar_label_backup()
        except Exception as ex:
            messagebox.showerror("Error en backup", str(ex))

    def _ver_backups(self):
        """Abre ventana con listado de backups disponibles."""
        win = tk.Toplevel(self)
        win.title("Backups disponibles")
        win.resizable(True, False)
        win.geometry("580x320")
        win.grab_set()

        ttk.Label(win, text=f"Carpeta: {BACKUP_DIR}",
                  font=("Segoe UI", 9),
                  foreground=COLORS["text_light"]).pack(anchor="w", padx=12, pady=(10, 2))

        cols   = ("nombre", "fecha", "tamaño")
        heads  = ("Archivo", "Fecha", "Tamaño (KB)")
        widths = (280, 140, 90)

        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=12, pady=6)

        vsb  = ttk.Scrollbar(frame, orient="vertical")
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            height=10, yscrollcommand=vsb.set)
        vsb.config(command=tree.yview)
        for c, h, w in zip(cols, heads, widths):
            tree.heading(c, text=h, anchor="w")
            tree.column(c, width=w, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        backups = listar_backups()
        if backups:
            for nombre, fecha, tam in backups:
                tree.insert("", "end", values=(nombre, fecha, tam))
        else:
            ttk.Label(win, text="No hay backups todavía.",
                      foreground=COLORS["text_light"]).pack(pady=10)

        def abrir_carpeta():
            import subprocess, sys
            if sys.platform.startswith("win"):
                os.startfile(BACKUP_DIR)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", BACKUP_DIR])
            else:
                subprocess.Popen(["xdg-open", BACKUP_DIR])

        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Button(bar, text="📂  Abrir carpeta", command=abrir_carpeta).pack(side="left")
        ttk.Button(bar, text="Cerrar", command=win.destroy).pack(side="right")

    def _actualizar_label_backup(self):
        backups = listar_backups()
        if backups:
            _, fecha, tam = backups[0]
            self.lbl_ultimo_backup.config(
                text=f"Último backup: {fecha}  ({tam} KB)",
                fg=COLORS["success"],
            )
        else:
            self.lbl_ultimo_backup.config(
                text="Sin backups todavía. Se recomienda hacer uno antes de usar el sistema.",
                fg=COLORS["warning"],
            )

    def refresh(self):
        # Actualizar label de backup
        self._actualizar_label_backup()

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

            hoy = datetime.now()
            rows_vencidas = (
                session.query(Deuda)
                .filter(Deuda.pago == False, Deuda.vencimiento < hoy)
                .order_by(Deuda.vencimiento)
                .limit(8)
                .all()
            )

            vencidas = []
            for d in rows_vencidas:
                nombre = ""
                if d.establecimiento:
                    nombre = (d.establecimiento.nombre_establecimiento or "").title()
                vencidas.append({
                    "codigo":      d.codigo_establecimiento or "",
                    "nombre":      nombre,
                    "periodo":     f"{d.periodo}/{d.anio}",
                    "vencimiento": d.vencimiento.strftime("%d/%m/%Y") if d.vencimiento else "—",
                    "saldo":       d.saldo,
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