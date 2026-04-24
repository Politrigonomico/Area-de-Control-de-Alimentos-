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
        ttk.Label(bar, text="Inscriptos / Titulares", font=FONT_TITLE).pack(side="left")

        ttk.Label(bar, text="Buscar:").pack(side="left", padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar, textvariable=self.search_var, width=26).pack(side="left")

        ttk.Button(bar, text="＋  Nuevo",  command=self._nuevo).pack(side="right", padx=4)
        ttk.Button(bar, text="✎  Editar",  command=self._editar).pack(side="right", padx=4)
        ttk.Button(bar, text="✕  Eliminar", style="Danger.TButton",
                   command=self._eliminar).pack(side="right", padx=4)

        self.tree, _ = scrolled_treeview(self, self.COLS, self.HEADINGS, self.WIDTHS, height=22)
        self.tree.bind("<Button-3>", self._menu_contextual)
        self.tree.bind("<Double-1>", lambda e: self._editar())

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
                f"¿Estás seguro de eliminar este inscripto del sistema?\n\n"
                "Esta acción no se puede deshacer."):
            return
        session = get_session()
        from database.models import Inscripto
        i = session.query(Inscripto).get(int(codigo))
        if i:
            session.delete(i)
            session.commit()
        session.close()
        self.refresh()

    def refresh(self):
        session = get_session()
        q = session.query(Inscripto)
        busqueda = self.search_var.get().strip()
        if busqueda:
            q = q.filter(
                Inscripto.apellido_razonsocial.ilike(f"%{busqueda}%") |
                Inscripto.nombres.ilike(f"%{busqueda}%") |
                Inscripto.numero_documento.ilike(f"%{busqueda}%") |
                Inscripto.numero_identificacion.ilike(f"%{busqueda}%")
            )
        rows = q.order_by(Inscripto.apellido_razonsocial).all()
        session.close()

        self.tree.delete(*self.tree.get_children())
        for i in rows:
            self.tree.insert("", "end", iid=str(i.codigo_inscripcion), values=(
                i.codigo_inscripcion,
                (i.apellido_razonsocial or "").title(),
                (i.nombres or "").title(),
                f"{i.tipo_documento or ''} {i.numero_documento or ''}".strip(),
                f"{i.tipo_identificacion or ''} {i.numero_identificacion or ''}".strip(),
                (i.localidad or "").title(),
                i.telefono or i.telefono_movil or "—",
                i.correo or "—",
            ))

    def _selected_codigo(self):
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
        codigo = self._selected_codigo()
        if codigo is None:
            return
        dlg = InscriptoDialog(self, codigo)
        self.wait_window(dlg)
        self.refresh()

    def _eliminar(self):
        codigo = self._selected_codigo()
        if codigo is None:
            return
        if not confirm_dialog(self, "Eliminar", "¿Eliminar este inscripto? Esta acción no se puede deshacer."):
            return
        session = get_session()
        i = session.query(Inscripto).get(codigo)
        if i:
            session.delete(i)
            session.commit()
        session.close()
        self.refresh()


