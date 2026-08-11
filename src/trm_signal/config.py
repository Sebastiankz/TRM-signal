"""Configuración del proyecto, leída del entorno."""

import os
from pathlib import Path

from dotenv import load_dotenv

# La raíz del proyecto se deriva de la ubicación de ESTE archivo,
# no del directorio desde el que se ejecute:
#   src/trm_signal/config.py -> src/trm_signal -> src -> raíz

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

load_dotenv(RAIZ_PROYECTO / ".env")

S3_BUCKET = os.environ["S3_BUCKET"]
DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "sslmode": os.environ["DB_SSLMODE"],
    "sslrootcert": os.environ["DB_SSLROOTCERT"],

}

