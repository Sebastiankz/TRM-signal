from datetime import date, timedelta

from trm_signal.extract import fetch_trm
from trm_signal.load import cargar_archivo
from trm_signal.storage import guardar_crudo
from trm_signal.transform import leer_staging, calcular_metricas, guardar_marts

VENTANA = timedelta(days=7)
MARGEN_FUTURO = timedelta(days=7)


metricas = guardar_marts(calcular_metricas(leer_staging()))
print(f"marts: {metricas} filas recalculadas")

"""Run diario es el proceso de actualizar la base de datos con los últimos datos de la TRM.
Se ejecuta todos los días, y descarga la TRM de los últimos 7 días más 7 días de margen futuro, para cubrir cualquier cambio en la TRM que pueda ocurrir en los últimos días."""

def main() -> None:
    hoy = date.today()
    desde, hasta = hoy - VENTANA, hoy + MARGEN_FUTURO

    texto = fetch_trm(desde, hasta)
    ruta = guardar_crudo(texto)
    filas = cargar_archivo(ruta)
    print(f"diario: {filas} filas [{desde} .. {hasta}] -> {ruta}")

if __name__ == "__main__":
    main()