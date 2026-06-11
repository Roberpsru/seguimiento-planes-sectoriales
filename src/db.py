"""
Acceso a la base de datos AGNÓSTICO DE MOTOR (SQLite o PostgreSQL).

La selección del motor se hace UNA sola vez al importar el módulo, en este
orden de prioridad:

  1. Variable de entorno DATABASE_URL  -> PostgreSQL con esa URL.
  2. st.secrets["DATABASE_URL"]         -> PostgreSQL con esa URL (Streamlit Cloud).
  3. En cualquier otro caso             -> SQLite en db/seguimiento.db.

Idea de diseño para no reescribir todas las consultas del proyecto:

  - En SQLite, get_conexion() devuelve la conexión NATIVA (sqlite3.Connection),
    con lo que el atajo `con.execute(...)`, el placeholder `?` y pandas se
    comportan EXACTAMENTE igual que antes.
  - En PostgreSQL, get_conexion() devuelve un adaptador fino (_ConexionPG) que
    imita la parte de la API de sqlite3.Connection que usa el proyecto
    (`con.execute(...)` como atajo, `con.cursor()` para pandas, commit/rollback/
    close) y TRADUCE automáticamente el placeholder `?` a `%s`.

Así, las consultas existentes con `?` son portables sin tocarlas. Para INSERTs
que necesitan el id generado, usar `insertar_devolver_id()` (gestiona la
diferencia entre `cursor.lastrowid` de SQLite y `RETURNING id` de PostgreSQL).
"""
import os
import sqlite3
from pathlib import Path

# Rutas del proyecto
RAIZ = Path(__file__).resolve().parent.parent
DB_PATH = RAIZ / "db" / "seguimiento.db"
SCHEMA_SQLITE = RAIZ / "db" / "schema_sqlite.sql"
SCHEMA_POSTGRES = RAIZ / "db" / "schema_postgres.sql"


