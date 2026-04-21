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
        # PyInstaller guarda los archivos adjuntos aquí adentro:
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

def to_bool(v): 
    return str(v).strip() in ['1', 'true', 'True', 'TRUE'] if v else False

def cargar_datos_iniciales():
    session = get_session()
    
    # Buscamos la carpeta data_export
    ruta_export = os.path.join(get_base_path(), '_internal', 'data_export')
    if not os.path.exists(ruta_export):
        ruta_export = os.path.join(get_base_path(), 'data_export')

    print("Comprobando migración de datos iniciales...")

    # --- 1. RUBROS ---
    if session.query(Rubro).first() is None:
        archivo = os.path.join(ruta_export, 'RUBROS.csv')
        if os.path.exists(archivo):
            print("Migrando Rubros...")
            with open(archivo, newline='', encoding='utf-8', errors='ignore') as f:
                for row in csv.DictReader(f):
                    session.add(Rubro(
                        id_rubro=to_int(row.get('Id_Rubro')),
                        nombre=row.get('RUBRO', ''),
                        valor=to_float(row.get('VALOR'))
                    ))
            try: session.commit()
            except: session.rollback()

    # --- 2. INSCRIPTOS ---
    if session.query(Inscripto).first() is None:
        archivo = os.path.join(ruta_export, 'INSCRIPTOS.csv')
        if os.path.exists(archivo):
            print("Migrando Inscriptos...")
            with open(archivo, newline='', encoding='utf-8', errors='ignore') as f:
                for row in csv.DictReader(f):
                    session.add(Inscripto(
                        codigo_inscripcion=to_int(row.get('Codigo_inscripcion')),
                        apellido_razonsocial=row.get('Apellido_Razonsocial'),
                        nombres=row.get('Nombres'),
                        tipo_documento=row.get('Tipo_Documento'),
                        numero_documento=row.get('Numero_Documento'),
                        tipo_identificacion=row.get('Tipo_Identificación_Personal'),
                        numero_identificacion=row.get('Numero_Identificación'),
                        domicilio=row.get('Domicilio'),
                        numero_domicilio=row.get('Numero_Domicilio'),
                        localidad=row.get('Localidad'),
                        codigo_postal=row.get('Codigo_postal'),
                        provincia=row.get('Provincia'),
                        telefono=row.get('Telefono'),
                        telefono_movil=row.get('Telefono_Movil'),
                        correo=row.get('Correo'),
                        observaciones=row.get('Observa'),
                        monto_sellado=to_float(row.get('Monto_sellado')),
                        fecha_inicio_tramite=parse_csv_date(row.get('Fecha_inicio_tramite'))
                    ))
            try: session.commit()
            except: session.rollback()

    # --- 3. ESTABLECIMIENTOS ---
    if session.query(Establecimiento).first() is None:
        archivo = os.path.join(ruta_export, 'ESTABLECIMIENTOS.csv')
        if os.path.exists(archivo):
            print("Migrando Establecimientos...")
            with open(archivo, newline='', encoding='utf-8', errors='ignore') as f:
                for row in csv.DictReader(f):
                    session.add(Establecimiento(
                        codigo_establecimiento=(row.get('CODIGO_ESTABLECIMIENTO') or '').strip().upper(),
                        codigo_inscripcion=to_int(row.get('CODIGO_INSCRIPCION')),
                        nombre_establecimiento=row.get('Nombre_Establecimiento', ''),
                        domicilio_establecimiento=row.get('Domicilio_Establecimiento', ''),
                        numero_establecimiento=row.get('Numero_Establecimiento', ''),
                        localidad_establecimiento=row.get('Localidad_Establecimiento', ''),
                        codigo_postal=to_int(row.get('Codigo_PostalEstab')),
                        provincia_establecimiento=row.get('Provincia_Establecimiento', ''),
                        telefono_establecimiento=row.get('Telefono_Establecimiento', ''),
                        rubro_id=to_int(row.get('Rubro')),
                        monto=to_float(row.get('Monto')),
                        anexo1_id=to_int(row.get('Anexo1')),
                        monto1=to_float(row.get('Monto1')),
                        anexo2_id=to_int(row.get('Anexo2')),
                        monto2=to_float(row.get('Monto2')),
                        anexo3_id=to_int(row.get('Anexo3')),
                        monto3=to_float(row.get('Monto3')),
                        estado_tramite=row.get('Estado_Tramite', ''),
                        fecha_certificado=parse_csv_date(row.get('Fecha_CertificadoInscripción')),
                        acta_emplazamiento=to_int(row.get('Acta_Emplazamiento_Nº')),
                        acta_infraccion=to_int(row.get('Acta_Infraccion_Nº')),
                        solicitudes=row.get('Solicitudes', ''),
                        observaciones=row.get('Observaciones', ''),
                        acta_multinfuncion=to_int(row.get('Acta_Multinfuncion')),
                        baja=to_bool(row.get('Baja'))
                    ))
            try: session.commit()
            except: session.rollback()

    # --- 4. DEUDAS ---
    if session.query(Deuda).first() is None:
        archivo = os.path.join(ruta_export, 'DEUDAS.csv')
        if os.path.exists(archivo):
            print("Migrando Deudas...")
            with open(archivo, newline='', encoding='utf-8', errors='ignore') as f:
                for row in csv.DictReader(f):
                    session.add(Deuda(
                        codigo_deuda=to_int(row.get('Codigo_deuda')),
                        codigo_establecimiento=(row.get('Codigo_establecimiento') or '').strip().upper(),
                        periodo=to_int(row.get('Periodo')),
                        anio=to_int(row.get('Año')),
                        vencimiento=parse_csv_date(row.get('Vencimiento')),
                        importe=to_float(row.get('Importe')),
                        pago=to_bool(row.get('Pago')),
                        fecha_pago=parse_csv_date(row.get('Fecha_pago')),
                        monto_abonado=to_float(row.get('Monto_abonado'))
                    ))
            try: session.commit()
            except: session.rollback()

    # --- 5. AUDITORIAS ---
    if session.query(Auditoria).first() is None:
        archivo = os.path.join(ruta_export, 'AUDITORIAS.csv')
        if os.path.exists(archivo):
            print("Migrando Auditorías...")
            with open(archivo, newline='', encoding='utf-8', errors='ignore') as f:
                for row in csv.DictReader(f):
                    session.add(Auditoria(
                        codigo_auditoria=to_int(row.get('Codigo_Auditoria')),
                        codigo_establecimiento=(row.get('Código Establecimiento') or '').strip().upper(),
                        numero_auditoria=to_float(row.get('Auditoría Nº')),
                        fecha_auditoria=parse_csv_date(row.get('Fecha Auditoría')),
                        alcances=row.get('Alcances de la Auditoría', ''),
                        conformidades=row.get('Conformidades', ''),
                        acta_multinfuncion=row.get('Acta_Multinfuncion', ''),
                        no_conformidades=row.get('No Conformidades', ''),
                        detalle_anexo=row.get('Detalle Anexo Auditoria', ''),
                        conclusiones=row.get('Conclusiones', ''),
                        material_adjunto=row.get('Material Adjunto', ''),
                        anexo_auditoria_num=row.get('Anexo Auditoria Nº', '')
                    ))
            try: session.commit()
            except: session.rollback()

    # --- 6. SANIDAD ---
    if session.query(Sanidad).first() is None:
        archivo = os.path.join(ruta_export, 'SANIDAD.csv')
        if os.path.exists(archivo):
            print("Migrando Sanidad...")
            with open(archivo, newline='', encoding='utf-8', errors='ignore') as f:
                for row in csv.DictReader(f):
                    session.add(Sanidad(
                        codigo_sanidad=to_int(row.get('CODIGO_SANIDAD')),
                        codigo_establecimiento=(row.get('CODIGO_ESTABLECIMIENTO') or '').strip().upper(),
                        libreta_sanitaria=to_bool(row.get('Libreta_Sanitaria')),
                        apellido_titular=row.get('Apellido_titular'),
                        nombre_titular=row.get('Nombre_titular'),
                        venc_libreta_titular=parse_csv_date(row.get('Venc_LibretaTitular')),
                        apellido_empleado1=row.get('Apellido_Empleado1'),
                        nombre_empleado1=row.get('Nombre_empleado1'),
                        venc_libreta_empleado1=parse_csv_date(row.get('Venc_Libretaempleado1')),
                        apellido_empleado2=row.get('Apellido_Empleado2'),
                        nombre_empleado2=row.get('Nombre_empleado2'),
                        venc_libreta_empleado2=parse_csv_date(row.get('Venc_Libretaempleado2')),
                        carnet_manipulador=to_bool(row.get('Carnet_Manipulador')),
                        certificado_manipulador=to_bool(row.get('Certificado_Manipulador')),
                        fecha_certificado_manip=parse_csv_date(row.get('Fecha_CertificadoManipulador')),
                        inscripto_curso_bpm=to_bool(row.get('Inscripto_CursoBPM'))
                    ))
            try: session.commit()
            except: session.rollback()



    # --- 7. EMISION ---
    if session.query(Emision).first() is None:
        archivo = os.path.join(ruta_export, 'EMISION.csv')
        if os.path.exists(archivo):
            print("Migrando Emisiones...")
            # El secreto está aquí: utf-8-sig ignora los caracteres fantasma de Excel
            with open(archivo, newline='', encoding='utf-8-sig', errors='ignore') as f:
                for row in csv.DictReader(f):
                    # Doble seguro: busca con o sin el caracter oculto
                    id_em = row.get('Id_Emision') or row.get('\ufeffId_Emision') or ''
                    
                    if not id_em.strip():
                        continue # Saltea filas vacías
                        
                    session.add(Emision(
                        id_emision=id_em.strip(),
                        periodo=row.get('Periodo', '').strip(),
                        anio=to_int(row.get('Año')),
                        vencimiento=parse_csv_date(row.get('Vencimiento')),
                        primer_mora=parse_csv_date(row.get('1er_Mora')),
                        segunda_mora=parse_csv_date(row.get('2da_Mora'))
                    ))
            try: 
                session.commit()
            except Exception as e: 
                session.rollback()

    session.close()

