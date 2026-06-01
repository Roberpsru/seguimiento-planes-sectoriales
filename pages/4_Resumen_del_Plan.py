"""
Página de RESUMEN DEL PLAN: vista ejecutiva consolidada.

Reúne en una sola pantalla, para el plan seleccionado:
  - Cabecera con nombre, periodo, objetivo macro y última actualización.
  - Métricas globales (actuaciones por estado, presupuesto comprometido y
    ejecutado, indicadores y sin dotación).
  - Distribución por estado (donut) y avance presupuestario por ámbito
    (barras horizontales agrupadas).
  - Tabla "Resumen por ámbito" y tabla "Resumen de indicadores" con un
    semáforo de avance.
  - Lista de los 10 últimos movimientos del histórico.

Sigue el mismo patrón que el resto de páginas: set_page_config →
aplicar_tema → selector_idioma → contenedores con key="bloque_*".
"""
import html
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Hacer accesibles los módulos compartidos en src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import consultas  # noqa: E402
from i18n import (  # noqa: E402
    asegurar_plan_id,
    etiquetas_estado,
    plan_actual,
    selector_idioma,
    textos,
)
from tema import aplicar_tema  # noqa: E402

st.set_page_config(
    page_title="Resumen del Plan",
    layout="wide",
)
aplicar_tema()

# --------------------------------------------------------------------------
# Idioma y textos
# --------------------------------------------------------------------------
idioma = selector_idioma()
t = textos(idioma)
plan_id = asegurar_plan_id()
etiq_estado = etiquetas_estado(t)

st.title(t["resumen_plan"])
if plan_id is not None:
    _p = plan_actual()
    _nombre_p = _p.get("nombre_eu") if idioma == "eu" and _p.get("nombre_eu") else _p.get("nombre_es", "")
    st.markdown(
        f"<div style='color:#666; font-size:0.85rem; margin:-0.5rem 0 1rem 0;'>"
        f"{t['plan_activo_etiqueta']}: {_nombre_p} "
        f"<span style='color:#999;'>({t['para_cambiar_portada']})</span></div>",
        unsafe_allow_html=True,
    )


def _nombre(item, campo_es, campo_eu):
    """Devuelve el nombre en el idioma activo, con fallback al castellano."""
    if idioma == "eu" and item.get(campo_eu):
        return item[campo_eu]
    return item.get(campo_es, "") or ""


def _formato_euros(v):
    """Formato '1.234.567 €'; '—' si el valor es nulo, NaN o no numérico.

    pd.to_numeric(coerce) tolera float, Decimal, None y cadenas (estas -> NaN),
    evitando ValueError según el motor de BD (PostgreSQL puede servir tipos o
    valores distintos a SQLite).
    """
    v = pd.to_numeric(v, errors="coerce")
    if pd.isna(v):
        return "—"
    return f"{float(v):,.0f} €".replace(",", ".")


