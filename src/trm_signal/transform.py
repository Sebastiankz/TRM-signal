"""módulo de transformación de la señal TRM. Lee la zona staging, calcula métricas derivadas y escribe la zona marts."""

import pandas as pd
import psycopg

from trm_signal.config import DB_CONFIG

CONSULTA = """
    SELECT valid_from, valid_to, value
    FROM landing.trm
    ORDER BY valid_from ASC
"""

DIAS_HABILES_ANIO = 252
MINIMO_PARA_VOLATILIDAD = 60

def leer_staging() -> pd.DataFrame:
    """Lee la tabla staging.trm y devuelve un DataFrame con las columnas valid_from, valid_to y value."""
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(CONSULTA)
            filas = cur.fetchall()
            columnas = [d.name for d in cur.description]

    df = pd.DataFrame(filas, columns=columnas)
    df["valid_from"] = pd.to_datetime(df["valid_from"])
    df["valid_to"] = pd.to_datetime(df["valid_to"])
    df["value"] = df["value"].astype(float)
    return df

def calcular_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega las métricas derivadas a la serie."""
    df = df.sort_values("valid_from").reset_index(drop=True)

    # El día de mercado que produjo este valor: el hábil anterior
    df["market_date"] = df["valid_from"] - pd.tseries.offsets.BDay(1)

    # Variación respecto a la publicación anterior (= 1 día hábil de mercado)
    df["pct_change"] = df["value"].pct_change() * 100

    # Promedios móviles: nulos hasta tener la ventana completa
    df["ma_7"] = df["value"].rolling(7, min_periods=7).mean()
    df["ma_30"] = df["value"].rolling(30, min_periods=30).mean()

    # Qué tan lejos está hoy de su promedio del último mes
    df["pct_vs_ma_30"] = (df["value"] / df["ma_30"] - 1) * 100

    # Z-score contra la volatilidad del último año, no de toda la historia
    ventana = df["pct_change"].rolling(
        DIAS_HABILES_ANIO, min_periods=MINIMO_PARA_VOLATILIDAD
    )
    df["z_score"] = (df["pct_change"] - ventana.mean()) / ventana.std()

    # Percentil empírico: qué lugar ocupa el movimiento de hoy entre
    # los últimos 252. No supone ninguna distribución, solo cuenta.

    df["pctl_abs"] = (
        df["pct_change"]
        .abs()
        .rolling(DIAS_HABILES_ANIO, min_periods=MINIMO_PARA_VOLATILIDAD)
        .rank(pct=True)
        * 100
    )

    return df

COLUMNAS_MARTS = [
    "valid_from", "valid_to", "market_date", "value", "pct_change",
    "ma_7", "ma_30", "pct_vs_ma_30", "z_score", "pctl_abs",
]

INSERT_MARTS = f"""
    INSERT INTO marts.trm_daily ({", ".join(COLUMNAS_MARTS)})
    VALUES ({", ".join(["%s"] * len(COLUMNAS_MARTS))})
"""

def _preparar_filas(df: pd.DataFrame) -> list[tuple]:
    """Convierte el DataFrame a tuplas listas para psycopg."""
    datos = df[COLUMNAS_MARTS].copy()

    for col in ("valid_from", "valid_to", "market_date"):
        datos[col] = datos[col].dt.date # pandas guarda fechas como Timestamp, que psycopg no entiende. Convertimos a date. (Timestamp('2026-08-04 00:00:00') → date(2026, 8, 4))

    # NaN/NaT de pandas -> None, que psycopg traduce a NULL
    datos = datos.astype(object).where(pd.notna(datos), None)

    return list(datos.itertuples(index=False, name=None))


def guardar_marts(df: pd.DataFrame) -> int:
    """Reemplaza por completo marts.trm_daily. Devuelve filas escritas."""
    filas = _preparar_filas(df)

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE marts.trm_daily")
            cur.executemany(INSERT_MARTS, filas)

    return len(filas)