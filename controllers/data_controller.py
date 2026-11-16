"""
Controlador: une los datos de los modelos y los guarda en caché (manual, apartado 6.1.1).
ttl = segundos que se guarda el resultado antes de volver a consultar la fuente.
"""

import pandas as pd
import streamlit as st

from models import api_model, csv_model, sqlite_model


@st.cache_data(ttl=3600, show_spinner="Consultando SQLite...")
def cargar_jugadores():
    return sqlite_model.obtener_jugadores()


@st.cache_data(ttl=3600, show_spinner="Consultando SQLite...")
def cargar_partidos():
    return sqlite_model.obtener_partidos()


@st.cache_data(ttl=3600, show_spinner="Leyendo el CSV...")
def cargar_carga_fisica():
    return csv_model.obtener_carga_fisica()


@st.cache_data(ttl=600, show_spinner="Consultando la API...")   # API: 10 minutos
def cargar_clasificacion():
    return api_model.obtener_clasificacion()


@st.cache_data(ttl=3600)
def jugadores_con_carga():
    """Une las estadísticas (SQLite) con la media de carga física de cada jugador (CSV)."""
    jugadores = cargar_jugadores()
    resumen = (cargar_carga_fisica()
               .groupby("jugador_id")
               .agg(distancia_media_km=("distancia_km", "mean"),
                    sprints_media=("sprints", "mean"),
                    velocidad_max_kmh=("velocidad_max_kmh", "max"))
               .round(2)
               .reset_index())
    df = jugadores.merge(resumen, left_on="id", right_on="jugador_id", how="left")
    return df.drop(columns=["jugador_id"])


@st.cache_data(ttl=3600)
def estadisticas_equipos():
    """Medias por equipo a partir de los partidos de SQLite (como local y como visitante)."""
    p = cargar_partidos()
    como_local = pd.DataFrame({"equipo": p["local"], "posesion": p["posesion_local"],
                               "tiros": p["tiros_local"], "goles": p["goles_local"]})
    como_visitante = pd.DataFrame({"equipo": p["visitante"], "posesion": 100 - p["posesion_local"],
                                   "tiros": p["tiros_visitante"], "goles": p["goles_visitante"]})
    todos = pd.concat([como_local, como_visitante])
    return (todos.groupby("equipo")
            .agg(posesion_media=("posesion", "mean"),
                 tiros_por_partido=("tiros", "mean"),
                 goles_por_partido=("goles", "mean"))
            .round(2)
            .reset_index())


@st.cache_data(ttl=600, show_spinner="Consultando la API...")
def cargar_top_api():
    return api_model.obtener_top_api()


def limpiar_cache():
    st.cache_data.clear()