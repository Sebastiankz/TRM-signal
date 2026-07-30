import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "sslmode": os.environ["DB_SSLMODE"],
    "sslrootcert": os.environ["DB_SSLROOTCERT"],
}

