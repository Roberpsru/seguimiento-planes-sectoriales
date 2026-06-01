"""
Página de ADMINISTRACIÓN: descarga y carga de Planes Sectoriales en Excel.

Complementa al script `scripts/importar_plan.py`, reutilizando la misma
lógica (vive en `src/importador.py`). Flujo:

  1. Descargar el plan activo como Plan_Sectorial_<codigo>.xlsx.
  2. Subir un Excel:
     · dry-run automático para preview + validación
     · si hay incidencias → se listan y no se permite cargar.
     · si OK y el plan no existe → botón "Crear plan".
     · si OK y el plan ya existe → aviso de impacto + "Reemplazar" / "Cancelar".

El selector de Plan vive en la portada (común a toda la app).
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import importador  # noqa: E402
from i18n import asegurar_plan_id, plan_actual, selector_idioma, textos  # noqa: E402
from tema import aplicar_tema  # noqa: E402


st.set_page_config(
    page_title="Administración",
    layout="wide",
)
aplicar_tema()

idioma = selector_idioma()
t = textos(idioma)
plan_id = asegurar_plan_id()

# A diferencia del resto de páginas, Administración debe poder usarse con la BD
# vacía: es justo donde se carga el primer plan (p. ej. el despliegue inicial en
# Streamlit Cloud + Supabase). Por eso NO hacemos st.stop() si no hay plan;
# solo ocultamos el bloque de descarga y mostramos una nota informativa.
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
else:
    st.info(t["admin_bd_vacia"])


# --------------------------------------------------------------------------
# Bloque 1 — Descargar plan actual (solo si hay planes en la BD)
# --------------------------------------------------------------------------
if hay_planes:
    with st.container(border=True, key="bloque_admin_descargar"):
        st.markdown(f"### {t['admin_descargar_titulo']}")
        st.write(t["admin_descargar_desc"])

        codigo_plan = plan_activo["codigo"] or "PLAN"

        # Generamos los bytes solo cuando el usuario está en la página (es
        # rápido para volúmenes razonables; si fuera lento se cachearía).
        bytes_excel = importador.exportar_plan_a_excel(plan_activo["id"])

        st.download_button(
            label=t["admin_descargar_boton"].format(codigo=codigo_plan),
            data=bytes_excel,
            file_name=f"Plan_Sectorial_{codigo_plan}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )


# --------------------------------------------------------------------------
# Bloque 2 — Subir Excel para añadir o reemplazar plan
# --------------------------------------------------------------------------
# Usamos un contador en session_state para forzar el reset del file_uploader
# tras cada operación (cambia la key del widget y Streamlit lo reinstancia).
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
        # Leemos los bytes una sola vez (UploadedFile se puede consumir).
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
                    t["admin_crear_plan"],
                    type="primary",
                    key="btn_admin_crear",
                ):
                    resultado = importador.cargar_plan_desde_excel(
                        contenido, reemplazar=False, dry_run=False,
                    )
                    if resultado["ok"]:
                        st.success(
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
                    if st.button(
                        t["admin_cancelar"],
                        key="btn_admin_cancelar",
                    ):
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
                            st.success(
                                resultado["mensaje"] + " "
                                + t["admin_refrescar_otras"]
                            )
                            _reset_uploader()
                            st.rerun()
                        else:
                            st.error(t["admin_error_carga"])
                            st.write(resultado["mensaje"])