# --- CLASE PRINCIPAL ---
class App(tk.Tk):
    NAV_ITEMS = [
        ("🏠",  "Inicio",           "dashboard"),
        ("🏪",  "Establecimientos", "establecimientos"),
        ("👤",  "Inscriptos",       "inscriptos"),
        ("💰",  "Deudas y Pagos",   "deudas"),
        ("🔍",  "Auditorías",       "auditorias"),
        ("🧼",  "Sanidad",          "sanidad"),
        ("📋",  "Rubros / Emisión", "rubros"),
        # ("📄",  "Reportes PDF",     "reportes"),  # temporalmente deshabilitado
    ]

    def __init__(self):
        super().__init__()
        self.title("Sistema Área de Alimentos — Fighiera")
        self.configure(bg=COLORS["bg_sidebar"])
        center_window(self, 1280, 820)
        self.minsize(1000, 680)

        configure_treeview_style()
        init_db()

        self._frames = {}
        self._build_layout()
        self._navigate("dashboard")

    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=COLORS["bg_sidebar"], width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="🌽", font=("Segoe UI", 32),
                 bg=COLORS["bg_sidebar"], fg="white").pack(pady=(24, 4))
        tk.Label(self.sidebar, text="Área de\nAlimentos",
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["bg_sidebar"], fg="white",
                 justify="center").pack(pady=(0, 2))
        tk.Label(self.sidebar, text="Fighiera",
                 font=("Segoe UI", 9),
                 bg=COLORS["bg_sidebar"], fg="#90cdf4").pack(pady=(0, 16))
        ttk.Separator(self.sidebar).pack(fill="x", padx=12, pady=4)

        self._nav_buttons = {}
        for icon, label, key in self.NAV_ITEMS:
            btn = tk.Button(
                self.sidebar,
                text=f"  {icon}  {label}",
                font=FONT_NORMAL,
                anchor="w", bd=0, relief="flat",
                padx=16, pady=11,
                bg=COLORS["bg_sidebar"], fg="white",
                activebackground=COLORS["accent"],
                activeforeground="white",
                cursor="hand2",
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x")
            self._nav_buttons[key] = btn

        # Contenedor apilable — todos los frames van en la misma celda grid
        self.content = tk.Frame(self, bg=COLORS["bg_app"])
        self.content.pack(side="left", fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _navigate(self, key: str):
        # Actualizar botones sidebar
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(bg=COLORS["accent"],
                              font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=COLORS["bg_sidebar"],
                              font=FONT_NORMAL)

        # Crear frame la primera vez
        if key not in self._frames:
            frame = self._create_frame(key)
            # Todos se colocan en fila=0, col=0; tkraise los apila
            frame.grid(row=0, column=0, sticky="nsew",
                       padx=20, pady=20)
            self._frames[key] = frame

        # Traer al frente — confiable en Windows/Linux/Mac
        self._frames[key].tkraise()

        # Refrescar datos si el módulo lo soporta
        if hasattr(self._frames[key], "refresh"):
            self._frames[key].refresh()

    def _create_frame(self, key: str):
        parent = self.content

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
        init_db() # Nos aseguramos de que las tablas estén creadas
        cargar_datos_iniciales() # Migramos los datos en silencio si hace falta
        
        app = App()
        app.mainloop()
    except Exception as exc:
        import traceback
        messagebox.showerror("Error fatal", traceback.format_exc())
        raise