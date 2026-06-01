"""
Capa fina de acceso a datos sobre src/db.py.

Cada función abre y cierra su propia conexión (SQLite es muy barato en eso)
y devuelve diccionarios planos, no sqlite3.Row, para que sean fáciles de
manipular desde la interfaz.

Los nombres de tablas y columnas se corresponden EXACTAMENTE con db/schema_sqlite.sql;
no se inventan campos.
"""
import pandas as pd

import db


def _a_dicts(filas):
    """Convierte una lista de sqlite3.Row en una lista de dicts."""
    return [dict(f) for f in filas]


# --------------------------------------------------------------------------
# Planes / Ámbitos / Actuaciones
# --------------------------------------------------------------------------
def listar_planes():
    """Devuelve todos los planes ordenados por id."""
    con = db.conectar()
    try:
        filas = con.execute(
            "SELECT id, codigo, nombre_es, nombre_eu, objetivo_macro_es, "
            "       objetivo_macro_eu, estado "
            "  FROM planes "
            " ORDER BY id"
        ).fetchall()
        return _a_dicts(filas)
    finally:
        con.close()


def listar_ambitos(plan_id):
    """Ámbitos de un plan, ordenados por su campo 'orden'."""
    con = db.conectar()
    try:
        filas = con.execute(
            "SELECT id, plan_id, codigo, nombre_es, nombre_eu, orden "
            "  FROM ambitos "
            " WHERE plan_id = ? "
            " ORDER BY orden, id",
            (plan_id,),
        ).fetchall()
        return _a_dicts(filas)
    finally:
        con.close()


def listar_actuaciones(ambito_id):
    """Actuaciones de un ámbito, ordenadas por su campo 'orden'."""
    con = db.conectar()
    try:
        filas = con.execute(
            "SELECT * FROM actuaciones "
            " WHERE ambito_id = ? "
            " ORDER BY orden, id",
            (ambito_id,),
        ).fetchall()
        return _a_dicts(filas)
    finally:
        con.close()


def obtener_actuacion(actuacion_id):
    """Devuelve una actuación concreta como dict, o None si no existe."""
    con = db.conectar()
    try:
        fila = con.execute(
            "SELECT * FROM actuaciones WHERE id = ?",
            (actuacion_id,),
        ).fetchone()
        return dict(fila) if fila else None
    finally:
        con.close()


def actualizar_actuacion(actuacion_id, estado, presupuesto_ejecutado,
                         fecha_inicio_prevista, fecha_fin_prevista):
    """
    Actualiza los campos editables de una actuación.

    Solo toca las columnas que se gestionan desde la página de edición;
    el resto (nombre, presupuesto previsto, código, etc.) se mantiene.
    """
    con = db.conectar()
    try:
        con.execute(
            """
            UPDATE actuaciones
               SET estado                = ?,
                   presupuesto_ejecutado = ?,
                   fecha_inicio_prevista = ?,
                   fecha_fin_prevista    = ?
             WHERE id = ?
            """,
            (
                estado,
                presupuesto_ejecutado,
                fecha_inicio_prevista,
                fecha_fin_prevista,
                actuacion_id,
            ),
        )
        con.commit()
    finally:
        con.close()


def actualizar_estado_actuacion(actuacion_id, estado):
    """Actualiza únicamente el estado de una actuación.

    Útil cuando, al añadir una anotación al historial, el usuario decide
    propagar ese estado al "estado actual" de la actuación.
    """
    con = db.conectar()
    try:
        con.execute(
            "UPDATE actuaciones SET estado = ? WHERE id = ?",
            (estado, actuacion_id),
        )
        con.commit()
    finally:
        con.close()


# --------------------------------------------------------------------------
# Bitácora de seguimientos
# --------------------------------------------------------------------------
def listar_seguimientos(actuacion_id):
    """Bitácora de seguimientos de una actuación, más reciente primero."""
    con = db.conectar()
    try:
        filas = con.execute(
            "SELECT * FROM seguimientos "
            " WHERE actuacion_id = ? "
            " ORDER BY fecha_corte DESC, id DESC",
            (actuacion_id,),
        ).fetchall()
        return _a_dicts(filas)
    finally:
        con.close()


