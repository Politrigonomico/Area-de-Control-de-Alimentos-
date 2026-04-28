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
        # Fila 1: título + filtros
        bar1 = ttk.Frame(self, padding=(0, 0, 0, 4))
        bar1.pack(fill="x")
        ttk.Label(bar1, text="Deudas y Pagos", font=FONT_TITLE).pack(side="left")

        ttk.Label(bar1, text="Año:").pack(side="left", padx=(20, 4))
        self.anio_var = tk.StringVar(value="Todos")
        anios = ["Todos"] + [str(y) for y in range(2014, datetime.now().year + 1)]
        ttk.Combobox(bar1, textvariable=self.anio_var, values=anios,
                     width=7, state="readonly").pack(side="left")
        self.anio_var.trace_add("write", lambda *_: self.refresh())

        ttk.Label(bar1, text="Estado:").pack(side="left", padx=(12, 4))
        self.estado_var = tk.StringVar(value="Todos")
        ttk.Combobox(bar1, textvariable=self.estado_var,
                     values=["Todos", "Impago", "Pagado"],
                     width=8, state="readonly").pack(side="left")
        self.estado_var.trace_add("write", lambda *_: self.refresh())

        ttk.Label(bar1, text="Buscar estab.:").pack(side="left", padx=(12, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar1, textvariable=self.search_var, width=20).pack(side="left")

        # Fila 2: botones de acción
        bar2 = ttk.Frame(self, padding=(0, 0, 0, 8))
        bar2.pack(fill="x")
        ttk.Button(bar2, text="＋  Nueva deuda",
                   command=self._nueva_deuda).pack(side="left", padx=(0, 4))
        ttk.Button(bar2, text="↩  Cancelar pago", style="Danger.TButton",
                   command=self._cancelar_pago).pack(side="left", padx=4)
        ttk.Button(bar2, text="💰  Registrar pago", style="Success.TButton",
                   command=self._registrar_pago).pack(side="left", padx=4)
        ttk.Button(bar2, text="🖨  Imprimir recibo",
                   command=self._imprimir_recibo).pack(side="left", padx=4)
        # Resumen
        self.lbl_resumen = ttk.Label(self,
            text="", font=("Segoe UI", 11, "bold"), foreground=COLORS["accent"])
        self.lbl_resumen.pack(anchor="e", padx=4)

        # Treeview
        self.tree, _ = scrolled_treeview(self, self.COLS, self.HEADINGS, self.WIDTHS, height=20)
        self.tree.configure(selectmode="extended")
        self.tree.bind("<Double-1>", lambda e: self._registrar_pago())
        self.tree.bind("<Button-3>", self._menu_contextual)


    def _menu_contextual(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="🗑  Eliminar del sistema",
                         command=lambda: self._eliminar(iid))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _eliminar(self, iid):
        if not confirm_dialog(self, "Eliminar",
                "¿Estás seguro de eliminar esta deuda del sistema?\n\n"
                "Esta acción no se puede deshacer."):
            return
        session = get_session()
        d = session.query(Deuda).get(int(iid))
        if d:
            session.delete(d)
            session.commit()
        session.close()
        self.refresh()

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
        ids = self._selected_ids()
        if not ids:
            return
        
        # Crear un menú desplegable en la posición del mouse
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="📋 Imprimir resumen de cuenta (Solo impagas)",
                         command=lambda: self._ejecutar_impresion("impagas", ids))
        menu.add_command(label="📚 Imprimir historial completo (Pagadas e impagas)",
                         command=lambda: self._ejecutar_impresion("completo", ids))
        menu.add_separator()
        menu.add_command(label="📄 Imprimir comprobante de la(s) selecciónada(s)",
                         command=lambda: self._ejecutar_impresion("seleccion", ids))
        
        try:
            # Mostrar el menú justo donde está el cursor
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _ejecutar_impresion(self, tipo, ids):
        from reports.documentos_institucionales import doc_detalle_deuda, doc_recibo_transaccion, _auto_path, abrir_pdf
        from database.db import get_session
        from database.models import Deuda
        from utils.ui_helpers import error_dialog
        
        session = get_session()
        d = session.query(Deuda).get(ids[0])
        if not d:
            session.close()
            return
        codigo = d.codigo_establecimiento
        session.close()
        
        try:
            from datetime import datetime as _dt
            ts = _dt.now().strftime("%Y%m%d_%H%M%S")
            session = get_session()
            
            if tipo == "impagas":
                path = _auto_path(f"deuda_{codigo}_impagas_{ts}.pdf")
                doc_detalle_deuda(session, path, codigo, solo_impagas=True)
            elif tipo == "completo":
                path = _auto_path(f"deuda_{codigo}_completo_{ts}.pdf")
                doc_detalle_deuda(session, path, codigo, solo_impagas=False)
            elif tipo == "seleccion":
                path = _auto_path(f"recibo_transaccion_{codigo}_{ts}.pdf")
                doc_recibo_transaccion(session, path, ids)
                
            session.close()
            abrir_pdf(path)
        except Exception as ex:
            error_dialog(self, "Error al generar el documento", str(ex))

    def _selected_deuda_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná una deuda primero.")
            return None
        return int(sel[0])

    def _selected_ids(self) -> list:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná al menos una deuda primero.")
            return []
        return [int(iid) for iid in sel]

    def _registrar_pago(self):
        ids = self._selected_ids()
        if not ids:
            return
        if len(ids) == 1:
            dlg = PagoDialog(self, ids[0])
        else:
            dlg = PagoMultipleDialog(self, ids)
        self.wait_window(dlg)
        self.refresh()

    def _cancelar_pago(self):
        ids = self._selected_ids()
        if not ids:
            return
            
        session = get_session()
        try:
            # OPTIMIZACIÓN: Solo 1 consulta filtrando directamente por los IDs seleccionados que estén pagados
            pagadas = session.query(Deuda).filter(Deuda.codigo_deuda.in_(ids), Deuda.pago == True).all()
            
            if not pagadas:
                messagebox.showinfo("Sin cambios", "Ninguna deuda seleccionada está marcada como pagada.")
                return
                
            if not confirm_dialog(self, "Cancelar pago", f"¿Revertir el pago de {len(pagadas)} deuda(s) a IMPAGO?"):
                return
                
            for d in pagadas:
                d.pago          = False
                d.fecha_pago    = None
                d.monto_abonado = 0.0
                d.medio_pago    = None
                
            session.commit()
            info_dialog(self, "Listo", f"{len(pagadas)} pago(s) revertidos a IMPAGO.")
            
        except Exception as ex:
            session.rollback()
            from utils.ui_helpers import error_dialog
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()
            
        self.refresh()

    def _nueva_deuda(self):
        dlg = DeudaDialog(self, None)
        self.wait_window(dlg)
        self.refresh()


