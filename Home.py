import streamlit as st

from common.login import requerir_login
from common.menu import generarMenu

st.set_page_config(page_title="Fútbol Analytics", page_icon="⚽", layout="wide")
usuario = requerir_login()
generarMenu(usuario)

st.title("⚽ Fútbol Analytics")
st.markdown(
    "Aplicación de análisis de **LaLiga 2024-25** que combina tres fuentes de datos: "
    "una base de datos **SQLite**, un archivo **CSV** con datos GPS y una **API** de internet."
)
st.page_link("pages/1_Jugadores.py", label="Ir a Jugadores", icon="🏃")
st.page_link("pages/2_Liga.py", label="Ir a Liga", icon="🏆")