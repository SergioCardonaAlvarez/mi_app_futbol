"""Modelo: acceso al CSV de carga física (datos GPS semanales)."""

import pandas as pd

from common.config import DATA_DIR

CSV_PATH = DATA_DIR / "carga_fisica.csv"


def obtener_carga_fisica():
    return pd.read_csv(CSV_PATH, parse_dates=["semana"])
