"""Backfill es el proceso de llenar la base de datos con datos históricos de la TRM."""

from datetime import date, timedelta
from trm_signal.extract import fetch_trm
from trm_signal.load import cargar_desde_s3
from trm_signal.storage import guardar_crudo

INICIO_HISTORICO = date(1991, 12, 1)
MARGEN_FUTURO = timedelta(days=7)

def main() -> None:
    hasta = date.today() + MARGEN_FUTURO
    texto = fetch_trm(INICIO_HISTORICO, hasta)
    uri = guardar_crudo(texto)
    filas = cargar_desde_s3(uri)
    print(f"backfill: {filas} filas [{INICIO_HISTORICO} .. {hasta}] -> {uri}")

if __name__ == "__main__":
    main()








