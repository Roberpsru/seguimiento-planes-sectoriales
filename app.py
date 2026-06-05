"""
Router de la aplicación "Seguimiento de Planes Sectoriales".

Este es el fichero que se pasa a `streamlit run app.py`. Con la API moderna
st.Page + st.navigation, app.py NO contiene contenido de página: actúa como
un router / marco común que se ejecuta en CADA rerun. Su trabajo es:

  1. Configuración global una sola vez: set_page_config, tema y arranque de BD.
  2. Pintar el ÚNICO selector de idioma de la app en el sidebar.
  3. Construir el menú de navegación con los títulos de página traducidos al
     idioma activo (st.navigation), y ejecutar la página seleccionada.

La portada vive ahora en vistas/Inicio.py (una página más del menú). El resto
de páginas funcionales están en vistas/. Ningún fichero debe llamar ya a
set_page_config / aplicar_tema / selector_idioma: lo hace este router.

Ejecutar:  streamlit run app.py
"""
import sys
from pathlib import Path

import streamlit as st

# Hacer accesibles los módulos compartidos en src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from arranque import inicializar_si_necesario  # noqa: E402
from i18n import (  # noqa: E402
    TITULOS_PAGINAS,
    idioma_actual,
    selector_idioma_portada,
)
from tema import aplicar_tema  # noqa: E402

st.set_page_config(
    page_title="Seguimiento de Planes Sectoriales",
    layout="wide",
)
aplicar_tema()

# Arranque: en SQLite local crea el esquema y carga los Excel de datos/ si la
# BD está vacía. En PostgreSQL no hace nada (la carga inicial es manual).
inicializar_si_necesario()

# Único selector de idioma de la app (sidebar). Se ejecuta en cada rerun, así
# que el radio aparece en todas las páginas; la elección persiste en
# st.session_state["idioma"].
selector_idioma_portada()

# Títulos del menú en el idioma activo.
idioma = idioma_actual()
tit = TITULOS_PAGINAS[idioma]

paginas = [
    st.Page("vistas/Inicio.py", title=tit["inicio"], default=True),
    st.Page("vistas/1_Vision_general.py", title=tit["vision_general"]),
    st.Page("vistas/2_Gestion_actuaciones.py", title=tit["gestion"]),
    st.Page("vistas/3_Indicadores.py", title=tit["indicadores"]),
    st.Page("vistas/4_Resumen_del_Plan.py", title=tit["resumen"]),
    st.Page("vistas/5_Administracion.py", title=tit["administracion"]),
]

pg = st.navigation(paginas)
pg.run()
