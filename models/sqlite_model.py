"""Modelo: acceso a la base de datos SQLite (jugadores y partidos)."""

import sqlite3

import pandas as pd

from common.config import DATA_DIR

DB_PATH = DATA_DIR / "futbol.db"


def _consultar(sql):
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query(sql, con)


def obtener_jugadores():
    return _consultar("SELECT * FROM jugadores ORDER BY equipo, nombre")


def obtener_partidos():
    df = _consultar("SELECT * FROM partidos ORDER BY jornada")
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df
