from datetime import date, timedelta

from trm_signal.extract import fetch_trm
from trm_signal.load import cargar_archivo
from trm_signal.storage import guardar_crudo
from trm_signal.transform import calcular_metricas, guardar_marts, leer_staging

INICIO_HISTORICO = date(1991, 12, 1)
MARGEN_FUTURO = timedelta(days=7)

"""Backfill es el proceso de llenar la base de datos con datos históricos de la TRM."""

def main() -> None:
    hasta = date.today() + MARGEN_FUTURO
    texto = fetch_trm(INICIO_HISTORICO, hasta)
    ruta = guardar_crudo(texto)
    filas = cargar_archivo(ruta)
    print(f"backfill: {filas} filas [{INICIO_HISTORICO} .. {hasta}] -> {ruta}")

if __name__ == "__main__":
    main()

metricas = guardar_marts(calcular_metricas(leer_staging()))
print(f"marts: {metricas} filas recalculadas")






