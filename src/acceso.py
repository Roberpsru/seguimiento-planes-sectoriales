"""
Control de acceso por CLAVE COMPARTIDA para las páginas de EDICIÓN
(Gestión de actuaciones, Indicadores, Administración).

Es una barrera ligera provisional hasta que haya un sistema de usuarios y
permisos (roadmap). Las páginas de solo consulta (Inicio, Visión general,
Resumen del Plan) NO se restringen.

La clave NUNCA está en el código ni en el repo: se lee de
st.secrets["CLAVE_GESTION"] o, en su defecto, de os.environ["CLAVE_GESTION"].
Si no está configurada en ningún sitio, las páginas quedan BLOQUEADAS
(fail-closed).

La autorización vale para TODA la sesión y las tres páginas a la vez: se guarda
en st.session_state["_acceso_gestion_ok"], una clave PERSISTENTE que NO es key
de ningún widget (pitfall 1 de CLAUDE.md), para que sobreviva a la navegación
entre páginas.
"""
import os

import streamlit as st

# Clave persistente compartida (NO usar como key de ningún widget).
_FLAG = "_acceso_gestion_ok"


def _clave_configurada():
    """Devuelve la clave de gestión configurada, o None si no hay ninguna.

    Prioridad: st.secrets["CLAVE_GESTION"] -> os.environ["CLAVE_GESTION"].
    El acceso a st.secrets se aísla en try/except porque lanza si no existe
    fichero de secrets.
    """
    try:
        if "CLAVE_GESTION" in st.secrets:
            return str(st.secrets["CLAVE_GESTION"])
    except Exception:
        pass
    return os.environ.get("CLAVE_GESTION")


def requiere_clave(t):
    """Exige la clave de gestión antes de renderizar la página.

    - Si la sesión ya está autorizada, no hace nada (la página continúa).
    - Si no hay clave configurada -> error fail-closed + st.stop().
    - Si la hay, pinta el formulario de clave; con clave correcta autoriza la
      sesión y hace st.rerun(); con clave incorrecta muestra error; mientras no
      esté autorizada, st.stop() (no se renderiza nada más de la página).

    `t` es el diccionario de textos del idioma activo (i18n.textos()).
    """
    if st.session_state.get(_FLAG):
        return

    clave = _clave_configurada()
    if not clave:  # None o cadena vacía -> fail-closed
        st.error(t["acceso_no_config"])
        st.stop()

    st.title(t["acceso_titulo"])
    with st.form(key="form_acceso_gestion"):
        entrada = st.text_input(t["acceso_campo"], type="password")
        if st.form_submit_button(t["acceso_boton"]):
            # Comparación EXACTA (distingue mayúsculas/minúsculas).
            if entrada == clave:
                st.session_state[_FLAG] = True
                st.rerun()
            else:
                st.error(t["acceso_error"])
    st.stop()
