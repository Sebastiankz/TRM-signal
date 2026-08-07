import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg

from trm_signal.config import DB_CONFIG

UPSERT = """
    INSERT INTO staging.trm
        (valid_from, valid_to, value, currency, source_file)
    VALUES
        (%(valid_from)s, %(valid_to)s, %(value)s, %(currency)s, %(source_file)s)
    ON CONFLICT (valid_from) DO UPDATE SET
        valid_to    = EXCLUDED.valid_to,
        value       = EXCLUDED.value,
        currency    = EXCLUDED.currency,
        source_file = EXCLUDED.source_file,
        ingested_at = now()
"""

def _a_fila(registro: dict, origen: Path) -> dict:
    """Traduce un registro de la API al esquema de staging."""
    return {
        "valid_from": datetime.fromisoformat(registro["vigenciadesde"]).date(),
        "valid_to": datetime.fromisoformat(registro["vigenciahasta"]).date(),
        "value": Decimal(registro["valor"]),
        "currency": registro["unidad"],
        "source_file": str(origen),       
    }

def cargar_archivo(ruta: Path) -> int:
    """Carga un archivo crudo a staging.trm. Devuelve cuántas filas procesó."""
    registros = json.loads(ruta.read_text(encoding="utf-8"))
    if not registros:
        return 0 # sabados, domingos y festivos

    filas = [_a_fila(r, ruta) for r in registros]

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT, filas)

    return len(filas)


