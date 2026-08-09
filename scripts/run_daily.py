
"""Actualiza la base con los últimos datos de la TRM.

Descarga una ventana móvil de 7 días hacia atrás y 7 hacia adelante:
el solapamiento hacia atrás rellena corridas fallidas, y el margen futuro
cubre que la TRM se publica con anticipación.
"""

from datetime import date, timedelta

from trm_signal.extract import fetch_trm
from trm_signal.load import cargar_archivo
from trm_signal.storage import guardar_crudo
from trm_signal.transform import leer_staging, calcular_metricas, guardar_marts

VENTANA = timedelta(days=7)
MARGEN_FUTURO = timedelta(days=7)

def main() -> None:
    hoy = date.today()
    desde, hasta = hoy - VENTANA, hoy + MARGEN_FUTURO

    texto = fetch_trm(desde, hasta)
    ruta = guardar_crudo(texto)
    filas = cargar_archivo(ruta)
    print(f"diario: {filas} filas [{desde} .. {hasta}] -> {ruta}")

    metricas = guardar_marts(calcular_metricas(leer_staging()))
    print(f"marts: {metricas} filas recalculadas")

if __name__ == "__main__":
    main()

