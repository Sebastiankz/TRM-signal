# Carga el JSON crudo de la zona raw a staging.trm.

import json
from datetime import datetime
from decimal import Decimal
#from pathlib import Path

import psycopg

from trm_signal.config import DB_CONFIG
from trm_signal.storage import descargar_crudo

UPSERT = """
    INSERT INTO landing.trm
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

def _a_fila(registro: dict, origen: str) -> dict:
    """Traduce un registro de la API al esquema de staging."""
    return {
        "valid_from": datetime.fromisoformat(registro["vigenciadesde"]).date(),
        "valid_to": datetime.fromisoformat(registro["vigenciahasta"]).date(),
        "value": Decimal(registro["valor"]),
        "currency": registro["unidad"],
        "source_file": str(origen),       
    }

def cargar_texto(texto:str, origen: str) -> int:
    """Parsea el JSON crudo y hace upsert a staging.trm.

    `origen` solo se registra para trazabilidad; no se usa para leer nada.
    Devuelve cuántas filas procesó.
    """
    registros = json.loads(texto)
    if not registros:
        return 0 # sabados, domingos y festivos no hay TRM, la API devuelve []
    
    filas = [_a_fila(r, origen) for r in registros]

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.executemany(UPSERT, filas)

    return len(filas)

def cargar_desde_s3(uri: str) -> int:
    """Descarga un objeto de la zona raw y lo carga a staging."""
    return cargar_texto(descargar_crudo(uri), uri)


