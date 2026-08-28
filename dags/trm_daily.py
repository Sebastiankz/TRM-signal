"""Pipeline diario de la TRM: extract → store → load → transform.

Descarga una ventana móvil de 7 días hacia atrás y 7 hacia adelante.
El solapamiento rellena corridas fallidas; el margen futuro cubre que
la TRM se publica con anticipación.

No se añade la ventana de backfill, que es más grande y se ejecuta por separado. Es innecesario
y costoso para airflow traer todo el tiempo el histórico completo, y además no es necesario recalcular métricas históricas.
"""

from datetime import timedelta

import pendulum
from airflow.sdk import dag, task

BOGOTA = pendulum.timezone("America/Bogota")

VENTANA_DIAS = 7
MARGEN_FUTURO_DIAS = 7

@dag(
    dag_id="trm_daily", 
    schedule="0 18 * * 1-5", # minuto, hora, día del mes, mes, día de la semana (1-5 = lunes a viernes)
    start_date=pendulum.datetime(2026, 8, 1, tz=BOGOTA),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["trm"],
    doc_md=__doc__,
)
def trm_daily():
    @task(
        retries=4,
        retry_delay=timedelta(minutes=10),
        retry_exponential_backoff=True,   
    )
    def extract() -> str:
        """Pide a la API la ventana de fechas. Devuelve el JSON crudo."""
        from datetime import date, timedelta as td

        from trm_signal.extract import fetch_trm

        hoy = date.today()
        return fetch_trm(
            hoy - td(days=VENTANA_DIAS),
            hoy + td(days=MARGEN_FUTURO_DIAS)
        )

    @task
    def store(texto: str) -> str:
        """Guarda el JSON crudo en S3 y devuelve la URI."""
        from trm_signal.storage import guardar_crudo

        return guardar_crudo(texto)

    @task
    def load(uri: str) -> int:
        """Carga el JSON crudo desde S3 a landing.trm. Devuelve filas procesadas."""
        from trm_signal.load import cargar_desde_s3

        return cargar_desde_s3(uri)

    @task.bash
    def dbt_build() -> str:
        """Construye y testea los modelos dbt. Falla si algún test falla."""
        return "cd /opt/airflow/dbt && dbt build --profiles-dir ."



    # @task
    # def transform() -> int:
    #     """Calcula métricas y reemplaza marts.trm_daily. Devuelve filas escritas."""
    #     from trm_signal.transform import calcular_metricas, guardar_marts, leer_staging

    #     return guardar_marts(calcular_metricas(leer_staging()))

    filas_cargadas = load(store(extract()))
    filas_cargadas >> dbt_build()

trm_daily()
