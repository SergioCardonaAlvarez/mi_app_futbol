import plotly.express as px
import streamlit as st

from common.config import get_config
from common.login import requerir_login
from common.menu import generarMenu
from controllers import data_controller as dc

st.set_page_config(page_title="Liga", page_icon="🏆", layout="wide")
usuario = requerir_login()
generarMenu(usuario)

# ---------- Datos (dos fuentes: API + SQLite) ----------
clasificacion, origen = dc.cargar_clasificacion()   # API (o copia local si la API da pocos equipos)
partidos = dc.cargar_partidos()                      # SQLite
estadisticas = dc.estadisticas_equipos()             # SQLite (medias por equipo)

# Unimos las dos fuentes por el nombre del equipo
liga = clasificacion.merge(estadisticas, left_on="Equipo", right_on="equipo", how="left")
liga = liga.drop(columns=["equipo"])

# ---------- Filtro en la barra lateral ----------
equipos = sorted(estadisticas["equipo"])
with st.sidebar:
    st.subheader("Filtros")
    equipo = st.selectbox("Equipo a analizar", equipos, index=equipos.index("Valencia"))

# ---------- Cabecera ----------
st.title("🏆 Liga y partidos")
st.caption("Fuentes: API de TheSportsDB (clasificación) + SQLite (tabla partidos)")

# ---------- Lo que devuelve la API en directo ----------
top_api = dc.cargar_top_api()
if top_api is None:
    st.warning("⚠ La API no responde ahora mismo: toda la clasificación sale de la copia local.")
else:
    st.success(f"✔ Conectado a la API de TheSportsDB: ha devuelto {len(top_api)} equipos en directo.")
    st.subheader(f"Top {len(top_api)} real de LaLiga {get_config('API_SEASON', '2024-2025')} (API en directo)")
    st.dataframe(top_api[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]],
                 hide_index=True, use_container_width=True)
    if origen == "respaldo":
        st.caption(f"La versión gratuita de la API solo devuelve {len(top_api)} equipos. "
                   "Para la clasificación completa y los cruces con SQLite se usa la copia local "
                   "(temporada simulada).")

# ---------- Partidos del equipo elegido (SQLite) ----------
pe = partidos[(partidos["local"] == equipo) | (partidos["visitante"] == equipo)].copy()
es_local = pe["local"] == equipo
pe["condicion"] = es_local.map({True: "Local", False: "Visitante"})
pe["rival"] = pe["visitante"].where(es_local, pe["local"])
pe["gf"] = pe["goles_local"].where(es_local, pe["goles_visitante"])
pe["gc"] = pe["goles_visitante"].where(es_local, pe["goles_local"])
pe["resultado"] = ["Victoria" if a > b else "Empate" if a == b else "Derrota"
                   for a, b in zip(pe["gf"], pe["gc"])]
pe["puntos_acumulados"] = pe["resultado"].map({"Victoria": 3, "Empate": 1, "Derrota": 0}).cumsum()

# ---------- Métricas ----------
lider = liga.iloc[0]
fila_equipo = liga[liga["Equipo"] == equipo]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Líder", lider["Equipo"], f"{int(lider['Pts'])} puntos", delta_color="off")
if not fila_equipo.empty:
    c2.metric(f"{equipo}", f"{int(fila_equipo['Pos'].iloc[0])}º",
              f"{int(fila_equipo['Pts'].iloc[0])} puntos", delta_color="off")
c3.metric("Goles en la liga (SQLite)", int(partidos["goles_local"].sum() + partidos["goles_visitante"].sum()))
c4.metric(f"Victorias de {equipo} (SQLite)", int((pe["resultado"] == "Victoria").sum()))

# ---------- Clasificación completa: tabla + gráfico ----------
st.subheader("Clasificación completa" + (" (API)" if origen == "api" else " (copia local)"))
t1, t2 = st.columns([1.1, 1])
with t1:
    st.dataframe(liga[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts", "Forma"]],
                 hide_index=True, use_container_width=True, height=740)
with t2:
    barras = liga.sort_values("Pts").copy()
    barras["grupo"] = ["Elegido" if e == equipo else "Resto" for e in barras["Equipo"]]
    fig = px.bar(barras, x="Pts", y="Equipo", orientation="h", color="grupo",
                 color_discrete_map={"Elegido": "#d9822b", "Resto": "#1f7a4d"},
                 title="Puntos por equipo")
    fig.update_layout(height=740, showlegend=False, yaxis_title="", xaxis_title="Puntos")
    fig.update_yaxes(categoryorder="total ascending")   # ordenar las barras por puntos
    st.plotly_chart(fig, use_container_width=True)

# ---------- Cruce de las dos fuentes ----------
st.subheader("Estilo de juego (SQLite) frente a resultados (clasificación)")
validos = liga.dropna(subset=["posesion_media"])
g1, g2 = st.columns(2)
with g1:
    fig = px.scatter(validos, x="posesion_media", y="Pts", text="Equipo",
                     title="Posesión media vs puntos")
    fig.update_traces(textposition="top center", marker_color="#1f7a4d", textfont_size=10)
    fig.update_layout(xaxis_title="Posesión media (%)", yaxis_title="Puntos", height=460)
    st.plotly_chart(fig, use_container_width=True)
with g2:
    fig = px.scatter(validos, x="tiros_por_partido", y="GF", text="Equipo", color="Pts",
                     color_continuous_scale="Greens", title="Tiros por partido vs goles a favor")
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.update_layout(xaxis_title="Tiros por partido", yaxis_title="Goles a favor", height=460)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Temporada del equipo elegido ----------
st.subheader(f"Temporada de {equipo} (SQLite)")
fig = px.line(pe, x="jornada", y="puntos_acumulados", markers=True,
              hover_data=["rival", "condicion", "gf", "gc", "resultado"],
              title="Puntos acumulados jornada a jornada")
fig.update_traces(line_color="#1f7a4d")
fig.update_layout(height=380, xaxis_title="Jornada", yaxis_title="Puntos")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(pe[["jornada", "fecha", "condicion", "rival", "gf", "gc", "resultado", "puntos_acumulados"]],
             hide_index=True, use_container_width=True)

# ---------- Imprimir y exportar a PDF ----------
from common.utils import barra_acciones, generar_pdf, grafico_barras

st.divider()
st.subheader("Imprimir y exportar")
pdf = generar_pdf(
    "Informe de liga y partidos",
    f"Equipo analizado: {equipo} · Clasificación completa: {'API' if origen == 'api' else 'copia local'}",
    liga[["Pos", "Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]],
    grafico_barras(liga["Equipo"], liga["Pts"], "Puntos por equipo"),
)
barra_acciones(pdf, "informe_liga")