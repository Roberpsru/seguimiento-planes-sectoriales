"""
Página de ADMINISTRACIÓN: dos pestañas (st.tabs).

  1. "Carga y descarga de Planes": descargar el plan activo como Excel y subir
     un Excel para crear/reemplazar un plan. Lógica en src/importador.py.
     (Contenido previo de la página, sin cambios funcionales.)
  2. "Coordinación": alta y listado de los registros de la tabla `coordinaciones`
     del plan activo (diario de coordinación por actuación; datos bilingües
     es/eu mostrados en el idioma activo con fallback).

El selector de Plan vive en la portada (común a toda la app). El idioma lo fija
el router app.py; aquí se lee con idioma_actual().
"""
import sys
from datetime import date, datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import acceso  # noqa: E402
import consultas  # noqa: E402
import importador  # noqa: E402
from i18n import asegurar_plan_id, idioma_actual, plan_actual, textos  # noqa: E402

idioma = idioma_actual()
t = textos(idioma)
acceso.requiere_clave(t)  # barrera de edición: corta aquí si no está autorizado
plan_id = asegurar_plan_id()

# Administración debe poder usarse con la BD vacía (es donde se carga el primer
# plan): por eso NO hacemos st.stop() si no hay plan.
plan_activo = plan_actual() if plan_id is not None else None
hay_planes = plan_activo is not None

st.title(t["administracion"])
if hay_planes:
    _nombre_p = (
        plan_activo.get("nombre_eu")
        if idioma == "eu" and plan_activo.get("nombre_eu")
        else plan_activo.get("nombre_es", "")
    )
    st.markdown(
        f"<div style='color:#666; font-size:0.85rem; margin:-0.5rem 0 1rem 0;'>"
        f"{t['plan_activo_etiqueta']}: {_nombre_p} "
        f"<span style='color:#999;'>({t['para_cambiar_portada']})</span></div>",
        unsafe_allow_html=True,
    )

# Flash que sobrevive a st.rerun() (alta de coordinación).
if "flash_ok" in st.session_state:
    st.success(st.session_state.pop("flash_ok"))


def _nombre(item, campo_es, campo_eu):
    """Nombre en el idioma activo, con fallback al castellano."""
    if idioma == "eu" and item.get(campo_eu):
        return item[campo_eu]
    return item.get(campo_es, "") or ""