def anadir_seguimiento(actuacion_id, fecha_corte, etiqueta_corte, estado, detalle_es):
    """Inserta una nueva entrada en la bitácora de seguimientos."""
    con = db.conectar()
    try:
        con.execute(
            """
            INSERT INTO seguimientos
                (actuacion_id, fecha_corte, etiqueta_corte, estado, detalle_es)
            VALUES (?, ?, ?, ?, ?)
            """,
            (actuacion_id, fecha_corte, etiqueta_corte, estado, detalle_es),
        )
        con.commit()
    finally:
        con.close()


# --------------------------------------------------------------------------
# Indicadores (KPI) y sus valores por periodo
# --------------------------------------------------------------------------
def listar_indicadores(plan_id, categoria=None):
    """Indicadores de un plan, ordenados por numero ascendente.

    Si se pasa una categoría no nula, filtra por ella; si no, devuelve
    todos los indicadores del plan.
    """
    con = db.conectar()
    try:
        if categoria is None:
            filas = con.execute(
                "SELECT * FROM indicadores "
                " WHERE plan_id = ? "
                " ORDER BY numero ASC, id",
                (plan_id,),
            ).fetchall()
        else:
            filas = con.execute(
                "SELECT * FROM indicadores "
                " WHERE plan_id = ? AND categoria = ? "
                " ORDER BY numero ASC, id",
                (plan_id, categoria),
            ).fetchall()
        return _a_dicts(filas)
    finally:
        con.close()


def listar_categorias(plan_id):
    """Categorías distintas (no nulas ni vacías) de los indicadores del plan."""
    con = db.conectar()
    try:
        filas = con.execute(
            "SELECT DISTINCT categoria FROM indicadores "
            " WHERE plan_id = ? AND categoria IS NOT NULL AND categoria <> '' "
            " ORDER BY categoria",
            (plan_id,),
        ).fetchall()
        return [f["categoria"] for f in filas]
    finally:
        con.close()


def obtener_indicador(indicador_id):
    """Devuelve un indicador concreto como dict, o None si no existe."""
    con = db.conectar()
    try:
        fila = con.execute(
            "SELECT * FROM indicadores WHERE id = ?",
            (indicador_id,),
        ).fetchone()
        return dict(fila) if fila else None
    finally:
        con.close()


def listar_valores_indicador(indicador_id):
    """Todos los valores registrados para un indicador, ordenados por periodo."""
    con = db.conectar()
    try:
        filas = con.execute(
            "SELECT * FROM indicador_valores "
            " WHERE indicador_id = ? "
            " ORDER BY periodo, id",
            (indicador_id,),
        ).fetchall()
        return _a_dicts(filas)
    finally:
        con.close()


def guardar_valor_indicador(indicador_id, periodo, valor, nota_es):
    """Upsert manual de un valor (indicador_id, periodo).

    No se apoya en una restricción UNIQUE del esquema: primero comprueba
    si existe una fila para ese (indicador, periodo); si la hay actualiza
    valor + nota_es (sin tocar valor_texto_es para no perder texto
    importado), y si no la inserta.
    """
    con = db.conectar()
    try:
        existente = con.execute(
            "SELECT id FROM indicador_valores "
            " WHERE indicador_id = ? AND periodo = ?",
            (indicador_id, periodo),
        ).fetchone()
        if existente:
            con.execute(
                "UPDATE indicador_valores "
                "   SET valor = ?, nota_es = ?, fecha_registro = CURRENT_TIMESTAMP "
                " WHERE id = ?",
                (valor, nota_es, existente["id"]),
            )
        else:
            con.execute(
                "INSERT INTO indicador_valores "
                "       (indicador_id, periodo, valor, nota_es) "
                "VALUES (?, ?, ?, ?)",
                (indicador_id, periodo, valor, nota_es),
            )
        con.commit()
    finally:
        con.close()


