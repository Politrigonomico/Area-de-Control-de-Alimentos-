"""
Módulo de Rubros y Emisión — tablas de configuración del sistema.
Incluye actualización masiva por porcentaje y Generación Masiva de Deudas.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from database.db import get_session
from database.models import Rubro, Anexo1, Anexo2, Anexo3, Emision, Establecimiento, Deuda
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

        fem = ttk.Frame(nb, padding=8)
        nb.add(fem, text="  Períodos de Emisión y Facturación  ")
        self._build_emision(fem)

    def _build_tab(self, parent, model, attr_prefix):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Button(bar, text="＋  Nuevo",
                   command=lambda: self._nuevo(model, attr_prefix)).pack(side="left", padx=2)
        ttk.Button(bar, text="✎  Editar",
                   command=lambda: self._editar(model, attr_prefix)).pack(side="left", padx=2)
        ttk.Button(bar, text="✕  Eliminar", style="Danger.TButton",
                   command=lambda: self._eliminar(model, attr_prefix)).pack(side="left", padx=2)
        ttk.Button(bar, text="📈  Actualizar por %",
                   command=lambda: self._actualizar_por_porcentaje(model, attr_prefix)).pack(
                       side="left", padx=(16, 2))

        cols = ("id", "nombre", "valor")
        heads = ("ID", "Nombre del rubro", "Valor $")
        widths = (60, 360, 120)
        tree, _ = scrolled_treeview(parent, cols, heads, widths, height=17)
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

    # ── Actualización masiva por porcentaje ──────────────────────────────────

    def _actualizar_por_porcentaje(self, model, attr_prefix):
        dlg = tk.Toplevel(self)
        dlg.title("Actualizar valores por porcentaje")
        dlg.resizable(False, False)
        center_window(dlg, 600, 470)
        dlg.grab_set()

        f = ttk.Frame(dlg, padding=20)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Actualización masiva de valores",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 4))

        ttk.Label(f, text=(
            "Ingresá el porcentaje de actualización.\n"
            "Ejemplos:  30  aumenta 30%  |  -10  reduce 10%"
        ), foreground=COLORS["text_light"]).pack(anchor="w", pady=(0, 12))

        pct_frame = ttk.Frame(f)
        pct_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(pct_frame, text="Porcentaje (%):").pack(side="left", padx=(0, 8))
        e_pct = ttk.Entry(pct_frame, width=12)
        e_pct.pack(side="left")
        e_pct.insert(0, "30")
        ttk.Label(pct_frame, text="(puede ser negativo para reducir)",
                  foreground=COLORS["text_light"]).pack(side="left", padx=(8, 0))

        session = get_session()
        total = session.query(model).count()
        session.close()
        ttk.Label(f, text=f"Se actualizarán {total} registros.",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))

        aviso = ttk.LabelFrame(f, text="⚠  Importante — Tasas históricas", padding=10)
        aviso.pack(fill="x", pady=(0, 12))
        ttk.Label(aviso, text=(
            "Esta actualización cambia los valores de REFERENCIA para nuevos\n"
            "establecimientos. Los establecimientos existentes CONSERVAN sus\n"
            "montos originales (tasas históricas).\n\n"
            "Para actualizar un establecimiento específico: editarlo y\n"
            "re-seleccionar el rubro en la pestaña 'Rubros y montos'."
        ), foreground=COLORS["text_light"]).pack(anchor="w")

        btn_frame = ttk.Frame(f)
        btn_frame.pack(fill="x", pady=(8, 0))

        def _previsualizar():
            pct_str = get_entry(e_pct).strip().replace(",", ".")
            try:
                pct = float(pct_str)
            except ValueError:
                error_dialog(dlg, "Error", "Ingresá un número válido (ej: 30 o -10).")
                return
            _mostrar_preview(pct)

        def _aplicar():
            pct_str = get_entry(e_pct).strip().replace(",", ".")
            try:
                pct = float(pct_str)
            except ValueError:
                error_dialog(dlg, "Error", "Ingresá un número válido (ej: 30 o -10).")
                return

            signo = "+" if pct >= 0 else ""
            if not confirm_dialog(dlg, "Confirmar actualización",
                                  f"¿Aplicar un {signo}{pct}% a los {total} registros?\n\n"
                                  "Esta acción no se puede deshacer automáticamente."):
                return

            session = get_session()
            try:
                factor = 1 + pct / 100
                actualizados = 0
                for r in session.query(model).all():
                    if r.valor and r.valor > 0:
                        r.valor = round(r.valor * factor, 2)
                        actualizados += 1
                if model == Rubro:
                    for anexo_model in [Anexo1, Anexo2, Anexo3]:
                        for r in session.query(anexo_model).all():
                            if r.valor and r.valor > 0:
                                r.valor = round(r.valor * factor, 2)
                session.commit()
                info_dialog(dlg, "Listo",
                            f"✓ {actualizados} valores actualizados con {signo}{pct}%.\n"
                            f"Los Anexos 1, 2 y 3 también fueron actualizados." if model == Rubro
                            else f"✓ {actualizados} valores actualizados con {signo}{pct}%.")
                dlg.destroy()
                self._refresh_tab(model, attr_prefix)
                if model == Rubro:
                    for ap in ["_anx1", "_anx2", "_anx3"]:
                        self._refresh_tab(
                            [Anexo1, Anexo2, Anexo3][["_anx1","_anx2","_anx3"].index(ap)], ap)
            except Exception as ex:
                session.rollback()
                error_dialog(dlg, "Error", str(ex))
            finally:
                session.close()

        def _mostrar_preview(pct):
            prev = tk.Toplevel(dlg)
            prev.title("Previsualización de cambios")
            prev.resizable(True, True)
            center_window(prev, 520, 450)

            ttk.Label(prev, text=f"Previsualización — {'+' if pct >= 0 else ''}{pct}%",
                      font=("Segoe UI", 11, "bold"), padding=8).pack(anchor="w")

            cols_p = ("nombre", "valor_actual", "valor_nuevo")
            tree_p = ttk.Treeview(prev, columns=cols_p, show="headings", height=15)
            tree_p.heading("nombre",       text="Rubro")
            tree_p.heading("valor_actual", text="Valor actual")
            tree_p.heading("valor_nuevo",  text="Valor nuevo")
            tree_p.column("nombre",       width=240)
            tree_p.column("valor_actual", width=120, anchor="e")
            tree_p.column("valor_nuevo",  width=120, anchor="e")

            vsb = ttk.Scrollbar(prev, orient="vertical", command=tree_p.yview)
            tree_p.configure(yscrollcommand=vsb.set)
            tree_p.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
            vsb.pack(side="left", fill="y", pady=8, padx=(0, 8))

            factor = 1 + pct / 100
            session = get_session()
            registros = session.query(model).order_by(model.nombre).all()
            session.close()
            for r in registros:
                nuevo = round((r.valor or 0) * factor, 2)
                tree_p.insert("", "end", values=(
                    r.nombre or "",
                    f"$ {r.valor:,.2f}" if r.valor else "$ 0,00",
                    f"$ {nuevo:,.2f}",
                ))

        ttk.Button(btn_frame, text="🔍  Previsualizar", command=_previsualizar).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=dlg.destroy).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="✓  Aplicar", style="Success.TButton", command=_aplicar).pack(side="right", padx=4)

    # ── Emisión y Generación Masiva ───────────────────────────────────────────

    def _build_emision(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 6))
        
        left_btns = ttk.Frame(bar)
        left_btns.pack(side="left")
        ttk.Button(left_btns, text="＋  Nuevo período", command=self._nueva_emision).pack(side="left", padx=2)
        ttk.Button(left_btns, text="✎  Editar", command=self._editar_emision).pack(side="left", padx=2)
        ttk.Button(left_btns, text="✕  Eliminar", style="Danger.TButton", command=self._eliminar_emision).pack(side="left", padx=2)

        right_btns = ttk.Frame(bar)
        right_btns.pack(side="right")
        # MEJORA: Botón de Generación Masiva
        ttk.Button(right_btns, text="⚡ Generar Deudas Masivas", command=self._generar_deudas_masivas).pack(side="left", padx=2)

        cols   = ("id", "periodo", "anio", "vencimiento", "primera_mora", "segunda_mora")
        heads  = ("ID Período", "Período", "Año", "Vencimiento", "1ª Mora", "2ª Mora")
        widths = (100, 70, 70, 120, 120, 120)
        self.tree_emision, _ = scrolled_treeview(parent, cols, heads, widths, height=17)
        self.tree_emision.bind("<Double-1>", lambda e: self._editar_emision())
        self._refresh_emision()

    def _refresh_emision(self):
        self.tree_emision.delete(*self.tree_emision.get_children())
        session = get_session()
        rows = session.query(Emision).order_by(Emision.anio.desc(), Emision.periodo.desc()).all()
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
        if not confirm_dialog(self, "Eliminar", f"¿Eliminar el período {eid}?\n\n(Las deudas ya generadas para este período no se borrarán)."):
            return
        session = get_session()
        e = session.query(Emision).get(eid)
        if e:
            session.delete(e)
            session.commit()
        session.close()
        self._refresh_emision()

    def _generar_deudas_masivas(self):
        """Genera boletas para todos los comercios activos usando sus tasas históricas."""
        eid = self._selected_emision_id()
        if not eid:
            return
            
        session = get_session()
        emision = session.query(Emision).get(eid)
        if not emision:
            session.close()
            return

        msg = (f"¿Generar deudas masivas para el período {emision.periodo} del año {emision.anio}?\n\n"
               "• Se recorrerán todos los establecimientos ACTIVOS.\n"
               "• Se utilizarán los valores (Tasas) guardados en cada local.\n"
               "• Los locales que ya tengan deuda para este período serán IGNORADOS para evitar duplicados.")
               
        if not confirm_dialog(self, "Generar Deudas Masivas", msg):
            session.close()
            return

        try:
            activos = session.query(Establecimiento).filter_by(baja=False).all()
            creadas = 0
            omitidas = 0

            for estab in activos:
                # Evitar duplicados
                existe = session.query(Deuda).filter_by(
                    codigo_establecimiento=estab.codigo_establecimiento,
                    anio=emision.anio,
                    periodo=emision.periodo
                ).first()

                if existe:
                    omitidas += 1
                    continue

                # Calculamos el importe leyendo la tasa histórica de ese local
                importe_total = (estab.monto or 0.0) + (estab.monto1 or 0.0) + (estab.monto2 or 0.0) + (estab.monto3 or 0.0)

                nueva_deuda = Deuda(
                    codigo_establecimiento=estab.codigo_establecimiento,
                    anio=emision.anio,
                    periodo=emision.periodo,
                    vencimiento=emision.vencimiento,
                    importe=importe_total,
                    pago=False,
                    monto_abonado=0.0
                )
                session.add(nueva_deuda)
                creadas += 1

            session.commit()
            info_dialog(self, "Generación Completada",
                        f"Proceso finalizado correctamente.\n\n"
                        f"✅ Boletas generadas: {creadas}\n"
                        f"⏭ Locales omitidos (ya tenían deuda): {omitidas}")
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error al generar deudas masivas", str(ex))
        finally:
            session.close()


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
        center_window(self, 400, 320)
        self.grab_set()
        self._build()
        if emision_id:
            self._load(emision_id)

    def _build(self):
        f = ttk.Frame(self, padding=20)
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        # MEJORA: Selectores seguros para evitar que el usuario tipee el ID a mano.
        ttk.Label(f, text="Período (1 ó 2) *").grid(row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        self.e_periodo = ttk.Combobox(f, values=["1", "2"], width=14, state="readonly" if self.emision_id else "normal")
        self.e_periodo.grid(row=0, column=1, sticky="w", pady=5)
        
        ttk.Label(f, text="Año (ej: 2026) *").grid(row=1, column=0, sticky="w", pady=5, padx=(0, 10))
        self.e_anio = ttk.Entry(f, width=16)
        self.e_anio.grid(row=1, column=1, sticky="w", pady=5)
        if self.emision_id:
            self.e_anio.configure(state="disabled")

        fields = [
            ("Vencimiento",       "e_venc",     2),
            ("1ª Mora",           "e_mora1",    3),
            ("2ª Mora",           "e_mora2",    4),
        ]
        for label, attr, row in fields:
            ttk.Label(f, text=label).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 10))
            e = ttk.Entry(f, width=16)
            e.grid(row=row, column=1, sticky="w", pady=5)
            setattr(self, attr, e)
            
        ttk.Label(f, text="(dd/mm/aaaa)", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="e")

        bar = ttk.Frame(f)
        bar.grid(row=6, column=0, columnspan=2, pady=(16, 0), sticky="e")
        ttk.Button(bar, text="Guardar", style="Success.TButton",
                   command=self._guardar).pack(side="right", padx=4)
        ttk.Button(bar, text="Cancelar", command=self.destroy).pack(side="right")

    def _load(self, eid):
        session = get_session()
        e = session.query(Emision).get(eid)
        if e:
            self.e_periodo.set(str(e.periodo or ""))
            set_entry(self.e_anio, str(e.anio or ""))
            set_entry(self.e_venc,    format_date(e.vencimiento))
            set_entry(self.e_mora1,   format_date(e.primer_mora))
            set_entry(self.e_mora2,   format_date(e.segunda_mora))
        session.close()

    def _guardar(self):
        periodo = self.e_periodo.get()
        anio_s  = get_entry(self.e_anio)
        
        if not periodo or not anio_s or not anio_s.isdigit():
            error_dialog(self, "Error", "El período y el año (numérico) son obligatorios.")
            return
            
        # Armado seguro del ID
        eid = f"{periodo}-{anio_s}"

        # MEJORA: Validación de fechas
        v_venc = get_entry(self.e_venc)
        v_mora1 = get_entry(self.e_mora1)
        v_mora2 = get_entry(self.e_mora2)

        f_venc = parse_date_str(v_venc) if v_venc else None
        f_mora1 = parse_date_str(v_mora1) if v_mora1 else None
        f_mora2 = parse_date_str(v_mora2) if v_mora2 else None

        if v_venc and not f_venc:
            error_dialog(self, "Error", "La fecha de Vencimiento no es válida (dd/mm/aaaa).")
            return
        if v_mora1 and not f_mora1:
            error_dialog(self, "Error", "La fecha de la 1ª Mora no es válida (dd/mm/aaaa).")
            return
        if v_mora2 and not f_mora2:
            error_dialog(self, "Error", "La fecha de la 2ª Mora no es válida (dd/mm/aaaa).")
            return

        session = get_session()
        if self.emision_id:
            em = session.query(Emision).get(self.emision_id)
        else:
            if session.query(Emision).get(eid):
                error_dialog(self, "Error", f"El Período '{eid}' ya existe en el sistema.")
                session.close()
                return
            em = Emision(id_emision=eid)
            session.add(em)
            
        em.periodo      = int(periodo)
        em.anio         = int(anio_s)
        em.vencimiento  = f_venc
        em.primer_mora  = f_mora1
        em.segunda_mora = f_mora2
        
        try:
            session.commit()
            info_dialog(self, "Guardado", "Período guardado correctamente.")
            self.destroy()
        except Exception as ex:
            session.rollback()
            error_dialog(self, "Error", str(ex))
        finally:
            session.close()