"""
Conexión a la base de datos SQLite
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base

# La base de datos se guarda en la carpeta del usuario
DB_DIR  = os.path.join(os.path.expanduser("~"), "SistemaAlimentos")
DB_PATH = os.path.join(DB_DIR, "alimentos_fighiera.db")

os.makedirs(DB_DIR, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)


def init_db():
    """Crea todas las tablas si no existen y aplica migraciones incrementales."""
    Base.metadata.create_all(engine)
    # Migraciones incrementales — columnas agregadas después del deploy inicial
    _apply_migrations()

def _apply_migrations():
    """Aplica ALTER TABLE para columnas nuevas sin romper DBs existentes."""
    migraciones = [
        "ALTER TABLE deudas ADD COLUMN medio_pago VARCHAR(20)",
    ]
    import sqlalchemy
    with engine.connect() as conn:
        for sql in migraciones:
            try:
                conn.execute(sqlalchemy.text(sql))
                conn.commit()
            except Exception:
                pass  # La columna ya existe, ignorar


def get_session():
    return Session()


def close_session():
    Session.remove()
