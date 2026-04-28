"""
Módulo de Establecimientos — listado, búsqueda, alta, edición, baja.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import get_session
from database.models import Establecimiento, Inscripto, Rubro
from utils.ui_helpers import (
    COLORS, FONT_NORMAL, FONT_HEADER, FONT_TITLE,
    scrolled_treeview, set_entry, get_entry,
    format_date, parse_date_str, parse_float_str,
    center_window, confirm_dialog, info_dialog, error_dialog,
)


class EstablecimientosFrame(ttk.Frame):
    COLS     = ("codigo", "nombre", "titular", "domicilio", "rubro", "estado", "monto", "baja")
    HEADINGS = ("Código", "Nombre", "Titular", "Domicilio", "Rubro", "Estado", "Monto Total", "Baja")
    WIDTHS   = (70, 200, 180, 180, 140, 100, 100, 50)

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="TFrame")
        self._build()
        self.refresh()

    def _build(self):
        bar = ttk.Frame(self, padding=(0, 0, 0, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="Establecimientos", font=FONT_TITLE).pack(side="left")
        ttk.Label(bar, text="Buscar:", font=FONT_NORMAL).pack(side="left", padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar, textvariable=self.search_var, width=26).pack(side="left")
        self.mostrar_bajas_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text="Incluir bajas",
                        variable=self.mostrar_bajas_var,
                        command=self.refresh).pack(side="left", padx=8)
        ttk.Button(bar, text="＋  Nuevo",       command=self._nuevo).pack(side="right", padx=4)
        ttk.Button(bar, text="✎  Editar",       command=self._editar).pack(side="right", padx=4)
        ttk.Button(bar, text="✕  Dar de baja",  style="Danger.TButton",
                   command=self._dar_baja).pack(side="right", padx=4)
        ttk.Button(bar, text="🖨  Imprimir",    style="Success.TButton",
                   command=self._menu_impresion).pack(side="right", padx=4)
        self.tree, _ = scrolled_treeview(self, self.COLS, self.HEADINGS, self.WIDTHS, height=22)
        self.tree.bind("<Double-1>", lambda e: self._editar())
        self.tree.bind("<Button-3>", self._menu_contextual)

    def refresh(self):
        session = get_session()
        q = session.query(Establecimiento)
        if not self.mostrar_bajas_var.get():
            q = q.filter(Establecimiento.baja == False)
        busqueda = self.search_var.get().strip().lower()
        if busqueda:
            q = q.filter(
                Establecimiento.nombre_establecimiento.ilike(f"%{busqueda}%") |
                Establecimiento.codigo_establecimiento.ilike(f"%{busqueda}%") |
                Establecimiento.domicilio_establecimiento.ilike(f"%{busqueda}%")
            )
        q = q.order_by(Establecimiento.codigo_establecimiento)
        rows = q.all()
        datos = []
        for e in rows:
            titular = ""
            if e.inscripto:
                titular = e.inscripto.nombre_completo
            rubro = e.rubro_rel.nombre if e.rubro_rel else "—"
            domicilio = f"{e.domicilio_establecimiento or ''} {e.numero_establecimiento or ''}".strip()
            datos.append((
                e.codigo_establecimiento,
                (e.nombre_establecimiento or "").title(),
                titular.title(),
                domicilio,
                rubro,
                e.estado_tramite or "—",
                f"$ {e.monto_total:,.2f}",
                "Sí" if e.baja else "No",
                "baja" if e.baja else "",
            ))
        session.close()
        self.tree.delete(*self.tree.get_children())
        for i, d in enumerate(datos):
            codigo_id = d[0] if d[0] and str(d[0]).strip() != "" else f"SIN_CODIGO_{i}"
            self.tree.insert("", "end", iid=codigo_id, tags=(d[8],), values=d[:8])

    def _selected_codigo(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná un establecimiento primero.")
            return None
        return sel[0]

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

    def _eliminar(self, codigo):
        if not confirm_dialog(self, "Eliminar",
                f"¿Eliminar '{codigo}' del sistema?\n\n"
                "Se borrarán también todas sus deudas, auditorías y registros.\n"
                "Esta acción no se puede deshacer."):
            return
        session = get_session()
        e = session.query(Establecimiento).get(codigo)
        if e:
            session.delete(e)
            session.commit()
        session.close()
        self.refresh()

    def _menu_impresion(self):
        codigo = self._selected_codigo()
        if not codigo:
            return
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Certificado de Inscripción",
                         command=lambda: self._imprimir_doc("certificado", codigo))
        menu.add_command(label="Recibo de Pago de Inicio de Trámite",
                         command=lambda: self._imprimir_doc("inicio", codigo))
        menu.add_command(label="Recibo Tasa de Inscripción",
                         command=lambda: self._imprimir_doc("tasa", codigo))
        menu.add_command(label="Detalle de Deuda con Intereses",
                         command=lambda: self._imprimir_doc("deuda", codigo))
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _imprimir_doc(self, tipo, codigo):
        from reports.documentos_institucionales import _auto_path, abrir_pdf
        try:
            session = get_session()
            if tipo == "certificado":
                from reports.documentos_institucionales import doc_certificado_inscripcion
                path = _auto_path(f"certificado_{codigo}.pdf")
                doc_certificado_inscripcion(session, path, codigo)
            elif tipo == "inicio":
                from reports.documentos_institucionales import doc_recibo_inicio_tramite
                e = session.query(Establecimiento).get(codigo)
                if not e or not e.codigo_inscripcion:
                    error_dialog(self, "Error", "El establecimiento no tiene inscripto asignado.")
                    session.close()
                    return
                path = _auto_path(f"recibo_inicio_{codigo}.pdf")
                doc_recibo_inicio_tramite(session, path, e.codigo_inscripcion)
            elif tipo == "tasa":
                from reports.documentos_institucionales import doc_recibo_tasa_inscripcion
                path = _auto_path(f"tasa_{codigo}.pdf")
                doc_recibo_tasa_inscripcion(session, path, codigo)
            elif tipo == "deuda":
                from reports.documentos_institucionales import doc_detalle_deuda
                path = _auto_path(f"deuda_{codigo}.pdf")
                doc_detalle_deuda(session, path, codigo, solo_impagas=True)
            session.close()
            abrir_pdf(path)
        except Exception as ex:
            error_dialog(self, "Error al generar PDF", str(ex))

    def _nuevo(self):
        dlg = EstablecimientoDialog(self, None)
        self.wait_window(dlg)
        self.refresh()

    def _editar(self):
        codigo = self._selected_codigo()
        if not codigo:
            return
        dlg = EstablecimientoDialog(self, codigo)
        self.wait_window(dlg)
        self.refresh()

    def _dar_baja(self):
        codigo = self._selected_codigo()
        if not codigo:
            return
        if not confirm_dialog(self, "Confirmar baja",
                              f"¿Dar de baja al establecimiento {codigo}?"):
            return
        session = get_session()
        e = session.query(Establecimiento).get(codigo)
        if e:
            e.baja = True
            session.commit()
        session.close()
        self.refresh()


class EstablecimientoDialog(tk.Toplevel):
    def __init__(self, parent, codigo=None):
        super().__init__(parent)
        self.codigo = codigo
        self.title("Nuevo establecimiento" if not codigo else f"Editar — {codigo}")
        self.resizable(False, False)
        center_window(self, 700, 620)
        self.grab_set()
        
        self._build()
        if codigo:
            self._load(codigo)

    def _build(self):
        self.configure(bg=COLORS["bg_app"])
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=12)

        f1 = ttk.Frame(nb, padding=16)
        nb.add(f1, text="  Datos generales  ")
        self._build_generales(f1)

        f2 = ttk.Frame(nb, padding=16)
        nb.add(f2, text="  Rubros y montos  ")
        self._build_montos(f2)

        f3 = ttk.Frame(nb, padding=16)
        nb.add(f3, text="  Observaciones  ")
        self._build_obs(f3)

        bar = ttk.Frame(self, padding=(12, 4, 12, 12))
        bar.pack(fill="x")
        ttk.Button(bar, text="Guardar", command=self._guardar,
                   style="Success.TButton").pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right", padx=4)

    def _build_generales(self, f):
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)
        self._f_generales = f

        # Código — siempre disabled, se genera automáticamente
        ttk.Label(f, text="Código").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_codigo = ttk.Entry(f, width=12, state="disabled")
        self.e_codigo.grid(row=0, column=1, sticky="w", pady=4)

        if not self.codigo:
            session = get_session()
            ultimo = (session.query(Establecimiento)
                      .order_by(Establecimiento.codigo_establecimiento.desc())
                      .first())
            num = int(''.join(filter(str.isdigit, ultimo.codigo_establecimiento))) if ultimo else 0
            siguiente_cod = f"EST{num + 1:03d}"
            # Si ese código ya existe (está en baja), seguir buscando
            while session.query(Establecimiento).get(siguiente_cod):
                num += 1
                siguiente_cod = f"EST{num + 1:03d}"
            # Guardar también el siguiente código de inscripto
            from database.models import Inscripto as _I
            ultimo_insc = session.query(_I).order_by(_I.codigo_inscripcion.desc()).first()
            self._siguiente_cod_inscripto = (ultimo_insc.codigo_inscripcion + 1) if ultimo_insc else 1
            session.close()
            self.e_codigo.configure(state="normal")
            self.e_codigo.insert(0, siguiente_cod)
            self.e_codigo.configure(state="disabled")

        ttk.Label(f, text="Estado tramite").grid(row=0, column=2, sticky="w", padx=(12, 8))
        self.e_estado = ttk.Combobox(f, values=[
            "FINALIZADO", "EN TRAMITE", "PENDIENTE", "BAJA", "SUSPENDIDO"],
            width=18, state="readonly")
        self.e_estado.grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(f, text="Nombre *").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_nombre = ttk.Entry(f, width=40)
        self.e_nombre.grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)

        # Titular
        ttk.Label(f, text="Titular (inscripto)").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        session = get_session()
        inscriptos = session.query(Inscripto).order_by(Inscripto.apellido_razonsocial).all()
        self._inscriptos_map = {i.nombre_completo.title(): i.codigo_inscripcion for i in inscriptos}
        session.close()

        titular_frame = ttk.Frame(f)
        titular_frame.grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)
        titular_frame.columnconfigure(0, weight=1)

        self.e_titular = ttk.Combobox(titular_frame,
            values=[""] + list(self._inscriptos_map.keys()), width=32, state="readonly")
        self.e_titular.grid(row=0, column=0, sticky="ew")

        if not self.codigo:
            self.inscripto_existe_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(titular_frame, text="¿Ya existe?",
                            variable=self.inscripto_existe_var,
                            command=self._toggle_nuevo_inscripto).grid(
                                row=0, column=1, padx=(8, 0))

            self._frame_nuevo_insc = ttk.LabelFrame(f, text="Nuevo inscripto / titular", padding=10)
            self._frame_nuevo_insc.columnconfigure(1, weight=1)
            self._frame_nuevo_insc.columnconfigure(3, weight=1)

            for label, attr, row, col in [
                ("Apellido / Razón Social *", "ni_apellido",  0, 0),
                ("Nombres",                   "ni_nombres",   0, 2),
                ("DNI",                       "ni_dni",       1, 0),
                ("CUIT/CUIL",                 "ni_cuit",      1, 2),
                ("Domicilio",                 "ni_domicilio", 2, 0),
                ("Localidad",                 "ni_localidad", 3, 0),
                ("Teléfono",                  "ni_tel",       3, 2),
                ("Email",                     "ni_email",     4, 0),
            ]:
                ttk.Label(self._frame_nuevo_insc, text=label).grid(
                    row=row, column=col, sticky="w", pady=3, padx=(0, 6))
                e = ttk.Entry(self._frame_nuevo_insc, width=20)
                e.grid(row=row, column=col + 1, sticky="ew", pady=3)
                setattr(self, attr, e)

        ttk.Label(f, text="Domicilio").grid(row=3, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_domicilio = ttk.Entry(f, width=30)
        self.e_domicilio.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(f, text="Número").grid(row=3, column=2, sticky="w", padx=(12, 8))
        self.e_num = ttk.Entry(f, width=10)
        self.e_num.grid(row=3, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Localidad").grid(row=4, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_localidad = ttk.Entry(f, width=24)
        self.e_localidad.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(f, text="Cod. Postal").grid(row=4, column=2, sticky="w", padx=(12, 8))
        self.e_cp = ttk.Entry(f, width=10)
        self.e_cp.grid(row=4, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Provincia").grid(row=5, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_prov = ttk.Entry(f, width=24)
        self.e_prov.grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(f, text="Teléfono").grid(row=5, column=2, sticky="w", padx=(12, 8))
        self.e_tel = ttk.Entry(f, width=18)
        self.e_tel.grid(row=5, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Fecha certificado").grid(row=6, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_cert = ttk.Entry(f, width=14)
        self.e_cert.grid(row=6, column=1, sticky="w", pady=4)
        ttk.Label(f, text="(dd/mm/aaaa)", font=("Segoe UI", 10)).grid(row=6, column=2, sticky="w")

    def _toggle_nuevo_inscripto(self):
        if not self.inscripto_existe_var.get():
            self._frame_nuevo_insc.grid(
                row=7, column=0, columnspan=4, sticky="ew",
                pady=(8, 4), in_=self._f_generales)
            self.e_titular.configure(state="disabled")
            self.e_titular.set("")
            center_window(self, 700, 820)
        else:
            self._frame_nuevo_insc.grid_remove()
            self.e_titular.configure(state="readonly")
            center_window(self, 700, 620)

    def _build_montos(self, f):
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)

        session = get_session()
        rubros = session.query(Rubro).order_by(Rubro.nombre).all()
        
        # Protección contra NULOS en Rubros
        self._rubros_map   = {f"{r.nombre or 'Sin nombre'} ($ {(r.valor or 0.0):,.0f})": r.id_rubro for r in rubros}
        self._rubros_valor = {r.id_rubro: (r.valor or 0.0) for r in rubros}
        session.close()
        
        rubro_vals = [""] + list(self._rubros_map.keys())

        for i, (lbl, attr_cb, attr_monto) in enumerate([
            ("Rubro principal", "e_rubro",  "e_monto"),
            ("Anexo 1",         "e_anexo1", "e_monto1"),
            ("Anexo 2",         "e_anexo2", "e_monto2"),
            ("Anexo 3",         "e_anexo3", "e_monto3"),
        ]):
            ttk.Label(f, text=lbl).grid(row=i, column=0, sticky="w", pady=5, padx=(0, 8))
            cb = ttk.Combobox(f, values=rubro_vals, width=34, state="readonly")
            cb.grid(row=i, column=1, sticky="ew", pady=5)
            setattr(self, attr_cb, cb)

            ttk.Label(f, text="Monto $").grid(row=i, column=2, sticky="w", padx=(12, 8))
            ent = ttk.Entry(f, width=14, state="disabled")
            ent.grid(row=i, column=3, sticky="w", pady=5)
            setattr(self, attr_monto, ent)

            def _on_select(event, entry=ent, combo=cb):
                rid = self._rubros_map.get(combo.get())
                if rid:
                    valor = self._rubros_valor.get(rid, 0)
                    entry.configure(state="normal")
                    entry.delete(0, "end")
                    entry.insert(0, f"{valor:.2f}")
                    entry.configure(state="disabled")
            cb.bind("<<ComboboxSelected>>", _on_select)

        if not self.codigo:
            ttk.Separator(f, orient="horizontal").grid(row=4, column=0, columnspan=4, sticky="ew", pady=(20, 10))
            self.pago_express_var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(f, text="💰 ¿Abonó la tasa de inscripción en ventanilla? (Pago Express)",
                                  variable=self.pago_express_var)
            chk.grid(row=5, column=0, columnspan=4, sticky="w", pady=5)

    def _build_obs(self, f):
        ttk.Label(f, text="Solicitudes").pack(anchor="w")
        self.e_solicitudes = ttk.Entry(f, width=60)
        self.e_solicitudes.pack(fill="x", pady=(0, 10))
        ttk.Label(f, text="Observaciones").pack(anchor="w")
        self.e_obs = tk.Text(f, height=8, width=60, font=FONT_NORMAL,
                             relief="solid", borderwidth=1)
        self.e_obs.pack(fill="both", expand=True)

    def _load(self, codigo):
        session = get_session()
        e = session.query(Establecimiento).get(codigo)
        if not e:
            session.close()
            return

        # Código
        self.e_codigo.configure(state="normal")
        self.e_codigo.delete(0, "end")
        self.e_codigo.insert(0, e.codigo_establecimiento)
        self.e_codigo.configure(state="disabled")

        set_entry(self.e_nombre, e.nombre_establecimiento or "")
        self.e_estado.set(e.estado_tramite or "")
        set_entry(self.e_domicilio, e.domicilio_establecimiento or "")
        set_entry(self.e_num, e.numero_establecimiento or "")
        set_entry(self.e_localidad, e.localidad_establecimiento or "")
        set_entry(self.e_cp, str(e.codigo_postal or ""))
        set_entry(self.e_prov, e.provincia_establecimiento or "")
        set_entry(self.e_tel, e.telefono_establecimiento or "")
        set_entry(self.e_cert, format_date(e.fecha_certificado))
        set_entry(self.e_solicitudes, e.solicitudes or "")
        if e.observaciones:
            self.e_obs.insert("1.0", e.observaciones)

        if e.inscripto:
            key = e.inscripto.nombre_completo.title()
            if key in self._inscriptos_map:
                self.e_titular.set(key)

        def set_rubro_cb(cb, rubro_id):
            for key, rid in self._rubros_map.items():
                if rid == rubro_id:
                    cb.set(key)
                    return

        set_rubro_cb(self.e_rubro,  e.rubro_id)
        set_rubro_cb(self.e_anexo1, e.anexo1_id)
        set_rubro_cb(self.e_anexo2, e.anexo2_id)
        set_rubro_cb(self.e_anexo3, e.anexo3_id)

        # Cargar montos históricos con protección contra NULOS
        for entry, val in [
            (self.e_monto,  e.monto),
            (self.e_monto1, e.monto1),
            (self.e_monto2, e.monto2),
            (self.e_monto3, e.monto3),
        ]:
            entry.configure(state="normal")
            entry.delete(0, "end")
            # Si el valor de la base de datos viene vacío (None), le pone 0.00
            entry.insert(0, f"{(val or 0.0):.2f}")
            entry.configure(state="disabled")

        session.close()

    def _guardar(self):
        self.e_codigo.configure(state="normal")
        codigo = get_entry(self.e_codigo).upper()
        self.e_codigo.configure(state="disabled")

        nombre = get_entry(self.e_nombre)
        if not codigo:
            error_dialog(self, "Error", "No se pudo generar el código.")
            return
        if not nombre:
            error_dialog(self, "Error", "El Nombre es obligatorio.")
            return

        session = get_session()
        if self.codigo:
            e = session.query(Establecimiento).get(self.codigo)
            if not e:
                error_dialog(self, "Error", "Establecimiento no encontrado.")
                session.close()
                return
            rubro_nuevo = self._rubros_map.get(self.e_rubro.get())
            if e.rubro_id and rubro_nuevo and e.rubro_id != rubro_nuevo:
                if not messagebox.askyesno("Cambio de rubro",
                        "Estás cambiando el rubro principal.\n"
                        "El monto se actualizará al valor actual del rubro.\n\n"
                        "¿Confirmar el cambio?", parent=self):
                    session.close()
                    return
        else:
            e = Establecimiento(codigo_establecimiento=codigo)
            session.add(e)

        e.nombre_establecimiento    = nombre.upper()
        e.estado_tramite            = self.e_estado.get() or None
        e.domicilio_establecimiento = get_entry(self.e_domicilio)
        e.numero_establecimiento    = get_entry(self.e_num)
        e.localidad_establecimiento = get_entry(self.e_localidad)
        e.provincia_establecimiento = get_entry(self.e_prov)
        e.telefono_establecimiento  = get_entry(self.e_tel)
        # Reemplazar la línea de e.fecha_certificado por:
        fecha_cert_str = get_entry(self.e_cert)
        if fecha_cert_str:
            fecha_valida = parse_date_str(fecha_cert_str)
            if not fecha_valida:
                error_dialog(self, "Error de Fecha", "La fecha del certificado no es válida. Usá el formato dd/mm/aaaa.")
                session.close()
                return
            e.fecha_certificado = fecha_valida
        else:
            e.fecha_certificado = None
        e.solicitudes               = get_entry(self.e_solicitudes)
        e.observaciones             = self.e_obs.get("1.0", "end").strip()
        cp_str = get_entry(self.e_cp)
        e.codigo_postal = int(cp_str) if cp_str.isdigit() else None

        if not self.codigo and hasattr(self, "inscripto_existe_var") and not self.inscripto_existe_var.get():
            apellido = get_entry(self.ni_apellido)
            if not apellido:
                error_dialog(self, "Error", "El Apellido del inscripto es obligatorio.")
                session.close()
                return
                
            # SEGURIDAD: Recalculamos el ID en este milisegundo para evitar colisiones si hay 2 PCs guardando a la vez
            from database.models import Inscripto as _I
            ultimo_insc = session.query(_I).order_by(_I.codigo_inscripcion.desc()).first()
            id_seguro = (ultimo_insc.codigo_inscripcion + 1) if ultimo_insc else 1
            
            nuevo_insc = Inscripto(
                codigo_inscripcion    = id_seguro,  # <--- Usamos el id_seguro
                apellido_razonsocial  = apellido.upper(),
                nombres               = get_entry(self.ni_nombres).upper(),
                numero_documento      = get_entry(self.ni_dni),
                numero_identificacion = get_entry(self.ni_cuit),
                domicilio             = get_entry(self.ni_domicilio),
                localidad             = get_entry(self.ni_localidad),
                telefono              = get_entry(self.ni_tel),
                correo                = get_entry(self.ni_email),
            )
            session.add(nuevo_insc)
            session.flush()
            e.codigo_inscripcion = nuevo_insc.codigo_inscripcion
        else:
            titular_sel = self.e_titular.get()
            e.codigo_inscripcion = self._inscriptos_map.get(titular_sel)

        def rubro_id_from_cb(cb):
            return self._rubros_map.get(cb.get())

        def leer_monto(entry):
            entry.configure(state="normal")
            v = parse_float_str(get_entry(entry))
            entry.configure(state="disabled")
            return v

        e.rubro_id  = rubro_id_from_cb(self.e_rubro)
        e.monto     = leer_monto(self.e_monto)
        e.anexo1_id = rubro_id_from_cb(self.e_anexo1)
        e.monto1    = leer_monto(self.e_monto1)
        e.anexo2_id = rubro_id_from_cb(self.e_anexo2)
        e.monto2    = leer_monto(self.e_monto2)
        e.anexo3_id = rubro_id_from_cb(self.e_anexo3)
        e.monto3    = leer_monto(self.e_monto3)

        try:
            session.commit()
            if not self.codigo:
                from database.models import Deuda, Emision
                anio_actual    = datetime.now().year
                periodo_actual = 1 if datetime.now().month <= 6 else 2
                id_emision     = f"{periodo_actual}-{anio_actual}"
                emision        = session.query(Emision).get(id_emision)
                vencimiento    = emision.vencimiento if emision else None
                
                importe_total = (e.monto or 0.0) + (e.monto1 or 0.0) + (e.monto2 or 0.0) + (e.monto3 or 0.0)

                es_pago_express = getattr(self, "pago_express_var", tk.BooleanVar(value=False)).get()

                deuda = Deuda(
                    codigo_establecimiento = e.codigo_establecimiento,
                    anio                  = anio_actual,
                    periodo               = periodo_actual,
                    vencimiento           = vencimiento,
                    importe               = importe_total,
                    pago                  = es_pago_express,
                    monto_abonado         = importe_total if es_pago_express else 0.0,
                    fecha_pago            = datetime.now() if es_pago_express else None,
                    medio_pago            = "EFECTIVO" if es_pago_express else None
                )
                session.add(deuda)
                session.commit()
                
                if es_pago_express:
                    if messagebox.askyesno("Guardado Exitoso",
                            f"✅ Establecimiento guardado y tasa inicial COBRADA por $ {importe_total:,.2f}.\n\n"
                            f"¿Querés imprimir el recibo de pago ahora?", parent=self):
                        from reports.documentos_institucionales import doc_detalle_deuda, _auto_path, abrir_pdf
                        try:
                            path = _auto_path(f"recibo_pago_{e.codigo_establecimiento}.pdf")
                            doc_detalle_deuda(session, path, e.codigo_establecimiento, solo_impagas=False)
                            abrir_pdf(path)
                        except Exception as ex:
                            error_dialog(self, "Error al imprimir recibo", str(ex))
                else:
                    info_dialog(self, "Guardado",
                        f"Establecimiento guardado correctamente.\n"
                        f"Se generó la deuda inicial (IMPAGA): período {periodo_actual}/{anio_actual} "
                        f"por $ {importe_total:,.2f}.")
            else:
                info_dialog(self, "Guardado", "Establecimiento modificado correctamente.")
            
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error al guardar", str(ex))
        finally:
            session.close()