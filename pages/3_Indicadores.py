"""
Página de SEGUIMIENTO DE INDICADORES (KPI).

Permite:
  1) Consultar la ficha del indicador (categoría, definición, meta textual,
     desarrollo y unidad).
  2) Editar la meta numérica (meta_valor) para usarla como línea de
     objetivo en los gráficos.
  3) Registrar valores por año (2025-2028) con observaciones.
  4) Visualizar la evolución por año respecto a la meta.

Sigue el mismo patrón que pages/1_Gestion_actuaciones.py:
  - selector de idioma compartido (st.session_state["idioma"])
  - mensaje flash que sobrevive a st.rerun()
  - st.cache_data.clear() tras cada guardado
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Hacer accesibles los módulos compartidos en src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import consultas  # noqa: E402
from i18n import asegurar_plan_id, plan_actual, selector_idioma, textos  # noqa: E402
from tema import aplicar_tema  # noqa: E402

st.set_page_config(
    page_title="Indicadores (KPI)",
    layout="wide",
)
aplicar_tema()

# Años de recogida de valores fijados por especificación.
# El "periodo" en la BD es un TEXT libre; aquí usamos el año como string.
ANIOS_KPI = [2025, 2026, 2027, 2028]


# --------------------------------------------------------------------------
# Idioma y textos
# --------------------------------------------------------------------------
idioma = selector_idioma()
t = textos(idioma)
plan_id = asegurar_plan_id()

st.title(t["indicadores_kpi"])
if plan_id is not None:
    _p = plan_actual()
    _nombre_p = _p.get("nombre_eu") if idioma == "eu" and _p.get("nombre_eu") else _p.get("nombre_es", "")
    st.markdown(
        f"<div style='color:#666; font-size:0.85rem; margin:-0.5rem 0 1rem 0;'>"
        f"{t['plan_activo_etiqueta']}: {_nombre_p} "
        f"<span style='color:#999;'>({t['para_cambiar_portada']})</span></div>",
        unsafe_allow_html=True,
    )

# Flash de éxito tras guardar (sobrevive a st.rerun)
if "flash_ok" in st.session_state:
    st.success(st.session_state.pop("flash_ok"))


def _nombre(item, campo_es, campo_eu):
    """Devuelve el nombre en el idioma activo, con fallback al castellano."""
    if idioma == "eu" and item.get(campo_eu):
        return item[campo_eu]
    return item.get(campo_es, "") or ""


# Filtro por tipo (categoría). Orden fijo solicitado y, después,
# cualquier categoría no prevista por orden alfabético.
_ORDEN_CATEGORIAS = ["Resultado / Impacto", "Ejecución", "Apoyo y seguimiento"]


def _ordenar_categorias(cats):
    """Coloca primero las categorías canónicas (en su orden fijo) y al final
    cualquier otra encontrada, alfabéticamente."""
    en_orden = [c for c in _ORDEN_CATEGORIAS if c in cats]
    resto = sorted(c for c in cats if c not in _ORDEN_CATEGORIAS)
    return en_orden + resto


def _etiqueta_indicador(ind):
    """Devuelve «N. nombre» (sin categoría: ya está filtrada arriba)."""
    num = ind.get("numero")
    num_txt = f"{num}." if num is not None else ""
    nombre = _nombre(ind, "nombre_es", "nombre_eu")
    return f"{num_txt} {nombre}".strip()


# --------------------------------------------------------------------------
# 1) Selección Tipo → Indicador (tarjeta "Filtros").
#    El Plan se elige en la portada y vive en st.session_state["_plan_id_actual"].
# --------------------------------------------------------------------------
if plan_id is None:
    st.warning(t["sin_planes"])
    st.stop()
plan = plan_actual()

with st.container(border=True, key="bloque_filtros_kpi"):
    st.markdown(f"### {t['filtros']}")

    categorias_plan = _ordenar_categorias(consultas.listar_categorias(plan["id"]))
    # None = "Todas" (sin filtro)
    opciones_categoria = [None] + categorias_plan

    # Clave dependiente del plan: al cambiar de plan, el widget se reinicia a
    # "Todas" en vez de quedarse pillado con una categoría del plan anterior.
    categoria_sel = st.selectbox(
        t["tipo_indicador"],
        options=opciones_categoria,
        format_func=lambda c: t["todas"] if c is None else c,
        key=f"cat_kpi_{plan['id']}",
    )

    indicadores = consultas.listar_indicadores(plan["id"], categoria_sel)
    if not indicadores:
        st.info(t["sin_indicadores"])
        st.stop()

    # Clave dependiente del plan y de la categoría: al cambiar cualquiera de
    # los dos filtros de arriba, el selector de indicador se reinicia al
    # primero de la nueva lista (no se queda en una selección anterior que
    # podría no estar ya disponible).
    ind_sel = st.selectbox(
        t["selecciona_indicador"],
        options=indicadores,
        format_func=_etiqueta_indicador,
        key=f"ind_kpi_{plan['id']}_{categoria_sel or 'TODAS'}",
    )

# Relectura tras posibles guardados (para que la ficha refleje meta_valor
# actualizada sin esperar a un cambio de plan).
ind = consultas.obtener_indicador(ind_sel["id"])

# --------------------------------------------------------------------------
# 2) Ficha del indicador (tarjeta: lectura + edición de meta numérica)
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_ficha"):
    st.markdown(f"### {t['ficha_indicador']}")

    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown(f"**{t['categoria_kpi']}**")
        st.write(ind.get("categoria") or "—")
        if ind.get("unidad"):
            st.markdown(f"**{t['unidad']}**")
            st.write(ind["unidad"])
    with c2:
        if ind.get("definicion_es") or ind.get("definicion_eu"):
            st.markdown(f"**{t['definicion']}**")
            st.write(_nombre(ind, "definicion_es", "definicion_eu"))
        if ind.get("meta_es") or ind.get("meta_eu"):
            st.markdown(f"**{t['meta_texto']}**")
            st.write(_nombre(ind, "meta_es", "meta_eu"))
        if ind.get("desarrollo_es") or ind.get("desarrollo_eu"):
            st.markdown(f"**{t['desarrollo']}**")
            st.write(_nombre(ind, "desarrollo_es", "desarrollo_eu"))

    # Edición de la meta numérica (formulario independiente para guardar solo eso)
    with st.form(key=f"form_meta_{ind['id']}"):
        st.caption(t["caption_kpi_meta"])
        # to_numeric(coerce): si meta_valor llega como cadena no numérica
        # (p. ej. servido por PostgreSQL) -> NaN, y el input queda vacío.
        meta_actual = pd.to_numeric(ind.get("meta_valor"), errors="coerce")
        cm1, cm2 = st.columns([1, 3])
        with cm1:
            nueva_meta = st.number_input(
                t["meta_valor"],
                value=float(meta_actual) if pd.notna(meta_actual) else None,
                step=0.01,
                format="%g",
                key=f"meta_input_{ind['id']}",
            )
        if st.form_submit_button(t["guardar_meta"]):
            consultas.actualizar_meta_valor(ind["id"], nueva_meta)
            st.cache_data.clear()
            st.session_state["flash_ok"] = t["meta_guardada"]
            st.rerun()

# --------------------------------------------------------------------------
# 3) Valores por año + visualización (tarjeta única: formulario y gráfico)
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_valores"):
    st.markdown(f"### {t['valores_por_anio']}")
    st.caption(t["caption_kpi_valor"])

    valores_existentes = consultas.listar_valores_indicador(ind["id"])
    # Indexamos por periodo (texto). Para los años usaremos "2025", "2026", ...
    por_periodo = {v["periodo"]: v for v in valores_existentes}

    with st.form(key=f"form_valores_{ind['id']}"):
        # Cabecera de columnas
        h1, h2, h3 = st.columns([1, 2, 4])
        h1.markdown(f"**{t['anio']}**")
        h2.markdown(f"**{t['valor']}**")
        h3.markdown(f"**{t['observaciones']}**")

        entradas = {}
        for anio in ANIOS_KPI:
            periodo = str(anio)
            actual = por_periodo.get(periodo, {})
            cy, cv, co = st.columns([1, 2, 4])
            with cy:
                st.markdown(f"### {anio}")
            with cv:
                valor_actual = pd.to_numeric(actual.get("valor"), errors="coerce")
                v = st.number_input(
                    f"{t['valor']} {anio}",
                    value=float(valor_actual) if pd.notna(valor_actual) else None,
                    step=0.01,
                    format="%g",
                    label_visibility="collapsed",
                    key=f"v_{ind['id']}_{anio}",
                )
            with co:
                # Precarga en el idioma activo (con fallback al castellano si el
                # _eu está vacío). Si no hay nota pero sí texto descriptivo
                # (valor_texto), lo usamos para que el usuario pueda revisarlo /
                # completarlo sin perder el dato.
                nota_inicial = (
                    _nombre(actual, "nota_es", "nota_eu")
                    or _nombre(actual, "valor_texto_es", "valor_texto_eu")
                    or ""
                )
                n = st.text_area(
                    f"{t['observaciones']} {anio}",
                    value=nota_inicial,
                    height=70,
                    label_visibility="collapsed",
                    key=f"n_{ind['id']}_{anio}",
                )
            entradas[periodo] = (v, n)

        if st.form_submit_button(t["guardar_valores"]):
            for periodo, (v, n) in entradas.items():
                nota = (n or "").strip() or None
                # Evitamos crear filas vacías (None/None) cuando no había nada
                # previo: así no ensuciamos la BD con basura.
                if v is None and nota is None and periodo not in por_periodo:
                    continue
                consultas.guardar_valor_indicador(ind["id"], periodo, v, nota)
            st.cache_data.clear()
            st.session_state["flash_ok"] = t["valores_guardados"]
            st.rerun()

    # ----------------------------------------------------------------------
    # Visualización: gráfico + métricas resumen
    # ----------------------------------------------------------------------
    st.markdown(f"### {t['grafico_valores']}")

    # Releemos por si acaba de haber un guardado en este mismo rerun.
    valores_existentes = consultas.listar_valores_indicador(ind["id"])
    # Omitimos puntos cuyo valor no sea numérico (to_numeric -> NaN), igual que
    # en el resto de la app, para no romper el gráfico con cadenas tipo 'N/D'.
    datos_num = []
    for v in valores_existentes:
        if not (v["periodo"] or "").isdigit():
            continue
        val = pd.to_numeric(v.get("valor"), errors="coerce")
        if pd.isna(val):
            continue
        datos_num.append((int(v["periodo"]), float(val)))
    datos_num.sort()

    if datos_num:
        df = pd.DataFrame(datos_num, columns=["anio", "valor"])
        eje_y = ind.get("unidad") or t["valor"]
        fig = px.bar(
            df, x="anio", y="valor",
            labels={"anio": t["anio"], "valor": eje_y},
            text_auto=True,
        )
        fig.update_traces(marker_color="#1f5f3a")
        # Coerción defensiva: meta_valor puede llegar no numérico desde la BD.
        meta_v = pd.to_numeric(ind.get("meta_valor"), errors="coerce")
        if pd.notna(meta_v):
            fig.add_hline(
                y=float(meta_v),
                line_dash="dash",
                annotation_text=f"{t['linea_meta']}: {float(meta_v):g}",
                annotation_position="top right",
            )
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            font=dict(color="#1f2a26", size=13),
            xaxis=dict(
                tickmode="array",
                tickvals=[d[0] for d in datos_num],
                tickfont=dict(color="#1f2a26", size=12),
            ),
            yaxis=dict(tickfont=dict(color="#1f2a26", size=13)),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Métricas: último valor + % de avance vs meta (si la hay)
        ultimo_anio, ultimo_v = datos_num[-1]
        mc1, mc2 = st.columns(2)
        mc1.metric(f"{t['ultimo_valor']} ({ultimo_anio})", f"{ultimo_v:g}")
        if pd.notna(meta_v) and float(meta_v) != 0:
            pct = ultimo_v / float(meta_v) * 100
            mc2.metric(t["avance_vs_meta"], f"{pct:.1f} %")
    else:
        st.caption(t["sin_valores_numericos"])
