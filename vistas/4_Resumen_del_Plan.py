"""
Página de RESUMEN DEL PLAN: vista ejecutiva consolidada en CUATRO pestañas
(st.tabs):

  a) "Cuadro resumen": cabecera (nombre, periodo, objetivo, última
     actualización), métricas globales, distribución por estado (donut +
     barras por ámbito), tabla "Resumen por ámbito" y tabla "Resumen de
     indicadores" con semáforo.
  b) "Cuadro de movimientos": el histórico de anotaciones desglosado en tres
     secciones por estado (Previsto / En curso / Ejecutado), con el mismo
     formato de tarjetas; tope por sección + aviso de cuántas quedan.
  c) "Cuadro de indicadores": réplica de SOLO LECTURA de la página Indicadores
     (selector + ficha + gráfico), reutilizando src/componentes_kpi.py.
  d) "Coordinación": tabla (st.dataframe) con todos los registros de
     coordinación del plan, con filtros (ámbito, actuación, rango de fechas,
     búsqueda de texto) y descarga a Excel de la tabla filtrada.

El router app.py aplica set_page_config / tema / selector de idioma; aquí se
lee el idioma con idioma_actual(). La exportación a PDF NO entra en esta fase.
"""
import html
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Hacer accesibles los módulos compartidos en src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import componentes_kpi as ckpi  # noqa: E402
import consultas  # noqa: E402
from i18n import (  # noqa: E402
    ESTADOS,
    asegurar_plan_id,
    etiquetas_estado,
    idioma_actual,
    plan_actual,
    textos,
    traducir_categoria,
)

# Tope de tarjetas visibles por sección en "Cuadro de movimientos".
TOPE_MOVS = 25

# Colores del semáforo de estado (clave = valor de BD).
_COLOR_ESTADO_HEX = {
    "Previsto":  "#8a9690",
    "En curso":  "#c87a1f",
    "Ejecutado": "#1f5f3a",
}

# --------------------------------------------------------------------------
# Idioma y textos (el selector global vive en el router app.py)
# --------------------------------------------------------------------------
idioma = idioma_actual()
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
    """Formato '1.234.567 €'; '—' si el valor es nulo, NaN o no numérico."""
    v = pd.to_numeric(v, errors="coerce")
    if pd.isna(v):
        return "—"
    return f"{float(v):,.0f} €".replace(",", ".")


def _formato_fecha(fecha_iso):
    """Convierte 'YYYY-MM-DD' en 'DD/MM/YYYY' o devuelve el texto crudo."""
    if not fecha_iso:
        return "—"
    try:
        return datetime.strptime(str(fecha_iso)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(fecha_iso)


@st.cache_data
def _cargar(plan_id, idioma):
    """Carga los agregados del cuadro resumen (pestaña a).

    `idioma` forma parte de la CLAVE DE CACHÉ: resumen_por_ambito y
    resumen_indicadores construyen SQL bilingüe leyendo el idioma activo. Los
    movimientos y las coordinaciones se cargan por separado en sus pestañas.
    """
    return (
        consultas.resumen_actuaciones(plan_id),
        consultas.resumen_por_ambito(plan_id),
        consultas.resumen_indicadores(plan_id),
    )


# --------------------------------------------------------------------------
# Plan activo (el selector vive en la portada — global a la app).
# --------------------------------------------------------------------------
if plan_id is None:
    st.warning(t["sin_planes"])
    st.stop()
plan = plan_actual()

resumen, df_ambito, df_kpi = _cargar(plan["id"], idioma)

tab_cuadro, tab_mov, tab_ind, tab_coord = st.tabs([
    t["resumen_tab_cuadro"],
    t["resumen_tab_movimientos"],
    t["resumen_tab_indicadores"],
    t["resumen_tab_coordinacion"],
])


# ==========================================================================
# Pestaña a) Cuadro resumen
# ==========================================================================
with tab_cuadro:
    # ---- Cabecera: nombre + periodo + objetivo + última actualización ----
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

        objetivo = _nombre(plan, "descripcion_es", "descripcion_eu")
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

    # ---- Resumen: dos filas de métricas + caption ----
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
            p2.metric(t["presupuesto_ejecutado"], _formato_euros(pe), delta=f"{pct_global:.1f} %")
        else:
            p2.metric(t["presupuesto_ejecutado"], _formato_euros(pe))

        st.caption(
            f"{t['indicadores']}: {len(df_kpi)} · "
            f"{t['sin_dotacion']}: {resumen['sin_dotacion']}"
        )

    # ---- Distribución por estado: donut + barras por ámbito ----
    with st.container(border=True, key="bloque_resumen_estado"):
        st.markdown(f"### {t['distribucion_estado']}")

        col_d, col_b = st.columns([1, 1.2])
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
                    height=320, margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(color="#1f2a26", size=13),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15),
                )
                st.plotly_chart(fig_d, use_container_width=True)
            else:
                st.caption("—")

        with col_b:
            st.markdown(f"**{t['avance_presupuestario_ambito']}**")
            hay_presupuesto = False
            if not df_ambito.empty:
                _suma_pres = pd.to_numeric(
                    df_ambito[["presupuesto_comprometido", "presupuesto_ejecutado"]].stack(),
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
                    height=320, margin=dict(l=0, r=0, t=10, b=0),
                    xaxis_title="€", yaxis_title="",
                    font=dict(color="#1f2a26", size=13),
                    yaxis=dict(tickfont=dict(color="#1f2a26", size=13)),
                    xaxis=dict(tickfont=dict(color="#1f2a26", size=12)),
                    legend=dict(title_text="", orientation="h", yanchor="bottom", y=-0.2),
                )
                st.plotly_chart(fig_b, use_container_width=True)

    # ---- Resumen por ámbito (tabla) ----
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
                lambda r: f"{r['ambito_codigo'] or ''} · {r['ambito_nombre']}".strip(" ·"),
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

    # ---- Resumen de indicadores (tabla con semáforo) ----
    with st.container(border=True, key="bloque_resumen_kpi"):
        st.markdown(f"### {t['resumen_indicadores']}")

        if df_kpi.empty:
            st.caption(t["sin_indicadores"])
        else:
            tabla_k = df_kpi.copy()

            def _ultimo(row):
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

            tabla_k["ult_str"]     = tabla_k.apply(_ultimo, axis=1)
            tabla_k["pct_str"]     = tabla_k["porcentaje_avance"].map(_pct_kpi)
            tabla_k["estado_html"] = tabla_k["porcentaje_avance"].map(_semaforo)
            tabla_k["meta_txt"]    = tabla_k["meta_texto"].fillna("—").replace("", "—")
            tabla_k["categoria_x"] = (tabla_k["categoria"]
                                      .map(lambda c: traducir_categoria(c, idioma))
                                      .fillna("—").replace("", "—"))
            tabla_k["numero_x"]    = tabla_k["numero"].fillna("—")

            cols_k = ["numero_x", "categoria_x", "nombre", "meta_txt",
                      "ult_str", "pct_str", "estado_html"]
            tabla_k = tabla_k[cols_k]
            tabla_k.columns = [
                "Nº", t["categoria_kpi"], t["indicador"], t["meta"],
                t["ultimo_valor"], t["porcentaje_avance"], t["estado"],
            ]
            html_tabla = tabla_k.to_html(escape=False, index=False, border=0)
            st.markdown(html_tabla, unsafe_allow_html=True)


