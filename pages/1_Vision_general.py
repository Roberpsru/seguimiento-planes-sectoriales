"""
Seguimiento de Planes Sectoriales — Visión general por plan.

Esta página muestra la visión general por plan (métricas, presupuesto por
ámbito, listado de actuaciones e indicadores). La ENTRADA de datos se
realiza desde la página "Gestión de actuaciones"
(pages/2_Gestion_actuaciones.py), que comparte con esta los módulos
src/i18n.py y src/consultas.py.

Antes vivía en la raíz como app.py; al añadir la portada se trasladó a
pages/ y app.py pasó a ser la página de inicio.
"""
import html
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Hacer accesibles los módulos compartidos en src/ (subimos dos niveles
# porque ahora este fichero vive en pages/, no en la raíz).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import db  # noqa: E402
import consultas  # noqa: E402
from i18n import asegurar_plan_id, plan_actual, selector_idioma, textos  # noqa: E402
from tema import aplicar_tema  # noqa: E402

st.set_page_config(page_title="Planes Sectoriales", layout="wide")
aplicar_tema()


@st.cache_data
def cargar(plan_codigo):
    """Carga en bloque los datos de un plan (cacheado para la visión general)."""
    con = db.conectar()
    plan = pd.read_sql_query(
        "SELECT * FROM planes WHERE codigo = ?", con, params=(plan_codigo,)
    ).iloc[0]
    ambitos = pd.read_sql_query(
        "SELECT * FROM ambitos WHERE plan_id = ? ORDER BY orden",
        con, params=(int(plan["id"]),),
    )
    # La subquery "ultimo_seguimiento" trae la etiqueta_corte más reciente
    # de cada actuación (o NULL si no hay seguimientos). Se ordena por
    # fecha_corte DESC y, como desempate, por id DESC.
    actuaciones = pd.read_sql_query(
        """SELECT ac.*, am.codigo AS ambito_cod, am.nombre_es AS ambito_nombre,
                  (SELECT s.etiqueta_corte
                     FROM seguimientos s
                    WHERE s.actuacion_id = ac.id
                    ORDER BY s.fecha_corte DESC, s.id DESC
                    LIMIT 1) AS ultimo_seguimiento
           FROM actuaciones ac JOIN ambitos am ON ac.ambito_id = am.id
           WHERE am.plan_id = ? ORDER BY am.orden, ac.orden""",
        con, params=(int(plan["id"]),),
    )
    indicadores = pd.read_sql_query(
        "SELECT * FROM indicadores WHERE plan_id = ? ORDER BY orden",
        con, params=(int(plan["id"]),),
    )
    con.close()
    return plan, ambitos, actuaciones, indicadores


# --------------------------------------------------------------------------
# Barra lateral: idioma + selector de plan globales (compartidos entre páginas)
# --------------------------------------------------------------------------
idioma = selector_idioma()
t = textos(idioma)
plan_id = asegurar_plan_id()
if plan_id is None:
    st.warning(t["sin_planes"])
    st.stop()

plan_record = plan_actual()
nombre_plan = (
    plan_record.get("nombre_eu")
    if idioma == "eu" and plan_record.get("nombre_eu")
    else plan_record["nombre_es"]
)

# --------------------------------------------------------------------------
# Cabecera
# --------------------------------------------------------------------------
st.title(f"{t['vision_general']} — {nombre_plan}")
st.markdown(
    f"<div style='color:#666; font-size:0.85rem; margin:-0.5rem 0 1rem 0;'>"
    f"{t['plan_activo_etiqueta']}: {html.escape(nombre_plan)} "
    f"<span style='color:#999;'>({t['para_cambiar_portada']})</span></div>",
    unsafe_allow_html=True,
)

plan, ambitos, actuaciones, indicadores = cargar(plan_record["codigo"])
if plan["objetivo_macro_es"]:
    st.markdown(
        f"""
        <div class="bloque-objetivo">
          <div class="titulo-objetivo">{html.escape(t["objetivo"])}</div>
          <div class="texto-objetivo">{html.escape(plan["objetivo_macro_es"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Métricas (envueltas en una tarjeta para destacar las cuatro métricas blancas
# sobre fondo verde pálido, igual que en el resto de páginas)
with st.container(border=True, key="bloque_metricas"):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t["ambitos"], len(ambitos))
    c2.metric(t["actuaciones"], len(actuaciones))
    total = actuaciones["presupuesto"].fillna(0).sum()
    c3.metric(t["presupuesto"], f"{total:,.0f} €".replace(",", "."))
    c4.metric(t["indicadores"], len(indicadores))

# --------------------------------------------------------------------------
# Pestañas
# --------------------------------------------------------------------------
tab1, tab2 = st.tabs([t["tab_act"], t["tab_kpi"]])

with tab1:
    # Gráfico presupuesto por ámbito
    df_pres = (actuaciones.assign(presupuesto=actuaciones["presupuesto"].fillna(0))
               .groupby("ambito_nombre", as_index=False)["presupuesto"].sum())
    df_pres = df_pres[df_pres["presupuesto"] > 0]
    if not df_pres.empty:
        fig = px.bar(df_pres, x="presupuesto", y="ambito_nombre", orientation="h",
                     title=t["presup_ambito"], text_auto=".2s")
        fig.update_traces(marker_color="#1f5f3a")
        fig.update_layout(
            yaxis_title="", xaxis_title="€", height=350,
            margin=dict(l=0, r=0, t=40, b=0),
            font=dict(color="#1f2a26", size=13),
            yaxis=dict(tickfont=dict(color="#1f2a26", size=13)),
            xaxis=dict(tickfont=dict(color="#1f2a26", size=12)),
            title=dict(font=dict(color="#1f5f3a", size=16)),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tabla de actuaciones por ámbito
    _COLOR_ESTADO = {
        "Previsto":  "#8a9690",
        "En curso":  "#c87a1f",
        "Ejecutado": "#1f5f3a",
    }

    def _estilo_estado(valor):
        color = _COLOR_ESTADO.get(valor)
        if color:
            return f"color: {color}; font-weight: 600;"
        return ""

    for _, am in ambitos.iterrows():
        sub = actuaciones[actuaciones["ambito_id"] == am["id"]]
        st.markdown(f"#### {am['codigo']} · {am['nombre_es']}")
        # Mostramos fecha inicio y fin por separado (antes salía solo "Fecha
        # prevista" con la de inicio, lo cual era confuso) y añadimos la
        # etiqueta del último seguimiento si existe.
        tabla = sub[["nombre_es", "estado", "presupuesto", "presupuesto_nota",
                     "fecha_inicio_prevista", "fecha_fin_prevista",
                     "ultimo_seguimiento"]].copy()
        tabla["presupuesto"] = tabla.apply(
            lambda r: f"{r['presupuesto']:,.0f} €".replace(",", ".")
            if pd.notna(r["presupuesto"]) else (r["presupuesto_nota"] or "—"), axis=1)
        tabla = tabla.drop(columns=["presupuesto_nota"])
        # Normalizamos NaN/None de las columnas de texto a guion para que la
        # tabla quede más limpia visualmente.
        for col in ("fecha_inicio_prevista", "fecha_fin_prevista", "ultimo_seguimiento"):
            tabla[col] = tabla[col].fillna("—").replace("", "—")
        # Prefijamos un punto al texto del estado (mismo color, gracias al
        # Styler de más abajo) para reforzar el indicador visual.
        tabla["estado"] = tabla["estado"].fillna("—").map(
            lambda v: f"● {v}" if v in _COLOR_ESTADO else v
        )
        tabla.columns = [t["actuaciones"], t["estado"], t["presupuesto"],
                         t["fecha_inicio"], t["fecha_fin"], t["ultimo_seguimiento"]]
        styler = (tabla.style
                  .map(lambda v: _estilo_estado(str(v).lstrip("● ").strip()),
                       subset=[t["estado"]])
                  .hide(axis="index"))
        st.table(styler)

with tab2:
    for cat in indicadores["categoria"].dropna().unique():
        st.markdown(f"#### {cat}")
        sub = indicadores[indicadores["categoria"] == cat]
        tabla = sub[["numero", "nombre_es", "meta_es"]].copy()
        tabla.columns = ["Nº", t["indicadores"], "Meta"]
        st.table(tabla.style.hide(axis="index"))
