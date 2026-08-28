#!/usr/bin/env bash
# Pipeline completo a mano: Python mueve el dato, dbt lo transforma.
set -euo pipefail

RAIZ="$(git rev-parse --show-toplevel)"
source "$RAIZ/scripts/psql-env.sh"

cd "$RAIZ"
uv run python scripts/run_daily.py

cd "$RAIZ/dbt"
uv run dbt build --profiles-dir .

# dale permisos: chmod +x scripts/run_pipeline.sh
