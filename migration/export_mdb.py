"""
Exporta tablas de un archivo .mdb a CSVs usando pyodbc (Windows).
Llamado desde MIGRAR_DATOS.bat.

Uso:
    python migration/export_mdb.py ruta/al/archivo.mdb ruta/salida/csv
"""
import sys
import os
import csv

TABLAS = [
    "AUDITORIAS",
    "DEUDAS",
    "EMISION",
    "ESTABLECIMIENTOS",
    "INSCRIPTOS",
    "SANIDAD",
    "RUBROS",
    "ANEXO1",
    "ANEXO2",
    "ANEXO3",
]


def exportar_con_pyodbc(mdb_path: str, csv_dir: str):
    try:
        import pyodbc
    except ImportError:
        print("[ERROR] pyodbc no está instalado. Ejecutá: pip install pyodbc")
        return False

    # Intentar con driver de Access 64-bit y 32-bit
    drivers = [
        r"Microsoft Access Driver (*.mdb, *.accdb)",
        r"Microsoft Access Driver (*.mdb)",
    ]
    conn = None
    for drv in drivers:
        try:
            conn_str = (
                f"DRIVER={{{drv}}};"
                f"DBQ={mdb_path};"
                "ExtendedAnsiSQL=1;"
            )
            conn = pyodbc.connect(conn_str, autocommit=True)
            print(f"  Conectado con driver: {drv}")
            break
        except pyodbc.Error:
            continue

    if not conn:
        print("[ERROR] No se encontró ningún driver de Access instalado.")
        print("  Descargá: https://www.microsoft.com/en-us/download/details.aspx?id=54920")
        return False

    cursor = conn.cursor()
    os.makedirs(csv_dir, exist_ok=True)
    ok = 0

    for tabla in TABLAS:
        try:
            cursor.execute(f"SELECT * FROM [{tabla}]")
            cols    = [col[0] for col in cursor.description]
            rows    = cursor.fetchall()
            csv_path = os.path.join(csv_dir, f"{tabla}.csv")

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                for row in rows:
                    # Convertir fechas y valores especiales a string
                    writer.writerow([
                        str(v) if v is not None else ""
                        for v in row
                    ])

            print(f"  {tabla}: {len(rows)} registros → {csv_path}")
            ok += 1

        except Exception as ex:
            print(f"  [ADVERTENCIA] No se pudo exportar {tabla}: {ex}")

    conn.close()
    print(f"\n  {ok}/{len(TABLAS)} tablas exportadas a: {csv_dir}")
    return ok > 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Uso: python {sys.argv[0]} archivo.mdb carpeta_salida")
        sys.exit(1)

    mdb_path = sys.argv[1]
    csv_dir  = sys.argv[2]

    if not os.path.exists(mdb_path):
        print(f"[ERROR] No existe el archivo: {mdb_path}")
        sys.exit(1)

    success = exportar_con_pyodbc(mdb_path, csv_dir)
    sys.exit(0 if success else 1)
