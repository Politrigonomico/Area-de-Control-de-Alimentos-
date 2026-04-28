"""
Sistema de Gestión — Área de Alimentos — Municipalidad de Fighiera
Punto de entrada principal.
"""
import sys
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, get_session
from database.models import Establecimiento, Rubro, Inscripto, Deuda, Auditoria, Sanidad, Emision
from utils.ui_helpers import (
    COLORS, FONT_NORMAL,
    center_window, configure_treeview_style,
)


# --- FUNCIONES AUXILIARES PARA IMPORTACIÓN ---
def get_base_path():
    """Obtiene la ruta correcta tanto si estás programando como si es el .exe compilado"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(__file__))

def parse_csv_date(val):
    if not val or val.strip() == "": return None
    try:
        fecha_str = val.split(" ")[0]
        return datetime.strptime(fecha_str, "%m/%d/%y")
    except:
        return None

def to_int(v): 
    return int(float(v)) if v and str(v).strip() else None

def to_float(v): 
    return float(str(v).replace(',', '.')) if v and str(v).strip() else 0.0

def cargar_datos_iniciales():
    """Carga datos desde CSVs si las tablas están vacías (Migración silenciosa)"""
    session = get_session()
    
    # Si ya hay establecimientos, asumimos que ya se migró
    if session.query(Establecimiento).count() > 0:
        session.close()
        return

    print("Comprobando migración de datos iniciales...")
    base = os.path.join(get_base_path(), "data_export")
    
    try:
        # 1. Rubros
        with open(os.path.join(base, "RUBROS.csv"), encoding='utf-8') as f:
            for r in csv.DictReader(f):
                session.add(Rubro(id_rubro=to_int(r['ID']), nombre=r['Nombre'], valor=to_float(r['Valor'])))
        
        # 2. Inscriptos
        with open(os.path.join(base, "INSCRIPTOS.csv"), encoding='utf-8') as f:
            for r in csv.DictReader(f):
                session.add(Inscripto(
                    codigo_inscripcion=to_int(r['Codigo']),
                    apellido_razonsocial=r['Apellido'],
                    nombres=r['Nombres'],
                    numero_documento=r['DNI'],
                    numero_identificacion=r['CUIT'],
                    domicilio=r['Domicilio'],
                    localidad=r['Localidad'],
                    telefono_movil=r['Telefono']
                ))
        
        # 3. Establecimientos
        with open(os.path.join(base, "ESTABLECIMIENTOS.csv"), encoding='utf-8') as f:
            for r in csv.DictReader(f):
                session.add(Establecimiento(
                    codigo_establecimiento=r['Codigo'],
                    nombre_establecimiento=r['Nombre'],
                    codigo_inscripcion=to_int(r['CodInscrip']),
                    domicilio_establecimiento=r['Domicilio'],
                    rubro_id=to_int(r['Rubro']),
                    monto=to_float(r['Monto']),
                    estado_tramite=r['Estado'],
                    baja=(r['Baja'] == 'True')
                ))

        session.commit()
        print("Migración completada con éxito.")
    except Exception as e:
        print(f"Error en migración: {e}")
        session.rollback()
    finally:
        session.close()


# --- APLICACIÓN PRINCIPAL ---

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Área de Alimentos — Comuna de Fighiera v2.0")
        center_window(self, 1200, 720)
        self.configure(bg=COLORS["bg_app"])
        
        configure_treeview_style()

        # Layout Principal
        self.sidebar = tk.Frame(self, bg=COLORS["bg_sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.container = tk.Frame(self, bg=COLORS["bg_app"])
        self.container.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.frames = {}
        self._build_sidebar()
        self._navigate("dashboard")

    def _build_sidebar(self):
        tk.Label(self.sidebar, text="MENÚ", font=("Segoe UI", 12, "bold"),
                 bg=COLORS["bg_sidebar"], fg="white", pady=20).pack()

        # Lista de botones de navegación
        buttons = [
            ("📊  Dashboard", "dashboard"),
            ("🏪  Establecimientos", "establecimientos"),
            ("👤  Inscriptos", "inscriptos"),
            ("💰  Deudas", "deudas"),
            ("🔍  Auditorías", "auditorias"),
            ("⚕  Sanidad", "sanidad"),
            ("🏷  Rubros y Emisión", "rubros"),
            ("📋  Reportes", "reportes"),  # REINTEGRADO
        ]

        self.nav_buttons = {}
        for text, key in buttons:
            btn = tk.Button(self.sidebar, text=text, font=FONT_NORMAL,
                            bg=COLORS["bg_sidebar"], fg="white",
                            relief="flat", anchor="w", padx=20, pady=10,
                            activebackground="#2d3748", activeforeground="white",
                            cursor="hand2",
                            command=lambda k=key: self._navigate(k))
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

    def _navigate(self, key):
        # Desmarcar botones
        for k, b in self.nav_buttons.items():
            b.configure(bg=COLORS["bg_sidebar"], fg="white")
        
        # Marcar activo
        self.nav_buttons[key].configure(bg="#2d3748", fg="#90cdf4")

        # Cambiar frame
        for f in self.container.winfo_children():
            f.pack_forget()

        if key not in self.frames:
            self.frames[key] = self._create_frame(key)
        
        self.frames[key].pack(fill="both", expand=True)
        if hasattr(self.frames[key], "refresh"):
            self.frames[key].refresh()

    def _create_frame(self, key):
        parent = self.container
        if key == "dashboard":
            from ui.dashboard import DashboardFrame
            return DashboardFrame(parent)
        elif key == "establecimientos":
            from ui.establecimientos import EstablecimientosFrame
            return EstablecimientosFrame(parent)
        elif key == "inscriptos":
            from ui.inscriptos import InscriptosFrame
            return InscriptosFrame(parent)
        elif key == "deudas":
            from ui.deudas import DeudasFrame
            return DeudasFrame(parent)
        elif key == "auditorias":
            from ui.sanidad_auditorias import AuditoriasFrame
            return AuditoriasFrame(parent)
        elif key == "sanidad":
            from ui.sanidad_auditorias import SanidadFrame
            return SanidadFrame(parent)
        elif key == "rubros":
            from ui.rubros_emision import RubrosFrame
            return RubrosFrame(parent)
        elif key == "reportes":
            from ui.reportes import ReportesFrame
            return ReportesFrame(parent)
        else:
            f = ttk.Frame(parent)
            ttk.Label(f, text=f"Módulo '{key}' no implementado.").pack(pady=40)
            return f


if __name__ == "__main__":
    try:
        init_db() 
        cargar_datos_iniciales() 
        
        app = App()
        app.mainloop()
    except Exception as exc:
        import traceback
        messagebox.showerror("Error fatal", traceback.format_exc())
        raise