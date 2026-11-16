import plotly.express as px
import streamlit as st

from common.login import requerir_login
from common.menu import generarMenu
from controllers import data_controller as dc

st.set_page_config(page_title="Jugadores", page_icon="🏃", layout="wide")
usuario = requerir_login()
generarMenu(usuario)

COLORES = {"Portero": "#8c9ba5", "Defensa": "#2b6cb0",
           "Centrocampista": "#1f7a4d", "Delantero": "#d9822b"}

# ---------- Datos (dos fuentes: SQLite + CSV) ----------
jugadores = dc.jugadores_con_carga()
carga = dc.cargar_carga_fisica()

# ---------- Filtros en la barra lateral ----------
with st.sidebar:
    st.subheader("Filtros")
    equipos = st.multiselect("Equipos", sorted(jugadores["equipo"].unique()),
                             default=["FC Barcelona", "Real Madrid", "Atlético de Madrid"])
    posiciones = st.multiselect("Posiciones", list(COLORES),
                                default=["Centrocampista", "Delantero"])
    min_minutos = st.slider("Minutos mínimos jugados", 0, 3000, 900, step=100)

df = jugadores[jugadores["equipo"].isin(equipos)
               & jugadores["posicion"].isin(posiciones)
               & (jugadores["minutos"] >= min_minutos)]

# ---------- Cabecera y métricas ----------
st.title("🏃 Jugadores y carga física")
st.caption("Fuentes: SQLite (tabla jugadores) + CSV (carga_fisica.csv)")

if df.empty:
    st.warning("Ningún jugador cumple los filtros. Cambia los filtros de la izquierda.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Jugadores", len(df))
c2.metric("Goles", int(df["goles"].sum()))
c3.metric("Asistencias", int(df["asistencias"].sum()))
c4.metric("Distancia media", f"{df['distancia_media_km'].mean():.1f} km/sem")

# ---------- Gráficos ----------
g1, g2 = st.columns(2)
with g1:
    top = df.nlargest(15, "goles").sort_values("goles")
    fig = px.bar(top, x="goles", y="nombre", orientation="h", color="equipo",
                 title="Top 15 goleadores (SQLite)")
    fig.update_layout(yaxis_title="", xaxis_title="Goles", legend_title="", height=450)
    st.plotly_chart(fig, use_container_width=True)
with g2:
    fig = px.scatter(df, x="xg", y="goles", color="posicion", size="minutos",
                     hover_name="nombre", color_discrete_map=COLORES,
                     title="Goles vs goles esperados (xG)")
    limite = float(max(df["xg"].max(), df["goles"].max(), 1))
    fig.add_shape(type="line", x0=0, y0=0, x1=limite, y1=limite,
                  line={"dash": "dash", "color": "grey"})
    fig.update_layout(height=450, legend_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Por encima de la línea discontinua: el jugador marca más de lo esperado.")

g3, g4 = st.columns(2)
with g3:
    fig = px.scatter(df, x="distancia_media_km", y="sprints_media", color="posicion",
                     hover_name="nombre", color_discrete_map=COLORES,
                     title="Perfil físico: distancia vs sprints (CSV)")
    fig.update_layout(xaxis_title="Km por semana", yaxis_title="Sprints por semana",
                      height=420, legend_title="")
    st.plotly_chart(fig, use_container_width=True)
with g4:
    nombres = df.sort_values("goles", ascending=False)["nombre"].tolist()
    elegidos = st.multiselect("Jugadores para la evolución semanal (máx. 5)", nombres,
                              default=nombres[:3], max_selections=5)
    ids = df[df["nombre"].isin(elegidos)]["id"]
    semanal = carga[carga["jugador_id"].isin(ids)].sort_values("semana")
    if semanal.empty:
        st.info("Elige al menos un jugador.")
    else:
        fig = px.line(semanal, x="semana", y="distancia_km", color="nombre", markers=True,
                      title="Distancia recorrida por semana (CSV)")
        fig.update_layout(xaxis_title="", yaxis_title="km", height=360, legend_title="")
        st.plotly_chart(fig, use_container_width=True)

# ---------- Tablas ----------
st.subheader("Datos")
tab1, tab2 = st.tabs(["📊 Estadísticas (SQLite) + resumen físico (CSV)", "🛰️ Registros GPS (CSV)"])
with tab1:
    st.dataframe(
        df.sort_values("goles", ascending=False)[
            ["nombre", "equipo", "posicion", "partidos", "minutos", "goles", "asistencias",
             "xg", "distancia_media_km", "sprints_media", "velocidad_max_kmh"]],
        hide_index=True, use_container_width=True)
with tab2:
    gps = carga[carga["jugador_id"].isin(df["id"])]
    st.dataframe(gps.drop(columns=["jugador_id"]), hide_index=True, use_container_width=True)

    # ---------- Imprimir y exportar a PDF ----------
from common.utils import barra_acciones, generar_pdf, grafico_barras

st.divider()
st.subheader("Imprimir y exportar")
top_pdf = df.nlargest(15, "goles")
pdf = generar_pdf(
    "Informe de jugadores y carga física",
    f"Equipos: {', '.join(equipos)} · Posiciones: {', '.join(posiciones)} · Minutos mínimos: {min_minutos}",
    df.sort_values("goles", ascending=False)[["nombre", "equipo", "posicion", "minutos", "goles",
                                             "asistencias", "xg", "distancia_media_km", "sprints_media"]],
    grafico_barras(top_pdf["nombre"], top_pdf["goles"], "Top 15 goleadores"),
)
barra_acciones(pdf, "informe_jugadores")