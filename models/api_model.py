"""
Modelo: clasificación de LaLiga desde la API de TheSportsDB.
Si la API no responde, usa la copia local data/api_respaldo/clasificacion.json.
"""

import json
import unicodedata

import pandas as pd
import requests

from common.config import DATA_DIR, get_config

API_URL = (f"{get_config('API_BASE_URL', 'https://www.thesportsdb.com/api/v1/json')}/"
           f"{get_config('API_KEY', '123')}/lookuptable.php")
PARAMETROS = {"l": get_config("API_LEAGUE_ID", "4335"),      # 4335 = LaLiga
              "s": get_config("API_SEASON", "2024-2025")}
RESPALDO = DATA_DIR / "api_respaldo" / "clasificacion.json"

COLUMNAS = {"intRank": "Pos", "strTeam": "Equipo", "intPlayed": "PJ", "intWin": "G",
            "intDraw": "E", "intLoss": "P", "intGoalsFor": "GF", "intGoalsAgainst": "GC",
            "intGoalDifference": "DG", "intPoints": "Pts", "strForm": "Forma"}

# La API llama a algunos equipos distinto que nuestra base de datos
ALIAS = {"barcelona": "FC Barcelona", "atletico madrid": "Atlético de Madrid",
         "athletic bilbao": "Athletic Club", "celta vigo": "Celta de Vigo",
         "leganes": "Leganés", "alaves": "Alavés", "deportivo alaves": "Alavés",
         "valladolid": "Real Valladolid", "ud las palmas": "Las Palmas"}


def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _normalizar(tabla):
    df = pd.DataFrame(tabla)
    df = df[[c for c in COLUMNAS if c in df.columns]].rename(columns=COLUMNAS)
    for col in ["Pos", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # W/D/L (inglés) -> V/E/D (español)
    df["Forma"] = (df["Forma"].fillna("").str.replace("W", "V")
                   .str.replace("D", "E").str.replace("L", "D"))
    df["Equipo"] = [ALIAS.get(_sin_tildes(e).lower(), e) for e in df["Equipo"]]
    return df.sort_values("Pos").reset_index(drop=True)


def _pedir_api():
    """Pide la clasificación a la API. Devuelve la lista de equipos (puede venir incompleta)."""
    respuesta = requests.get(API_URL, params=PARAMETROS, timeout=8)
    respuesta.raise_for_status()
    return respuesta.json().get("table") or []


def obtener_top_api():
    """Lo que devuelve la API, aunque sea parcial (la versión gratuita solo da 5 equipos).
    Devuelve None si la API no responde."""
    try:
        tabla = _pedir_api()
        return _normalizar(tabla) if tabla else None
    except Exception:
        return None


def obtener_clasificacion():
    """Clasificación COMPLETA. Devuelve (tabla, origen):
    origen = 'api' si la API da los 20 equipos, o 'respaldo' si no (se usa la copia local)."""
    try:
        tabla = _pedir_api()
        if len(tabla) < 10:
            raise ValueError("La API ha devuelto una tabla incompleta")
        return _normalizar(tabla), "api"
    except Exception:
        tabla = json.loads(RESPALDO.read_text(encoding="utf-8"))["table"]
        return _normalizar(tabla), "respaldo"