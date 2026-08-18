#!/usr/bin/env bash
# Traduce las variables DB_* del .env a los nombres PG* que entiende libpq.
# Uso:  source scripts/psql-env.sh
set -a
source "$(git rev-parse --show-toplevel)/.env"
set +a

export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"
export PGDATABASE="$DB_NAME"
export PGUSER="$DB_USER"
export PGPASSWORD="$DB_PASSWORD"
export PGSSLMODE="$DB_SSLMODE"
export PGSSLROOTCERT="$DB_SSLROOTCERT"
