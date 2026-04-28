"""
Módulo de Inscriptos — titulares de establecimientos.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from database.db import get_session
from database.models import Inscripto
from utils.ui_helpers import (
    COLORS, FONT_NORMAL, FONT_TITLE,
    scrolled_treeview, set_entry, get_entry,
    format_date, parse_date_str, parse_float_str,
    center_window, confirm_dialog, info_dialog, error_dialog,
)

class InscriptosFrame(ttk.Frame):
    COLS     = ("codigo", "apellido", "nombres", "doc", "cuit", "localidad", "telefono", "correo")
    HEADINGS = ("Código", "Apellido / Razón Social", "Nombres", "DNI", "CUIT/CUIL", "Localidad", "Teléfono", "Correo")
    WIDTHS   = (60, 200, 160, 90, 120, 130, 110, 180)

    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        bar = ttk.Frame(self, padding=(0, 0, 0, 8))
        bar.pack(fill="x")
        
        # Panel izquierdo
        left_side = ttk.Frame(bar)
        left_side.pack(side="left", fill="x", expand=True)
        
        ttk.Label(left_side, text="Inscriptos / Titulares", font=FONT_TITLE).pack(side="left")
        ttk.Label(left_side, text="Buscar:").pack(side="left", padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(left_side, textvariable=self.search_var, width=28).pack(side="left")

        # Panel derecho
        right_side = ttk.Frame(bar)
        right_side.pack(side="right")
        
        ttk.Button(right_side, text="＋  Nuevo",  command=self._nuevo).pack(side="left", padx=4)
        ttk.Button(right_side, text="✎  Editar",  command=self._editar).pack(side="left", padx=4)
        ttk.Button(right_side, text="✕  Eliminar", style="Danger.TButton",
                   command=self._eliminar).pack(side="left", padx=4)

        self.tree, _ = scrolled_treeview(self, self.COLS, self.HEADINGS, self.WIDTHS, height=22)
        self.tree.bind("<Double-1>", lambda e: self._editar())
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

    def _eliminar(self, iid=None):
        if not iid:
            sel = self.tree.selection()
            if not sel:
                messagebox.showwarning("Selección", "Seleccioná un inscripto primero.")
                return
            iid = sel[0]

        session = get_session()
        i = session.query(Inscripto).get(int(iid))
        if not i:
            session.close()
            return
            
        # MEJORA CRÍTICA: Prevenir borrado si tiene comercios asociados para no corromper la BD
        if i.establecimientos:
            error_dialog(self, "No se puede eliminar", 
                         f"El titular {i.apellido_razonsocial} tiene establecimientos asociados a su nombre.\n\n"
                         "Debés reasignar los comercios a otro titular o darlos de baja antes de poder eliminar este registro.")
            session.close()
            return

        if not confirm_dialog(self, "Eliminar",
                f"¿Estás seguro de eliminar a {i.apellido_razonsocial} del sistema?\n\n"
                "Esta acción no se puede deshacer."):
            session.close()
            return

        try:
            session.delete(i)
            session.commit()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()
            
        self.refresh()

    def refresh(self):
        session = get_session()
        q = session.query(Inscripto)
        busq = self.search_var.get().strip()
        if busq:
            q = q.filter(
                Inscripto.apellido_razonsocial.ilike(f"%{busq}%") |
                Inscripto.nombres.ilike(f"%{busq}%") |
                Inscripto.numero_documento.ilike(f"%{busq}%") |
                Inscripto.numero_identificacion.ilike(f"%{busq}%")
            )
        rows = q.order_by(Inscripto.apellido_razonsocial).all()

        datos = []
        for i in rows:
            datos.append((
                str(i.codigo_inscripcion),
                (i.apellido_razonsocial or "").upper(),
                (i.nombres or "").title(),
                f"{(i.tipo_documento or 'DNI')}: {i.numero_documento or ''}",
                f"{(i.tipo_identificacion or 'CUIT')}: {i.numero_identificacion or ''}",
                (i.localidad or "").title(),
                i.telefono or i.telefono_movil or "",
                i.correo or "",
            ))
        session.close()

        self.tree.delete(*self.tree.get_children())
        for d in datos:
            self.tree.insert("", "end", iid=d[0], values=d)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná un inscripto primero.")
            return None
        return int(sel[0])

    def _nuevo(self):
        dlg = InscriptoDialog(self, None)
        self.wait_window(dlg)
        self.refresh()

    def _editar(self):
        iid = self._selected_id()
        if not iid:
            return
        dlg = InscriptoDialog(self, iid)
        self.wait_window(dlg)
        self.refresh()


class InscriptoDialog(tk.Toplevel):
    def __init__(self, parent, codigo=None):
        super().__init__(parent)
        self.codigo = codigo
        self.title("Nuevo Inscripto" if not codigo else f"Editar Inscripto #{codigo}")
        self.resizable(False, False)
        center_window(self, 640, 480)
        self.grab_set()
        self._build()
        if codigo:
            self._load(codigo)

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)

        ttk.Label(f, text="Apellido / Razón Social *").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_ap_rs = ttk.Entry(f, width=28)
        self.e_ap_rs.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(f, text="Nombres").grid(row=0, column=2, sticky="w", padx=(12, 8))
        self.e_nombres = ttk.Entry(f, width=28)
        self.e_nombres.grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(f, text="Tipo Documento").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_tipodoc = ttk.Combobox(f, values=["DNI", "LC", "LE", "PASAPORTE"], width=10, state="readonly")
        self.e_tipodoc.grid(row=1, column=1, sticky="w", pady=4)
        self.e_tipodoc.set("DNI")

        ttk.Label(f, text="Nº Documento").grid(row=1, column=2, sticky="w", padx=(12, 8))
        self.e_nrodoc = ttk.Entry(f, width=20)
        self.e_nrodoc.grid(row=1, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Tipo Identif.").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_tipoint = ttk.Combobox(f, values=["CUIT", "CUIL", "CDI"], width=10, state="readonly")
        self.e_tipoint.grid(row=2, column=1, sticky="w", pady=4)
        self.e_tipoint.set("CUIT")

        ttk.Label(f, text="Nº Identif. (CUIT)").grid(row=2, column=2, sticky="w", padx=(12, 8))
        self.e_nroint = ttk.Entry(f, width=20)
        self.e_nroint.grid(row=2, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Domicilio").grid(row=3, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_domicilio = ttk.Entry(f, width=28)
        self.e_domicilio.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(f, text="Número").grid(row=3, column=2, sticky="w", padx=(12, 8))
        self.e_numdom = ttk.Entry(f, width=10)
        self.e_numdom.grid(row=3, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Localidad").grid(row=4, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_localidad = ttk.Entry(f, width=28)
        self.e_localidad.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(f, text="Provincia").grid(row=4, column=2, sticky="w", padx=(12, 8))
        self.e_prov = ttk.Entry(f, width=20)
        self.e_prov.grid(row=4, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Cód. Postal").grid(row=5, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_cp = ttk.Entry(f, width=10)
        self.e_cp.grid(row=5, column=1, sticky="w", pady=4)

        ttk.Label(f, text="Tel. Fijo").grid(row=5, column=2, sticky="w", padx=(12, 8))
        self.e_tel = ttk.Entry(f, width=20)
        self.e_tel.grid(row=5, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Celular / Móvil").grid(row=6, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_movil = ttk.Entry(f, width=28)
        self.e_movil.grid(row=6, column=1, sticky="ew", pady=4)

        ttk.Label(f, text="Correo Electrónico").grid(row=6, column=2, sticky="w", padx=(12, 8))
        self.e_correo = ttk.Entry(f, width=28)
        self.e_correo.grid(row=6, column=3, sticky="ew", pady=4)

        ttk.Label(f, text="Fecha Inicio Trámite").grid(row=7, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_fecha = ttk.Entry(f, width=14)
        self.e_fecha.grid(row=7, column=1, sticky="w", pady=4)
        
        ttk.Label(f, text="Monto Sellado $").grid(row=7, column=2, sticky="w", padx=(12, 8))
        self.e_sellado = ttk.Entry(f, width=14)
        self.e_sellado.grid(row=7, column=3, sticky="w", pady=4)

        ttk.Label(f, text="Observaciones").grid(row=8, column=0, sticky="nw", pady=4, padx=(0, 8))
        self.e_obs = tk.Text(f, height=3, width=60, font=FONT_NORMAL)
        self.e_obs.grid(row=8, column=1, columnspan=3, sticky="ew", pady=4)

        bar = ttk.Frame(f)
        bar.grid(row=9, column=0, columnspan=4, pady=(16, 0), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton",
                   command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _load(self, codigo):
        session = get_session()
        i = session.query(Inscripto).get(codigo)
        if not i:
            session.close()
            return

        set_entry(self.e_ap_rs, i.apellido_razonsocial or "")
        set_entry(self.e_nombres, i.nombres or "")
        self.e_tipodoc.set((i.tipo_documento or "DNI").upper())
        set_entry(self.e_nrodoc, i.numero_documento or "")
        self.e_tipoint.set((i.tipo_identificacion or "CUIT").upper())
        set_entry(self.e_nroint, i.numero_identificacion or "")
        set_entry(self.e_domicilio, i.domicilio or "")
        set_entry(self.e_numdom, i.numero_domicilio or "")
        set_entry(self.e_localidad, i.localidad or "")
        set_entry(self.e_prov, i.provincia or "")
        set_entry(self.e_cp, i.codigo_postal or "")
        set_entry(self.e_tel, i.telefono or "")
        set_entry(self.e_movil, i.telefono_movil or "")
        set_entry(self.e_correo, (i.correo or "").lower())
        set_entry(self.e_fecha, format_date(i.fecha_inicio_tramite))
        set_entry(self.e_sellado, f"{i.monto_sellado:.2f}" if i.monto_sellado else "0.00")
        if i.observaciones:
            self.e_obs.insert("1.0", i.observaciones)

        session.close()

    def _guardar(self):
        apellido = get_entry(self.e_ap_rs)
        if not apellido:
            error_dialog(self, "Error", "El Apellido o Razón Social es obligatorio.")
            return

        # MEJORA: Validación estricta de fecha
        fecha_str = get_entry(self.e_fecha)
        fecha_valida = None
        if fecha_str:
            fecha_valida = parse_date_str(fecha_str)
            if not fecha_valida:
                error_dialog(self, "Error de Fecha", "La fecha de inicio de trámite no es válida. Usá el formato dd/mm/aaaa.")
                return

        session = get_session()
        if self.codigo:
            i = session.query(Inscripto).get(self.codigo)
            if not i:
                error_dialog(self, "Error", "Inscripto no encontrado.")
                session.close()
                return
        else:
            from sqlalchemy import func as _func
            ultimo_num = session.query(_func.max(Inscripto.codigo_inscripcion)).scalar() or 0
            i = Inscripto()
            i.codigo_inscripcion = ultimo_num + 1
            session.add(i)

        i.apellido_razonsocial  = apellido.upper()
        i.nombres               = get_entry(self.e_nombres).upper()
        i.tipo_documento        = get_entry(self.e_tipodoc).upper()
        i.numero_documento      = get_entry(self.e_nrodoc)
        i.tipo_identificacion   = get_entry(self.e_tipoint).upper()
        i.numero_identificacion = get_entry(self.e_nroint)
        i.domicilio             = get_entry(self.e_domicilio)
        i.numero_domicilio      = get_entry(self.e_numdom)
        i.localidad             = get_entry(self.e_localidad).upper()
        i.provincia             = get_entry(self.e_prov).upper()
        i.codigo_postal         = get_entry(self.e_cp)
        i.telefono              = get_entry(self.e_tel)
        i.telefono_movil        = get_entry(self.e_movil)
        i.correo                = get_entry(self.e_correo).lower() # MEJORA: forzar minúsculas
        i.monto_sellado         = parse_float_str(get_entry(self.e_sellado))
        i.fecha_inicio_tramite  = fecha_valida
        i.observaciones         = self.e_obs.get("1.0", "end").strip()

        try:
            session.commit()
            info_dialog(self, "Guardado", "Titular guardado correctamente.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error al guardar", str(ex))
        finally:
            session.close()