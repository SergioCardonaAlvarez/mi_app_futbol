"""Menú lateral común a todas las páginas (manual, apartado 6.4)."""

import streamlit as st

from common.login import cerrar_sesion


def generarMenu(usuario):
    with st.sidebar:
        st.markdown("## ⚽ Fútbol Analytics")
        st.caption(f"Sesión iniciada como **{usuario}**")
        st.divider()

        st.page_link("Home.py", label="Inicio", icon="🏠")
        st.page_link("pages/1_Jugadores.py", label="Jugadores y carga física", icon="🏃")
        st.page_link("pages/2_Liga.py", label="Liga y partidos", icon="🏆")

        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            cerrar_sesion("Has cerrado la sesión correctamente.")
            st.switch_page("Home.py")