# Sistema Área de Alimentos — Fighiera
**Versión 3.0 — Python + SQLite + SQLAlchemy**

---

## Requisitos

- Python 3.10 o superior (https://www.python.org/downloads/)
- Ninguna otra instalación externa — todo corre local.

---

## Instalación (primera vez)

Abrí una terminal en la carpeta `sistema_alimentos/` y ejecutá:

```bash
pip install -r requirements.txt
```

Eso instala dos paquetes:
- `sqlalchemy` — manejo de la base de datos
- `reportlab` — generación de PDFs

---

## Migración de datos (primera vez)

Para importar los datos del sistema viejo (archivo `.mdb`), primero
exportá las tablas a CSV con la herramienta `mdbtools` y luego ejecutá:

```bash
python -m migration.migrate --csv-dir /ruta/a/los/csv
```

Si estás en Windows y ya tenés los CSV en la misma carpeta que el sistema:

```bash
python -m migration.migrate --csv-dir ./data_export
```

La base de datos SQLite se crea automáticamente en:
```
C:\Users\TuUsuario\SistemaAlimentos\alimentos_fighiera.db
```

---

## Iniciar el sistema

```bash
python main.py
```

---

## Estructura del proyecto

```
sistema_alimentos/
├── main.py                  # Punto de entrada
├── requirements.txt
├── database/
│   ├── models.py            # Modelos de datos (SQLAlchemy)
│   └── db.py                # Conexión SQLite
├── migration/
│   └── migrate.py           # Importador de datos desde CSV/MDB
├── ui/
│   ├── dashboard.py         # Pantalla de inicio con estadísticas
│   ├── establecimientos.py  # CRUD establecimientos
│   ├── inscriptos.py        # CRUD inscriptos/titulares
│   ├── deudas.py            # Deudas y registro de pagos
│   └── sanidad_auditorias.py # Sanidad y auditorías
├── reports/
│   └── pdf_reports.py       # Generación de PDFs con ReportLab
└── utils/
    └── ui_helpers.py        # Estilos y utilidades de interfaz
```

---

## Tablas migradas

| Tabla original | Módulo en el nuevo sistema |
|---|---|
| ESTABLECIMIENTOS | Establecimientos |
| INSCRIPTOS | Inscriptos / Titulares |
| DEUDAS | Deudas y Pagos |
| EMISION | (datos de referencia) |
| AUDITORIAS | Auditorías |
| SANIDAD | Sanidad |
| RUBROS / ANEXO1/2/3 | Datos de referencia de montos |

---

## Reportes PDF disponibles

- **Padrón de Establecimientos** — listado con filtro activos/todos
- **Estado de Deudas** — por año, con opción solo impagas
- **Ficha de Establecimiento** — datos completos + historial de deudas
- **Registro de Auditorías** — listado completo

---

## Base de datos

La base de datos es un único archivo `.db` que podés respaldar copiándolo.
Por defecto está en `~/SistemaAlimentos/alimentos_fighiera.db`.