# --------------------------------------------------------------------------
# Resolución del motor activo (una vez por proceso)
# --------------------------------------------------------------------------
def _resolver_motor():
    """Devuelve (motor, url) según el orden de prioridad documentado arriba."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return "postgres", url

    # st.secrets puede lanzar si no hay fichero de secrets; lo aislamos.
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return "postgres", str(st.secrets["DATABASE_URL"])
    except Exception:
        pass

    return "sqlite", None


MOTOR_BD, DATABASE_URL = _resolver_motor()


# --------------------------------------------------------------------------
# Placeholder dinámico
# --------------------------------------------------------------------------
def P():
    """Placeholder de parámetros del motor activo: '?' (sqlite) o '%s' (postgres)."""
    return "%s" if MOTOR_BD == "postgres" else "?"


def _traducir(sql):
    """Traduce el placeholder canónico '?' al del motor activo.

    En SQLite no toca nada. En PostgreSQL sustituye cada '?' por '%s'. En el
    SQL del proyecto '?' solo aparece como marcador de parámetro (nunca dentro
    de literales), por lo que la sustitución es segura.
    """
    if MOTOR_BD == "postgres":
        return sql.replace("?", "%s")
    return sql


# --------------------------------------------------------------------------
# Adaptador para PostgreSQL (imita la API mínima de sqlite3.Connection)
# --------------------------------------------------------------------------
class _CursorPG:
    """Cursor que traduce '?'->'%s' en execute y delega todo lo demás."""

    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, params=None):
        self._cur.execute(_traducir(sql), params if params is not None else ())
        return self

    def __getattr__(self, nombre):
        return getattr(self._cur, nombre)

    def __iter__(self):
        return iter(self._cur)


class _ConexionPG:
    """Adaptador sobre una conexión psycopg2.

    Expone la parte de la API de sqlite3.Connection que usa el proyecto:
    `execute()` como atajo, `cursor()` (para pandas), commit/rollback/close
    y `raw` para acceder a la conexión psycopg2 subyacente.

    Importante — dos tipos de cursor según el consumidor:
      - `cursor()` devuelve un cursor de TUPLAS. Lo usa pandas.read_sql_query,
        que NO es compatible con cursores tipo dict (RealDictCursor): con dicts
        construye un DataFrame con los nombres de columna repetidos como datos.
      - `execute()` usa un RealDictCursor para que el resto del código acceda a
        las filas por nombre (fila["id"], dict(fila)), igual que sqlite3.Row.
    """

    def __init__(self, con):
        self._con = con

    def cursor(self):
        # Cursor de TUPLAS (para pandas.read_sql_query).
        return _CursorPG(self._con.cursor())

    def execute(self, sql, params=None):
        # Cursor RealDict (acceso por nombre, como sqlite3.Row).
        import psycopg2.extras
        cur = _CursorPG(
            self._con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        )
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._con.commit()

    def rollback(self):
        self._con.rollback()

    def close(self):
        self._con.close()

    @property
    def raw(self):
        return self._con


# --------------------------------------------------------------------------
# Conexión
# --------------------------------------------------------------------------
def get_conexion():
    """Devuelve una conexión al motor activo.

    - SQLite: sqlite3.Connection nativa, con row_factory=sqlite3.Row y claves
      foráneas activadas (acceso a columnas por nombre: fila["plan_id"]).
    - PostgreSQL: _ConexionPG sobre psycopg2. El cursor por defecto devuelve
      TUPLAS (necesario para pandas.read_sql_query); el acceso por nombre se
      obtiene en _ConexionPG.execute() con un RealDictCursor explícito.
    """
    if MOTOR_BD == "postgres":
        import psycopg2
        con = psycopg2.connect(DATABASE_URL)
        return _ConexionPG(con)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con


def conectar():
    """Alias retrocompatible de get_conexion() (usado por todo el proyecto)."""
    return get_conexion()


# --------------------------------------------------------------------------
# Helpers de inserción / ejecución
# --------------------------------------------------------------------------
def insertar_devolver_id(con, tabla, columnas, valores, columna_id="id"):
    """Inserta una fila y devuelve el id generado, agnóstico de motor.

    - SQLite: usa cursor.lastrowid.
    - PostgreSQL: añade RETURNING <columna_id> y lee el resultado.

    Parámetros:
      con       conexión devuelta por get_conexion()
      tabla     nombre de la tabla
      columnas  lista/tupla de nombres de columna
      valores   lista/tupla de valores (mismo orden que columnas)
    """
    cols = ", ".join(columnas)
    marcadores = ", ".join(["?"] * len(valores))  # _traducir() los adapta
    if MOTOR_BD == "postgres":
        sql = (
            f"INSERT INTO {tabla} ({cols}) VALUES ({marcadores}) "
            f"RETURNING {columna_id}"
        )
        cur = con.execute(sql, tuple(valores))
        fila = cur.fetchone()
        return fila[columna_id]

    sql = f"INSERT INTO {tabla} ({cols}) VALUES ({marcadores})"
    cur = con.execute(sql, tuple(valores))
    return cur.lastrowid


def ultimo_id(cursor, tabla=None, columna="id"):
    """Devuelve el id de la última fila insertada con ese cursor (SQLite).

    En PostgreSQL no existe lastrowid; para obtener el id usar
    insertar_devolver_id() (que añade RETURNING). Esta función se mantiene
    por compatibilidad con el flujo SQLite.
    """
    if MOTOR_BD == "postgres":
        fila = cursor.fetchone()
        if fila is None:
            return None
        return fila[columna] if not isinstance(fila, tuple) else fila[0]
    return cursor.lastrowid


def ejecutar(query, params=None, fetch=None):
    """Ejecuta una consulta gestionando conexión, commit, errores y cierre.

    - `query` puede usar el marcador `{P}` (o directamente `?`); ambos se
      traducen al placeholder del motor activo.
    - `fetch`: "one" -> fetchone(), "all" -> fetchall(), None -> sin retorno.

    Hace commit si todo va bien y rollback ante cualquier excepción.
    """
    query = query.replace("{P}", P())
    con = get_conexion()
    try:
        cur = con.execute(query, params if params is not None else ())
        resultado = None
        if fetch == "one":
            resultado = cur.fetchone()
        elif fetch == "all":
            resultado = cur.fetchall()
        con.commit()
        return resultado
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def leer_df(query, params=None):
    """Ejecuta un SELECT y devuelve un pandas.DataFrame, agnóstico de motor.

    IMPORTANTE: NO usa `pd.read_sql_query(con, ...)` a propósito. pandas itera
    el cursor esperando TUPLAS (acceso posicional); con un RealDictCursor recibe
    dicts y construye un DataFrame con los NOMBRES DE COLUMNA como valores en
    cada celda. Aquí obtenemos filas + nombres de columna explícitamente desde
    el cursor por defecto (tuplas en PostgreSQL, sqlite3.Row en SQLite —ambos
    iterables posicionalmente—) y construimos el DataFrame nosotros, sin
    depender de cómo pandas maneje la conexión. Ver pitfall 6 en CLAUDE.md.

    `query` admite el marcador `{P}` o el placeholder `?` (se traducen al motor).
    """
    import pandas as pd

    query = query.replace("{P}", P())
    con = get_conexion()
    try:
        cur = con.cursor()
        cur.execute(query, params if params is not None else ())
        columnas = [d[0] for d in cur.description]
        filas = cur.fetchall()
        datos = [list(f) for f in filas] if filas else []
        return pd.DataFrame(datos, columns=columnas)
    finally:
        con.close()


# --------------------------------------------------------------------------
# Inicialización del esquema (elige el .sql según el motor)
# --------------------------------------------------------------------------
def inicializar_db():
    """Crea las tablas a partir del esquema correspondiente al motor activo.

    Ambos esquemas usan CREATE TABLE IF NOT EXISTS, por lo que es idempotente.
    """
    schema = SCHEMA_POSTGRES if MOTOR_BD == "postgres" else SCHEMA_SQLITE
    sql = schema.read_text(encoding="utf-8")

    con = get_conexion()
    try:
        if MOTOR_BD == "postgres":
            # psycopg2 ejecuta varias sentencias separadas por ';' en un execute.
            cur = con.raw.cursor()
            cur.execute(sql)
        else:
            con.executescript(sql)
        con.commit()
    finally:
        con.close()

    # NUNCA imprimir DATABASE_URL ni la cadena de conexión (contiene
    # credenciales y host). En SQLite mostramos la ruta del fichero local
    # (sin secretos); en PostgreSQL solo el nombre del motor.
    if MOTOR_BD == "postgres":
        print("Base de datos lista. Motor de BD: postgres")
    else:
        print(f"Base de datos lista. Motor de BD: sqlite ({DB_PATH})")


if __name__ == "__main__":
    inicializar_db()
