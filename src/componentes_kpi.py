"""
Componentes reutilizables de Indicadores (KPI), de SOLO LECTURA:

  - selector_categoria_indicador(): los dos selectboxes canónicos (Tipo +
    Indicador) y devuelve el indicador seleccionado.
  - ficha_indicador(): ficha del indicador (categoría, unidad, definición, meta
    textual, desarrollo).
  - grafico_valores(): gráfico de evolución por año con línea de meta y métricas.

Los usan la página de edición `vistas/3_Indicadores.py` (que además añade sus
formularios de edición) y la pestaña de solo lectura de
`vistas/4_Resumen_del_Plan.py`, para no duplicar la lógica.

Estas funciones NO abren contenedores (`st.container`) ni usan `st.stop()`: el
llamador decide cómo envolverlas y cómo gestionar el caso "sin indicadores"
(devuelve None). Así son seguras dentro de `st.tabs` (un st.stop() rompería el
resto de pestañas).
"""
import pandas as pd
import plotly.express as px
import streamlit as st

import consultas
from i18n import traducir_categoria

# Orden fijo de categorías; el resto, alfabético al final.
_ORDEN_CATEGORIAS = ["Resultado / Impacto", "Ejecución", "Apoyo y seguimiento"]

# Años de la tabla estática de valores (espejo de ANIOS_KPI en
# vistas/3_Indicadores.py: los mismos años que muestra el formulario de edición).
ANIOS_KPI = [2025, 2026, 2027, 2028]


def _nombre(item, campo_es, campo_eu, idioma):
    """Texto en el idioma activo, con fallback al castellano."""
    if idioma == "eu" and item.get(campo_eu):
        return item[campo_eu]
    return item.get(campo_es, "") or ""


def ordenar_categorias(cats):
    """Categorías canónicas primero (en su orden fijo) y el resto alfabético."""
    en_orden = [c for c in _ORDEN_CATEGORIAS if c in cats]
    resto = sorted(c for c in cats if c not in _ORDEN_CATEGORIAS)
    return en_orden + resto


def etiqueta_indicador(ind, idioma):
    """«N. nombre» (sin categoría: ya está filtrada en el selector)."""
    num = ind.get("numero")
    num_txt = f"{num}." if num is not None else ""
    nombre = _nombre(ind, "nombre_es", "nombre_eu", idioma)
    return f"{num_txt} {nombre}".strip()


def selector_categoria_indicador(plan, t, idioma, key_prefix):
    """Pinta los selectboxes de Tipo (categoría) e Indicador.

    Patrón canónico: options=IDs estables (categoría = strings de BD), nombre
    traducido vía format_func, key estable que NO depende del label. El
    `key_prefix` evita que dos vistas (edición y solo lectura) compartan estado.

    Devuelve el dict del indicador seleccionado (consultas.obtener_indicador) o
    None si el plan no tiene indicadores (en cuyo caso muestra un st.info).
    """
    categorias_plan = ordenar_categorias(consultas.listar_categorias(plan["id"]))
    opciones_categoria = [None] + categorias_plan  # None = "Todas"
    categoria_sel = st.selectbox(
        t["tipo_indicador"],
        options=opciones_categoria,
        format_func=lambda c: t["todas"] if c is None else traducir_categoria(c, idioma),
        key=f"{key_prefix}_cat_{plan['id']}",
    )

    indicadores = consultas.listar_indicadores(plan["id"], categoria_sel)
    if not indicadores:
        st.info(t["sin_indicadores"])
        return None

    indicadores_por_id = {i["id"]: i for i in indicadores}
    ind_id = st.selectbox(
        t["selecciona_indicador"],
        options=[i["id"] for i in indicadores],
        format_func=lambda i: etiqueta_indicador(indicadores_por_id[i], idioma),
        key=f"{key_prefix}_ind_{plan['id']}_{categoria_sel or 'TODAS'}",
    )
    return consultas.obtener_indicador(ind_id)


