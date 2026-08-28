# TRM Signal

**La TRM se publica todos los días como un número suelto. Nadie te dice si el de hoy es normal.**

Colombia recibió USD 13.098 millones en remesas durante 2025 — cerca del 3 % del PIB, con hasta 2,1 millones de personas beneficiadas directamente. A eso se suma quien cobra un freelance en dólares, importa, o simplemente ahorra. Todos enfrentan la misma decisión: *¿convierto hoy o espero?*

Y todos tienen la misma información: un número, sin contexto.

Este proyecto convierte ese dato aislado en una señal legible:

> **29 de agosto de 2026 — TRM $3.202,79**
> Subió 1,86 % respecto a la publicación anterior.
> Está 1,41 % por encima de su promedio de los últimos 30 días.
> Ese movimiento es más grande que el **98 %** de los movimientos del último año.

Nada de eso existe ya calculado en ningún sitio público.

---

## Qué hace

Todos los días hábiles, sin intervención manual: descarga la TRM oficial, preserva el JSON crudo, lo carga a un warehouse, recalcula las métricas y valida 23 supuestos sobre el dato.

**35 años de historia** — 8.336 publicaciones desde el 2 de diciembre de 1991.

## Arquitectura

```
datos.gov.co  (API Socrata, dataset 32sa-8pi3)
      │
      ▼   Python: extract
   S3  raw/2026/08/29/trm_*.json          JSON verbatim, inmutable
      │
      ▼   Python: load  (UPSERT idempotente)
   RDS landing.trm                         una fila por publicación
      │
      ▼   dbt build
   RDS staging.stg_trm                     view
       intermediate.int_trm_returns        table
       intermediate.int_trm_rolling        view
       intermediate.int_trm_pctl           view
       marts.trm_daily                     table  ← la serie con métricas
       marts.trm_by_weekday                table
       marts.trm_month_end                 table

Orquestado por Airflow — 18:00 hora Colombia, lunes a viernes.
```

Cada capa se reconstruye desde la anterior, nunca al revés. Si mañana cambia una fórmula, se recalculan 35 años sin llamar a la API ni una vez.

---

## Tres hallazgos

### 1. Existe un gradiente por día de la semana — y casi nadie lo mediría bien

| Día de mercado | n | Variación media | Error estándar |
|---|---|---|---|
| **Lunes** | 1.347 | **+0,0723 %** | 0,0199 |
| Martes | 1.775 | +0,0485 % | 0,0160 |
| Miércoles | 1.770 | +0,0205 % | 0,0155 |
| Jueves | 1.716 | −0,0081 % | 0,0163 |
| **Viernes** | 1.727 | **−0,0153 %** | 0,0155 |

La diferencia lunes-viernes da **t ≈ 3,5**. Lo fuerte no es que el lunes destaque —eso podría ser azar entre cinco pruebas— sino que los cinco días caen en **orden monótono**.

**La trampa metodológica:** agrupar por la fecha de publicación da un resultado falso. En 35 años el dataset tiene **1.727 sábados y un solo lunes**, porque la publicación del sábado rige hasta el lunes. Hay que agrupar por el **día hábil cuyas operaciones produjeron el valor**, no por el día en que rige. Con la fecha equivocada, la pregunta parece incontestable; con la correcta, la respuesta estaba ahí desde 1991.

### 2. Las variaciones tienen colas pesadas — el z-score engaña

| Umbral | Observado | Si fuera normal | Exceso |
|---|---|---|---|
| \|z\| > 3 | 1,5 % de los días | 0,3 % | 5,6× |
| \|z\| > 4 | 45 veces | menos de 1 | **86×** |
| \|z\| > 5 | 24 veces | ≈ 0 | — |

Curtosis **9,4** contra 3 de una distribución normal. Un movimiento de 4 desviaciones debería ocurrir una vez cada 30 años; ocurrió 45 veces.

Por eso el proyecto reporta **percentil empírico** además del z-score: el z-score comunica bien, pero traducirlo a probabilidad sería falso por un factor de 5. El percentil es un conteo, no una inferencia.

El movimiento más extremo de la serie: **10 de marzo de 2020, +6,11 %** (z = 7,89).

### 3. No hay efecto de fin de mes

