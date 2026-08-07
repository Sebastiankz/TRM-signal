import pandas as pd
import psycopg

from trm_signal.config import DB_CONFIG

CONSULTA = """
    SELECT valid_from, valid_to, value
    FROM staging.trm
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

    return df