def actualizar_meta_valor(indicador_id, meta_valor):
    """Actualiza únicamente meta_valor (el objetivo numérico para gráficos)."""
    con = db.conectar()
    try:
        con.execute(
            "UPDATE indicadores SET meta_valor = ? WHERE id = ?",
            (meta_valor, indicador_id),
        )
        con.commit()
    finally:
        con.close()


# --------------------------------------------------------------------------
# Resumen ejecutivo del plan (página "Resumen del Plan")
# --------------------------------------------------------------------------
def resumen_actuaciones(plan_id):
    """
    Estadísticos agregados de las actuaciones de un plan.

    Devuelve un dict con:
      - total: nº total de actuaciones
      - por_estado: dict {"Previsto": n, "En curso": n, "Ejecutado": n}
      - presupuesto_total, presupuesto_ejecutado (sumas en €)
      - sin_dotacion: nº de actuaciones marcadas con presupuesto_nota
        = "Sin dotación"
      - ultima_fecha_seguimiento: la fecha_corte más reciente entre TODAS
        las actuaciones del plan (texto ISO o None si no hay seguimientos)
    """
    con = db.conectar()
    try:
        fila = con.execute(
            """
            SELECT
                COUNT(*)                                                AS total,
                SUM(CASE WHEN ac.estado = 'Previsto'   THEN 1 ELSE 0 END) AS n_previsto,
                SUM(CASE WHEN ac.estado = 'En curso'   THEN 1 ELSE 0 END) AS n_en_curso,
                SUM(CASE WHEN ac.estado = 'Ejecutado'  THEN 1 ELSE 0 END) AS n_ejecutado,
                COALESCE(SUM(ac.presupuesto), 0)                        AS presupuesto_total,
                COALESCE(SUM(ac.presupuesto_ejecutado), 0)              AS presupuesto_ejecutado,
                SUM(CASE WHEN ac.presupuesto_nota = 'Sin dotación'
                         THEN 1 ELSE 0 END)                             AS sin_dotacion
            FROM actuaciones ac
            JOIN ambitos     am ON ac.ambito_id = am.id
            WHERE am.plan_id = ?
            """,
            (plan_id,),
        ).fetchone()

        ultima = con.execute(
            """
            SELECT MAX(s.fecha_corte) AS fecha_corte
            FROM seguimientos s
            JOIN actuaciones ac ON s.actuacion_id = ac.id
            JOIN ambitos     am ON ac.ambito_id = am.id
            WHERE am.plan_id = ?
            """,
            (plan_id,),
        ).fetchone()

        return {
            "total":                    fila["total"] or 0,
            "por_estado": {
                "Previsto":  fila["n_previsto"]  or 0,
                "En curso":  fila["n_en_curso"]  or 0,
                "Ejecutado": fila["n_ejecutado"] or 0,
            },
            "presupuesto_total":        fila["presupuesto_total"]      or 0,
            "presupuesto_ejecutado":    fila["presupuesto_ejecutado"]  or 0,
            "sin_dotacion":             fila["sin_dotacion"]           or 0,
            "ultima_fecha_seguimiento": ultima["fecha_corte"],
        }
    finally:
        con.close()


def resumen_por_ambito(plan_id):
    """
    DataFrame con el desglose por ámbito (filas) para el resumen:

      ambito_codigo, ambito_nombre, n_actuaciones,
      n_previsto, n_en_curso, n_ejecutado,
      presupuesto_comprometido, presupuesto_ejecutado

    Incluye ámbitos sin actuaciones (LEFT JOIN), ordenados por el campo
    'orden' del ámbito.
    """
    con = db.conectar()
    try:
        return pd.read_sql_query(
            """
            SELECT
                am.codigo    AS ambito_codigo,
                am.nombre_es AS ambito_nombre,
                COUNT(ac.id) AS n_actuaciones,
                SUM(CASE WHEN ac.estado = 'Previsto'  THEN 1 ELSE 0 END) AS n_previsto,
                SUM(CASE WHEN ac.estado = 'En curso'  THEN 1 ELSE 0 END) AS n_en_curso,
                SUM(CASE WHEN ac.estado = 'Ejecutado' THEN 1 ELSE 0 END) AS n_ejecutado,
                COALESCE(SUM(ac.presupuesto), 0)           AS presupuesto_comprometido,
                COALESCE(SUM(ac.presupuesto_ejecutado), 0) AS presupuesto_ejecutado
            FROM ambitos am
            LEFT JOIN actuaciones ac ON ac.ambito_id = am.id
            WHERE am.plan_id = ?
            GROUP BY am.id, am.codigo, am.nombre_es, am.orden
            ORDER BY am.orden, am.id
            """,
            con,
            params=(plan_id,),
        )
    finally:
        con.close()


