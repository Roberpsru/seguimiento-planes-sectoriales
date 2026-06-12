"""
Tema visual de la aplicación: inyecta el CSS común a todas las páginas.

Se llama a `aplicar_tema()` una sola vez, justo después de
`st.set_page_config(...)`, en el router `app.py`. Como el router se ejecuta
en cada rerun (antes de pintar la página seleccionada por st.navigation), el
CSS queda aplicado a todas las páginas de `vistas/`. Define una paleta sobria
con acento verde y aplica estilos consistentes a títulos, métricas, tablas,
pestañas y botones.
"""
import streamlit as st


_CSS = """
<style>
:root {
    --color-primario: #1f5f3a;
    --color-primario-claro: #2d8a55;
    --color-fondo-suave: #f5f7f5;
    --color-borde: #d9e1dd;
    --color-texto-secundario: #5a6a63;
    --color-amber: #c87a1f;
    --color-gris: #8a9690;
    --color-cabecera-tabla: #eaf0ec;
}

/* --------------------------------------------------------------------- */
/* Fondos base: área principal en BLANCO, sidebar en verde pálido        */
/* --------------------------------------------------------------------- */
.stApp,
[data-testid="stMain"],
[data-testid="stAppViewContainer"] > section.main,
[data-testid="stAppViewContainer"] section[tabindex="-1"]:not([data-testid="stSidebar"]) {
    background-color: #ffffff !important;
}

section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div:first-child {
    background-color: #eaf0ec !important;
    border-right: 1px solid #c5d0c8 !important;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05) !important;
}

/* Asegura que el texto y los labels del sidebar permanezcan legibles
   sobre el fondo verde pálido. */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #1f2a26;
}

/* Encabezados de sección del menú (st.navigation, testid stNavSectionHeader
   en Streamlit 1.57): en NEGRITA, con peso/tamaño similares a la etiqueta
   "Idioma" del sidebar (0.95rem / 600), texto oscuro y sin mayúsculas forzadas. */
section[data-testid="stSidebar"] [data-testid="stNavSectionHeader"],
section[data-testid="stSidebar"] [data-testid="stNavSectionHeader"] * {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #1f2a26 !important;
    text-transform: none !important;
}

/* --------------------------------------------------------------------- */
/* Encabezados: jerarquía por color + peso + tamaño (sin barra lateral)  */
/* --------------------------------------------------------------------- */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: var(--color-primario);
    font-weight: 700;
    margin-top: 1.2rem;
}
.stApp h2 { font-size: 1.7rem; }
.stApp h3 { font-size: 1.35rem; }
.stApp h4 { font-size: 1.1rem; }

/* Ocultar los iconos de ancla (eslabón) que Streamlit añade a los h# */
[data-testid="stHeaderActionElements"] { display: none !important; }

/* --------------------------------------------------------------------- */
/* Etiquetas de widgets: más legibles                                     */
/* --------------------------------------------------------------------- */
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stDateInput"] label,
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #1f2a26 !important;
}
[data-testid="stSelectbox"] label p,
[data-testid="stNumberInput"] label p,
[data-testid="stTextInput"] label p,
[data-testid="stTextArea"] label p,
[data-testid="stDateInput"] label p,
[data-testid="stWidgetLabel"] p {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #1f2a26 !important;
}

/* --------------------------------------------------------------------- */
/* Tarjetas: bloques con borde de st.container(border=True, key=...)      */
/* Streamlit convierte la "key" en la clase .st-key-<nombre>, lo que da   */
/* un selector estable que no depende de data-testids cambiantes.         */
/* --------------------------------------------------------------------- */
.stApp [class*="st-key-bloque"] {
    background-color: #ffffff !important;
    border: 1.5px solid #1f5f3a !important;
    border-radius: 10px !important;
    padding: 1.4rem 1.5rem !important;
    margin-bottom: 1.5rem !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12) !important;
}

/* --------------------------------------------------------------------- */
/* Tarjetas de la portada: cada acceso rápido con su propio acento de    */
/* color. Solo afecta a app.py; el resto de páginas mantienen el verde.  */
/* --------------------------------------------------------------------- */

/* Tarjeta "Visión general" — verde */
.stApp [class*="st-key-bloque_inicio_visiongeneral"] {
    background-color: #eaf0ec !important;
    border-color: #1f5f3a !important;
}
.stApp [class*="st-key-bloque_inicio_visiongeneral"] h3 {
    color: #1f5f3a !important;
}

/* Tarjeta "Gestión de actuaciones" — azul */
.stApp [class*="st-key-bloque_inicio_gestion"] {
    background-color: #e6eef5 !important;
    border-color: #2a5e8c !important;
}
.stApp [class*="st-key-bloque_inicio_gestion"] h3 {
    color: #2a5e8c !important;
}

/* Tarjeta "Indicadores (KPI)" — ámbar */
.stApp [class*="st-key-bloque_inicio_indicadores"] {
    background-color: #f5ede0 !important;
    border-color: #a86419 !important;
}
.stApp [class*="st-key-bloque_inicio_indicadores"] h3 {
    color: #a86419 !important;
}

/* Tarjeta "Resumen del Plan" — morado */
.stApp [class*="st-key-bloque_inicio_resumen"] {
    background-color: #ede6f0 !important;
    border-color: #6a4a7a !important;
}
.stApp [class*="st-key-bloque_inicio_resumen"] h3 {
    color: #6a4a7a !important;
}

/* --------------------------------------------------------------------- */
/* Tarjetas de st.metric: blancas para destacar dentro del bloque verde   */
/* --------------------------------------------------------------------- */
[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #c5d0c8 !important;
    border-left: 4px solid #1f5f3a !important;
    border-radius: 6px;
    padding: 1rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
[data-testid="stMetricLabel"] {
    color: var(--color-texto-secundario);
    font-weight: 500;
}
[data-testid="stMetricLabel"] p {
    color: var(--color-texto-secundario);
    font-weight: 500;
}
[data-testid="stMetricValue"] {
    color: var(--color-primario);
    font-weight: 700;
}

/* --------------------------------------------------------------------- */
/* Cabeceras de tablas (st.dataframe y st.table): suaves, no agresivas    */
/* --------------------------------------------------------------------- */
[data-testid="stDataFrame"] thead tr th,
[data-testid="stTable"] thead tr th,
.stTable thead tr th,
table thead th {
    background: var(--color-cabecera-tabla) !important;
    color: var(--color-primario) !important;
    font-weight: 600 !important;
    border-bottom: 2px solid var(--color-primario) !important;
}
[data-testid="stDataFrame"] thead tr th * ,
[data-testid="stTable"] thead tr th * ,
.stTable thead tr th * ,
table thead th * {
    color: var(--color-primario) !important;
    font-weight: 600 !important;
}

/* Filas alternas (cebra) */
[data-testid="stDataFrame"] tbody tr:nth-child(even) td,
[data-testid="stTable"] tbody tr:nth-child(even) td,
.stTable tbody tr:nth-child(even) td,
table tbody tr:nth-child(even) td {
    background: var(--color-fondo-suave);
}

/* --------------------------------------------------------------------- */
/* Pestañas de st.tabs activas                                            */
/* --------------------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    color: var(--color-primario);
}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p {
    color: var(--color-primario);
    font-weight: 600;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--color-primario);
}

/* --------------------------------------------------------------------- */
/* Botones primarios                                                      */
/* --------------------------------------------------------------------- */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"],
.stFormSubmitButton > button[data-testid="baseButton-primary"] {
    background-color: var(--color-primario);
    border-color: var(--color-primario);
    color: #ffffff;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover,
.stFormSubmitButton > button[data-testid="baseButton-primary"]:hover {
    background-color: var(--color-primario-claro);
    border-color: var(--color-primario-claro);
}

/* --------------------------------------------------------------------- */
/* Caja de "Objetivo" personalizada (la usa app.py en lugar de st.info)   */
/* --------------------------------------------------------------------- */
.bloque-objetivo {
    background: #eaf0ec;
    padding: 1rem 1.2rem;
    border-radius: 4px;
    margin: 0.5rem 0 1rem 0;
}
.bloque-objetivo .titulo-objetivo {
    color: var(--color-primario);
    font-weight: 600;
    margin-bottom: 0.3rem;
}
.bloque-objetivo .texto-objetivo {
    color: var(--color-texto-secundario);
}

/* --------------------------------------------------------------------- */
/* Indicador de estado (punto de color delante del texto) en tablas HTML  */
/* --------------------------------------------------------------------- */
.punto-estado {
    display: inline-block;
    width: 0.65rem;
    height: 0.65rem;
    border-radius: 50%;
    margin-right: 0.45rem;
    vertical-align: middle;
}
.punto-previsto  { background: var(--color-gris); }
.punto-en-curso  { background: var(--color-amber); }
.punto-ejecutado { background: var(--color-primario); }
</style>
"""


def aplicar_tema():
    """Inyecta el bloque CSS común. Llamar tras st.set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)