# ==========================================================================
# Pestaña b) Cuadro de movimientos (por estado de la anotación)
# ==========================================================================
def _render_movimiento(m):
    """Tarjeta de un movimiento (mismo formato visual que antes)."""
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
        f"<div style='margin-top:0.3rem; color:#1f2a26;'>{html.escape(detalle)}</div>"
        if detalle else ""
    )
    st.markdown(
        f"""
        <div style="margin:0.4rem 0 0.6rem 0; padding:0.6rem 0.9rem;
                    border-left:3px solid {color_dot};
                    background:#f9faf9; border-radius:4px;">
          <div style="font-weight:600; font-size:0.85rem; color:#5a6a63;">
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


def _seccion_movimientos(titulo, sub, key):
    """Pinta una sección (un estado) con tope TOPE_MOVS y aviso de resto."""
    with st.container(border=True, key=key):
        st.markdown(f"### {titulo}")
        if sub.empty:
            st.caption(t["sin_movimientos"])
            return
        for _, m in sub.head(TOPE_MOVS).iterrows():
            _render_movimiento(m)
        if len(sub) > TOPE_MOVS:
            st.caption(t["movs_mas"].format(n=len(sub) - TOPE_MOVS))


with tab_mov:
    df_mov = consultas.listar_movimientos(plan["id"], idioma)
    if df_mov.empty:
        st.caption(t["sin_movimientos"])
    else:
        # Tres secciones canónicas en orden Previsto -> En curso -> Ejecutado.
        for estado_bd in ESTADOS:
            sub = df_mov[df_mov["estado"] == estado_bd]
            slug = estado_bd.replace(" ", "").lower()
            _seccion_movimientos(etiq_estado.get(estado_bd, estado_bd), sub,
                                 key=f"bloque_mov_{slug}")
        # "Otros": anotaciones con estado NULL o fuera de las tres canónicas.
        sub_otros = df_mov[~df_mov["estado"].isin(ESTADOS)]
        if not sub_otros.empty:
            _seccion_movimientos(t["mov_otros"], sub_otros, key="bloque_mov_otros")


# ==========================================================================
# Pestaña c) Cuadro de indicadores (SOLO LECTURA, reutiliza componentes_kpi)
# ==========================================================================
with tab_ind:
    st.caption(t["resumen_kpi_solo_lectura"])
    with st.container(border=True, key="bloque_resumen_kpi_filtros"):
        st.markdown(f"### {t['filtros']}")
        ind = ckpi.selector_categoria_indicador(plan, t, idioma, key_prefix="resumen_kpi")
    if ind is not None:
        with st.container(border=True, key="bloque_resumen_kpi_ficha"):
            ckpi.ficha_indicador(ind, t, idioma)
        with st.container(border=True, key="bloque_resumen_kpi_valores"):
            ckpi.tabla_valores_solo_lectura(ind, t, idioma)
        with st.container(border=True, key="bloque_resumen_kpi_grafico"):
            ckpi.grafico_valores(ind, t)


# ==========================================================================
# Pestaña d) Coordinación (tabla filtrable + descarga Excel)
# ==========================================================================
with tab_coord:
    df_c = consultas.listar_coordinaciones(plan["id"], idioma)

    with st.container(border=True, key="bloque_coord_filtros"):
        st.markdown(f"### {t['filtros']}")

        ambitos = consultas.listar_ambitos(plan["id"])
        amb_por_id = {a["id"]: a for a in ambitos}

        cf1, cf2 = st.columns(2)
        with cf1:
            amb_sel = st.selectbox(
                t["selecciona_ambito"],
                options=[None] + [a["id"] for a in ambitos],
                format_func=lambda i: t["coord_todos"] if i is None else
                    f"{amb_por_id[i].get('codigo') or ''} · "
                    f"{_nombre(amb_por_id[i], 'nombre_es', 'nombre_eu')}".strip(" ·"),
                key=f"coord_filt_amb_{plan['id']}",
            )
        with cf2:
            if amb_sel is not None:
                acts = consultas.listar_actuaciones(amb_sel)
                act_por_id = {a["id"]: a for a in acts}
                act_sel = st.selectbox(
                    t["selecciona_actuacion"],
                    options=[None] + [a["id"] for a in acts],
                    format_func=lambda i: t["coord_todos"] if i is None else
                        f"{act_por_id[i].get('codigo') or ''} · "
                        f"{_nombre(act_por_id[i], 'nombre_es', 'nombre_eu')}".strip(" ·"),
                    key=f"coord_filt_act_{plan['id']}_{amb_sel}",
                )
            else:
                act_sel = None

        cf3, cf4 = st.columns(2)
        with cf3:
            f_desde = st.date_input(
                t["coord_fecha_desde"], value=None, format="DD/MM/YYYY",
                key=f"coord_filt_desde_{plan['id']}",
            )
        with cf4:
            f_hasta = st.date_input(
                t["coord_fecha_hasta"], value=None, format="DD/MM/YYYY",
                key=f"coord_filt_hasta_{plan['id']}",
            )
        texto = st.text_input(t["coord_buscar"], key=f"coord_filt_txt_{plan['id']}")

    # ---- Aplicar filtros sobre el DataFrame ----
    df_f = df_c.copy()
    if not df_f.empty:
        if amb_sel is not None:
            df_f = df_f[df_f["ambito_id"] == amb_sel]
        if act_sel is not None:
            df_f = df_f[df_f["actuacion_id"] == act_sel]
        if f_desde is not None:
            df_f = df_f[df_f["fecha"] >= f_desde.isoformat()]
        if f_hasta is not None:
            df_f = df_f[df_f["fecha"] <= f_hasta.isoformat()]
        if texto and texto.strip():
            tl = texto.strip().lower()

            def _match(r):
                for c in ("encargo", "gestor", "resultado"):
                    val = r.get(c)
                    if pd.notna(val) and tl in str(val).lower():
                        return True
                return False

            df_f = df_f[df_f.apply(_match, axis=1)]

    with st.container(border=True, key="bloque_coord_tabla"):
        st.markdown(f"### {t['coord_registros_titulo']}")
        if df_f.empty:
            st.caption(t["coord_sin_registros"])
        else:
            vista = df_f.copy()
            vista["fecha"] = vista["fecha"].map(_formato_fecha)
            vista["ambito"] = vista.apply(
                lambda r: f"{r['ambito_codigo'] or ''} · {r['ambito_nombre'] or ''}".strip(" ·"),
                axis=1,
            )
            vista["actuacion"] = vista.apply(
                lambda r: f"{r['act_codigo'] or ''} · {r['actuacion_nombre'] or ''}".strip(" ·"),
                axis=1,
            )
            for c in ("encargo", "gestor", "resultado"):
                vista[c] = vista[c].fillna("—").replace("", "—")
            vista = vista[["fecha", "ambito", "actuacion", "encargo", "gestor", "resultado"]]
            vista.columns = [
                t["coord_fecha"], t["coord_col_ambito"], t["coord_col_actuacion"],
                t["coord_encargo"], t["coord_gestor"], t["coord_resultado"],
            ]
            # st.dataframe: scroll propio y ordenación por columna.
            st.dataframe(vista, use_container_width=True, hide_index=True)

            # Descarga de la tabla FILTRADA como Excel.
            buf = BytesIO()
            vista.to_excel(buf, index=False, engine="openpyxl")
            codigo_plan = plan.get("codigo") or "PLAN"
            st.download_button(
                t["coord_descargar"],
                data=buf.getvalue(),
                file_name=f"Coordinacion_{codigo_plan}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