| Tramo | n | Variación media | t |
|---|---|---|---|
| Primeros 3 días | 1.251 | −0,0303 % | −1,47 |
| Resto del mes | 5.833 | +0,0322 % | +3,69 |
| Últimos 3 días | 1.251 | +0,0236 % | +1,29 |

Los últimos 3 días no se distinguen del resto (**t = −0,43**). Es un resultado negativo y se reporta como tal.

*(Los primeros 3 días sí quedan por debajo del resto, con t ≈ −2,8. No se afirma como hallazgo: son tres comparaciones y esa es la única significativa. Queda como hipótesis a verificar.)*

---

## Lo que este proyecto **no** es

**No es asesoría financiera.** Entrega información descriptiva —qué tan atípico es el movimiento de hoy frente al histórico— no una recomendación de compra o venta.

**El gradiente semanal no es accionable.** La diferencia lunes-viernes es de ~0,09 %, muy por debajo del spread de conversión que paga cualquier persona real. Es estadísticamente sólido y económicamente irrelevante para quien convierte dólares.

**La TRM refleja el día hábil anterior.** No es el mercado en tiempo real: el valor vigente hoy se calculó con las operaciones de ayer.

**Los hallazgos agrupan 35 años** con regímenes cambiarios distintos — banda hasta 1999, flotación después. Partir la serie por década es la verificación pendiente.

---

## Stack

| Etapa | Herramienta |
|---|---|
| Extracción | Python + `requests` |
| Zona raw | AWS S3 |
| Warehouse | PostgreSQL en AWS RDS |
| Transformación | dbt (7 modelos, 23 tests) |
| Orquestación | Apache Airflow 3.3 (Docker Compose, LocalExecutor) |

## Decisiones de ingeniería

**Idempotencia por clave natural.** `valid_from` no se repite en 8.336 publicaciones, así que es la clave primaria y la carga usa `ON CONFLICT DO UPDATE`. La base impide el duplicado — no el código.

**Ventana solapada de 7 días.** La corrida diaria pide siempre los últimos 7 días. Si una corrida falla, la siguiente rellena el hueco sola. El auto-sanado solo es posible porque la carga es idempotente.

**El JSON crudo se preserva antes de interpretarlo.** Cada respuesta de la API queda intacta en S3, particionada por fecha de ingesta en UTC. Reprocesar 35 años no cuesta una sola llamada a la fuente.

**Los tests protegen supuestos, no sintaxis.** El más importante, `assert_serie_contigua`, verifica que cada publicación empiece el día después de que expira la anterior. De ese invariante depende toda la definición de "día de mercado": si la fuente introduce un hueco, el test falla en vez de dejar que las métricas se degraden en silencio.

---

## Cómo correrlo

**Requisitos:** Python 3.12, Docker, una base PostgreSQL y un bucket S3.

```bash
uv sync
cp .env.example .env        # completar credenciales
psql -f sql/001_landing.sql
```

Carga histórica y pipeline manual:

```bash
uv run python scripts/run_backfill.py   # una sola vez: 35 años
./scripts/run_pipeline.sh               # Python mueve, dbt transforma
```

Orquestado:

```bash
docker compose --env-file .env.docker up -d
# UI en http://localhost:8080 — activar el DAG trm_daily
```

Documentación y linaje de los modelos:

```bash
cd dbt && uv run dbt docs serve --profiles-dir . --port 8081
```

---

## Documentación

| Archivo | Contenido |
|---|---|
| [docs/metricas.md](docs/metricas.md) | Qué significa cada métrica y cómo interpretarla |
| [docs/exploracion_api.md](docs/exploracion_api.md) | Comportamiento real de la fuente y sus trampas |
| [docs/decisiones.md](docs/decisiones.md) | Decisiones de diseño y alternativas descartadas |
| [docs/hallazgos.md](docs/hallazgos.md) | Los hallazgos con su desarrollo completo |

## Roadmap

- **Fase 4** — Dashboard (Streamlit) con la serie, el promedio móvil y la señal del día
- **Fase 5** — Alertas cuando la señal supere un umbral; partir el análisis por década

---

*Fuente: [datos.gov.co, dataset 32sa-8pi3](https://www.datos.gov.co/resource/32sa-8pi3.json), que replica la serie oficial del Banco de la República. Cifras de remesas: Banco de la República y Migración Colombia.*
