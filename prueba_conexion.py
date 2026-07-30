import psycopg
from src.trm_signal.config import DB_CONFIG

with psycopg.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        print(cur.fetchone()[0])
