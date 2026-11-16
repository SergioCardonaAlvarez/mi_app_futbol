"""
Generador de datos simulados para la app de fútbol.

Crea tres fuentes de datos dentro de data/:
  1. futbol.db                       -> SQLite con las tablas `jugadores` y `partidos`
  2. carga_fisica.csv                -> datos GPS semanales de cada jugador
  3. api_respaldo/clasificacion.json -> copia de la clasificación con el formato de la API,
                                        por si la API de internet no responde

Equipos reales de LaLiga 2024-25; jugadores y estadísticas SIMULADOS.
Uso:  python data/generador_de_datos.py
"""

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
rng = np.random.default_rng(2024)  # semilla fija: siempre salen los mismos datos

# Equipo: (fuerza de ataque, debilidad defensiva)
EQUIPOS = {
    "Real Madrid": (2.2, 0.8), "FC Barcelona": (2.4, 0.9), "Atlético de Madrid": (1.8, 0.8),
    "Athletic Club": (1.6, 0.9), "Villarreal": (1.7, 1.2), "Real Betis": (1.5, 1.1),
    "Celta de Vigo": (1.4, 1.3), "Rayo Vallecano": (1.2, 1.1), "Osasuna": (1.2, 1.2),
    "Mallorca": (1.1, 1.2), "Real Sociedad": (1.1, 1.1), "Valencia": (1.2, 1.3),
    "Getafe": (1.0, 1.1), "Espanyol": (1.0, 1.4), "Alavés": (1.1, 1.4),
    "Girona": (1.3, 1.5), "Sevilla": (1.1, 1.4), "Leganés": (1.0, 1.5),
    "Las Palmas": (1.1, 1.6), "Real Valladolid": (0.7, 1.9),
}
NOMBRES = ["Álex", "Hugo", "Pablo", "Daniel", "Adrián", "Javier", "Sergio", "Iker", "Marc",
           "Raúl", "Iván", "Diego", "Mario", "Óscar", "Rubén", "Carlos", "Unai", "Jon",
           "Nico", "Gonzalo", "Víctor", "Aitor", "Lucas", "Martín", "Bruno", "Thiago",
           "Mateo", "Samuel", "Leo", "Joel", "Enzo", "Kevin", "Yeray", "Ander", "Pau"]
APELLIDOS = ["García", "Martínez", "López", "Sánchez", "Pérez", "Gómez", "Ruiz", "Díaz",
             "Moreno", "Muñoz", "Álvarez", "Romero", "Navarro", "Torres", "Domínguez",
             "Vázquez", "Ramos", "Gil", "Serrano", "Blanco", "Molina", "Castro", "Ortega",
             "Rubio", "Marín", "Sanz", "Iglesias", "Medina", "Garrido", "Cortés", "Castillo",
             "Lozano", "Guerrero", "Cano", "Prieto", "Méndez", "Cruz", "Calvo", "Gallego"]
NACIONALIDADES = ["España"] * 12 + ["Argentina", "Francia", "Brasil", "Portugal", "Uruguay",
                                    "Marruecos", "Países Bajos", "Colombia", "Alemania", "Senegal"]
PLANTILLA = {"Portero": 2, "Defensa": 7, "Centrocampista": 7, "Delantero": 6}
TITULARES = {"Portero": 1, "Defensa": 4, "Centrocampista": 4, "Delantero": 3}


def nombre_unico(usados):
    while True:
        nombre = f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)}"
        if nombre not in usados:
            usados.add(nombre)
            return nombre


def generar_jugadores():
    filas, usados, jugador_id = [], set(), 1
    for equipo, (ataque, _) in EQUIPOS.items():
        for posicion, cantidad in PLANTILLA.items():
            for i in range(cantidad):
                titular = i < TITULARES[posicion]
                partidos = int(rng.integers(28, 38) if titular else rng.integers(4, 26))
                minutos = int(partidos * (rng.uniform(78, 90) if titular else rng.uniform(25, 60)))
                f_gol = {"Portero": 0.0, "Defensa": 0.04, "Centrocampista": 0.12, "Delantero": 0.42}[posicion]
                f_asi = {"Portero": 0.005, "Defensa": 0.07, "Centrocampista": 0.16, "Delantero": 0.14}[posicion]
                xg = round(minutos / 90 * f_gol * ataque / 1.4 * rng.uniform(0.6, 1.4), 2)
                xa = round(minutos / 90 * f_asi * ataque / 1.4 * rng.uniform(0.6, 1.4), 2)
                edad = int(rng.integers(18, 36))
                valor = round(max(0.3, rng.lognormal(1.6, 0.8) * ataque * (1.4 if titular else 0.6)
                                  * (1.2 if edad < 27 else 0.8)), 1)
                filas.append({
                    "id": jugador_id, "nombre": nombre_unico(usados), "equipo": equipo,
                    "posicion": posicion, "edad": edad, "nacionalidad": str(rng.choice(NACIONALIDADES)),
                    "partidos": partidos, "minutos": minutos,
                    "goles": int(rng.poisson(max(xg, 0.01))),
                    "asistencias": int(rng.poisson(max(xa, 0.01))),
                    "xg": xg, "xa": xa,
                    "precision_pases": round(float(rng.uniform(68, 93)), 1),
                    "valor_mercado_meur": valor,
                })
                jugador_id += 1
    return pd.DataFrame(filas)