def ficha_indicador(ind, t, idioma):
    """Ficha de SOLO LECTURA del indicador. No abre contenedor."""
    st.markdown(f"### {t['ficha_indicador']}")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown(f"**{t['categoria_kpi']}**")
        st.write(traducir_categoria(ind.get("categoria"), idioma) or "—")
        if ind.get("unidad"):
            st.markdown(f"**{t['unidad']}**")
            st.write(ind["unidad"])
    with c2:
        if ind.get("definicion_es") or ind.get("definicion_eu"):
            st.markdown(f"**{t['definicion']}**")
            st.write(_nombre(ind, "definicion_es", "definicion_eu", idioma))
        if ind.get("meta_es") or ind.get("meta_eu"):
            st.markdown(f"**{t['meta_texto']}**")
            st.write(_nombre(ind, "meta_es", "meta_eu", idioma))
        if ind.get("desarrollo_es") or ind.get("desarrollo_eu"):
            st.markdown(f"**{t['desarrollo']}**")
            st.write(_nombre(ind, "desarrollo_es", "desarrollo_eu", idioma))


def grafico_valores(ind, t):
    """Gráfico de evolución por año (px.bar) + línea de meta + métricas
    (último valor, % avance). SOLO LECTURA. No abre contenedor."""
    st.markdown(f"### {t['grafico_valores']}")

    valores_existentes = consultas.listar_valores_indicador(ind["id"])
    # Omitimos puntos cuyo valor no sea numérico (to_numeric -> NaN) o cuyo
    # periodo no sea un año, igual que en la página de edición.
    datos_num = []
    for v in valores_existentes:
        if not (v["periodo"] or "").isdigit():
            continue
        val = pd.to_numeric(v.get("valor"), errors="coerce")
        if pd.isna(val):
            continue
        datos_num.append((int(v["periodo"]), float(val)))
    datos_num.sort()

    if not datos_num:
        st.caption(t["sin_valores_numericos"])
        return

    df = pd.DataFrame(datos_num, columns=["anio", "valor"])
    eje_y = ind.get("unidad") or t["valor"]
    fig = px.bar(
        df, x="anio", y="valor",
        labels={"anio": t["anio"], "valor": eje_y},
        text_auto=True,
    )
    fig.update_traces(marker_color="#1f5f3a")
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

    ultimo_anio, ultimo_v = datos_num[-1]
    mc1, mc2 = st.columns(2)
    mc1.metric(f"{t['ultimo_valor']} ({ultimo_anio})", f"{ultimo_v:g}")
    if pd.notna(meta_v) and float(meta_v) != 0:
        pct = ultimo_v / float(meta_v) * 100
        mc2.metric(t["avance_vs_meta"], f"{pct:.1f} %")


def tabla_valores_solo_lectura(ind, t, idioma):
    """Tabla estática (no editable) "Valores por año" del indicador.

    Mismos años que el formulario de edición (ANIOS_KPI). La observación se
    sirve en el idioma activo con fallback, igual que la precarga del
    formulario: nota_es/nota_eu y, si falta, valor_texto_es/valor_texto_eu.
    Se omiten los años sin valor y sin observación (no se pintan filas vacías).
    No usa ningún input.
    """
    st.markdown(f"### {t['valores_por_anio']}")

    valores = consultas.listar_valores_indicador(ind["id"])
    por_periodo = {v["periodo"]: v for v in valores}

    filas = []
    for anio in ANIOS_KPI:
        actual = por_periodo.get(str(anio), {})
        valor_num = pd.to_numeric(actual.get("valor"), errors="coerce")
        valor_txt = f"{float(valor_num):g}" if pd.notna(valor_num) else ""
        obs = (
            _nombre(actual, "nota_es", "nota_eu", idioma)
            or _nombre(actual, "valor_texto_es", "valor_texto_eu", idioma)
            or ""
        )
        if not valor_txt and not obs:
            continue  # año sin valor y sin observación: no se pinta
        filas.append({
            t["anio"]: str(anio),
            t["valor"]: valor_txt or "—",
            t["observaciones"]: obs or "—",
        })

    if not filas:
        st.caption(t["sin_valores_numericos"])
        return
    st.table(pd.DataFrame(filas).style.hide(axis="index"))