def _formato_fecha(fecha_iso):
    """Convierte 'YYYY-MM-DD' en 'DD/MM/YYYY' o devuelve el texto crudo."""
    if not fecha_iso:
        return "—"
    try:
        return datetime.strptime(fecha_iso[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(fecha_iso)


@st.cache_data
def _cargar(plan_id):
    """Carga en bloque los cuatro conjuntos de datos del resumen."""
    return (
        consultas.resumen_actuaciones(plan_id),
        consultas.resumen_por_ambito(plan_id),
        consultas.resumen_indicadores(plan_id),
        consultas.ultimos_movimientos(plan_id, 10),
    )


# --------------------------------------------------------------------------
# a) Plan activo (el selector vive ahora en el sidebar — global a la app).
# --------------------------------------------------------------------------
if plan_id is None:
    st.warning(t["sin_planes"])
    st.stop()
plan = plan_actual()

resumen, df_ambito, df_kpi, df_mov = _cargar(plan["id"])


# --------------------------------------------------------------------------
# b) Cabecera: nombre del plan + periodo + objetivo + última actualización
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_resumen_cabecera"):
    st.markdown(
        f"<div style='font-size:2rem; font-weight:700; color:#1f5f3a; "
        f"margin-top:0.2rem; margin-bottom:0.8rem; "
        f"border-bottom:2px solid #d9e1dd; padding-bottom:0.4rem;'>"
        f"{html.escape(_nombre(plan, 'nombre_es', 'nombre_eu'))}</div>",
        unsafe_allow_html=True,
    )

    pi, pf = plan.get("periodo_inicio"), plan.get("periodo_fin")
    if pi and pf:
        st.markdown(f"**{pi} – {pf}**")
    elif pi or pf:
        st.markdown(f"**{pi or pf}**")

    objetivo = _nombre(plan, "objetivo_macro_es", "objetivo_macro_eu")
    if objetivo:
        st.markdown(
            f"""
            <div class="bloque-objetivo">
              <div class="titulo-objetivo">{html.escape(t["objetivo"])}</div>
              <div class="texto-objetivo">{html.escape(objetivo)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption(
        f"{t['ultima_actualizacion']}: "
        f"{_formato_fecha(resumen.get('ultima_fecha_seguimiento'))}"
    )


# --------------------------------------------------------------------------
# c) Resumen: dos filas de métricas + caption final
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_resumen_metricas"):
    st.markdown(f"### {t['resumen']}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t["total_actuaciones"], resumen["total"])
    m2.metric(t["estado_previsto"],  resumen["por_estado"].get("Previsto", 0))
    m3.metric(t["estado_en_curso"],  resumen["por_estado"].get("En curso", 0))
    m4.metric(t["estado_ejecutado"], resumen["por_estado"].get("Ejecutado", 0))

    pt = pd.to_numeric(resumen["presupuesto_total"], errors="coerce")
    pe = pd.to_numeric(resumen["presupuesto_ejecutado"], errors="coerce")
    pt = 0.0 if pd.isna(pt) else float(pt)
    pe = 0.0 if pd.isna(pe) else float(pe)
    p1, p2 = st.columns(2)
    p1.metric(t["presupuesto"], _formato_euros(pt))
    if pt > 0:
        pct_global = pe / pt * 100
        p2.metric(
            t["presupuesto_ejecutado"],
            _formato_euros(pe),
            delta=f"{pct_global:.1f} %",
        )
    else:
        p2.metric(t["presupuesto_ejecutado"], _formato_euros(pe))

    st.caption(
        f"{t['indicadores']}: {len(df_kpi)} · "
        f"{t['sin_dotacion']}: {resumen['sin_dotacion']}"
    )


# --------------------------------------------------------------------------
# d) Distribución por estado: donut + barras por ámbito
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_resumen_estado"):
    st.markdown(f"### {t['distribucion_estado']}")

    col_d, col_b = st.columns([1, 1.2])

    # ---- Donut por estado ----------------------------------------------
    with col_d:
        df_donut = pd.DataFrame({
            "estado": [
                etiq_estado["Previsto"],
                etiq_estado["En curso"],
                etiq_estado["Ejecutado"],
            ],
            "n": [
                resumen["por_estado"].get("Previsto", 0),
                resumen["por_estado"].get("En curso", 0),
                resumen["por_estado"].get("Ejecutado", 0),
            ],
        })
        df_donut = df_donut[df_donut["n"] > 0]
        if not df_donut.empty:
            fig_d = px.pie(
                df_donut, names="estado", values="n", hole=0.5,
                color="estado",
                color_discrete_map={
                    etiq_estado["Previsto"]:  "#8a9690",
                    etiq_estado["En curso"]:  "#c87a1f",
                    etiq_estado["Ejecutado"]: "#1f5f3a",
                },
            )
            fig_d.update_layout(
                height=320,
                margin=dict(l=0, r=0, t=10, b=0),
                font=dict(color="#1f2a26", size=13),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15),
            )
            st.plotly_chart(fig_d, use_container_width=True)
        else:
            st.caption("—")

    # ---- Barras por ámbito (Comprometido vs Ejecutado) -----------------
    with col_b:
        st.markdown(f"**{t['avance_presupuestario_ambito']}**")
        # Sumamos los presupuestos coaccionando a numérico (PostgreSQL puede
        # devolver Decimal o, si la columna fuese de texto, cadenas que
        # romperían float()). Los no numéricos se ignoran (NaN).
        hay_presupuesto = False
        if not df_ambito.empty:
            _suma_pres = pd.to_numeric(
                df_ambito[["presupuesto_comprometido", "presupuesto_ejecutado"]]
                .stack(),
                errors="coerce",
            ).sum()
            hay_presupuesto = float(_suma_pres) > 0
        if hay_presupuesto:
            df_long = df_ambito.melt(
                id_vars=["ambito_nombre"],
                value_vars=["presupuesto_comprometido", "presupuesto_ejecutado"],
                var_name="tipo", value_name="importe",
            )
            mapa_tipo = {
                "presupuesto_comprometido": t["comprometido"],
                "presupuesto_ejecutado":    t["ejecutado"],
            }
            df_long["tipo"] = df_long["tipo"].map(mapa_tipo)
            df_long["importe"] = pd.to_numeric(df_long["importe"], errors="coerce")
            fig_b = px.bar(
                df_long, x="importe", y="ambito_nombre",
                color="tipo", orientation="h", barmode="group",
                color_discrete_map={
                    t["comprometido"]: "#c5d0c8",
                    t["ejecutado"]:    "#1f5f3a",
                },
            )
            fig_b.update_layout(
                height=320,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="€", yaxis_title="",
                font=dict(color="#1f2a26", size=13),
                yaxis=dict(tickfont=dict(color="#1f2a26", size=13)),
                xaxis=dict(tickfont=dict(color="#1f2a26", size=12)),
                legend=dict(title_text="", orientation="h",
                            yanchor="bottom", y=-0.2),
            )
            st.plotly_chart(fig_b, use_container_width=True)


# --------------------------------------------------------------------------
# e) Resumen por ámbito (tabla)
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_resumen_ambito"):
    st.markdown(f"### {t['resumen_por_ambito']}")

    if df_ambito.empty:
        st.caption("—")
    else:
        tabla_a = df_ambito.copy()

        def _pct_avance(row):
            comp = pd.to_numeric(row["presupuesto_comprometido"], errors="coerce")
            ej = pd.to_numeric(row["presupuesto_ejecutado"], errors="coerce")
            if pd.isna(comp) or float(comp) == 0:
                return "—"
            if pd.isna(ej):
                ej = 0.0
            return f"{float(ej) / float(comp) * 100:.1f} %"

        tabla_a["pct_avance"] = tabla_a.apply(_pct_avance, axis=1)
        tabla_a["comp_fmt"] = tabla_a["presupuesto_comprometido"].map(_formato_euros)
        tabla_a["ej_fmt"]   = tabla_a["presupuesto_ejecutado"].map(_formato_euros)
        tabla_a["ambito"] = tabla_a.apply(
            lambda r: (
                f"{r['ambito_codigo'] or ''} · {r['ambito_nombre']}".strip(" ·")
            ),
            axis=1,
        )

        cols = ["ambito", "n_actuaciones", "n_previsto", "n_en_curso",
                "n_ejecutado", "comp_fmt", "ej_fmt", "pct_avance"]
        tabla_a = tabla_a[cols]
        tabla_a.columns = [
            t["ambitos"], t["n_actuaciones"],
            t["estado_previsto"], t["estado_en_curso"], t["estado_ejecutado"],
            t["pres_comprometido"], t["pres_ejecutado"], t["porcentaje_avance"],
        ]
        st.table(tabla_a.style.hide(axis="index"))


# --------------------------------------------------------------------------
# f) Resumen de indicadores (tabla con semáforo)
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_resumen_kpi"):
    st.markdown(f"### {t['resumen_indicadores']}")

    if df_kpi.empty:
        st.caption(t["sin_indicadores"])
    else:
        tabla_k = df_kpi.copy()

        def _ultimo(row):
            # to_numeric(coerce) evita ValueError si ultimo_valor llega como
            # cadena no numérica (mismo motivo que en consultas.resumen_indicadores).
            v = pd.to_numeric(row["ultimo_valor"], errors="coerce")
            if not pd.isna(v):
                return f"{float(v):g}"
            valor_texto = row.get("ultimo_valor_texto")
            txt = "" if pd.isna(valor_texto) else str(valor_texto).strip()
            if not txt:
                return "—"
            return txt[:80] + "…" if len(txt) > 80 else txt

        def _pct_kpi(v):
            v = pd.to_numeric(v, errors="coerce")
            if pd.isna(v):
                return "—"
            return f"{float(v):.1f} %"

        def _semaforo(v):
            """Punto coloreado: verde >= 90, ámbar 50-90, rojo < 50."""
            v = pd.to_numeric(v, errors="coerce")
            if pd.isna(v):
                return "—"
            v = float(v)
            if v >= 90:
                color = "#1f5f3a"
            elif v >= 50:
                color = "#c87a1f"
            else:
                color = "#c0392b"
            return (
                f'<span style="color:{color}; font-size:1.3rem; '
                f'line-height:1;">●</span>'
            )

        tabla_k["ult_str"]      = tabla_k.apply(_ultimo, axis=1)
        tabla_k["pct_str"]      = tabla_k["porcentaje_avance"].map(_pct_kpi)
        tabla_k["estado_html"]  = tabla_k["porcentaje_avance"].map(_semaforo)
        tabla_k["meta_txt"]     = tabla_k["meta_texto"].fillna("—").replace("", "—")
        tabla_k["categoria_x"]  = tabla_k["categoria"].fillna("—").replace("", "—")
        tabla_k["numero_x"]     = tabla_k["numero"].fillna("—")

        cols_k = ["numero_x", "categoria_x", "nombre", "meta_txt",
                  "ult_str", "pct_str", "estado_html"]
        tabla_k = tabla_k[cols_k]
        tabla_k.columns = [
            "Nº", t["categoria_kpi"], t["indicador"], t["meta"],
            t["ultimo_valor"], t["porcentaje_avance"], t["estado"],
        ]

        # Renderizamos a HTML para permitir el span de color en "Estado".
        # La cabecera y la cebra ya las pinta el CSS global (table thead th /
        # table tbody tr:nth-child(even) td en src/tema.py).
        html_tabla = tabla_k.to_html(escape=False, index=False, border=0)
        st.markdown(html_tabla, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# g) Últimos movimientos (lista, no tabla)
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_resumen_movimientos"):
    st.markdown(f"### {t['ultimos_movimientos']}")

    if df_mov.empty:
        st.caption(t["sin_movimientos"])
    else:
        _COLOR_ESTADO_HEX = {
            "Previsto":  "#8a9690",
            "En curso":  "#c87a1f",
            "Ejecutado": "#1f5f3a",
        }
        for _, m in df_mov.iterrows():
            estado_raw    = m.get("estado")
            estado_v      = "" if pd.isna(estado_raw) else str(estado_raw).strip()
            color_dot     = _COLOR_ESTADO_HEX.get(estado_v, "#8a9690")
            estado_txt    = etiq_estado.get(estado_v, estado_v) or "—"
            fecha_fmt     = _formato_fecha(m.get("fecha_corte"))
            etiqueta_raw  = m.get("etiqueta_corte")
            etiqueta      = "" if pd.isna(etiqueta_raw) else str(etiqueta_raw).strip()
            actuacion_raw = m.get("actuacion_nombre")
            actuacion     = "" if pd.isna(actuacion_raw) else str(actuacion_raw).strip()
            detalle_raw   = m.get("detalle")
            detalle       = "" if pd.isna(detalle_raw) else str(detalle_raw).strip()
            if len(detalle) > 200:
                detalle = detalle[:200] + "…"

            detalle_html = (
                f"<div style='margin-top:0.3rem; color:#1f2a26;'>"
                f"{html.escape(detalle)}</div>"
                if detalle else ""
            )

            st.markdown(
                f"""
                <div style="margin:0.4rem 0 0.6rem 0; padding:0.6rem 0.9rem;
                            border-left:3px solid {color_dot};
                            background:#f9faf9; border-radius:4px;">
                  <div style="font-weight:600; font-size:0.85rem;
                              color:#5a6a63;">
                    {html.escape(fecha_fmt)} · {html.escape(etiqueta)}
                  </div>
                  <div style="margin-top:0.2rem;">
                    <span style="color:{color_dot}; font-weight:700;">●</span>
                    <strong>{html.escape(actuacion)}</strong>
                    <span style="color:#5a6a63;"> — {html.escape(estado_txt)}</span>
                  </div>
                  {detalle_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