class InscriptoDialog(tk.Toplevel):
    def __init__(self, parent, codigo=None):
        super().__init__(parent)
        self.codigo = codigo
        self.title("Nuevo inscripto" if not codigo else f"Editar inscripto #{codigo}")
        self.resizable(False, False)
        center_window(self, 620, 530)
        self.grab_set()
        self._build()
        if codigo:
            self._load(codigo)

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)

        fields = [
            # (label, attr, row, col, width)
            ("Apellido / Razón Social *", "e_apellido",  0, 0, 28),
            ("Nombres",                   "e_nombres",   0, 2, 22),
            ("Tipo doc.",                 "e_tipodoc",   1, 0,  8),
            ("Nro. documento",            "e_nrodoc",    1, 2, 14),
            ("Tipo ident.",               "e_tipoint",   2, 0,  8),
            ("Nro. identificación",       "e_nroint",    2, 2, 16),
            ("Domicilio",                 "e_domicilio", 3, 0, 26),
            ("Número",                    "e_numdom",    3, 2, 10),
            ("Localidad",                 "e_localidad", 4, 0, 22),
            ("Provincia",                 "e_prov",      4, 2, 18),
            ("Código postal",             "e_cp",        5, 0, 10),
            ("Teléfono fijo",             "e_tel",       5, 2, 14),
            ("Teléfono móvil",            "e_movil",     6, 0, 16),
            ("Correo electrónico",        "e_correo",    6, 2, 24),
            ("Monto sellado",             "e_sellado",   7, 0, 12),
            ("Fecha inicio trámite",      "e_fecha",     7, 2, 14),
        ]
        for label, attr, row, col, width in fields:
            ttk.Label(f, text=label).grid(
                row=row, column=col*2, sticky="w", pady=4, padx=(0, 8))
            e = ttk.Entry(f, width=width)
            e.grid(row=row, column=col*2+1, sticky="ew", pady=4, padx=(0, 12))
            setattr(self, attr, e)

        ttk.Label(f, text="Observaciones").grid(
            row=8, column=0, sticky="nw", pady=4, padx=(0, 8))
        self.e_obs = tk.Text(f, height=4, width=50, font=FONT_NORMAL,
                             relief="solid", borderwidth=1)
        self.e_obs.grid(row=8, column=1, columnspan=3, sticky="ew", pady=4)

        # Botones
        bar = ttk.Frame(f)
        bar.grid(row=9, column=0, columnspan=4, pady=(12, 0), sticky="e")
        ttk.Button(bar, text="Guardar", command=self._guardar,
                   style="Success.TButton").pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _load(self, codigo):
        session = get_session()
        i = session.query(Inscripto).get(codigo)
        if not i:
            session.close()
            return
        set_entry(self.e_apellido,  i.apellido_razonsocial or "")
        set_entry(self.e_nombres,   i.nombres or "")
        set_entry(self.e_tipodoc,   i.tipo_documento or "")
        set_entry(self.e_nrodoc,    i.numero_documento or "")
        set_entry(self.e_tipoint,   i.tipo_identificacion or "")
        set_entry(self.e_nroint,    i.numero_identificacion or "")
        set_entry(self.e_domicilio, i.domicilio or "")
        set_entry(self.e_numdom,    i.numero_domicilio or "")
        set_entry(self.e_localidad, i.localidad or "")
        set_entry(self.e_prov,      i.provincia or "")
        set_entry(self.e_cp,        i.codigo_postal or "")
        set_entry(self.e_tel,       i.telefono or "")
        set_entry(self.e_movil,     i.telefono_movil or "")
        set_entry(self.e_correo,    i.correo or "")
        set_entry(self.e_sellado,   str(i.monto_sellado or 0))
        set_entry(self.e_fecha,     format_date(i.fecha_inicio_tramite))
        if i.observaciones:
            self.e_obs.insert("1.0", i.observaciones)
        session.close()

    def _guardar(self):
        apellido = get_entry(self.e_apellido)
        if not apellido:
            error_dialog(self, "Error", "Apellido / Razón Social es obligatorio.")
            return

        session = get_session()
        if self.codigo:
            i = session.query(Inscripto).get(self.codigo)
        else:
            from sqlalchemy import func
            ultimo_num = session.query(func.max(Inscripto.codigo_inscripcion)).scalar() or 0
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
        i.correo                = get_entry(self.e_correo)
        i.monto_sellado         = parse_float_str(get_entry(self.e_sellado))
        i.fecha_inicio_tramite  = parse_date_str(get_entry(self.e_fecha))
        i.observaciones         = self.e_obs.get("1.0", "end").strip()

        try:
            session.commit()
            info_dialog(self, "Guardado", "Inscripto guardado correctamente.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error al guardar", str(ex))
        finally:
            session.close()
