"""
Portada de la aplicación "Seguimiento de Planes Sectoriales".

Esta página es la primera que ve el usuario al abrir la app. Presenta el
proyecto, los logos institucionales y cuatro tarjetas de acceso rápido a
las páginas funcionales (Visión general, Gestión de actuaciones,
Indicadores y Resumen del Plan), que viven en pages/.

Ejecutar:  streamlit run app.py
"""
import base64
import sys
from pathlib import Path

import streamlit as st

# Hacer accesibles los módulos compartidos en src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from arranque import inicializar_si_necesario  # noqa: E402
from i18n import selector_idioma, selector_plan_portada, textos  # noqa: E402
from tema import aplicar_tema  # noqa: E402

st.set_page_config(
    page_title="Seguimiento de Planes Sectoriales",
    layout="wide",
)
aplicar_tema()

# Arranque: en SQLite local crea el esquema y carga los Excel de datos/ si la
# BD está vacía. En PostgreSQL no hace nada (la carga inicial es manual).
inicializar_si_necesario()

# Idioma (compartido entre páginas vía st.session_state)
idioma = selector_idioma()
t = textos(idioma)

# Rutas a los logos institucionales (en datos/)
_RAIZ = Path(__file__).resolve().parent


def _img_b64(nombre):
    """Devuelve un fichero de datos/ codificado en base64 (para incrustarlo
    en una etiqueta <img src='data:image/...'> y poder controlar la altura
    exacta con CSS)."""
    with open(_RAIZ / "datos" / nombre, "rb") as f:
        return base64.b64encode(f.read()).decode()


# --------------------------------------------------------------------------
# Cabecera: dos logos alineados a la misma altura, centrados (flexbox)
# --------------------------------------------------------------------------
_gova_b64 = _img_b64("gova.jpg")
_hazi_b64 = _img_b64("hazi.jpg")

st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center;
                gap: 4rem; padding: 1.5rem 0;">
      <img src="data:image/jpeg;base64,{_gova_b64}"
           style="height: 110px; width: auto;">
      <img src="data:image/jpeg;base64,{_hazi_b64}"
           style="height: 80px; width: auto;">
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# --------------------------------------------------------------------------
# Título grande + descripción
# --------------------------------------------------------------------------
st.markdown(
    f"<div style='font-size:2.4rem; font-weight:700; color:#1f5f3a; "
    f"text-align:center; margin:0.5rem 0 1.2rem 0;'>"
    f"{t['portada_titulo']}</div>",
    unsafe_allow_html=True,
)

# Los párrafos se renderizan con st.markdown plano (sin envoltorio HTML)
# para que la sintaxis **negrita** del propio texto se procese.
st.markdown(t["portada_intro_1"])
st.markdown(t["portada_intro_2"])

# --------------------------------------------------------------------------
# Selector de Plan Sectorial (global a toda la app vía session_state).
# Se centra con una fila de columnas para que no ocupe todo el ancho.
# --------------------------------------------------------------------------
st.write("")
_, _col_plan, _ = st.columns([1, 2, 1])
with _col_plan:
    selector_plan_portada()
st.write("")

# --------------------------------------------------------------------------
# Cuatro tarjetas de acceso rápido (cuadrícula 2x2)
# --------------------------------------------------------------------------
fila1_a, fila1_b = st.columns(2)
with fila1_a:
    with st.container(border=True, key="bloque_inicio_visiongeneral"):
        st.markdown(f"### {t['portada_vision_titulo']}")
        st.write(t["portada_vision_desc"])
        st.page_link(
            "pages/1_Vision_general.py",
            label=t["portada_vision_link"],
        )
with fila1_b:
    with st.container(border=True, key="bloque_inicio_gestion"):
        st.markdown(f"### {t['portada_gestion_titulo']}")
        st.write(t["portada_gestion_desc"])
        st.page_link(
            "pages/2_Gestion_actuaciones.py",
            label=t["portada_gestion_link"],
        )

fila2_a, fila2_b = st.columns(2)
with fila2_a:
    with st.container(border=True, key="bloque_inicio_indicadores"):
        st.markdown(f"### {t['portada_kpi_titulo']}")
        st.write(t["portada_kpi_desc"])
        st.page_link(
            "pages/3_Indicadores.py",
            label=t["portada_kpi_link"],
        )
with fila2_b:
    with st.container(border=True, key="bloque_inicio_resumen"):
        st.markdown(f"### {t['portada_resumen_titulo']}")
        st.write(t["portada_resumen_desc"])
        st.page_link(
            "pages/4_Resumen_del_Plan.py",
            label=t["portada_resumen_link"],
        )

# --------------------------------------------------------------------------
# Pie de página
# --------------------------------------------------------------------------
st.markdown(
    f"<p style='text-align:center; font-style:italic; font-size:0.9rem; "
    f"color:#5a6a63; margin-top:2rem;'>{t['portada_pie']}</p>",
    unsafe_allow_html=True,
)