class PagoDialog(tk.Toplevel):
    """Registra o modifica el pago de una deuda, permitiendo aplicar descuentos por moratorias."""
    def __init__(self, parent, deuda_id: int):
        super().__init__(parent)
        self.deuda_id = deuda_id
        self.title("Registrar pago")
        self.resizable(False, False)
        center_window(self, 460, 420)
        self.grab_set()
        
        # Variables para recalcular descuentos
        self._nominal = 0.0
        self._intereses_generados = 0.0
        
        self._build()
        self._load()

    def _imprimir_recibo_desde_dialogo(self, deuda_id: int):
        from reports.documentos_institucionales import doc_recibo_transaccion, _auto_path, abrir_pdf
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
            from datetime import datetime as _dt
            ts = _dt.now().strftime("%Y%m%d_%H%M%S")
            path = _auto_path(f"recibo_pago_{codigo}_{ts}.pdf")
            
            session = get_session()
            # Acá está la magia: usamos doc_recibo_transaccion y le pasamos solo el ID que pagaste
            doc_recibo_transaccion(session, path, [deuda_id])
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

        ttk.Label(f, text="Capital Original:").grid(row=2, column=0, sticky="w", pady=5)
        self.lbl_importe = ttk.Label(f, text="")
        self.lbl_importe.grid(row=2, column=1, sticky="w")

        # NUEVO: Campo para Moratorias
        ttk.Separator(f, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=8)
        
        ttk.Label(f, text="Descuento en Intereses (%):").grid(row=4, column=0, sticky="w", pady=5)
        self.e_descuento = ttk.Entry(f, width=8)
        self.e_descuento.grid(row=4, column=1, sticky="w")
        self.e_descuento.insert(0, "0")
        self.e_descuento.bind("<KeyRelease>", self._recalcular_monto)
        ttk.Label(f, text="(Resoluciones o Moratorias)", font=("Segoe UI", 8)).grid(row=4, column=1, sticky="e")

        ttk.Label(f, text="Monto abonado $").grid(row=5, column=0, sticky="w", pady=5)
        self.e_monto = ttk.Entry(f, width=16)
        self.e_monto.grid(row=5, column=1, sticky="w")

        ttk.Label(f, text="Fecha de pago").grid(row=6, column=0, sticky="w", pady=5)
        self.e_fecha = ttk.Entry(f, width=14)
        self.e_fecha.grid(row=6, column=1, sticky="w")
        ttk.Label(f, text="(dd/mm/aaaa)", font=("Segoe UI", 10)).grid(row=6, column=1, sticky="e")

        ttk.Label(f, text="Medio de pago").grid(row=7, column=0, sticky="w", pady=5)
        self.e_medio = ttk.Combobox(f, values=["EFECTIVO", "TRANSFERENCIA"], width=18, state="readonly")
        self.e_medio.grid(row=7, column=1, sticky="w")
        self.e_medio.set("EFECTIVO")

        bar = ttk.Frame(f)
        bar.grid(row=8, column=0, columnspan=2, pady=(16, 8), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton", command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _recalcular_monto(self, event=None):
        desc_str = self.e_descuento.get().strip()
        try:
            desc = float(desc_str) if desc_str else 0.0
        except ValueError:
            desc = 0.0
        
        # Validar límites
        if desc < 0: desc = 0.0
        if desc > 100: desc = 100.0

        intereses_con_descuento = self._intereses_generados * (1 - (desc / 100.0))
        nuevo_total = self._nominal + intereses_con_descuento

        from utils.ui_helpers import set_entry
        set_entry(self.e_monto, f"{nuevo_total:.2f}")

    def _load(self):
        session = get_session()
        d = session.query(Deuda).get(self.deuda_id)
        if not d:
            session.close()
            return
        
        nombre = (d.establecimiento.nombre_establecimiento or "").title() if d.establecimiento else ""
        self.lbl_estab.config(text=f"{d.codigo_establecimiento} — {nombre}")
        self.lbl_periodo.config(text=f"Período {d.periodo}/{d.anio}")

        self._nominal = d.importe or 0.0

        from reports.documentos_institucionales import _calcular_interes
        if d.vencimiento and not d.pago:
            meses, int_porcentaje, actualizado = _calcular_interes(d.importe, d.vencimiento)
            
            # SOLUCIÓN: Calculamos el dinero real del interés, no el porcentaje
            monto_interes = actualizado - d.importe 
            
            self._intereses_generados = monto_interes
            self.lbl_importe.config(text=f"$ {d.importe:,.2f}  (+ $ {monto_interes:,.2f} de int.)")
            from utils.ui_helpers import set_entry
            set_entry(self.e_monto, f"{actualizado:.2f}")
        else:
            self._intereses_generados = 0.0
            self.lbl_importe.config(text=f"$ {d.importe:,.2f}")
            from utils.ui_helpers import set_entry
            set_entry(self.e_monto, str(d.monto_abonado or d.importe))
            self.e_descuento.configure(state="disabled")

        if d.fecha_pago:
            from utils.ui_helpers import set_entry, format_date
            set_entry(self.e_fecha, format_date(d.fecha_pago))
        else:
            from utils.ui_helpers import set_entry
            set_entry(self.e_fecha, datetime.now().strftime("%d/%m/%Y"))

        self.e_medio.set(d.medio_pago or "EFECTIVO")
        session.close()

        if d.fecha_pago:
            from utils.ui_helpers import set_entry, format_date
            set_entry(self.e_fecha, format_date(d.fecha_pago))
        else:
            from utils.ui_helpers import set_entry
            set_entry(self.e_fecha, datetime.now().strftime("%d/%m/%Y"))

        self.e_medio.set(d.medio_pago or "EFECTIVO")
        session.close()

    def _guardar(self):
        session = get_session()
        d = session.query(Deuda).get(self.deuda_id)
        if not d:
            session.close()
            return
        
        from utils.ui_helpers import parse_float_str, parse_date_str, get_entry, error_dialog
        d.pago          = True
        d.monto_abonado = parse_float_str(get_entry(self.e_monto))
        d.fecha_pago    = parse_date_str(get_entry(self.e_fecha))
        d.medio_pago    = self.e_medio.get() or "EFECTIVO"
        
        try:
            session.commit()
            from tkinter import messagebox
            if messagebox.askyesno("Guardado", "Pago registrado correctamente.\n¿Querés imprimir el recibo?", parent=self):
                self._imprimir_recibo_desde_dialogo(self.deuda_id)
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()


class PagoMultipleDialog(tk.Toplevel):
    """Registra pago de múltiples deudas con moratoria masiva."""
    def __init__(self, parent, ids: list):
        super().__init__(parent)
        self.ids = ids
        self.title(f"Registrar pagos múltiples ({len(ids)} deudas)")
        self.resizable(False, False)
        center_window(self, 520, 500)
        self.grab_set()
        
        self._deudas_data = []
        self._total_nominal = 0.0
        self._total_intereses = 0.0

        self._build()
        self._load()

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        ttk.Label(f, text=f"Se van a registrar {len(self.ids)} pagos:", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.tree_prev = ttk.Treeview(f, columns=("estab", "periodo", "nominal", "interes"), show="headings", height=6)
        self.tree_prev.heading("estab",      text="Establecimiento")
        self.tree_prev.heading("periodo",    text="Período")
        self.tree_prev.heading("nominal",    text="Nominal")
        self.tree_prev.heading("interes",    text="Interés")
        self.tree_prev.column("estab",       width=160)
        self.tree_prev.column("periodo",     width=70, anchor="center")
        self.tree_prev.column("nominal",     width=90, anchor="e")
        self.tree_prev.column("interes",     width=90, anchor="e")
        self.tree_prev.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        # Sección de recálculo de mora
        ttk.Separator(f, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=6)
        
        ttk.Label(f, text="Descuento masivo en Intereses (%):").grid(row=3, column=0, sticky="w", pady=5)
        self.e_descuento = ttk.Entry(f, width=8)
        self.e_descuento.grid(row=3, column=1, sticky="w")
        self.e_descuento.insert(0, "0")
        self.e_descuento.bind("<KeyRelease>", self._recalcular_totales)
        
        self.lbl_total = ttk.Label(f, text="", font=("Segoe UI", 11, "bold"), foreground=COLORS["accent"])
        self.lbl_total.grid(row=4, column=0, columnspan=2, sticky="e", pady=8)

        ttk.Label(f, text="Fecha de pago").grid(row=5, column=0, sticky="w", pady=5)
        self.e_fecha = ttk.Entry(f, width=14)
        self.e_fecha.grid(row=5, column=1, sticky="w")
        self.e_fecha.insert(0, datetime.now().strftime("%d/%m/%Y"))

        ttk.Label(f, text="Medio de pago").grid(row=6, column=0, sticky="w", pady=5)
        self.e_medio = ttk.Combobox(f, values=["EFECTIVO", "TRANSFERENCIA"], width=18, state="readonly")
        self.e_medio.grid(row=6, column=1, sticky="w")
        self.e_medio.set("EFECTIVO")

        bar = ttk.Frame(f)
        bar.grid(row=7, column=0, columnspan=2, pady=(12, 0), sticky="e")
        ttk.Button(bar, text="Guardar todos", style="Success.TButton", command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _recalcular_totales(self, event=None):
        desc_str = self.e_descuento.get().strip()
        try:
            desc = float(desc_str) if desc_str else 0.0
        except ValueError:
            desc = 0.0
        
        if desc < 0: desc = 0.0
        if desc > 100: desc = 100.0

        intereses_con_descuento = self._total_intereses * (1 - (desc / 100.0))
        nuevo_total = self._total_nominal + intereses_con_descuento

        self.lbl_total.config(text=f"Total a pagar (con dto.): $ {nuevo_total:,.2f}")

    def _load(self):
        from reports.documentos_institucionales import _calcular_interes
        session = get_session()
        
        for did in self.ids:
            d = session.query(Deuda).get(did)
            if not d: continue
            
            nombre = (d.establecimiento.nombre_establecimiento or "").title() if d.establecimiento else ""
            
            if d.vencimiento and not d.pago:
                _, _, actualizado = _calcular_interes(d.importe, d.vencimiento)
                
                # SOLUCIÓN: Calculamos el dinero real del interés
                monto_interes = actualizado - d.importe
            else:
                monto_interes = 0.0

            self._total_nominal += (d.importe or 0.0)
            self._total_intereses += monto_interes

            self._deudas_data.append({
                "id": did, "nominal": d.importe, "intereses": monto_interes
            })
            
            self.tree_prev.insert("", "end", values=(
                nombre,
                f"{d.periodo}/{d.anio}",
                f"$ {d.importe:,.2f}",
                f"$ {monto_interes:,.2f}",
            ))
            
        session.close()
        self._recalcular_totales()

    def _guardar(self):
        from utils.ui_helpers import parse_date_str, get_entry, error_dialog
        fecha    = parse_date_str(get_entry(self.e_fecha)) or datetime.now()
        medio    = self.e_medio.get() or "EFECTIVO"
        
        desc_str = self.e_descuento.get().strip()
        try:
            desc = float(desc_str) if desc_str else 0.0
        except ValueError:
            desc = 0.0
        if desc < 0: desc = 0.0
        if desc > 100: desc = 100.0

        session  = get_session()
        try:
            for item in self._deudas_data:
                d = session.query(Deuda).get(item["id"])
                if d:
                    int_con_descuento = item["intereses"] * (1 - (desc / 100.0))
                    total_deuda = item["nominal"] + int_con_descuento
                    
                    d.pago          = True
                    d.fecha_pago    = fecha
                    d.monto_abonado = total_deuda
                    d.medio_pago    = medio
            
            session.commit()
            if messagebox.askyesno("Guardado", f"{len(self._deudas_data)} pagos registrados.\n¿Querés imprimir el recibo unificado?", parent=self):
                self._imprimir()
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()

    def _imprimir(self):
        from reports.documentos_institucionales import doc_recibo_transaccion, _auto_path, abrir_pdf
        from utils.ui_helpers import error_dialog
        ids = [item["id"] for item in self._deudas_data]
        if not ids: return
        session = get_session()
        d = session.query(Deuda).get(ids[0])
        codigo = d.codigo_establecimiento if d else "EST"
        session.close()
        try:
            from datetime import datetime as _dt
            ts   = _dt.now().strftime("%Y%m%d_%H%M%S")
            path = _auto_path(f"recibo_multiple_{codigo}_{ts}.pdf")
            session = get_session()
            doc_recibo_transaccion(session, path, ids)
            session.close()
            abrir_pdf(path)
        except Exception as ex:
            error_dialog(self, "Error PDF", str(ex))

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
        self.e_estab = ttk.Combobox(f, values=list(self._estab_map.keys()), width=34)
        self.e_estab.grid(row=0, column=1, sticky="ew", pady=5)

        self._todos_estab = list(self._estab_map.keys())

        def _filtrar(event):
            if event.keysym in ("Down", "Up", "Return", "Escape", "Tab"):
                return
            texto = self.e_estab.get().lower()
            if not texto:
                self.e_estab["values"] = self._todos_estab
            else:
                self.e_estab["values"] = [k for k in self._todos_estab if texto in k.lower()]
            try:
                self.e_estab.tk.call(self.e_estab._w, "post")
            except Exception:
                pass

        self.e_estab.bind("<KeyRelease>", _filtrar)

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
