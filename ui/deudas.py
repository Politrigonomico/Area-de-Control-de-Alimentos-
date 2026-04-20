"""
Módulo de Deudas — visualización, registro de pagos, generación.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from reports.documentos_institucionales import doc_detalle_deuda, _auto_path, abrir_pdf
from database.db import get_session
from database.models import Deuda
from utils.ui_helpers import error_dialog
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
        ttk.Button(bar, text="↩  Cancelar pago", style="Danger.TButton",
                   command=self._cancelar_pago).pack(side="right", padx=4)
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
        self.tree.configure(selectmode="extended")   # permite Ctrl+clic y Shift+clic
        # doble clic eliminado — el pago ahora es solo por botón explícito

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
        """Abre menú con opciones de impresión."""
        ids = self._selected_ids()
        if not ids:
            return

        # Tomar código del primer seleccionado
        session = get_session()
        d = session.query(Deuda).get(ids[0])
        if not d:
            session.close()
            return
        codigo = d.codigo_establecimiento
        session.close()

        # Menú contextual de opciones
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label="📄  Solo deudas impagas",
            command=lambda: self._generar_pdf_filtrado(codigo, solo_impagas=True, pagadas=False)
        )
        menu.add_command(
            label="✅  Solo deudas pagadas",
            command=lambda: self._generar_pdf_filtrado(codigo, solo_impagas=False, pagadas=True)
        )
        menu.add_separator()
        menu.add_command(
            label="📋  Historial completo",
            command=lambda: self._generar_pdf_filtrado(codigo, solo_impagas=False, pagadas=False)
        )
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _generar_pdf_filtrado(self, codigo: str, solo_impagas: bool, pagadas: bool):
        """Genera PDF del establecimiento con el filtro indicado."""
        from reports.documentos_institucionales import doc_detalle_deuda, _auto_path, abrir_pdf
        from database.db import get_session
        from database.models import Deuda
        from utils.ui_helpers import error_dialog
        from datetime import datetime as _dt

        # Determinar sufijo del archivo y filtro de query
        if solo_impagas:
            sufijo  = "impagas"
            filtro  = True   # solo_impagas=True en doc_detalle_deuda
        elif pagadas:
            sufijo  = "pagadas"
            filtro  = None   # manejo especial abajo
        else:
            sufijo  = "completo"
            filtro  = False  # solo_impagas=False muestra todo

        ts   = _dt.now().strftime("%Y%m%d_%H%M%S")
        path = _auto_path(f"deuda_{codigo}_{sufijo}_{ts}.pdf")

        try:
            session = get_session()
            if pagadas:
                # doc_detalle_deuda no tiene filtro "solo pagadas" —
                # creamos una versión con IDs específicos usando doc_recibo_transaccion
                from reports.documentos_institucionales import doc_recibo_transaccion
                ids_pagadas = [
                    d.codigo_deuda
                    for d in session.query(Deuda)
                    .filter_by(codigo_establecimiento=codigo.upper(), pago=True)
                    .all()
                ]
                if not ids_pagadas:
                    from utils.ui_helpers import info_dialog
                    info_dialog(self, "Sin datos", "Este establecimiento no tiene deudas pagadas.")
                    session.close()
                    return
                doc_recibo_transaccion(session, path, ids_pagadas)
            else:
                doc_detalle_deuda(session, path, codigo, solo_impagas=filtro)
            session.close()
            abrir_pdf(path)
        except Exception as ex:
            error_dialog(self, "Error al generar PDF", str(ex))

    def _imprimir_recibo_ids(self, ids: list[int]):
            """Imprime recibo de transacción para una lista específica de IDs de deuda."""
            from reports.documentos_institucionales import doc_recibo_transaccion, _auto_path, abrir_pdf
            from utils.ui_helpers import error_dialog
            # Tomar código estab del primer ID para el nombre del archivo
            session = get_session()
            d = session.query(Deuda).get(ids[0])
            codigo = d.codigo_establecimiento if d else "EST"
            session.close()
            try:
                from datetime import datetime as _dt
                ts = _dt.now().strftime("%Y%m%d_%H%M%S")
                path = _auto_path(f"recibo_transaccion_{codigo}_{ts}.pdf")
                session = get_session()
                doc_recibo_transaccion(session, path, ids)
                session.close()
                abrir_pdf(path)
            except Exception as ex:
                error_dialog(self, "Error al generar recibo", str(ex))

    def _selected_ids(self) -> list[int]:
        """Devuelve lista de IDs de las filas seleccionadas."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná al menos una deuda primero.")
            return []
        return [int(iid) for iid in sel]

    # Mantener por compatibilidad con otros métodos que usan id único
    def _selected_deuda_id(self):
        ids = self._selected_ids()
        return ids[0] if ids else None

    def _registrar_pago(self):
        ids = self._selected_ids()
        if not ids:
            return
        # Si solo hay una deuda seleccionada: flujo actual con diálogo
        if len(ids) == 1:
            dlg = PagoDialog(self, ids[0])
            self.wait_window(dlg)
            self.refresh()
            return
        # Múltiples deudas: confirmar y aplicar fecha/medio en lote
        if not confirm_dialog(self, "Registrar pago múltiple",
                              f"¿Registrar pago de {len(ids)} deudas seleccionadas?\n"
                              "Se usará la fecha de hoy y medio EFECTIVO.\n"
                              "Podés editar cada una individualmente después."):
            return
        session = get_session()
        deudas_pagadas = []
        try:
            for did in ids:
                d = session.query(Deuda).get(did)
                if d and not d.pago:
                    d.pago          = True
                    d.fecha_pago    = datetime.now()
                    d.monto_abonado = d.importe
                    d.medio_pago    = "EFECTIVO"
                    deudas_pagadas.append(did)
            session.commit()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
            session.close()
            return
        session.close()
        self.refresh()
        if deudas_pagadas and messagebox.askyesno(
                "Pago registrado",
                f"{len(deudas_pagadas)} deudas marcadas como pagadas.\n"
                "¿Querés imprimir el recibo de esta transacción?"):
            self._imprimir_recibo_ids(deudas_pagadas)

    def _cancelar_pago(self):
        """Revierte el estado de pago de las deudas seleccionadas."""
        ids = self._selected_ids()
        if not ids:
            return
        # Filtrar solo las que están pagadas
        session = get_session()
        deudas_pagadas = [
            session.query(Deuda).get(did)
            for did in ids
            if session.query(Deuda).get(did) and session.query(Deuda).get(did).pago
        ]
        session.close()
        if not deudas_pagadas:
            messagebox.showinfo("Sin cambios", "Ninguna de las deudas seleccionadas está marcada como pagada.")
            return
        if not confirm_dialog(self, "Cancelar pago",
                              f"¿Revertir el pago de {len(deudas_pagadas)} deuda(s) a IMPAGO?"):
            return
        session = get_session()
        try:
            for d in deudas_pagadas:
                d_db = session.query(Deuda).get(d.codigo_deuda)
                d_db.pago          = False
                d_db.fecha_pago    = None
                d_db.monto_abonado = 0.0
                d_db.medio_pago    = None
            session.commit()
            info_dialog(self, "Listo", f"{len(deudas_pagadas)} pago(s) revertidos a IMPAGO.")
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()
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
        center_window(self, 420, 360)
        self.grab_set()
        self._build()
        self._load()

    def _imprimir_recibo_transaccion(self, deuda_id: int):
        """Imprime recibo solo con la deuda de esta transacción."""
        from reports.documentos_institucionales import doc_recibo_transaccion, _auto_path, abrir_pdf
        from database.db import get_session
        from database.models import Deuda
        from utils.ui_helpers import error_dialog
        from datetime import datetime as _dt
        session = get_session()
        d = session.query(Deuda).get(deuda_id)
        if not d:
            session.close()
            return
        codigo = d.codigo_establecimiento
        session.close()
        try:
            ts   = _dt.now().strftime("%Y%m%d_%H%M%S")
            path = _auto_path(f"recibo_transaccion_{codigo}_{ts}.pdf")
            session = get_session()
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
        bar.grid(row=8, column=0, columnspan=2, pady=(16, 8), sticky="e")
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
                self._imprimir_recibo_transaccion(self.deuda_id)
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

        lista_original = list(self._estab_map.keys())

        ttk.Label(f, text="Establecimiento *").grid(row=0, column=0, sticky="w", pady=5, padx=(0, 8))
        
        self.e_estab = ttk.Entry(f, width=34)
        self.e_estab.grid(row=0, column=1, sticky="ew", pady=5)

        self.lista_sugerencias = tk.Listbox(f, height=6)

        def actualizar_sugerencias(event):
            if event.keysym in ('Up', 'Down', 'Return', 'Left', 'Right', 'Tab'):
                return
            
            texto = self.e_estab.get().lower()
            self.lista_sugerencias.delete(0, tk.END)
            
            if texto == '':
                self.lista_sugerencias.place_forget()
                return

            coincidencias = [item for item in lista_original if texto in item.lower()]
            
            if coincidencias:
                for item in coincidencias:
                    self.lista_sugerencias.insert(tk.END, item)
                
                self.update_idletasks()
                self.lista_sugerencias.place(in_=self.e_estab, x=0, rely=1, relwidth=1.0)
                self.lista_sugerencias.lift()
            else:
                self.lista_sugerencias.place_forget()

        def seleccionar_item(event):
            if not self.lista_sugerencias.curselection():
                return
            seleccion = self.lista_sugerencias.get(self.lista_sugerencias.curselection())
            self.e_estab.delete(0, tk.END)
            self.e_estab.insert(0, seleccion)
            self.lista_sugerencias.place_forget()
            self.e_estab.focus_set()

        self.e_estab.bind('<KeyRelease>', actualizar_sugerencias)
        self.lista_sugerencias.bind('<ButtonRelease-1>', seleccionar_item)
        
        self.bind('<Button-1>', lambda e: self.lista_sugerencias.place_forget() 
                  if e.widget != self.lista_sugerencias and e.widget != self.e_estab else None)

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
        ttk.Button(bar, text="Guardar", style="Success.TButton", command=self._guardar).pack(side="right", padx=4)
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
