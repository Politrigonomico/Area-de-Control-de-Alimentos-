"""
Panel de inicio — dashboard con estadísticas rápidas, backup de DB y alertas.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
# Agregar junto con las importaciones de la UI (aprox línea 12)
from ui.deudas import PagoDialog
from ui.establecimientos import EstablecimientoDialog
from database.db import get_session
# Añadido modelo Sanidad para las alertas
from database.models import Establecimiento, Inscripto, Deuda, Auditoria, Sanidad
from utils.ui_helpers import COLORS, FONT_TITLE, FONT_HEADER, FONT_NORMAL
from utils.backup import hacer_backup, listar_backups, BACKUP_DIR
# Modifica la línea de importaciones de la UI (aprox línea 13) para que quede así:
from ui.deudas import PagoDialog
from ui.establecimientos import EstablecimientoDialog
from ui.sanidad_auditorias import SanidadDialog



class DashboardFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        # ── Encabezado ──────────────────────────────────────────────────────
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

        # ── Tarjetas de Estadísticas ─────────────────────────────────────────
        self.cards_frame = ttk.Frame(self, padding=(20, 10))
        self.cards_frame.pack(fill="x")

        # ── Contenedor de Alertas (Dividido en 2 columnas) ───────────────────
        # Usamos expand=True para corregir la distribución de la UI
        self.tables_container = ttk.Frame(self, padding=(20, 0, 20, 20))
        self.tables_container.pack(fill="both", expand=True)

        # Panel Izquierdo: Deudas
        self.deudas_frame = ttk.LabelFrame(
            self.tables_container, text="⚠  Deudas vencidas hoy o antes", padding=12)
        self.deudas_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Panel Derecho: Sanidad
        self.sanidad_frame = ttk.LabelFrame(
            self.tables_container, text="⚕  Alertas Sanitarias (Libretas Vencidas)", padding=12)
        self.sanidad_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

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
        self._actualizar_label_backup()

        # Limpiar widgets anteriores
        for w in self.cards_frame.winfo_children(): w.destroy()
        for w in self.deudas_frame.winfo_children(): w.destroy()
        for w in self.sanidad_frame.winfo_children(): w.destroy()

        session = get_session()
        try:
            from sqlalchemy import func, or_

            # Estadísticas Generales
            total_estab  = session.query(Establecimiento).filter_by(baja=False).count()
            total_bajas  = session.query(Establecimiento).filter_by(baja=True).count()
            total_inscr  = session.query(Inscripto).count()
            total_deudas = session.query(Deuda).filter_by(pago=False).count()
            total_audits = session.query(Auditoria).count()
            saldo_result = session.query(
                func.sum(Deuda.importe - Deuda.monto_abonado)
            ).filter(Deuda.pago == False).scalar() or 0.0

            hoy = datetime.now()

            # 1. Consulta optimizada: Establecimientos morosos (sin desglosar deuda)
            rows_estabs_morosos = session.query(Establecimiento).join(Deuda).filter(
                Deuda.pago == False,
                Deuda.vencimiento < hoy
            ).distinct().limit(25).all()

            estabs_morosos = []
            for e in rows_estabs_morosos:
                estabs_morosos.append({
                    "codigo": e.codigo_establecimiento,
                    "nombre": (e.nombre_establecimiento or "").title()
                })

            # 2. Consulta de Alertas de Sanidad (Libretas vencidas)
            rows_sanidad = session.query(Sanidad).filter(
                or_(
                    Sanidad.venc_libreta_titular < hoy,
                    Sanidad.venc_libreta_empleado1 < hoy,
                    Sanidad.venc_libreta_empleado2 < hoy
                )
            ).limit(15).all()

            alertas_sanidad = []
            for s in rows_sanidad:
                estab = s.establecimiento
                nombre_estab = (estab.nombre_establecimiento or "").title() if estab else "Desconocido"
                
                if s.venc_libreta_titular and s.venc_libreta_titular < hoy:
                    alertas_sanidad.append({
                        "codigo": s.codigo_establecimiento, "estab": nombre_estab,
                        "persona": f"Titular: {s.apellido_titular or 'S/N'}", 
                        "vence": s.venc_libreta_titular.strftime("%d/%m/%Y")
                    })
                if s.venc_libreta_empleado1 and s.venc_libreta_empleado1 < hoy:
                    alertas_sanidad.append({
                        "codigo": s.codigo_establecimiento, "estab": nombre_estab,
                        "persona": f"Emp 1: {s.apellido_empleado1 or 'S/N'}", 
                        "vence": s.venc_libreta_empleado1.strftime("%d/%m/%Y")
                    })
                if s.venc_libreta_empleado2 and s.venc_libreta_empleado2 < hoy:
                    alertas_sanidad.append({
                        "codigo": s.codigo_establecimiento, "estab": nombre_estab,
                        "persona": f"Emp 2: {s.apellido_empleado2 or 'S/N'}", 
                        "vence": s.venc_libreta_empleado2.strftime("%d/%m/%Y")
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
            card.grid(row=row_idx, column=col_idx, padx=8, pady=8, sticky="nsew")
            self.cards_frame.columnconfigure(col_idx, weight=1)

            tk.Label(card, text=icon, font=("Segoe UI", 30), bg=COLORS["bg_panel"]).pack(pady=(16, 4))
            tk.Label(card, text=value, font=("Segoe UI", 22, "bold"), fg=color, bg=COLORS["bg_panel"]).pack()
            tk.Label(card, text=label, font=FONT_NORMAL, fg=COLORS["text_light"], bg=COLORS["bg_panel"]).pack(pady=(2, 16))

        # ── Tabla Izquierda: Establecimientos con Deudas ──────────────────────
        if not estabs_morosos:
            ttk.Label(self.deudas_frame, text="Sin deudas vencidas pendientes. ✓", foreground=COLORS["success"]).pack(anchor="w", pady=10)
        else:
            ttk.Label(self.deudas_frame, text="Hay deudas pendientes para estos est:").pack(anchor="w", pady=(0, 5))
            cols   = ("codigo", "nombre")
            heads  = ("Código", "Establecimiento")
            widths = (80, 240)
            
            frame_tv_d = ttk.Frame(self.deudas_frame)
            frame_tv_d.pack(fill="both", expand=True)
            
            vsb_d = ttk.Scrollbar(frame_tv_d, orient="vertical")
            tree_d = ttk.Treeview(frame_tv_d, columns=cols, show="headings", yscrollcommand=vsb_d.set)
            vsb_d.config(command=tree_d.yview)
            
            for c, h, w in zip(cols, heads, widths):
                tree_d.heading(c, text=h, anchor="w")
                tree_d.column(c, width=w, anchor="w")
                
            for e in estabs_morosos:
                tree_d.insert("", "end", text=e["codigo"], tags=("vencido",), values=(
                    e["codigo"], e["nombre"]
                ))
            
            tree_d.tag_configure("vencido", background="#fff3cd", foreground="#7c4f00")
            tree_d.pack(side="left", fill="both", expand=True)
            vsb_d.pack(side="right", fill="y")
            
            def on_moroso_double_click(event):
                item_id = tree_d.focus()
                if item_id:
                    # Obtenemos el código de forma segura
                    item_data = tree_d.item(item_id)
                    codigo = item_data.get('text') or (item_data.get('values')[0] if item_data.get('values') else None)
                    
                    if codigo:
                        dlg = EstablecimientoDialog(self.winfo_toplevel(), codigo)
                        # Solo esperamos si la ventana no se autodestruyó por error
                        if dlg.winfo_exists():
                            self.wait_window(dlg)
                            self.refresh()

            tree_d.bind("<Double-1>", on_moroso_double_click)

        ttk.Label(self.deudas_frame, text="Doble clic para ver ficha de establecimiento", font=("Segoe UI", 8), foreground=COLORS["text_light"]).pack(anchor="e")

        # ── Tabla Derecha: Alertas de Sanidad ────────────────────────────────
        if not alertas_sanidad:
            ttk.Label(self.sanidad_frame, text="Todo en regla. No hay libretas vencidas. ✓", foreground=COLORS["success"]).pack(anchor="w", pady=10)
        else:
            cols_s   = ("estab", "persona", "vence")
            heads_s  = ("Establecimiento", "Persona Afectada", "Vencimiento")
            widths_s = (150, 150, 80)
            
            frame_tv_s = ttk.Frame(self.sanidad_frame)
            frame_tv_s.pack(fill="both", expand=True)
            
            vsb_s = ttk.Scrollbar(frame_tv_s, orient="vertical")
            tree_s = ttk.Treeview(frame_tv_s, columns=cols_s, show="headings", yscrollcommand=vsb_s.set)
            vsb_s.config(command=tree_s.yview)
            
            for c, h, w in zip(cols_s, heads_s, widths_s):
                tree_s.heading(c, text=h, anchor="w")
                tree_s.column(c, width=w, anchor="w")
                
            for s in alertas_sanidad:
                tree_s.insert("", "end", tags=("alerta_s",), values=(
                    s["estab"], s["persona"], s["vence"]
                ), text=s["codigo"]) 
            
            tree_s.tag_configure("alerta_s", background="#f8d7da", foreground="#721c24")
            tree_s.pack(side="left", fill="both", expand=True)
            vsb_s.pack(side="right", fill="y")
            
            def on_sanidad_double_click(event):
                item_id = tree_s.focus()
                if item_id:
                    codigo = tree_s.item(item_id, 'text')
                    if codigo:
                        # Ahora abrimos SanidadDialog pasando el codigo_estab
                        dlg = SanidadDialog(self.winfo_toplevel(), codigo_estab=codigo)
                        if dlg.winfo_exists():
                            self.wait_window(dlg)
                        self.refresh()

            tree_s.bind("<Double-1>", on_sanidad_double_click)

        ttk.Label(self.sanidad_frame, text=f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", font=("Segoe UI", 8), foreground=COLORS["text_light"]).pack(anchor="e")
