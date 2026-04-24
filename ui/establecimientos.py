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
    """Panel principal de Establecimientos."""

    COLS     = ("codigo", "nombre", "titular", "domicilio", "rubro", "estado", "monto", "baja")
    HEADINGS = ("Código", "Nombre", "Titular", "Domicilio", "Rubro", "Estado", "Monto Total", "Baja")
    WIDTHS   = (70, 200, 180, 180, 140, 100, 100, 50)

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="TFrame")
        self._build()
        self.refresh()

    def _build(self):
        # Toolbar superior
        bar = ttk.Frame(self, padding=(0, 0, 0, 8))
        bar.pack(fill="x")

        ttk.Label(bar, text="Establecimientos",
                  font=FONT_TITLE).pack(side="left")

        # Búsqueda
        ttk.Label(bar, text="Buscar:", font=FONT_NORMAL).pack(side="left", padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar, textvariable=self.search_var, width=26).pack(side="left")

        # Filtro estado
        self.mostrar_bajas_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text="Incluir bajas",
                        variable=self.mostrar_bajas_var,
                        command=self.refresh).pack(side="left", padx=8)

        # Botones acción
        ttk.Button(bar, text="＋  Nuevo", command=self._nuevo).pack(side="right", padx=4)
        ttk.Button(bar, text="✎  Editar", command=self._editar).pack(side="right", padx=4)
        ttk.Button(bar, text="✕  Dar de baja", style="Danger.TButton",
                   command=self._dar_baja).pack(side="right", padx=4)

        # Treeview
        self.tree, _ = scrolled_treeview(self, self.COLS, self.HEADINGS, self.WIDTHS, height=22)
        self.tree.bind("<Double-1>", lambda e: self._editar())

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

        # Serializar relaciones ANTES de cerrar la sesión (evita DetachedInstanceError)
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
            # Si el comercio no tiene código en el sistema viejo, le inventamos un ID temporal
            codigo_id = d[0] if d[0] and str(d[0]).strip() != "" else f"SIN_CODIGO_{i}"
            self.tree.insert("", "end", iid=codigo_id, tags=(d[8],), values=d[:8])

    def _selected_codigo(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná un establecimiento primero.")
            return None
        return sel[0]

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
    """Diálogo para crear o editar un establecimiento."""

    def __init__(self, parent, codigo=None):
        super().__init__(parent)
        self.codigo  = codigo
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

        # Tab 1: Datos generales
        f1 = ttk.Frame(nb, padding=16)
        nb.add(f1, text="  Datos generales  ")
        self._build_generales(f1)

        # Tab 2: Montos / rubros
        f2 = ttk.Frame(nb, padding=16)
        nb.add(f2, text="  Rubros y montos  ")
        self._build_montos(f2)

        # Tab 3: Observaciones
        f3 = ttk.Frame(nb, padding=16)
        nb.add(f3, text="  Observaciones  ")
        self._build_obs(f3)

        # Botones
        bar = ttk.Frame(self, padding=(12, 4, 12, 12))
        bar.pack(fill="x")
        ttk.Button(bar, text="Guardar", command=self._guardar,
                   style="Success.TButton").pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right", padx=4)

    def _build_generales(self, f):
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)

        # Código
        ttk.Label(f, text="Código *").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_codigo = ttk.Entry(f, width=12)
        self.e_codigo.grid(row=0, column=1, sticky="w", pady=4)
        if self.codigo:
            self.e_codigo.configure(state="disabled")

        ttk.Label(f, text="Estado tramite").grid(row=0, column=2, sticky="w", padx=(12, 8))
        self.e_estado = ttk.Combobox(f, values=[
            "FINALIZADO", "EN TRAMITE", "PENDIENTE", "BAJA", "SUSPENDIDO"], width=18, state="readonly")
        self.e_estado.grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(f, text="Nombre *").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_nombre = ttk.Entry(f, width=40)
        self.e_nombre.grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(f, text="Titular (inscripto)").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        session = get_session()
        inscriptos = session.query(Inscripto).order_by(Inscripto.apellido_razonsocial).all()
        self._inscriptos_map = {i.nombre_completo.title(): i.codigo_inscripcion for i in inscriptos}
        session.close()
        self.e_titular = ttk.Combobox(f,
            values=[""] + list(self._inscriptos_map.keys()), width=38, state="readonly")
        self.e_titular.grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)

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

    def _build_montos(self, f):
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)

        session = get_session()
        rubros = session.query(Rubro).order_by(Rubro.nombre).all()
        self._rubros_map = {f"{r.nombre} ($ {r.valor:,.0f})": r.id_rubro for r in rubros}
        session.close()
        rubro_vals = [""] + list(self._rubros_map.keys())

        for i, (lbl, attr_cb, attr_monto) in enumerate([
            ("Rubro principal",  "e_rubro",  "e_monto"),
            ("Anexo 1",          "e_anexo1", "e_monto1"),
            ("Anexo 2",          "e_anexo2", "e_monto2"),
            ("Anexo 3",          "e_anexo3", "e_monto3"),
        ]):
            ttk.Label(f, text=lbl).grid(row=i, column=0, sticky="w", pady=5, padx=(0, 8))
            cb = ttk.Combobox(f, values=rubro_vals, width=34, state="readonly")
            cb.grid(row=i, column=1, sticky="ew", pady=5)
            setattr(self, attr_cb, cb)

            ttk.Label(f, text="Monto $").grid(row=i, column=2, sticky="w", padx=(12, 8))
            ent = ttk.Entry(f, width=14)
            ent.grid(row=i, column=3, sticky="w", pady=5)
            setattr(self, attr_monto, ent)

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

        set_entry(self.e_codigo, e.codigo_establecimiento)
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

        # Titular
        if e.inscripto:
            key = e.inscripto.nombre_completo.title()
            if key in self._inscriptos_map:
                self.e_titular.set(key)

        # Rubros — busca la clave que contiene el nombre
        def set_rubro_cb(cb, rubro_id):
            for key, rid in self._rubros_map.items():
                if rid == rubro_id:
                    cb.set(key)
                    return

        set_rubro_cb(self.e_rubro,  e.rubro_id)
        set_rubro_cb(self.e_anexo1, e.anexo1_id)
        set_rubro_cb(self.e_anexo2, e.anexo2_id)
        set_rubro_cb(self.e_anexo3, e.anexo3_id)
        set_entry(self.e_monto,  str(e.monto or 0))
        set_entry(self.e_monto1, str(e.monto1 or 0))
        set_entry(self.e_monto2, str(e.monto2 or 0))
        set_entry(self.e_monto3, str(e.monto3 or 0))

        session.close()

    def _guardar(self):
        codigo = get_entry(self.e_codigo).upper()
        nombre = get_entry(self.e_nombre)
        if not codigo or not nombre:
            error_dialog(self, "Error", "Código y Nombre son obligatorios.")
            return

        session = get_session()
        if self.codigo:
            e = session.query(Establecimiento).get(self.codigo)
            if not e:
                error_dialog(self, "Error", "Establecimiento no encontrado.")
                session.close()
                return
        else:
            if session.query(Establecimiento).get(codigo):
                error_dialog(self, "Error", f"El código '{codigo}' ya existe.")
                session.close()
                return
            e = Establecimiento(codigo_establecimiento=codigo)
            session.add(e)

        e.nombre_establecimiento     = nombre.upper()
        e.estado_tramite             = self.e_estado.get() or None
        e.domicilio_establecimiento  = get_entry(self.e_domicilio)
        e.numero_establecimiento     = get_entry(self.e_num)
        e.localidad_establecimiento  = get_entry(self.e_localidad)
        e.provincia_establecimiento  = get_entry(self.e_prov)
        e.telefono_establecimiento   = get_entry(self.e_tel)
        e.fecha_certificado          = parse_date_str(get_entry(self.e_cert))
        e.solicitudes                = get_entry(self.e_solicitudes)
        e.observaciones              = self.e_obs.get("1.0", "end").strip()

        cp_str = get_entry(self.e_cp)
        e.codigo_postal = int(cp_str) if cp_str.isdigit() else None

        titular_sel = self.e_titular.get()
        e.codigo_inscripcion = self._inscriptos_map.get(titular_sel)

        def rubro_id_from_cb(cb):
            return self._rubros_map.get(cb.get())

        e.rubro_id  = rubro_id_from_cb(self.e_rubro)
        e.monto     = parse_float_str(get_entry(self.e_monto))
        e.anexo1_id = rubro_id_from_cb(self.e_anexo1)
        e.monto1    = parse_float_str(get_entry(self.e_monto1))
        e.anexo2_id = rubro_id_from_cb(self.e_anexo2)
        e.monto2    = parse_float_str(get_entry(self.e_monto2))
        e.anexo3_id = rubro_id_from_cb(self.e_anexo3)
        e.monto3    = parse_float_str(get_entry(self.e_monto3))

        try:
            session.commit()
            info_dialog(self, "Guardado", "Establecimiento guardado correctamente.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error al guardar", str(ex))
        finally:
            session.close()
