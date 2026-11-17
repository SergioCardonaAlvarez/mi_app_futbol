# ⚽ Fútbol Analytics

Aplicación web en Streamlit para analizar LaLiga 2024-25, desarrollada para la tarea del
Módulo 8 (Creación y Despliegue de Aplicaciones en Streamlit) del V Máster en Python
Avanzado aplicado al Deporte.

- **App publicada:** https://futbol-analytics-sergio.streamlit.app
- **Usuario / contraseña:** admin / admin

## Qué hace

- **Login** con control de sesión (caduca tras 30 minutos de inactividad).
- **Menú lateral** con dos páginas:
  - **Jugadores y carga física:** combina SQLite (estadísticas) y CSV (datos GPS).
  - **Liga y partidos:** combina la API de TheSportsDB (clasificación en directo) y SQLite (partidos).
- **Gráficos interactivos** con Plotly, filtros y tablas.
- Botones para **imprimir** la página y **exportar a PDF**.
- **Caché** de datos con `st.cache_data`.

## Estructura del proyecto

    .streamlit/    configuración y tema
    common/        configuración, login, menú, imprimir y PDF
    controllers/   une los datos y aplica la caché
    data/          base de datos SQLite, CSV y copia de respaldo de la API
    models/        acceso a cada fuente de datos
    pages/         páginas Jugadores y Liga
    Home.py        página principal

## Cómo ejecutarla en local

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    streamlit run Home.py

## Datos

Los equipos son los reales de LaLiga 2024-25. Los jugadores, los datos GPS y las
estadísticas de partido están simulados con `data/generador_de_datos.py`.
