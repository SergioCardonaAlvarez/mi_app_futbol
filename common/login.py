"""
Login y control de sesión (manual, apartado 8.2).
- Guarda en st.session_state si el usuario ha entrado.
- La sesión caduca tras X minutos sin actividad.
- Tiene una función para cerrar sesión.
"""

import hmac
from datetime import datetime, timedelta

import streamlit as st

from common.config import APP_PASSWORD, APP_USER, SESSION_MINUTES


def _credenciales_validas(usuario, password):
    # compare_digest compara de forma segura (evita ataques de temporización)
    return (hmac.compare_digest(usuario.strip(), APP_USER)
            and hmac.compare_digest(password, APP_PASSWORD))


def _sesion_caducada():
    ultima = st.session_state.get("ultima_actividad")
    return ultima is not None and datetime.now() - ultima > timedelta(minutes=SESSION_MINUTES)


def cerrar_sesion(mensaje=None):
    for clave in list(st.session_state.keys()):
        del st.session_state[clave]
    if mensaje:
        st.session_state["mensaje_login"] = mensaje


def _formulario_login():
    st.markdown("<h1 style='text-align:center; color:#1f7a4d;'>⚽ Fútbol Analytics</h1>",
                unsafe_allow_html=True)
    st.caption("Accede con tus credenciales para ver los análisis.")

    aviso = st.session_state.pop("mensaje_login", None)
    if aviso:
        st.info(aviso)

    _, centro, _ = st.columns([1, 2, 1])
    with centro:
        with st.form("form_login"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if entrar:
            if not usuario or not password:
                st.warning("Introduce usuario y contraseña.")
            elif _credenciales_validas(usuario, password):
                ahora = datetime.now()
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario.strip()
                st.session_state["ultima_actividad"] = ahora
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")


def requerir_login():
    """Se llama al principio de CADA página. Si no hay sesión, muestra el login y para."""
    if st.session_state.get("autenticado") and _sesion_caducada():
        cerrar_sesion(f"Tu sesión ha caducado tras {SESSION_MINUTES} minutos sin actividad.")

    if not st.session_state.get("autenticado"):
        _formulario_login()
        st.stop()   # no se ejecuta nada más de la página

    st.session_state["ultima_actividad"] = datetime.now()
    return st.session_state["usuario"]