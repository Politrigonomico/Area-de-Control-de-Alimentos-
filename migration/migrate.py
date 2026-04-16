"""
Migración de datos desde archivos CSV exportados del .mdb original
a la base de datos SQLite nueva.

Uso:
    python -m migration.migrate --csv-dir /ruta/a/csvs
"""
import os
import csv
import sys
import argparse
from datetime import datetime

# Permite ejecutar el módulo directamente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_session, DB_PATH
from database.models import (
    Rubro, Anexo1, Anexo2, Anexo3,
    Inscripto, Establecimiento,
    Emision, Deuda, Auditoria, Sanidad,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def parse_date(value: str):
    """Convierte varios formatos de fecha a datetime, o None."""
    if not value or value.strip() == "":
        return None
    for fmt in ("%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_bool(value: str) -> bool:
    return str(value).strip() in ("1", "True", "true", "yes", "Yes", "-1")


def parse_float(value: str) -> float:
    try:
        return float(str(value).strip().replace(",", ".")) if value else 0.0
    except ValueError:
        return 0.0


def parse_int(value: str):
    try:
        v = str(value).strip()
        return int(float(v)) if v else None
    except (ValueError, TypeError):
        return None


def read_csv(path: str):
    """Lee un CSV y devuelve lista de dicts."""
    if not os.path.exists(path):
        print(f"  [ADVERTENCIA] No se encontró: {path}")
        return []
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Migradores por tabla
# --------------------------------------------------------------------------- #

def migrate_rubros(session, csv_dir):
    rows = read_csv(os.path.join(csv_dir, "RUBROS.csv"))
    count = 0
    for r in rows:
        obj = Rubro(
            id_rubro=parse_int(r.get("Id_Rubro")),
            nombre=r.get("RUBRO", "").strip(),
            valor=parse_float(r.get("VALOR")),
        )
        session.merge(obj)
        count += 1
    print(f"  RUBROS: {count} registros")


def migrate_anexo(session, csv_dir, n: int):
    model_map = {1: Anexo1, 2: Anexo2, 3: Anexo3}
    Model = model_map[n]
    rows = read_csv(os.path.join(csv_dir, f"ANEXO{n}.csv"))
    count = 0
    for r in rows:
        obj = Model(
            id_rubro=parse_int(r.get("Id_Rubro")),
            nombre=r.get("RUBRO", "").strip(),
            valor=parse_float(r.get("VALOR")),
        )
        session.merge(obj)
        count += 1
    print(f"  ANEXO{n}: {count} registros")


def migrate_inscriptos(session, csv_dir):
    rows = read_csv(os.path.join(csv_dir, "INSCRIPTOS.csv"))
    count = 0
    for r in rows:
        obj = Inscripto(
            codigo_inscripcion=parse_int(r.get("Codigo_inscripcion")),
            apellido_razonsocial=r.get("Apellido_Razonsocial", "").strip(),
            nombres=r.get("Nombres", "").strip(),
            tipo_documento=r.get("Tipo_Documento", "").strip(),
            numero_documento=r.get("Numero_Documento", "").strip(),
            tipo_identificacion=r.get("Tipo_Identificación_Personal", "").strip(),
            numero_identificacion=r.get("Numero_Identificación", "").strip(),
            domicilio=r.get("Domicilio", "").strip(),
            numero_domicilio=r.get("Numero_Domicilio", "").strip(),
            localidad=r.get("Localidad", "").strip(),
            codigo_postal=r.get("Codigo_postal", "").strip(),
            provincia=r.get("Provincia", "").strip(),
            telefono=r.get("Telefono", "").strip(),
            telefono_movil=r.get("Telefono_Movil", "").strip(),
            correo=r.get("Correo", "").strip(),
            observaciones=r.get("Observa", "").strip(),
            monto_sellado=parse_float(r.get("Monto_sellado")),
            fecha_inicio_tramite=parse_date(r.get("Fecha_inicio_tramite")),
        )
        session.merge(obj)
        count += 1
    print(f"  INSCRIPTOS: {count} registros")


def migrate_establecimientos(session, csv_dir):
    rows = read_csv(os.path.join(csv_dir, "ESTABLECIMIENTOS.csv"))
    count = 0
    for r in rows:
        codigo = r.get("CODIGO_ESTABLECIMIENTO", "").strip().upper()
        if not codigo:
            continue
        obj = Establecimiento(
            codigo_establecimiento=codigo,
            codigo_inscripcion=parse_int(r.get("CODIGO_INSCRIPCION")),
            nombre_establecimiento=r.get("Nombre_Establecimiento", "").strip(),
            domicilio_establecimiento=r.get("Domicilio_Establecimiento", "").strip(),
            numero_establecimiento=r.get("Numero_Establecimiento", "").strip(),
            localidad_establecimiento=r.get("Localidad_Establecimiento", "").strip(),
            codigo_postal=parse_int(r.get("Codigo_PostalEstab")),
            provincia_establecimiento=r.get("Provincia_Establecimiento", "").strip(),
            telefono_establecimiento=r.get("Telefono_Establecimiento", "").strip(),
            rubro_id=parse_int(r.get("Rubro")),
            monto=parse_float(r.get("Monto")),
            anexo1_id=parse_int(r.get("Anexo1")),
            monto1=parse_float(r.get("Monto1")),
            anexo2_id=parse_int(r.get("Anexo2")),
            monto2=parse_float(r.get("Monto2")),
            anexo3_id=parse_int(r.get("Anexo3")),
            monto3=parse_float(r.get("Monto3")),
            estado_tramite=r.get("Estado_Tramite", "").strip(),
            fecha_certificado=parse_date(r.get("Fecha_CertificadoInscripción")),
            acta_emplazamiento=parse_int(r.get("Acta_Emplazamiento_Nº")),
            acta_infraccion=parse_int(r.get("Acta_Infraccion_Nº")),
            solicitudes=r.get("Solicitudes", "").strip(),
            observaciones=r.get("Observaciones", "").strip(),
            acta_multinfuncion=parse_int(r.get("Acta_Multinfuncion")),
            planilla_descargo=parse_date(r.get("Planilla_Descargo")),
            baja=parse_bool(r.get("Baja")),
        )
        session.merge(obj)
        count += 1
    print(f"  ESTABLECIMIENTOS: {count} registros")


def migrate_emision(session, csv_dir):
    rows = read_csv(os.path.join(csv_dir, "EMISION.csv"))
    count = 0
    for r in rows:
        obj = Emision(
            id_emision=r.get("Id_Emision", "").strip(),
            periodo=r.get("Periodo", "").strip(),
            anio=parse_int(r.get("Año")),
            vencimiento=parse_date(r.get("Vencimiento")),
            primer_mora=parse_date(r.get("1er_Mora")),
            segunda_mora=parse_date(r.get("2da_Mora")),
        )
        session.merge(obj)
        count += 1
    print(f"  EMISION: {count} registros")


def migrate_deudas(session, csv_dir):
    rows = read_csv(os.path.join(csv_dir, "DEUDAS.csv"))
    count = 0
    for r in rows:
        obj = Deuda(
            codigo_deuda=parse_int(r.get("Codigo_deuda")),
            codigo_establecimiento=r.get("Codigo_establecimiento", "").strip().upper(),
            periodo=parse_int(r.get("Periodo")),
            anio=parse_int(r.get("Año")),
            vencimiento=parse_date(r.get("Vencimiento")),
            importe=parse_float(r.get("Importe")),
            pago=parse_bool(r.get("Pago")),
            fecha_pago=parse_date(r.get("Fecha_pago")),
            monto_abonado=parse_float(r.get("Monto_abonado")),
        )
        session.merge(obj)
        count += 1
    print(f"  DEUDAS: {count} registros")


def migrate_auditorias(session, csv_dir):
    rows = read_csv(os.path.join(csv_dir, "AUDITORIAS.csv"))
    count = 0
    for r in rows:
        # Normalizar código de establecimiento
        cod = r.get("Código Establecimiento", "").strip().upper()
        obj = Auditoria(
            codigo_auditoria=parse_int(r.get("Codigo_Auditoria")),
            codigo_establecimiento=cod if cod else None,
            numero_auditoria=parse_float(r.get("Auditoría Nº")),
            fecha_auditoria=parse_date(r.get("Fecha Auditoría")),
            alcances=r.get("Alcances de la Auditoría", "").strip(),
            conformidades=r.get("Conformidades", "").strip(),
            acta_multinfuncion=r.get("Acta_Multinfuncion", "").strip(),
            no_conformidades=r.get("No Conformidades", "").strip(),
            detalle_anexo=r.get("Detalle Anexo Auditoria", "").strip(),
            conclusiones=r.get("Conclusiones", "").strip(),
            material_adjunto=r.get("Material Adjunto", "").strip(),
            anexo_auditoria_num=r.get("Anexo Auditoria Nº", "").strip(),
        )
        session.merge(obj)
        count += 1
    print(f"  AUDITORIAS: {count} registros")


def migrate_sanidad(session, csv_dir):
    rows = read_csv(os.path.join(csv_dir, "SANIDAD.csv"))
    count = 0
    for r in rows:
        obj = Sanidad(
            codigo_sanidad=parse_int(r.get("CODIGO_SANIDAD")),
            codigo_establecimiento=r.get("CODIGO_ESTABLECIMIENTO", "").strip().upper(),
            libreta_sanitaria=parse_bool(r.get("Libreta_Sanitaria")),
            apellido_titular=r.get("Apellido_titular", "").strip(),
            nombre_titular=r.get("Nombre_titular", "").strip(),
            venc_libreta_titular=parse_date(r.get("Venc_LibretaTitular")),
            apellido_empleado1=r.get("Apellido_Empleado1", "").strip(),
            nombre_empleado1=r.get("Nombre_empleado1", "").strip(),
            venc_libreta_empleado1=parse_date(r.get("Venc_Libretaempleado1")),
            apellido_empleado2=r.get("Apellido_Empleado2", "").strip(),
            nombre_empleado2=r.get("Nombre_empleado2", "").strip(),
            venc_libreta_empleado2=parse_date(r.get("Venc_Libretaempleado2")),
            carnet_manipulador=parse_bool(r.get("Carnet_Manipulador")),
            certificado_manipulador=parse_bool(r.get("Certificado_Manipulador")),
            fecha_certificado_manip=parse_date(r.get("Fecha_CertificadoManipulador")),
            inscripto_curso_bpm=parse_bool(r.get("Inscripto_CursoBPM")),
        )
        session.merge(obj)
        count += 1
    print(f"  SANIDAD: {count} registros")


# --------------------------------------------------------------------------- #
# Función principal
# --------------------------------------------------------------------------- #

def run_migration(csv_dir: str):
    print(f"\n{'='*55}")
    print("  MIGRACIÓN DE DATOS - Sistema Área de Alimentos Fighiera")
    print(f"{'='*55}")
    print(f"  Origen CSV : {csv_dir}")
    print(f"  Destino DB : {DB_PATH}")
    print(f"{'='*55}\n")

    init_db()
    session = get_session()

    try:
        print("Migrando tablas de referencia...")
        migrate_rubros(session, csv_dir)
        migrate_anexo(session, csv_dir, 1)
        migrate_anexo(session, csv_dir, 2)
        migrate_anexo(session, csv_dir, 3)
        session.commit()

        print("\nMigrando personas y establecimientos...")
        migrate_inscriptos(session, csv_dir)
        session.commit()
        migrate_establecimientos(session, csv_dir)
        session.commit()

        print("\nMigrando operaciones...")
        migrate_emision(session, csv_dir)
        migrate_deudas(session, csv_dir)
        migrate_auditorias(session, csv_dir)
        migrate_sanidad(session, csv_dir)
        session.commit()

        print(f"\n{'='*55}")
        print("  ✓ Migración completada sin errores.")
        print(f"{'='*55}\n")

    except Exception as exc:
        session.rollback()
        print(f"\n[ERROR] Migración falló: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrar datos MDB → SQLite")
    parser.add_argument("--csv-dir", required=True,
                        help="Directorio con los CSV exportados del .mdb")
    args = parser.parse_args()
    run_migration(args.csv_dir)
