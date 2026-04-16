"""
Módulos de Auditorías y Sanidad.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from database.db import get_session
from database.models import Auditoria, Sanidad, Establecimiento
from utils.ui_helpers import (
    COLORS, FONT_NORMAL, FONT_TITLE,
    scrolled_treeview, set_entry, get_entry,
    format_date, parse_date_str,
    center_window, confirm_dialog, info_dialog, error_dialog,
)


# ═══════════════════════════════════════════════════════════════════════
#  AUDITORÍAS
# ═══════════════════════════════════════════════════════════════════════

class AuditoriasFrame(ttk.Frame):
    COLS     = ("num", "establecimiento", "fecha", "alcances", "conformidades", "no_conf")
    HEADINGS = ("Nº", "Establecimiento", "Fecha", "Alcances", "Conformidades", "No Conformidades")
    WIDTHS   = (50, 220, 100, 200, 160, 200)

    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        bar = ttk.Frame(self, padding=(0, 0, 0, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="Auditorías", font=FONT_TITLE).pack(side="left")

        ttk.Label(bar, text="Buscar:").pack(side="left", padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar, textvariable=self.search_var, width=26).pack(side="left")

        ttk.Button(bar, text="＋  Nueva",  command=self._nueva).pack(side="right", padx=4)
        ttk.Button(bar, text="✎  Editar",  command=self._editar).pack(side="right", padx=4)
        ttk.Button(bar, text="✕  Eliminar", style="Danger.TButton",
                   command=self._eliminar).pack(side="right", padx=4)
        ttk.Button(bar, text="🖨  Imprimir Acta", style="Success.TButton",
                   command=self._imprimir_acta).pack(side="left", padx=4)

        self.tree, _ = scrolled_treeview(self, self.COLS, self.HEADINGS, self.WIDTHS, height=22)
        self.tree.bind("<Double-1>", lambda e: self._editar())

    def refresh(self):
        session = get_session()
        q = session.query(Auditoria)
        busq = self.search_var.get().strip()
        if busq:
            q = q.filter(
                Auditoria.codigo_establecimiento.ilike(f"%{busq}%") |
                Auditoria.alcances.ilike(f"%{busq}%")
            )
        rows = q.order_by(Auditoria.fecha_auditoria.desc()).all()

        # Serializar relaciones ANTES de cerrar la sesión
        datos = []
        for a in rows:
            nombre = ""
            if a.establecimiento:
                nombre = (a.establecimiento.nombre_establecimiento or "").title()
            elif a.codigo_establecimiento:
                nombre = a.codigo_establecimiento
            datos.append((
                str(a.codigo_auditoria),
                int(a.numero_auditoria) if a.numero_auditoria else "—",
                nombre,
                format_date(a.fecha_auditoria),
                (a.alcances or "—")[:60],
                (a.conformidades or "—")[:50],
                (a.no_conformidades or "—")[:60],
            ))
        session.close()

        self.tree.delete(*self.tree.get_children())
        for d in datos:
            self.tree.insert("", "end", iid=d[0], values=d[1:])

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná una auditoría primero.")
            return None
        return int(sel[0])

    def _imprimir_acta(self):
        aid = self._selected_id()
        if aid is None:
            return
        from tkinter import filedialog
        from reports.imprimir import imprimir_acta_auditoria
        import os
        session = get_session()
        a = session.query(Auditoria).get(aid)
        if not a:
            session.close()
            return
        # Pre-cargar relaciones
        e = a.establecimiento
        if e:
            _ = e.inscripto
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"acta_auditoria_{int(a.numero_auditoria) if a.numero_auditoria else aid}.pdf",
        )
        if path:
            try:
                imprimir_acta_auditoria(a, path)
                session.close()
                from utils.ui_helpers import info_dialog
                info_dialog(self, "Listo", f"Acta generada:\n{path}")
                try:
                    import subprocess, sys
                    if sys.platform.startswith("win"):
                        os.startfile(path)
                    else:
                        subprocess.Popen(["xdg-open", path])
                except Exception:
                    pass
            except Exception as ex:
                session.close()
                from utils.ui_helpers import error_dialog
                error_dialog(self, "Error", str(ex))
        else:
            session.close()

    def _imprimir_acta(self):
        from tkinter import filedialog
        from reports.documentos_institucionales import doc_acta_auditoria
        from database.db import get_session
        from utils.ui_helpers import error_dialog, info_dialog
        aid = self._selected_id()
        if aid is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"acta_auditoria_{aid}.pdf",
            title="Guardar Acta de Auditoría",
        )
        if not path:
            return
        try:
            session = get_session()
            doc_acta_auditoria(session, path, aid)
            session.close()
            info_dialog(self, "Listo", f"Acta generada:\n{path}")
            import subprocess, sys, os
            if sys.platform.startswith("win"):
                os.startfile(path)
        except Exception as ex:
            error_dialog(self, "Error", str(ex))

    def _nueva(self):
        dlg = AuditoriaDialog(self, None)
        self.wait_window(dlg)
        self.refresh()

    def _editar(self):
        aid = self._selected_id()
        if aid is None:
            return
        dlg = AuditoriaDialog(self, aid)
        self.wait_window(dlg)
        self.refresh()

    def _eliminar(self):
        aid = self._selected_id()
        if aid is None:
            return
        if not confirm_dialog(self, "Eliminar", "¿Eliminar esta auditoría?"):
            return
        session = get_session()
        a = session.query(Auditoria).get(aid)
        if a:
            session.delete(a)
            session.commit()
        session.close()
        self.refresh()


class AuditoriaDialog(tk.Toplevel):
    def __init__(self, parent, auditoria_id=None):
        super().__init__(parent)
        self.auditoria_id = auditoria_id
        self.title("Nueva auditoría" if not auditoria_id else f"Editar auditoría #{auditoria_id}")
        self.resizable(False, False)
        center_window(self, 640, 560)
        self.grab_set()
        self._build()
        if auditoria_id:
            self._load(auditoria_id)

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)

        session = get_session()
        estabs = session.query(Establecimiento).filter_by(baja=False).order_by(
            Establecimiento.nombre_establecimiento).all()
        self._estab_map = {
            f"{e.codigo_establecimiento} — {(e.nombre_establecimiento or '').title()}": e.codigo_establecimiento
            for e in estabs}
        session.close()

        ttk.Label(f, text="Establecimiento").grid(row=0, column=0, sticky="w", pady=5, padx=(0, 8))
        self.e_estab = ttk.Combobox(f, values=[""] + list(self._estab_map.keys()),
                                    width=38, state="readonly")
        self.e_estab.grid(row=0, column=1, columnspan=3, sticky="ew", pady=5)

        ttk.Label(f, text="Nº Auditoría").grid(row=1, column=0, sticky="w", pady=5, padx=(0, 8))
        self.e_num = ttk.Entry(f, width=10)
        self.e_num.grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(f, text="Fecha").grid(row=1, column=2, sticky="w", padx=(12, 8))
        self.e_fecha = ttk.Entry(f, width=14)
        self.e_fecha.grid(row=1, column=3, sticky="w", pady=5)
        ttk.Label(f, text="(dd/mm/aaaa)", font=("Segoe UI", 10)).grid(row=1, column=3, sticky="e")

        for row, lbl, attr in [
            (2, "Alcances",           "e_alcances"),
            (3, "Conformidades",      "e_conf"),
            (4, "No Conformidades",   "e_noconf"),
            (5, "Conclusiones",       "e_conclusiones"),
            (6, "Acta Multifunción",  "e_acta"),
            (7, "Material Adjunto",   "e_material"),
        ]:
            ttk.Label(f, text=lbl).grid(row=row, column=0, sticky="nw", pady=5, padx=(0, 8))
            if lbl in ("No Conformidades", "Conclusiones"):
                widget = tk.Text(f, height=3, width=55, font=FONT_NORMAL,
                                 relief="solid", borderwidth=1)
                widget.grid(row=row, column=1, columnspan=3, sticky="ew", pady=5)
            else:
                widget = ttk.Entry(f, width=55)
                widget.grid(row=row, column=1, columnspan=3, sticky="ew", pady=5)
            setattr(self, attr, widget)

        bar = ttk.Frame(f)
        bar.grid(row=8, column=0, columnspan=4, pady=(12, 0), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton",
                   command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _text_set(self, widget, val):
        if isinstance(widget, tk.Text):
            widget.delete("1.0", "end")
            if val:
                widget.insert("1.0", val)
        else:
            set_entry(widget, val or "")

    def _text_get(self, widget):
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end").strip()
        return get_entry(widget)

    def _load(self, aid):
        session = get_session()
        a = session.query(Auditoria).get(aid)
        if not a:
            session.close()
            return
        # Establecimiento
        for key, cod in self._estab_map.items():
            if cod == a.codigo_establecimiento:
                self.e_estab.set(key)
                break
        set_entry(self.e_num, str(int(a.numero_auditoria)) if a.numero_auditoria else "")
        set_entry(self.e_fecha, format_date(a.fecha_auditoria))
        self._text_set(self.e_alcances,    a.alcances)
        self._text_set(self.e_conf,        a.conformidades)
        self._text_set(self.e_noconf,      a.no_conformidades)
        self._text_set(self.e_conclusiones,a.conclusiones)
        self._text_set(self.e_acta,        a.acta_multinfuncion)
        self._text_set(self.e_material,    a.material_adjunto)
        session.close()

    def _guardar(self):
        session = get_session()
        if self.auditoria_id:
            a = session.query(Auditoria).get(self.auditoria_id)
        else:
            a = Auditoria()
            session.add(a)

        estab_key = self.e_estab.get()
        a.codigo_establecimiento = self._estab_map.get(estab_key)
        num_s = get_entry(self.e_num)
        try:
            a.numero_auditoria = float(num_s) if num_s else None
        except ValueError:
            a.numero_auditoria = None
        a.fecha_auditoria   = parse_date_str(get_entry(self.e_fecha))
        a.alcances          = self._text_get(self.e_alcances)
        a.conformidades     = self._text_get(self.e_conf)
        a.no_conformidades  = self._text_get(self.e_noconf)
        a.conclusiones      = self._text_get(self.e_conclusiones)
        a.acta_multinfuncion= self._text_get(self.e_acta)
        a.material_adjunto  = self._text_get(self.e_material)

        try:
            session.commit()
            info_dialog(self, "Guardado", "Auditoría guardada.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()


# ═══════════════════════════════════════════════════════════════════════
#  SANIDAD
# ═══════════════════════════════════════════════════════════════════════

class SanidadFrame(ttk.Frame):
    COLS     = ("codigo", "establecimiento", "titular", "venc_titular",
                "libreta", "carnet", "curso_bpm")
    HEADINGS = ("Cód. Estab.", "Establecimiento", "Titular", "Venc. Libreta",
                "Libreta", "Carnet Manip.", "Curso BPM")
    WIDTHS   = (90, 200, 200, 110, 70, 90, 80)

    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        bar = ttk.Frame(self, padding=(0, 0, 0, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="Sanidad / Libretas", font=FONT_TITLE).pack(side="left")

        ttk.Label(bar, text="Buscar:").pack(side="left", padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar, textvariable=self.search_var, width=24).pack(side="left")

        ttk.Button(bar, text="＋  Nuevo",  command=self._nuevo).pack(side="right", padx=4)
        ttk.Button(bar, text="✎  Editar",  command=self._editar).pack(side="right", padx=4)

        self.tree, _ = scrolled_treeview(self, self.COLS, self.HEADINGS, self.WIDTHS, height=22)
        self.tree.bind("<Double-1>", lambda e: self._editar())

    def refresh(self):
        session = get_session()
        q = session.query(Sanidad)
        busq = self.search_var.get().strip()
        if busq:
            q = q.filter(
                Sanidad.codigo_establecimiento.ilike(f"%{busq}%") |
                Sanidad.apellido_titular.ilike(f"%{busq}%") |
                Sanidad.nombre_titular.ilike(f"%{busq}%")
            )
        rows = q.order_by(Sanidad.codigo_establecimiento).all()

        # Serializar relaciones ANTES de cerrar la sesión
        datos = []
        for s in rows:
            nombre_estab = ""
            if s.establecimiento:
                nombre_estab = (s.establecimiento.nombre_establecimiento or "").title()
            titular = f"{(s.apellido_titular or '').title()} {(s.nombre_titular or '').title()}".strip()
            datos.append((
                str(s.codigo_sanidad),
                s.codigo_establecimiento,
                nombre_estab,
                titular,
                format_date(s.venc_libreta_titular),
                "✓" if s.libreta_sanitaria else "✗",
                "✓" if s.carnet_manipulador else "✗",
                "✓" if s.inscripto_curso_bpm else "✗",
            ))
        session.close()

        self.tree.delete(*self.tree.get_children())
        for d in datos:
            self.tree.insert("", "end", iid=d[0], values=d[1:])

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccioná un registro primero.")
            return None
        return int(sel[0])

    def _nuevo(self):
        dlg = SanidadDialog(self, None)
        self.wait_window(dlg)
        self.refresh()

    def _editar(self):
        sid = self._selected_id()
        if sid is None:
            return
        dlg = SanidadDialog(self, sid)
        self.wait_window(dlg)
        self.refresh()


class SanidadDialog(tk.Toplevel):
    def __init__(self, parent, sanidad_id=None):
        super().__init__(parent)
        self.sanidad_id = sanidad_id
        self.title("Nueva sanidad" if not sanidad_id else f"Editar sanidad #{sanidad_id}")
        self.resizable(False, False)
        center_window(self, 600, 520)
        self.grab_set()
        self._build()
        if sanidad_id:
            self._load(sanidad_id)

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)

        session = get_session()
        estabs = session.query(Establecimiento).filter_by(baja=False).order_by(
            Establecimiento.nombre_establecimiento).all()
        self._estab_map = {
            f"{e.codigo_establecimiento} — {(e.nombre_establecimiento or '').title()}": e.codigo_establecimiento
            for e in estabs}
        session.close()

        ttk.Label(f, text="Establecimiento *").grid(row=0, column=0, sticky="w", pady=5, padx=(0, 8))
        self.e_estab = ttk.Combobox(f, values=[""] + list(self._estab_map.keys()),
                                    width=40, state="readonly")
        self.e_estab.grid(row=0, column=1, columnspan=3, sticky="ew", pady=5)

        # Titular
        ttk.Label(f, text="Apellido titular").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_ap_tit = ttk.Entry(f, width=22)
        self.e_ap_tit.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(f, text="Nombre titular").grid(row=1, column=2, sticky="w", padx=(12, 8))
        self.e_nom_tit = ttk.Entry(f, width=22)
        self.e_nom_tit.grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(f, text="Venc. libreta titular").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        self.e_venc_tit = ttk.Entry(f, width=14)
        self.e_venc_tit.grid(row=2, column=1, sticky="w", pady=4)

        # Empleados
        for i, (ap_attr, nom_attr, venc_attr) in enumerate([
            ("e_ap_emp1", "e_nom_emp1", "e_venc_emp1"),
            ("e_ap_emp2", "e_nom_emp2", "e_venc_emp2"),
        ], start=1):
            row = 2 + i
            ttk.Label(f, text=f"Apellido empleado {i}").grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
            ap_e = ttk.Entry(f, width=20)
            ap_e.grid(row=row, column=1, sticky="ew", pady=4)
            setattr(self, ap_attr, ap_e)

            ttk.Label(f, text=f"Nombre empleado {i}").grid(row=row, column=2, sticky="w", padx=(12, 8))
            nom_e = ttk.Entry(f, width=20)
            nom_e.grid(row=row, column=3, sticky="ew", pady=4)
            setattr(self, nom_attr, nom_e)

            row2 = row + 2
            ttk.Label(f, text=f"Venc. libreta emp. {i}").grid(row=row2, column=0, sticky="w", pady=4, padx=(0, 8))
            venc_e = ttk.Entry(f, width=14)
            venc_e.grid(row=row2, column=1, sticky="w", pady=4)
            setattr(self, venc_attr, venc_e)

        # Checks
        checks_frame = ttk.LabelFrame(f, text="Habilitaciones", padding=10)
        checks_frame.grid(row=7, column=0, columnspan=4, sticky="ew", pady=10)

        self.v_libreta = tk.BooleanVar()
        self.v_carnet  = tk.BooleanVar()
        self.v_certif  = tk.BooleanVar()
        self.v_bpm     = tk.BooleanVar()

        ttk.Checkbutton(checks_frame, text="Libreta sanitaria",
                        variable=self.v_libreta).grid(row=0, column=0, padx=12)
        ttk.Checkbutton(checks_frame, text="Carnet manipulador",
                        variable=self.v_carnet).grid(row=0, column=1, padx=12)
        ttk.Checkbutton(checks_frame, text="Certificado manipulador",
                        variable=self.v_certif).grid(row=0, column=2, padx=12)
        ttk.Checkbutton(checks_frame, text="Inscripto Curso BPM",
                        variable=self.v_bpm).grid(row=0, column=3, padx=12)

        ttk.Label(checks_frame, text="Fecha certificado manip.:").grid(row=1, column=0, sticky="w", pady=4)
        self.e_fecha_certif = ttk.Entry(checks_frame, width=14)
        self.e_fecha_certif.grid(row=1, column=1, sticky="w")

        bar = ttk.Frame(f)
        bar.grid(row=8, column=0, columnspan=4, pady=(12, 0), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton",
                   command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _load(self, sid):
        session = get_session()
        s = session.query(Sanidad).get(sid)
        if not s:
            session.close()
            return
        for key, cod in self._estab_map.items():
            if cod == s.codigo_establecimiento:
                self.e_estab.set(key)
                break
        set_entry(self.e_ap_tit,  s.apellido_titular or "")
        set_entry(self.e_nom_tit, s.nombre_titular or "")
        set_entry(self.e_venc_tit, format_date(s.venc_libreta_titular))
        set_entry(self.e_ap_emp1,  s.apellido_empleado1 or "")
        set_entry(self.e_nom_emp1, s.nombre_empleado1 or "")
        set_entry(self.e_venc_emp1, format_date(s.venc_libreta_empleado1))
        set_entry(self.e_ap_emp2,  s.apellido_empleado2 or "")
        set_entry(self.e_nom_emp2, s.nombre_empleado2 or "")
        set_entry(self.e_venc_emp2, format_date(s.venc_libreta_empleado2))
        self.v_libreta.set(bool(s.libreta_sanitaria))
        self.v_carnet.set(bool(s.carnet_manipulador))
        self.v_certif.set(bool(s.certificado_manipulador))
        self.v_bpm.set(bool(s.inscripto_curso_bpm))
        set_entry(self.e_fecha_certif, format_date(s.fecha_certificado_manip))
        session.close()

    def _guardar(self):
        estab_key = self.e_estab.get()
        if not estab_key:
            error_dialog(self, "Error", "Seleccioná un establecimiento.")
            return
        session = get_session()
        if self.sanidad_id:
            s = session.query(Sanidad).get(self.sanidad_id)
        else:
            s = Sanidad()
            session.add(s)

        s.codigo_establecimiento = self._estab_map[estab_key]
        s.apellido_titular       = get_entry(self.e_ap_tit)
        s.nombre_titular         = get_entry(self.e_nom_tit)
        s.venc_libreta_titular   = parse_date_str(get_entry(self.e_venc_tit))
        s.apellido_empleado1     = get_entry(self.e_ap_emp1)
        s.nombre_empleado1       = get_entry(self.e_nom_emp1)
        s.venc_libreta_empleado1 = parse_date_str(get_entry(self.e_venc_emp1))
        s.apellido_empleado2     = get_entry(self.e_ap_emp2)
        s.nombre_empleado2       = get_entry(self.e_nom_emp2)
        s.venc_libreta_empleado2 = parse_date_str(get_entry(self.e_venc_emp2))
        s.libreta_sanitaria      = self.v_libreta.get()
        s.carnet_manipulador     = self.v_carnet.get()
        s.certificado_manipulador= self.v_certif.get()
        s.inscripto_curso_bpm    = self.v_bpm.get()
        s.fecha_certificado_manip= parse_date_str(get_entry(self.e_fecha_certif))

        try:
            session.commit()
            info_dialog(self, "Guardado", "Registro de sanidad guardado.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()
