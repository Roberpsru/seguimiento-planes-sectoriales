"""
Página de SEGUIMIENTO DE INDICADORES (KPI) — edición.

Permite:
  1) Consultar la ficha del indicador (categoría, definición, meta textual,
     desarrollo y unidad).
  2) Editar la meta numérica (meta_valor) para usarla como línea de objetivo.
  3) Registrar valores por año (2025-2028) con observaciones.
  4) Visualizar la evolución por año respecto a la meta.

El selector de Tipo→Indicador, la ficha y el gráfico viven en
`src/componentes_kpi.py` (solo lectura) y se comparten con la pestaña
"Cuadro de indicadores" de Resumen del Plan. Esta página AÑADE los dos
formularios de edición (meta numérica y valores anuales).

Patrón común con el resto de páginas: idioma activo (idioma_actual()), mensaje
flash que sobrevive a st.rerun() y st.cache_data.clear() tras cada guardado.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Hacer accesibles los módulos compartidos en src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import componentes_kpi as ckpi  # noqa: E402
import consultas  # noqa: E402
from i18n import (  # noqa: E402
    asegurar_plan_id,
    idioma_actual,
    plan_actual,
    textos,
)

# Años de recogida de valores fijados por especificación.
# El "periodo" en la BD es un TEXT libre; aquí usamos el año como string.
ANIOS_KPI = [2025, 2026, 2027, 2028]


# --------------------------------------------------------------------------
# Idioma y textos
# --------------------------------------------------------------------------
idioma = idioma_actual()
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
    ind = ckpi.selector_categoria_indicador(plan, t, idioma, key_prefix="kpi")

if ind is None:
    # El plan no tiene indicadores (el selector ya mostró el aviso).
    st.stop()

# --------------------------------------------------------------------------
# 2) Ficha del indicador (solo lectura) + edición de la meta numérica
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_ficha"):
    ckpi.ficha_indicador(ind, t, idioma)

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
# 3) Valores por año (edición) + visualización (gráfico de solo lectura)
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
    # Visualización (gráfico + métricas) — lógica compartida, solo lectura.
    # ----------------------------------------------------------------------
    ckpi.grafico_valores(ind, t)