def resumen_indicadores(plan_id):
    """
    DataFrame con un resumen por indicador para el cuadro de mando:

      numero, categoria, nombre, meta_texto, meta_valor,
      ultimo_periodo, ultimo_valor, ultimo_valor_texto, porcentaje_avance

    ultimo_valor = valor numérico de mayor periodo (lex.) cuyo valor es no NULL.
    ultimo_valor_texto = COALESCE(valor_texto_es, valor_texto_eu) del último
                         registro (haya o no número), para enseñar el matiz
                         cualitativo cuando no haya número.
    porcentaje_avance = (ultimo_valor / meta_valor) * 100 cuando ambos existen;
                        None en caso contrario.
    """
    con = db.conectar()
    try:
        df = pd.read_sql_query(
            """
            SELECT
                i.numero,
                i.categoria,
                i.nombre_es AS nombre,
                i.meta_es   AS meta_texto,
                i.meta_valor,
                (SELECT iv.periodo
                   FROM indicador_valores iv
                  WHERE iv.indicador_id = i.id
                    AND iv.valor IS NOT NULL
                  ORDER BY iv.periodo DESC, iv.id DESC
                  LIMIT 1) AS ultimo_periodo,
                (SELECT iv.valor
                   FROM indicador_valores iv
                  WHERE iv.indicador_id = i.id
                    AND iv.valor IS NOT NULL
                  ORDER BY iv.periodo DESC, iv.id DESC
                  LIMIT 1) AS ultimo_valor,
                (SELECT COALESCE(iv.valor_texto_es, iv.valor_texto_eu)
                   FROM indicador_valores iv
                  WHERE iv.indicador_id = i.id
                  ORDER BY iv.periodo DESC, iv.id DESC
                  LIMIT 1) AS ultimo_valor_texto
            FROM indicadores i
            WHERE i.plan_id = ?
            ORDER BY i.numero ASC, i.id
            """,
            con,
            params=(plan_id,),
        )
        # Calculamos el % de avance en Python (más legible que en SQL y
        # evita problemas de NULL/0 division).
        def _pct(row):
            mv = row["meta_valor"]
            uv = row["ultimo_valor"]
            if mv is None or uv is None:
                return None
            if pd.isna(mv) or pd.isna(uv) or mv == 0:
                return None
            return float(uv) / float(mv) * 100.0
        df["porcentaje_avance"] = df.apply(_pct, axis=1)
        return df
    finally:
        con.close()


def ultimos_movimientos(plan_id, limite=10):
    """
    DataFrame con los últimos N movimientos del histórico (seguimientos)
    de un plan, ordenados por fecha de corte descendente:

      fecha_corte, etiqueta_corte, actuacion_nombre, ambito_nombre,
      estado, detalle
    """
    con = db.conectar()
    try:
        return pd.read_sql_query(
            """
            SELECT
                s.fecha_corte,
                s.etiqueta_corte,
                ac.nombre_es AS actuacion_nombre,
                am.nombre_es AS ambito_nombre,
                s.estado,
                s.detalle_es AS detalle
            FROM seguimientos s
            JOIN actuaciones ac ON s.actuacion_id = ac.id
            JOIN ambitos     am ON ac.ambito_id = am.id
            WHERE am.plan_id = ?
            ORDER BY s.fecha_corte DESC, s.id DESC
            LIMIT ?
            """,
            con,
            params=(plan_id, int(limite)),
        )
    finally:
        con.close()
