"""
Módulo de Rubros y Emisión — tablas de configuración del sistema.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from database.db import get_session
from database.models import Rubro, Anexo1, Anexo2, Anexo3, Emision
from utils.ui_helpers import (
    COLORS, FONT_NORMAL, FONT_TITLE,
    scrolled_treeview, set_entry, get_entry,
    format_date, parse_date_str, parse_float_str,
    center_window, confirm_dialog, info_dialog, error_dialog,
)


class RubrosFrame(ttk.Frame):
    """Administración de rubros y anexos."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ttk.Label(self, text="Rubros y Tablas de Valores", font=FONT_TITLE).pack(
            anchor="w", pady=(0, 12))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        for tab_label, model, attr in [
            ("Rubros principales", Rubro,  "_rub"),
            ("Anexo 1",            Anexo1, "_anx1"),
            ("Anexo 2",            Anexo2, "_anx2"),
            ("Anexo 3",            Anexo3, "_anx3"),
        ]:
            f = ttk.Frame(nb, padding=8)
            nb.add(f, text=f"  {tab_label}  ")
            self._build_tab(f, model, attr)

        # Emisión en tab separado
        fem = ttk.Frame(nb, padding=8)
        nb.add(fem, text="  Períodos de Emisión  ")
        self._build_emision(fem)

    def _build_tab(self, parent, model, attr_prefix):
        # Toolbar
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Button(bar, text="＋  Nuevo",   command=lambda: self._nuevo(model, attr_prefix)).pack(side="left", padx=2)
        ttk.Button(bar, text="✎  Editar",   command=lambda: self._editar(model, attr_prefix)).pack(side="left", padx=2)
        ttk.Button(bar, text="✕  Eliminar", style="Danger.TButton",
                   command=lambda: self._eliminar(model, attr_prefix)).pack(side="left", padx=2)

        cols = ("id", "nombre", "valor")
        heads = ("ID", "Nombre del rubro", "Valor $")
        widths = (60, 360, 120)
        tree, _ = scrolled_treeview(parent, cols, heads, widths, height=18)
        tree.bind("<Double-1>", lambda e: self._editar(model, attr_prefix))
        setattr(self, f"tree{attr_prefix}", tree)
        self._refresh_tab(model, attr_prefix)

    def _refresh_tab(self, model, attr_prefix):
        tree = getattr(self, f"tree{attr_prefix}")
        tree.delete(*tree.get_children())
        session = get_session()
        rows = session.query(model).order_by(model.id_rubro).all()
        session.close()
        for r in rows:
            tree.insert("", "end", iid=str(r.id_rubro), values=(
                r.id_rubro,
                r.nombre or "",
                f"$ {r.valor:,.2f}" if r.valor else "$ 0,00",
            ))

    def _selected_id(self, attr_prefix):
        tree = getattr(self, f"tree{attr_prefix}")
        sel  = tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná un rubro primero.")
            return None
        return int(sel[0])

    def _nuevo(self, model, attr_prefix):
        dlg = RubroDialog(self, model, None)
        self.wait_window(dlg)
        self._refresh_tab(model, attr_prefix)

    def _editar(self, model, attr_prefix):
        rid = self._selected_id(attr_prefix)
        if rid is None:
            return
        dlg = RubroDialog(self, model, rid)
        self.wait_window(dlg)
        self._refresh_tab(model, attr_prefix)

    def _eliminar(self, model, attr_prefix):
        rid = self._selected_id(attr_prefix)
        if rid is None:
            return
        if not confirm_dialog(self, "Eliminar", "¿Eliminar este rubro?"):
            return
        session = get_session()
        obj = session.query(model).get(rid)
        if obj:
            session.delete(obj)
            session.commit()
        session.close()
        self._refresh_tab(model, attr_prefix)

    def _build_emision(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Button(bar, text="＋  Nuevo período", command=self._nueva_emision).pack(side="left", padx=2)
        ttk.Button(bar, text="✎  Editar",         command=self._editar_emision).pack(side="left", padx=2)
        ttk.Button(bar, text="✕  Eliminar", style="Danger.TButton",
                   command=self._eliminar_emision).pack(side="left", padx=2)

        cols   = ("id", "periodo", "anio", "vencimiento", "primera_mora", "segunda_mora")
        heads  = ("ID", "Per.", "Año", "Vencimiento", "1ª Mora", "2ª Mora")
        widths = (80, 50, 60, 120, 120, 120)
        self.tree_emision, _ = scrolled_treeview(parent, cols, heads, widths, height=18)
        self.tree_emision.bind("<Double-1>", lambda e: self._editar_emision())
        self._refresh_emision()

    def _refresh_emision(self):
        self.tree_emision.delete(*self.tree_emision.get_children())
        session = get_session()
        rows = session.query(Emision).order_by(Emision.anio.desc(), Emision.periodo).all()
        session.close()
        for e in rows:
            self.tree_emision.insert("", "end", iid=e.id_emision, values=(
                e.id_emision,
                e.periodo or "",
                e.anio or "",
                format_date(e.vencimiento),
                format_date(e.primer_mora),
                format_date(e.segunda_mora),
            ))

    def _selected_emision_id(self):
        sel = self.tree_emision.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná un período primero.")
            return None
        return sel[0]

    def _nueva_emision(self):
        dlg = EmisionDialog(self, None)
        self.wait_window(dlg)
        self._refresh_emision()

    def _editar_emision(self):
        eid = self._selected_emision_id()
        if not eid:
            return
        dlg = EmisionDialog(self, eid)
        self.wait_window(dlg)
        self._refresh_emision()

    def _eliminar_emision(self):
        eid = self._selected_emision_id()
        if not eid:
            return
        if not confirm_dialog(self, "Eliminar", f"¿Eliminar el período {eid}?"):
            return
        session = get_session()
        e = session.query(Emision).get(eid)
        if e:
            session.delete(e)
            session.commit()
        session.close()
        self._refresh_emision()


class RubroDialog(tk.Toplevel):
    def __init__(self, parent, model, rubro_id=None):
        super().__init__(parent)
        self.model    = model
        self.rubro_id = rubro_id
        self.title("Nuevo rubro" if not rubro_id else f"Editar rubro #{rubro_id}")
        self.resizable(False, False)
        center_window(self, 380, 200)
        self.grab_set()
        self._build()
        if rubro_id:
            self._load(rubro_id)

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        ttk.Label(f, text="Nombre del rubro *").grid(row=0, column=0, sticky="w", pady=6, padx=(0, 10))
        self.e_nombre = ttk.Entry(f, width=32)
        self.e_nombre.grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(f, text="Valor $").grid(row=1, column=0, sticky="w", pady=6, padx=(0, 10))
        self.e_valor = ttk.Entry(f, width=16)
        self.e_valor.grid(row=1, column=1, sticky="w", pady=6)

        bar = ttk.Frame(f)
        bar.grid(row=2, column=0, columnspan=2, pady=(14, 0), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton",
                   command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _load(self, rid):
        session = get_session()
        r = session.query(self.model).get(rid)
        if r:
            set_entry(self.e_nombre, r.nombre or "")
            set_entry(self.e_valor,  str(r.valor or 0))
        session.close()

    def _guardar(self):
        nombre = get_entry(self.e_nombre)
        if not nombre:
            error_dialog(self, "Error", "El nombre es obligatorio.")
            return
        session = get_session()
        if self.rubro_id:
            obj = session.query(self.model).get(self.rubro_id)
        else:
            obj = self.model()
            session.add(obj)
        obj.nombre = nombre.upper()
        obj.valor  = parse_float_str(get_entry(self.e_valor))
        try:
            session.commit()
            info_dialog(self, "Guardado", "Rubro guardado.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()


class EmisionDialog(tk.Toplevel):
    def __init__(self, parent, emision_id=None):
        super().__init__(parent)
        self.emision_id = emision_id
        self.title("Nuevo período" if not emision_id else f"Editar período {emision_id}")
        self.resizable(False, False)
        center_window(self, 400, 300)
        self.grab_set()
        self._build()
        if emision_id:
            self._load(emision_id)

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        fields = [
            ("ID (ej: 1-2025) *", "e_id",      0),
            ("Período (1 ó 2) *", "e_periodo",  1),
            ("Año *",             "e_anio",     2),
            ("Vencimiento",       "e_venc",     3),
            ("1ª Mora",           "e_mora1",    4),
            ("2ª Mora",           "e_mora2",    5),
        ]
        for label, attr, row in fields:
            ttk.Label(f, text=label).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 10))
            e = ttk.Entry(f, width=16)
            e.grid(row=row, column=1, sticky="w", pady=5)
            setattr(self, attr, e)
        ttk.Label(f, text="(dd/mm/aaaa)", font=("Segoe UI", 10)).grid(
            row=3, column=1, sticky="e")

        if self.emision_id:
            self.e_id.configure(state="disabled")

        bar = ttk.Frame(f)
        bar.grid(row=6, column=0, columnspan=2, pady=(12, 0), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton",
                   command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _load(self, eid):
        session = get_session()
        e = session.query(Emision).get(eid)
        if e:
            set_entry(self.e_id,      e.id_emision or "")
            set_entry(self.e_periodo, e.periodo or "")
            set_entry(self.e_anio,    str(e.anio or ""))
            set_entry(self.e_venc,    format_date(e.vencimiento))
            set_entry(self.e_mora1,   format_date(e.primer_mora))
            set_entry(self.e_mora2,   format_date(e.segunda_mora))
        session.close()

    def _guardar(self):
        eid     = get_entry(self.e_id) or (self.emision_id or "")
        periodo = get_entry(self.e_periodo)
        anio_s  = get_entry(self.e_anio)
        if not eid or not periodo or not anio_s:
            error_dialog(self, "Error", "ID, período y año son obligatorios.")
            return
        session = get_session()
        if self.emision_id:
            em = session.query(Emision).get(self.emision_id)
        else:
            if session.query(Emision).get(eid):
                error_dialog(self, "Error", f"El ID '{eid}' ya existe.")
                session.close()
                return
            em = Emision(id_emision=eid)
            session.add(em)
        em.periodo      = periodo
        em.anio         = int(anio_s) if anio_s.isdigit() else None
        em.vencimiento  = parse_date_str(get_entry(self.e_venc))
        em.primer_mora  = parse_date_str(get_entry(self.e_mora1))
        em.segunda_mora = parse_date_str(get_entry(self.e_mora2))
        try:
            session.commit()
            info_dialog(self, "Guardado", "Período guardado.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()
