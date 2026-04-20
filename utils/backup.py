"""
Backup automático de la base de datos SQLite.
Copia el archivo .db a una subcarpeta 'backups/' con timestamp.
Mantiene los últimos 30 backups y elimina los más viejos automáticamente.
"""
import os
import shutil
from datetime import datetime

from database.db import DB_PATH, DB_DIR

BACKUP_DIR = os.path.join(DB_DIR, "backups")
MAX_BACKUPS = 30


def hacer_backup() -> str:
    """
    Copia la DB a backups/alimentos_fighiera_YYYYMMDD_HHMMSS.db
    Devuelve la ruta del archivo generado, o lanza excepción si falla.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"No se encontró la base de datos en: {DB_PATH}")

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre      = f"alimentos_fighiera_{timestamp}.db"
    destino     = os.path.join(BACKUP_DIR, nombre)

    shutil.copy2(DB_PATH, destino)
    _limpiar_backups_viejos()
    return destino


def _limpiar_backups_viejos():
    """Elimina backups más antiguos si se supera MAX_BACKUPS."""
    try:
        archivos = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")],
            reverse=True,  # más nuevo primero
        )
        for viejo in archivos[MAX_BACKUPS:]:
            os.remove(os.path.join(BACKUP_DIR, viejo))
    except Exception:
        pass  # no interrumpir el flujo si la limpieza falla


def listar_backups() -> list:
    """Devuelve lista de (nombre, fecha_str, tamaño_kb) ordenada de más nuevo a más viejo."""
    if not os.path.exists(BACKUP_DIR):
        return []
    resultado = []
    for nombre in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if not nombre.endswith(".db"):
            continue
        ruta = os.path.join(BACKUP_DIR, nombre)
        try:
            mtime   = os.path.getmtime(ruta)
            fecha   = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
            tam_kb  = os.path.getsize(ruta) // 1024
            resultado.append((nombre, fecha, tam_kb))
        except OSError:
            continue
    return resultado