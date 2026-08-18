---
name: project-rds-connection-setup
description: Estado de la configuración de conexión psql/PG* hacia RDS en TRM-signal, verificado el 2026-08-18
metadata:
  type: project
---

Verificado el 2026-08-18 (leyendo el entorno, sin exponer secretos): no había variables `PG*`
exportadas en el shell actual, no existía `~/.pgpass`, y `~/.zshrc` no tenía ninguna referencia a
`PG*`. Es decir, la sugerencia previa (exportar PGHOST/PGPORT/PGDATABASE/PGUSER/PGSSLMODE/PGSSLROOTCERT
en `~/.zshrc` y usar `~/.pgpass`) **no se había aplicado todavía** en ese momento.

El `.env` del proyecto usa el prefijo `DB_` (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
DB_SSLMODE, DB_SSLROOTCERT) — estos nombres los lee el código Python (via `os.getenv`), pero
**no** son reconocidos por libpq/psql, que solo entiende las variables oficiales `PG*`. Cargar el
`.env` tal cual (`source .env`) no resuelve la conexión de psql por sí solo; hace falta mapear a
`PG*` o pasar flags/connection string explícitos.

**Por qué importa:** si en una próxima sesión el usuario reporta de nuevo
`connection to server on socket "/tmp/.s.PGSQL.5432" failed`, no asumir que ya configuró las
variables — volver a verificar (`env | grep ^PG`, `ls -la ~/.pgpass`, `grep PG ~/.zshrc`) antes de
diagnosticar, porque es probable que siga sin aplicar el cambio o que haya recargado mal la shell.

**Cómo aplicar:** al ayudar con psql/conexión a RDS en este proyecto, recordar el matiz DB_* vs PG*
y confirmar el estado real del entorno antes de dar por sentado que "ya está resuelto". Dato de
infra (no cambia salvo migración de proveedor): Postgres vive en AWS RDS
(trm-signal-db.ccve8msw6bd0.us-east-1.rds.amazonaws.com:5432, db `trm`), requiere
`sslmode=verify-full` con `sslrootcert` apuntando a `global-bundle.pem` en la raíz del repo.
