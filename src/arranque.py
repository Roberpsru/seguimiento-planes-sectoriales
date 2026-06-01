"""
Inicialización automática de la base de datos en el arranque de la app.

Comportamiento por motor (ver src/db.py):

  - SQLite (uso local, sin DATABASE_URL): si la BD no existe o está vacía,
    se crea el esquema y se cargan automáticamente todos los Excel
    `datos/Plan_Sectorial_*.xlsx`. Así, basta `streamlit run app.py` para
    tener la app lista sin pasos manuales.

  - PostgreSQL (Supabase / Streamlit Cloud): NO se hace carga automática.
    Se asume que la primera carga se realizó previamente con
    `scripts/importar_plan.py` desde una red sin restricciones. Esto evita
    duplicar datos en cada arranque.
"""
from pathlib import Path

import db

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"


def _bd_vacia():
    """True si la tabla 'planes' no existe todavía o no tiene filas."""
    con = db.get_conexion()
    try:
        fila = con.execute("SELECT COUNT(*) AS n FROM planes").fetchone()
        if fila is None:
            return True
        n = fila["n"] if not isinstance(fila, tuple) else fila[0]
        return (n or 0) == 0
    except Exception:
        # La tabla aún no existe (BD recién creada o sin esquema).
        return True
    finally:
        con.close()


def inicializar_si_necesario():
    """Prepara la BD en el arranque. Solo actúa (carga Excel) en SQLite."""
    if db.MOTOR_BD != "sqlite":
        # En PostgreSQL no tocamos nada: la carga inicial es manual (CLI).
        return

    # Crea el esquema si no existe (idempotente: CREATE TABLE IF NOT EXISTS).
    db.inicializar_db()

    if not _bd_vacia():
        return

    # BD vacía -> cargamos todos los planes estándar disponibles en datos/.
    from importador import cargar_plan_desde_excel
    for excel in sorted(DATOS.glob("Plan_Sectorial_*.xlsx")):
        cargar_plan_desde_excel(excel, reemplazar=False, dry_run=False)
