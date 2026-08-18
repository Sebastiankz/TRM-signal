---
name: user-learning-profile
description: Perfil del desarrollador junior en TRM-signal y cómo prefiere aprender
metadata:
  type: user
---

Desarrollador junior trabajando en TRM-signal (proyecto de datos, señales sobre la TRM, pipeline
con Airflow + Postgres en AWS RDS). Está en fase de aprendizaje activo de infraestructura de datos:
conexión a bases remotas, SSL, orquestación con Airflow, variables de entorno.

Aprende con enfoque socrático en español — reforzado también por CLAUDE.local.md del repo (que
tiene prioridad y ya cubre las reglas generales de "explicar antes de codear", "no modificar
archivos sin permiso", "dar snippets para que los escriba a mano"). No hace falta repetir esas
reglas acá; sí vale la pena registrar matices específicos de este usuario que no están en el
CLAUDE.md, como confusiones recurrentes.

**Confusión detectada (2026-08-18):** no tenía claro que las variables de entorno con prefijo
propio (`DB_HOST`, etc., usadas por su código Python) y las variables oficiales de libpq
(`PGHOST`, etc., usadas por `psql`) son namespaces completamente distintos — exportar/tener un
`.env` no alimenta automáticamente a `psql`. Buen concepto para verificar que haya quedado claro
en próximas interacciones sobre conexión a bases de datos. Ver [[project-rds-connection-setup]].
