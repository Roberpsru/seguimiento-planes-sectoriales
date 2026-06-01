"""
Página de GESTIÓN DE ACTUACIONES (entrada de datos).

Flujo:
  1) Se elige Plan → Ámbito → Actuación.
  2) Se editan los campos básicos (estado, presupuesto ejecutado, fechas).
  3) Se ve el % ejecutado calculado.
  4) Se consulta y se amplía la bitácora de seguimientos.

Tras cualquier guardado se ejecuta st.cache_data.clear() para que la
visión general (app.py) refleje los cambios.
"""
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# Añadimos src/ al path para poder importar los módulos compartidos
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import consultas  # noqa: E402
from i18n import (  # noqa: E402
    ANIOS,
    ESTADOS,
    PERIODOS,
    asegurar_plan_id,
    etiqueta_desde_fecha,
    etiquetas_estado,
    etiquetas_periodo,
    plan_actual,
    selector_idioma,
    textos,
)
from tema import aplicar_tema  # noqa: E402


# --------------------------------------------------------------------------
# Helpers de fecha "periodo + año"
#
# Las fechas se guardan en la MISMA columna de texto del esquema
# (fecha_inicio_prevista / fecha_fin_prevista) con el formato canónico
# "<Periodo> <Año>", por ejemplo "1º semestre 2025". Aquí se ofrecen
# funciones para descomponer un texto existente en (periodo, año) y para
# recomponerlo a partir de los valores del formulario.
# --------------------------------------------------------------------------
_RE_ANIO_FINAL = re.compile(r"(20\d{2})\s*$")

# Variantes admitidas al leer el texto (tras pasar a minúsculas y aplastar
# espacios). El valor del diccionario es el periodo canónico que se mostrará
# en el desplegable.
_VARIANTES_PERIODO = {
    "1º semestre":        "1º semestre",
    "1er semestre":       "1º semestre",
    "1.º semestre":       "1º semestre",
    "primer semestre":    "1º semestre",
    "2º semestre":        "2º semestre",
    "2do semestre":       "2º semestre",
    "2.º semestre":       "2º semestre",
    "segundo semestre":   "2º semestre",
    "año completo":       "Año completo",
    "anio completo":      "Año completo",
}


def descomponer_fecha(texto):
    """
    A partir del texto guardado intenta extraer (periodo_canónico, año, texto_libre).

    Si el texto encaja en el patrón conocido, devuelve (periodo, año, None).
    Si no encaja (p. ej. "2025-2026"), devuelve ("", None, texto_original)
    para que la página pueda mostrarlo como referencia de solo lectura.
    """
    if not texto:
        return "", None, None
    t = texto.strip()
    m = _RE_ANIO_FINAL.search(t)
    if not m:
        return "", None, t
    anio = int(m.group(1))
    prefijo = t[:m.start()].strip().lower()
    periodo = _VARIANTES_PERIODO.get(prefijo)
    if periodo:
        return periodo, anio, None
    return "", None, t


def recomponer_fecha(periodo, anio):
    """Devuelve "<Periodo> <Año>" o None si falta cualquiera de los dos."""
    if periodo and anio:
        return f"{periodo} {anio}"
    return None

