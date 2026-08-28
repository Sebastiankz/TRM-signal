"""Actualiza landing.trm con los últimos datos de la TRM.

Ventana móvil de 7 días hacia atrás y 7 hacia adelante: el solapamiento
rellena corridas fallidas, el margen futuro cubre la publicación anticipada.

Las métricas se calculan aparte, con `dbt build`.
"""

from datetime import date, timedelta

from trm_signal.extract import fetch_trm
from trm_signal.load import cargar_desde_s3
from trm_signal.storage import guardar_crudo

VENTANA = timedelta(days=7)
MARGEN_FUTURO = timedelta(days=7)


def main() -> None:
    hoy = date.today()
    desde, hasta = hoy - VENTANA, hoy + MARGEN_FUTURO

    texto = fetch_trm(desde, hasta)
    uri = guardar_crudo(texto)
    filas = cargar_desde_s3(uri)
    print(f"diario: {filas} filas [{desde} .. {hasta}] -> {uri}")


if __name__ == "__main__":
    main()
