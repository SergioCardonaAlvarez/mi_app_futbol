"""Configuración: lee los valores del archivo .env (en local) o de los Secrets (en Streamlit Cloud)."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent   # carpeta raíz del proyecto
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")


def get_config(clave, por_defecto=""):
    """Busca primero en .env, después en st.secrets y si no, usa el valor por defecto."""
    valor = os.getenv(clave)
    if valor:
        return valor
    try:
        import streamlit as st
        if clave in st.secrets:
            return str(st.secrets[clave])
    except Exception:
        pass
    return por_defecto


APP_USER = get_config("APP_USER", "admin")
APP_PASSWORD = get_config("APP_PASSWORD", "admin")
SESSION_MINUTES = int(get_config("SESSION_MINUTES", "30"))