def generar_partidos():
    """Liga a doble vuelta: 38 jornadas, todos contra todos."""
    equipos = list(EQUIPOS)
    n = len(equipos)
    rotacion = equipos[:]
    ida = []
    for _ in range(n - 1):
        # Alternamos local/visitante para que nadie juegue muchas jornadas seguidas en casa
        jornada = [(rotacion[i], rotacion[n - 1 - i]) if len(ida) % 2 == 0
                   else (rotacion[n - 1 - i], rotacion[i]) for i in range(n // 2)]
        ida.append(jornada)
        rotacion = [rotacion[0]] + [rotacion[-1]] + rotacion[1:-1]
    vuelta = [[(v, l) for l, v in jornada] for jornada in ida]

    filas, partido_id, inicio = [], 1, date(2024, 8, 17)
    for num, jornada in enumerate(ida + vuelta, start=1):
        fecha = inicio + timedelta(days=7 * (num - 1))
        for local, visitante in jornada:
            at_l, def_l = EQUIPOS[local]
            at_v, def_v = EQUIPOS[visitante]
            goles_esp_local = at_l * def_v
            goles_esp_visit = at_v * def_l / 1.25
            posesion = float(np.clip(50 + (at_l - at_v) * 9 + rng.normal(0, 6), 28, 75))
            filas.append({
                "id": partido_id, "jornada": num, "fecha": fecha.isoformat(),
                "local": local, "visitante": visitante,
                "goles_local": int(rng.poisson(goles_esp_local)),
                "goles_visitante": int(rng.poisson(goles_esp_visit)),
                "posesion_local": round(posesion, 1),
                "tiros_local": int(rng.poisson(8 + goles_esp_local * 4)),
                "tiros_visitante": int(rng.poisson(7 + goles_esp_visit * 4)),
            })
            partido_id += 1
    return pd.DataFrame(filas)


def generar_carga_fisica(jugadores, semanas=12):
    base_km = {"Portero": 5.5, "Defensa": 10.2, "Centrocampista": 11.4, "Delantero": 10.0}
    base_sprints = {"Portero": 3, "Defensa": 18, "Centrocampista": 22, "Delantero": 28}
    filas, inicio = [], date(2025, 2, 3)
    for _, j in jugadores.iterrows():
        nivel = rng.uniform(0.9, 1.1)
        for s in range(semanas):
            minutos = int(np.clip(rng.normal(j["minutos"] / 38, 15), 0, 180))
            proporcion = minutos / 90
            filas.append({
                "jugador_id": int(j["id"]), "nombre": j["nombre"], "equipo": j["equipo"],
                "semana": (inicio + timedelta(weeks=s)).isoformat(),
                "minutos_jugados": minutos,
                "distancia_km": round(base_km[j["posicion"]] * proporcion * nivel * rng.uniform(0.9, 1.1), 2),
                "sprints": int(rng.poisson(base_sprints[j["posicion"]] * proporcion * nivel)),
                "velocidad_max_kmh": round(float(rng.normal(31 if j["posicion"] != "Portero" else 26, 1.5)), 1),
                "carga_entreno_ua": int(rng.normal(1800, 250) * nivel),
            })
    return pd.DataFrame(filas)


def clasificacion_desde_partidos(partidos):
    """Calcula la clasificación con el mismo formato que devuelve la API de TheSportsDB."""
    tabla = {e: {"PJ": 0, "G": 0, "E": 0, "P": 0, "GF": 0, "GC": 0, "forma": []} for e in EQUIPOS}
    for _, p in partidos.sort_values("jornada").iterrows():
        for equipo, gf, gc in ((p.local, p.goles_local, p.goles_visitante),
                               (p.visitante, p.goles_visitante, p.goles_local)):
            t = tabla[equipo]
            t["PJ"] += 1
            t["GF"] += gf
            t["GC"] += gc
            res = "W" if gf > gc else "D" if gf == gc else "L"
            t["G" if res == "W" else "E" if res == "D" else "P"] += 1
            t["forma"].append(res)
    orden = sorted(tabla.items(), key=lambda kv: (-(kv[1]["G"] * 3 + kv[1]["E"]),
                                                  -(kv[1]["GF"] - kv[1]["GC"]), -kv[1]["GF"]))
    return [{
        "intRank": str(i), "strTeam": equipo, "intPlayed": str(t["PJ"]), "intWin": str(t["G"]),
        "intDraw": str(t["E"]), "intLoss": str(t["P"]), "intGoalsFor": str(t["GF"]),
        "intGoalsAgainst": str(t["GC"]), "intGoalDifference": str(t["GF"] - t["GC"]),
        "intPoints": str(t["G"] * 3 + t["E"]), "strForm": "".join(t["forma"][-5:]),
    } for i, (equipo, t) in enumerate(orden, start=1)]


def main():
    jugadores = generar_jugadores()
    partidos = generar_partidos()
    carga = generar_carga_fisica(jugadores)

    # 1) Base de datos SQLite
    db_path = DATA_DIR / "futbol.db"
    db_path.unlink(missing_ok=True)
    with sqlite3.connect(db_path) as con:
        jugadores.to_sql("jugadores", con, index=False)
        partidos.to_sql("partidos", con, index=False)

    # 2) CSV
    carga.to_csv(DATA_DIR / "carga_fisica.csv", index=False)

    # 3) Respaldo de la API
    respaldo = DATA_DIR / "api_respaldo" / "clasificacion.json"
    respaldo.parent.mkdir(exist_ok=True)
    respaldo.write_text(json.dumps({"table": clasificacion_desde_partidos(partidos)},
                                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"jugadores: {len(jugadores)} | partidos: {len(partidos)} | registros GPS: {len(carga)}")


if __name__ == "__main__":
    main()