def _formato_fecha(fecha_iso):
    """'AAAA-MM-DD' -> 'DD/MM/YYYY'; o el texto crudo si no parsea."""
    if not fecha_iso:
        return "—"
    try:
        return datetime.strptime(str(fecha_iso)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(fecha_iso)


tab_carga, tab_coord = st.tabs([t["admin_tab_carga"], t["admin_tab_coordinacion"]])


# ==========================================================================
# Pestaña 1 — Carga y descarga de Planes (contenido previo, sin cambios)
# ==========================================================================
with tab_carga:
    if not hay_planes:
        st.info(t["admin_bd_vacia"])

    # ---- Descargar plan actual (solo si hay planes en la BD) ----
    if hay_planes:
        with st.container(border=True, key="bloque_admin_descargar"):
            st.markdown(f"### {t['admin_descargar_titulo']}")
            st.write(t["admin_descargar_desc"])

            codigo_plan = plan_activo["codigo"] or "PLAN"
            bytes_excel = importador.exportar_plan_a_excel(plan_activo["id"])

            st.download_button(
                label=t["admin_descargar_boton"].format(codigo=codigo_plan),
                data=bytes_excel,
                file_name=f"Plan_Sectorial_{codigo_plan}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )

    # ---- Subir Excel para añadir o reemplazar plan ----
    # Contador en session_state para forzar el reset del file_uploader tras cada
    # operación (cambia la key del widget y Streamlit lo reinstancia).
    if "_admin_uploader_key" not in st.session_state:
        st.session_state["_admin_uploader_key"] = 0

    def _reset_uploader():
        st.session_state["_admin_uploader_key"] += 1

    with st.container(border=True, key="bloque_admin_subir"):
        st.markdown(f"### {t['admin_subir_titulo']}")
        st.write(t["admin_subir_desc"])

        archivo = st.file_uploader(
            t["admin_subir_label"],
            type=["xlsx"],
            key=f"admin_uploader_{st.session_state['_admin_uploader_key']}",
        )

        if archivo is not None:
            contenido = archivo.getvalue()

            # Validación previa (dry_run): no toca la BD.
            preview = importador.cargar_plan_desde_excel(contenido, dry_run=True)

            if preview["incidencias"]:
                st.error(t["admin_incidencias"])
                with st.expander(t["admin_ver_incidencias"], expanded=True):
                    for inc in preview["incidencias"]:
                        st.write(f"- {inc}")
            else:
                r = preview["resumen"]
                st.success(
                    t["admin_preview"].format(
                        codigo=preview["plan_codigo"],
                        nombre=preview["plan_nombre"],
                        ambitos=r["ambitos"],
                        actuaciones=r["actuaciones"],
                        indicadores=r["indicadores"],
                        valores=r["valores"],
                        seguimientos=r["seguimientos"],
                    )
                )

                if not preview["plan_existia_antes"]:
                    st.info(t["admin_plan_nuevo"])
                    if st.button(
                        t["admin_crear_plan"], type="primary", key="btn_admin_crear",
                    ):
                        resultado = importador.cargar_plan_desde_excel(
                            contenido, reemplazar=False, dry_run=False,
                        )
                        if resultado["ok"]:
                            # Flash que sobrevive al rerun (antes el st.success se
                            # perdía al rerun inmediato).
                            st.session_state["flash_ok"] = (
                                resultado["mensaje"] + " " + t["admin_refrescar_otras"]
                            )
                            _reset_uploader()
                            st.rerun()
                        else:
                            st.error(t["admin_error_carga"])
                            st.write(resultado["mensaje"])
                else:
                    impacto = preview["afectado_si_reemplaza"] or {}
                    st.warning(
                        t["admin_plan_existe_aviso"].format(
                            actuaciones=impacto.get("actuaciones", 0),
                            seguimientos=impacto.get("seguimientos", 0),
                            indicadores=impacto.get("indicadores", 0),
                            valores=impacto.get("valores", 0),
                        )
                    )
                    col_cancel, col_reempl = st.columns(2)
                    with col_cancel:
                        if st.button(t["admin_cancelar"], key="btn_admin_cancelar"):
                            _reset_uploader()
                            st.rerun()
                    with col_reempl:
                        if st.button(
                            t["admin_reemplazar_plan"],
                            type="primary",
                            key="btn_admin_reemplazar",
                        ):
                            resultado = importador.cargar_plan_desde_excel(
                                contenido, reemplazar=True, dry_run=False,
                            )
                            if resultado["ok"]:
                                # Flash que sobrevive al rerun.
                                st.session_state["flash_ok"] = (
                                    resultado["mensaje"] + " "
                                    + t["admin_refrescar_otras"]
                                )
                                _reset_uploader()
                                st.rerun()
                            else:
                                st.error(t["admin_error_carga"])
                                st.write(resultado["mensaje"])


# ==========================================================================
# Pestaña 2 — Coordinación (alta + listado del plan activo)
# ==========================================================================
with tab_coord:
    if not hay_planes:
        st.info(t["admin_bd_vacia"])
    else:
        plan = plan_activo

        # ---- Alta de un registro de coordinación ----
        with st.container(border=True, key="bloque_coord_alta"):
            st.markdown(f"### {t['coord_anadir_titulo']}")

            ambitos = consultas.listar_ambitos(plan["id"])
            if not ambitos:
                st.info(t["sin_ambitos"])
            else:
                # Selectores canónicos: options=IDs, nombre traducido vía
                # format_func, key estable (no depende del label).
                ambitos_por_id = {a["id"]: a for a in ambitos}
                ambito_id = st.selectbox(
                    t["selecciona_ambito"],
                    options=[a["id"] for a in ambitos],
                    format_func=lambda i: f"{ambitos_por_id[i].get('codigo') or ''} · "
                                          f"{_nombre(ambitos_por_id[i], 'nombre_es', 'nombre_eu')}".strip(" ·"),
                    key=f"coord_amb_{plan['id']}",
                )

                actuaciones = consultas.listar_actuaciones(ambito_id)
                if not actuaciones:
                    st.info(t["sin_actuaciones"])
                else:
                    actuaciones_por_id = {ac["id"]: ac for ac in actuaciones}
                    actuacion_id = st.selectbox(
                        t["selecciona_actuacion"],
                        options=[ac["id"] for ac in actuaciones],
                        format_func=lambda i: f"{actuaciones_por_id[i].get('codigo') or ''} · "
                                              f"{_nombre(actuaciones_por_id[i], 'nombre_es', 'nombre_eu')}".strip(" ·"),
                        key=f"coord_act_{plan['id']}_{ambito_id}",
                    )

                    # Sin key= en los campos del formulario para que se limpien
                    # tras guardar (igual que el detalle en Gestión). Las
                    # etiquetas son únicas, así que no colisionan.
                    with st.form(key=f"form_coord_{actuacion_id}"):
                        fecha = st.date_input(
                            t["coord_fecha"],
                            value=date.today(),
                            format="DD/MM/YYYY",
                        )
                        col_es, col_eu = st.columns(2)
                        with col_es:
                            encargo_es = st.text_area(
                                f"{t['coord_encargo']} ({t['coord_suf_es']})")
                            gestor_es = st.text_area(
                                f"{t['coord_gestor']} ({t['coord_suf_es']})")
                            resultado_es = st.text_area(
                                f"{t['coord_resultado']} ({t['coord_suf_es']})")
                        with col_eu:
                            encargo_eu = st.text_area(
                                f"{t['coord_encargo']} ({t['coord_suf_eu']})")
                            gestor_eu = st.text_area(
                                f"{t['coord_gestor']} ({t['coord_suf_eu']})")
                            resultado_eu = st.text_area(
                                f"{t['coord_resultado']} ({t['coord_suf_eu']})")

                        if st.form_submit_button(t["coord_guardar"]):
                            campos = {
                                "encargo_es":   (encargo_es or "").strip() or None,
                                "encargo_eu":   (encargo_eu or "").strip() or None,
                                "gestor_es":    (gestor_es or "").strip() or None,
                                "gestor_eu":    (gestor_eu or "").strip() or None,
                                "resultado_es": (resultado_es or "").strip() or None,
                                "resultado_eu": (resultado_eu or "").strip() or None,
                            }
                            # Anti-registro-vacío: al menos un texto con contenido.
                            if not any(campos.values()):
                                st.error(t["coord_validar_texto"])
                            else:
                                consultas.anadir_coordinacion(
                                    actuacion_id,
                                    fecha.isoformat(),
                                    campos["encargo_es"], campos["encargo_eu"],
                                    campos["gestor_es"], campos["gestor_eu"],
                                    campos["resultado_es"], campos["resultado_eu"],
                                )
                                st.cache_data.clear()
                                st.session_state["flash_ok"] = t["coord_guardado_ok"]
                                st.rerun()

        # ---- Listado de registros de coordinación del plan activo ----
        with st.container(border=True, key="bloque_coord_lista"):
            st.markdown(f"### {t['coord_registros_titulo']}")

            df = consultas.listar_coordinaciones(plan["id"], idioma)
            if df.empty:
                st.caption(t["coord_sin_registros"])
            else:
                tabla = df.copy()
                tabla["fecha"] = tabla["fecha"].map(_formato_fecha)
                tabla["actuacion"] = tabla.apply(
                    lambda r: f"{r['act_codigo'] or ''} · {r['actuacion_nombre'] or ''}".strip(" ·"),
                    axis=1,
                )
                for col in ("encargo", "gestor", "resultado"):
                    tabla[col] = tabla[col].fillna("—").replace("", "—")
                tabla = tabla[["fecha", "actuacion", "encargo", "gestor", "resultado"]]
                tabla.columns = [
                    t["coord_fecha"], t["coord_col_actuacion"],
                    t["coord_encargo"], t["coord_gestor"], t["coord_resultado"],
                ]
                st.table(tabla.style.hide(axis="index"))
