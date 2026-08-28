FROM apache/airflow:3.3.0

RUN pip install --no-cache-dir \
    "psycopg[binary]" \
    requests \
    python-dotenv \
    boto3 \
    "dbt-postgres>=1.9"