st.set_page_config(
    page_title="Gestión de actuaciones",
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
etiq_periodo = etiquetas_periodo(t)

st.title(t["gestion_actuaciones"])
if plan_id is not None:
    _p = plan_actual()
    _nombre_p = _p.get("nombre_eu") if idioma == "eu" and _p.get("nombre_eu") else _p.get("nombre_es", "")
    st.markdown(
        f"<div style='color:#666; font-size:0.85rem; margin:-0.5rem 0 1rem 0;'>"
        f"{t['plan_activo_etiqueta']}: {_nombre_p} "
        f"<span style='color:#999;'>({t['para_cambiar_portada']})</span></div>",
        unsafe_allow_html=True,
    )

# Mensaje "flash" que sobrevive a un st.rerun() (lo dejamos en session_state
# para que aparezca tras guardar y desaparezca al siguiente render).
if "flash_ok" in st.session_state:
    st.success(st.session_state.pop("flash_ok"))


def _nombre(item, campo_es, campo_eu):
    """Devuelve el nombre en el idioma activo, con fallback al castellano."""
    if idioma == "eu" and item.get(campo_eu):
        return item[campo_eu]
    return item.get(campo_es, "")


# --------------------------------------------------------------------------
# 1) Selección Ámbito → Actuación (tarjeta "Filtros").
#    El Plan se elige en la portada y vive en st.session_state["_plan_id_actual"].
# --------------------------------------------------------------------------
if plan_id is None:
    st.warning(t["sin_planes"])
    st.stop()
plan = plan_actual()

with st.container(border=True, key="bloque_filtros"):
    st.markdown(f"### {t['filtros']}")

    ambitos = consultas.listar_ambitos(plan["id"])
    if not ambitos:
        st.info(t["sin_ambitos"])
        st.stop()

    ambito = st.selectbox(
        t["selecciona_ambito"],
        options=ambitos,
        format_func=lambda a: f"{a.get('codigo') or ''} · "
                              f"{_nombre(a, 'nombre_es', 'nombre_eu')}".strip(" ·"),
    )

    actuaciones = consultas.listar_actuaciones(ambito["id"])
    if not actuaciones:
        st.info(t["sin_actuaciones"])
        st.stop()

    actuacion_sel = st.selectbox(
        t["selecciona_actuacion"],
        options=actuaciones,
        format_func=lambda ac: f"{ac.get('codigo') or ''} · "
                               f"{_nombre(ac, 'nombre_es', 'nombre_eu')}".strip(" ·"),
    )

# Lectura fresca de la actuación seleccionada (en cada rerun) para asegurarnos
# de mostrar los valores actuales tras posibles guardados.
actuacion = consultas.obtener_actuacion(actuacion_sel["id"])

# --------------------------------------------------------------------------
# 2) Datos de la actuación (tarjeta con formulario + tarjetas de presupuesto)
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_datos"):
    st.markdown(f"### {t['datos_actuacion']}")

    with st.form(key=f"form_actuacion_{actuacion['id']}"):
        # Si el estado actual no encaja con la lista canónica (datos heredados),
        # lo añadimos puntualmente para no perderlo al guardar.
        estado_actual = actuacion.get("estado") or "Previsto"
        opciones_estado = list(ESTADOS)
        if estado_actual not in opciones_estado:
            opciones_estado.append(estado_actual)

        estado = st.selectbox(
            t["estado"],
            options=opciones_estado,
            index=opciones_estado.index(estado_actual),
            format_func=lambda v: etiq_estado.get(v, v),
        )

        # Presupuesto ejecutado: number_input en €.
        # Coerción defensiva: si llega como cadena/Decimal/None desde la BD,
        # se trata como 0.0 sin romper (PostgreSQL puede servir otros tipos).
        _pe = pd.to_numeric(actuacion.get("presupuesto_ejecutado"), errors="coerce")
        valor_pe = float(_pe) if pd.notna(_pe) else 0.0
        presupuesto_ejecutado = st.number_input(
            t["presupuesto_ejecutado"],
            min_value=0.0,
            value=valor_pe,
            step=1000.0,
            format="%.2f",
        )

        # Fechas previstas: dos desplegables (Periodo + Año) por cada extremo.
        # Al guardar se recomponen como texto "<Periodo> <Año>" y se almacenan
        # en la MISMA columna del esquema (no se modifica la BD).
        def _render_fecha(label, valor_actual, prefijo_keys):
            """Pinta los desplegables de Periodo y Año y devuelve (periodo, anio)."""
            periodo_ini, anio_ini, texto_libre = descomponer_fecha(valor_actual)
            st.markdown(f"**{label}**")
            cp, ca = st.columns([2, 1])
            with cp:
                opciones_periodo = list(PERIODOS)
                # Si el periodo prefijado no estuviera en la lista canónica
                # (escenario improbable), lo añadimos al vuelo.
                if periodo_ini and periodo_ini not in opciones_periodo:
                    opciones_periodo.append(periodo_ini)
                periodo = st.selectbox(
                    t["periodo"],
                    options=opciones_periodo,
                    index=opciones_periodo.index(periodo_ini),
                    format_func=lambda v: etiq_periodo.get(v, v),
                    key=f"{prefijo_keys}_periodo",
                )
            with ca:
                opciones_anio = [None] + list(ANIOS)
                # Si el año actual cae fuera del rango aceptado, lo añadimos
                # también para no perderlo.
                if anio_ini and anio_ini not in opciones_anio:
                    opciones_anio.append(anio_ini)
                idx_anio = opciones_anio.index(anio_ini) if anio_ini in opciones_anio else 0
                anio = st.selectbox(
                    t["anio"],
                    options=opciones_anio,
                    index=idx_anio,
                    format_func=lambda v: "" if v is None else str(v),
                    key=f"{prefijo_keys}_anio",
                )
            # Si el texto original no encajaba en el patrón, lo mostramos como
            # referencia (solo lectura) y avisamos de que al guardar vacío se
            # perderá.
            if texto_libre:
                st.caption(
                    f"{t['fecha_no_parseable']}: «{texto_libre}». "
                    f"{t['fecha_sera_sobrescrita']}"
                )
            return periodo, anio

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            periodo_ini, anio_ini = _render_fecha(
                t["fecha_inicio"], actuacion.get("fecha_inicio_prevista"),
                prefijo_keys=f"ini_{actuacion['id']}",
            )
        with col_f2:
            periodo_fin, anio_fin = _render_fecha(
                t["fecha_fin"], actuacion.get("fecha_fin_prevista"),
                prefijo_keys=f"fin_{actuacion['id']}",
            )

        if st.form_submit_button(t["guardar_cambios"]):
            consultas.actualizar_actuacion(
                actuacion["id"],
                estado,
                presupuesto_ejecutado,
                recomponer_fecha(periodo_ini, anio_ini),
                recomponer_fecha(periodo_fin, anio_fin),
            )
            st.cache_data.clear()  # refresca la visión general
            st.session_state["flash_ok"] = t["guardado_ok"]
            st.rerun()

    # ----------------------------------------------------------------------
    # Presupuesto y % ejecutado (tarjetas de métrica)
    # ----------------------------------------------------------------------
    def _formato_euros(v):
        v = pd.to_numeric(v, errors="coerce")
        if pd.isna(v):
            return "—"
        return f"{float(v):,.0f} €".replace(",", ".")

    # Coerción defensiva de los importes que vienen de la BD.
    _presup = pd.to_numeric(actuacion.get("presupuesto"), errors="coerce")
    presupuesto = None if pd.isna(_presup) else float(_presup)
    _ejec = pd.to_numeric(actuacion.get("presupuesto_ejecutado"), errors="coerce")
    ejecutado = 0.0 if pd.isna(_ejec) else float(_ejec)

    col_a, col_b, col_c = st.columns(3)
    if presupuesto is not None:
        col_a.metric(t["presupuesto_actuacion"], _formato_euros(presupuesto))
        col_b.metric(t["presupuesto_ejecutado"], _formato_euros(ejecutado))
        if presupuesto > 0:
            porc = ejecutado / presupuesto * 100
            col_c.metric(t["porcentaje_ejecutado"], f"{porc:.1f} %")
        else:
            col_c.metric(t["porcentaje_ejecutado"], t["no_aplica"])
    else:
        # Sin dotación: mostramos la nota explicativa si la hay
        col_a.metric(
            t["presupuesto_actuacion"],
            actuacion.get("presupuesto_nota") or t["sin_dotacion"],
        )
        col_b.metric(t["presupuesto_ejecutado"], _formato_euros(ejecutado))

# --------------------------------------------------------------------------
# 3) Bitácora de seguimientos (tarjeta historial + formulario)
# --------------------------------------------------------------------------
with st.container(border=True, key="bloque_historial"):
    st.markdown(f"### {t['bitacora']}")
    st.caption(t["caption_bitacora"])

    seguimientos = consultas.listar_seguimientos(actuacion["id"])
    if not seguimientos:
        st.caption(t["sin_seguimientos"])
    else:
        for s in seguimientos:
            etiqueta = s.get("etiqueta_corte") or s.get("fecha_corte") or ""
            with st.expander(f"**{etiqueta}**"):
                if s.get("estado"):
                    st.write(f"**{t['estado']}:** {etiq_estado.get(s['estado'], s['estado'])}")
                if s.get("fecha_corte"):
                    st.caption(s["fecha_corte"])
                if s.get("detalle_es"):
                    st.write(s["detalle_es"])

    # Formulario para registrar una nueva anotación en el historial
    with st.form(key=f"form_seguim_{actuacion['id']}"):
        st.markdown(f"**{t['nuevo_seguimiento']}**")
        st.caption(t["caption_nuevo_seguim"])

        cs1, cs2 = st.columns([1, 2])
        with cs1:
            # Calendario con la fecha de hoy por defecto.
            fecha_revision = st.date_input(
                t["fecha_revision"],
                value=date.today(),
                format="DD/MM/YYYY",
                key=f"fecha_seg_{actuacion['id']}",
            )
        with cs2:
            estado_seg = st.selectbox(
                t["estado_en_esa_fecha"],
                options=ESTADOS,
                format_func=lambda v: etiq_estado.get(v, v),
                key=f"estado_seg_{actuacion['id']}",
            )

        detalle = st.text_area(t["detalle"])

        # Si está marcado, además de añadir la anotación al historial,
        # actualiza el campo 'estado' de la propia actuación.
        propagar_estado = st.checkbox(
            t["actualizar_estado_actual"],
            value=False,
            key=f"propagar_estado_{actuacion['id']}",
        )

        if st.form_submit_button(t["anadir"]):
            # fecha_corte en ISO (AAAA-MM-DD); etiqueta_corte se calcula
            # automáticamente como "MES AAAA" (siempre en castellano).
            fecha_iso = fecha_revision.isoformat()
            etiqueta_auto = etiqueta_desde_fecha(fecha_revision)
            consultas.anadir_seguimiento(
                actuacion["id"],
                fecha_iso,
                etiqueta_auto,
                estado_seg,
                (detalle or "").strip() or None,
            )
            if propagar_estado:
                consultas.actualizar_estado_actuacion(actuacion["id"], estado_seg)
            st.cache_data.clear()
            st.session_state["flash_ok"] = t["seguim_anadido"]
            st.rerun()
