"""
Módulo de Deudas — visualización, registro de pagos, generación.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import get_session
from database.models import Deuda, Establecimiento, Emision
from utils.ui_helpers import (
    COLORS, FONT_NORMAL, FONT_TITLE,
    scrolled_treeview, set_entry, get_entry,
    format_date, parse_date_str, parse_float_str,
    center_window, confirm_dialog, info_dialog, error_dialog,
)


class DeudasFrame(ttk.Frame):
    COLS     = ("codigo", "nombre", "anio", "periodo", "vencimiento",
                "importe", "estado", "saldo", "fecha_pago")
    HEADINGS = ("Cód. Estab.", "Establecimiento", "Año", "Per.", "Vencimiento",
                "Importe", "Estado", "Saldo", "Fecha Pago")
    WIDTHS   = (80, 200, 55, 45, 100, 100, 70, 100, 100)

    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        # Toolbar
        bar = ttk.Frame(self, padding=(0, 0, 0, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="Deudas y Pagos", font=FONT_TITLE).pack(side="left")

        # Filtros
        ttk.Label(bar, text="Año:").pack(side="left", padx=(20, 4))
        self.anio_var = tk.StringVar(value="Todos")
        anios = ["Todos"] + [str(y) for y in range(2014, datetime.now().year + 1)]
        ttk.Combobox(bar, textvariable=self.anio_var, values=anios,
                     width=7, state="readonly").pack(side="left")
        self.anio_var.trace_add("write", lambda *_: self.refresh())

        ttk.Label(bar, text="Estado:").pack(side="left", padx=(12, 4))
        self.estado_var = tk.StringVar(value="Todos")
        ttk.Combobox(bar, textvariable=self.estado_var,
                     values=["Todos", "Impago", "Pagado"],
                     width=8, state="readonly").pack(side="left")
        self.estado_var.trace_add("write", lambda *_: self.refresh())

        ttk.Label(bar, text="Buscar estab.:").pack(side="left", padx=(12, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar, textvariable=self.search_var, width=20).pack(side="left")

        # Acciones
        ttk.Button(bar, text="💰  Registrar pago", style="Success.TButton",
                   command=self._registrar_pago).pack(side="right", padx=4)
        ttk.Button(bar, text="＋  Nueva deuda",
                   command=self._nueva_deuda).pack(side="right", padx=4)
        ttk.Button(bar, text="🖨  Imprimir recibo",
                   command=self._imprimir_recibo).pack(side="left", padx=4)

        # Resumen
        self.lbl_resumen = ttk.Label(self,
            text="", font=("Segoe UI", 11, "bold"), foreground=COLORS["accent"])
        self.lbl_resumen.pack(anchor="e", padx=4)

        # Treeview
        self.tree, _ = scrolled_treeview(self, self.COLS, self.HEADINGS, self.WIDTHS, height=20)
        self.tree.bind("<Double-1>", lambda e: self._registrar_pago())

    def refresh(self):
        session = get_session()
        q = (session.query(Deuda)
             .join(Establecimiento,
                   Deuda.codigo_establecimiento == Establecimiento.codigo_establecimiento,
                   isouter=True))

        anio = self.anio_var.get()
        if anio != "Todos":
            q = q.filter(Deuda.anio == int(anio))

        estado = self.estado_var.get()
        if estado == "Impago":
            q = q.filter(Deuda.pago == False)
        elif estado == "Pagado":
            q = q.filter(Deuda.pago == True)

        busqueda = self.search_var.get().strip()
        if busqueda:
            q = q.filter(
                Deuda.codigo_establecimiento.ilike(f"%{busqueda}%") |
                Establecimiento.nombre_establecimiento.ilike(f"%{busqueda}%")
            )

        deudas = q.order_by(Deuda.anio, Deuda.periodo, Deuda.codigo_establecimiento).all()

        # Serializar relaciones ANTES de cerrar la sesión
        datos = []
        total_deuda = 0.0
        total_saldo = 0.0
        for d in deudas:
            nombre = ""
            if d.establecimiento:
                nombre = (d.establecimiento.nombre_establecimiento or "").title()
            saldo = d.saldo
            total_deuda += d.importe or 0
            total_saldo += saldo
            datos.append({
                "id":     str(d.codigo_deuda),
                "codigo": d.codigo_establecimiento,
                "nombre": nombre,
                "anio":   d.anio or "",
                "periodo":d.periodo or "",
                "venc":   format_date(d.vencimiento),
                "importe":d.importe or 0,
                "pagado": bool(d.pago),
                "saldo":  saldo,
                "fpago":  format_date(d.fecha_pago) or "—",
            })
        session.close()

        self.tree.delete(*self.tree.get_children())
        for d in datos:
            tag = "pagado" if d["pagado"] else "impago"
            self.tree.insert("", "end", iid=d["id"], tags=(tag,), values=(
                d["codigo"],
                d["nombre"],
                d["anio"],
                d["periodo"],
                d["venc"],
                f"$ {d['importe']:,.2f}",
                "PAGADO" if d["pagado"] else "IMPAGO",
                f"$ {d['saldo']:,.2f}",
                d["fpago"],
            ))

        self.lbl_resumen.config(
            text=f"Registros: {len(deudas)}   |   "
                 f"Total emitido: $ {total_deuda:,.2f}   |   "
                 f"Total adeudado: $ {total_saldo:,.2f}"
        )

    def _imprimir_recibo(self):
        from reports.documentos_institucionales import doc_detalle_deuda, _auto_path, abrir_pdf
        from database.db import get_session
        from database.models import Deuda
        from utils.ui_helpers import error_dialog
        did = self._selected_deuda_id()
        if did is None:
            return
        session = get_session()
        d = session.query(Deuda).get(did)
        if not d:
            session.close()
            return
        codigo = d.codigo_establecimiento
        session.close()
        try:
            path = _auto_path(f"deuda_{codigo}.pdf")
            session = get_session()
            doc_detalle_deuda(session, path, codigo, solo_impagas=True)
            session.close()
            abrir_pdf(path)
        except Exception as ex:
            error_dialog(self, "Error", str(ex))

    def _selected_deuda_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná una deuda primero.")
            return None
        return int(sel[0])

    def _registrar_pago(self):
        did = self._selected_deuda_id()
        if did is None:
            return
        dlg = PagoDialog(self, did)
        self.wait_window(dlg)
        self.refresh()

    def _nueva_deuda(self):
        dlg = DeudaDialog(self, None)
        self.wait_window(dlg)
        self.refresh()


class PagoDialog(tk.Toplevel):
    """Registra o modifica el pago de una deuda."""
    def __init__(self, parent, deuda_id: int):
        super().__init__(parent)
        self.deuda_id = deuda_id
        self.title("Registrar pago")
        self.resizable(False, False)
        center_window(self, 420, 310)
        self.grab_set()
        self._build()
        self._load()

    def _imprimir_recibo_desde_dialogo(self, deuda_id: int):
        from reports.documentos_institucionales import doc_detalle_deuda, _auto_path, abrir_pdf
        from database.db import get_session
        from database.models import Deuda
        from utils.ui_helpers import error_dialog
        session = get_session()
        d = session.query(Deuda).get(deuda_id)
        if not d:
            session.close()
            return
        codigo = d.codigo_establecimiento
        session.close()
        try:
            path = _auto_path(f"recibo_pago_{codigo}.pdf")
            session = get_session()
            # Solo mostrar la deuda específica en el recibo de pago
            doc_detalle_deuda(session, path, codigo, solo_impagas=False)
            session.close()
            abrir_pdf(path)
        except Exception as ex:
            error_dialog(self, "Error al generar PDF", str(ex))

    def _build(self):
        f = ttk.Frame(self, padding=24)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        ttk.Label(f, text="Establecimiento:").grid(row=0, column=0, sticky="w", pady=5)
        self.lbl_estab = ttk.Label(f, text="", font=("Segoe UI", 11, "bold"))
        self.lbl_estab.grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(f, text="Período:").grid(row=1, column=0, sticky="w", pady=5)
        self.lbl_periodo = ttk.Label(f, text="")
        self.lbl_periodo.grid(row=1, column=1, sticky="w")

        ttk.Label(f, text="Importe original:").grid(row=2, column=0, sticky="w", pady=5)
        self.lbl_importe = ttk.Label(f, text="")
        self.lbl_importe.grid(row=2, column=1, sticky="w")

        ttk.Separator(f, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=8)

        ttk.Label(f, text="¿Pagado?").grid(row=4, column=0, sticky="w", pady=5)
        self.pago_var = tk.BooleanVar()
        ttk.Checkbutton(f, variable=self.pago_var).grid(row=4, column=1, sticky="w")

        ttk.Label(f, text="Monto abonado $").grid(row=5, column=0, sticky="w", pady=5)
        self.e_monto = ttk.Entry(f, width=16)
        self.e_monto.grid(row=5, column=1, sticky="w")

        ttk.Label(f, text="Fecha de pago").grid(row=6, column=0, sticky="w", pady=5)
        self.e_fecha = ttk.Entry(f, width=14)
        self.e_fecha.grid(row=6, column=1, sticky="w")
        ttk.Label(f, text="(dd/mm/aaaa)", font=("Segoe UI", 10)).grid(row=6, column=1, sticky="e")

        ttk.Label(f, text="Medio de pago").grid(row=7, column=0, sticky="w", pady=5)
        self.e_medio = ttk.Combobox(f, values=["EFECTIVO", "TRANSFERENCIA"],
                                    width=18, state="readonly")
        self.e_medio.grid(row=7, column=1, sticky="w")
        self.e_medio.set("EFECTIVO")

        bar = ttk.Frame(f)
        bar.grid(row=7, column=0, columnspan=2, pady=(16, 0), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton",
                   command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _load(self):
        session = get_session()
        d = session.query(Deuda).get(self.deuda_id)
        if not d:
            session.close()
            return
        nombre = ""
        if d.establecimiento:
            nombre = (d.establecimiento.nombre_establecimiento or "").title()
        self.lbl_estab.config(text=f"{d.codigo_establecimiento} — {nombre}")
        self.lbl_periodo.config(text=f"Período {d.periodo}/{d.anio}")
        self.lbl_importe.config(text=f"$ {d.importe:,.2f}")
        self.pago_var.set(bool(d.pago))
        set_entry(self.e_monto, str(d.monto_abonado or ""))
        set_entry(self.e_fecha, format_date(d.fecha_pago))
        session.close()

    def _guardar(self):
        session = get_session()
        d = session.query(Deuda).get(self.deuda_id)
        if not d:
            session.close()
            return
        d.pago         = self.pago_var.get()
        d.monto_abonado= parse_float_str(get_entry(self.e_monto))
        d.fecha_pago   = parse_date_str(get_entry(self.e_fecha))
        try:
            session.commit()
            from tkinter import messagebox
            if messagebox.askyesno("Guardado",
                                   "Pago registrado correctamente.\n¿Querés imprimir el recibo?",
                                   parent=self):
                self._imprimir_recibo_desde_dialogo(self.deuda_id)
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()


class DeudaDialog(tk.Toplevel):
    """Alta manual de una deuda."""
    def __init__(self, parent, deuda_id=None):
        super().__init__(parent)
        self.deuda_id = deuda_id
        self.title("Nueva deuda")
        self.resizable(False, False)
        center_window(self, 420, 320)
        self.grab_set()
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=24)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        session = get_session()
        estabs = session.query(Establecimiento).filter_by(baja=False).order_by(
            Establecimiento.nombre_establecimiento).all()
        self._estab_map = {
            f"{e.codigo_establecimiento} — {(e.nombre_establecimiento or '').title()}": e.codigo_establecimiento
            for e in estabs}
        session.close()

        ttk.Label(f, text="Establecimiento *").grid(row=0, column=0, sticky="w", pady=5, padx=(0, 8))
        self.e_estab = ttk.Combobox(f, values=list(self._estab_map.keys()), width=34, state="readonly")
        self.e_estab.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(f, text="Año *").grid(row=1, column=0, sticky="w", pady=5, padx=(0, 8))
        self.e_anio = ttk.Entry(f, width=8)
        self.e_anio.grid(row=1, column=1, sticky="w", pady=5)
        self.e_anio.insert(0, str(datetime.now().year))

        ttk.Label(f, text="Período (1 ó 2) *").grid(row=2, column=0, sticky="w", pady=5, padx=(0, 8))
        self.e_periodo = ttk.Combobox(f, values=["1", "2"], width=6, state="readonly")
        self.e_periodo.grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(f, text="Vencimiento").grid(row=3, column=0, sticky="w", pady=5, padx=(0, 8))
        self.e_venc = ttk.Entry(f, width=14)
        self.e_venc.grid(row=3, column=1, sticky="w", pady=5)

        ttk.Label(f, text="Importe $").grid(row=4, column=0, sticky="w", pady=5, padx=(0, 8))
        self.e_importe = ttk.Entry(f, width=16)
        self.e_importe.grid(row=4, column=1, sticky="w", pady=5)

        bar = ttk.Frame(f)
        bar.grid(row=5, column=0, columnspan=2, pady=(16, 0), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton",
                   command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _guardar(self):
        estab_key = self.e_estab.get()
        anio_s    = get_entry(self.e_anio)
        periodo_s = self.e_periodo.get()
        if not estab_key or not anio_s or not periodo_s:
            error_dialog(self, "Error", "Establecimiento, año y período son obligatorios.")
            return
        session = get_session()
        d = Deuda(
            codigo_establecimiento=self._estab_map[estab_key],
            anio=int(anio_s),
            periodo=int(periodo_s),
            vencimiento=parse_date_str(get_entry(self.e_venc)),
            importe=parse_float_str(get_entry(self.e_importe)),
            pago=False,
            monto_abonado=0.0,
        )
        session.add(d)
        try:
            session.commit()
            info_dialog(self, "Guardado", "Deuda registrada.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()
