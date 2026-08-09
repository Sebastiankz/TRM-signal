# Fase 2 — Orquestación con Airflow

> **Objetivo de la fase:** el DAG corriendo solo, varios días seguidos, sin intervención manual.
>
> **Estado del proyecto al escribir esto:** Fase 1 cerrada en el commit `c32ff85`.

---

## Índice

- [Parte A — Verificación de la Fase 1](#parte-a--verificación-de-la-fase-1)
- [Parte B — Plan de ejecución](#parte-b--plan-de-ejecución)
  - [Paso 0 — Restaurar el acceso a RDS](#paso-0--restaurar-el-acceso-a-rds)
  - [Paso 1 — Arreglar el bug de orden](#paso-1--arreglar-el-bug-de-orden)
  - [Paso 2 — Migrar la zona raw a S3](#paso-2--migrar-la-zona-raw-a-s3)
  - [Paso 3 — Preparar la configuración para Docker](#paso-3--preparar-la-configuración-para-docker)
  - [Paso 4 — Levantar Airflow con Docker Compose](#paso-4--levantar-airflow-con-docker-compose)
  - [Paso 5 — Escribir el DAG](#paso-5--escribir-el-dag)
  - [Paso 6 — Verificación end-to-end](#paso-6--verificación-end-to-end)
- [Resumen de archivos](#resumen-de-archivos)
- [Riesgos conocidos](#riesgos-conocidos)

---

## Por qué esta fase empieza arreglando la Fase 1

> **Airflow no arregla un pipeline roto. Solo lo ejecuta roto todos los días a la misma hora.**

Antes de envolver el código en un DAG hay que confirmar que el flujo manual funciona de verdad. La verificación encontró que sí funciona, pero con tres brechas que hay que cerrar *primero*. Por eso la Fase 2 tiene dos mitades: **sanear** y después **orquestar**.

---

# Parte A — Verificación de la Fase 1

Criterio original (sección 10 del documento de planeación):

> *Script en Python que llama la API, guarda el crudo en S3, calcula las métricas básicas con pandas, y carga a Postgres. Todo corrido a mano.*

## Lo que sí está resuelto ✅

| Pieza | Archivo | Estado |
|---|---|---|
| Extracción de la API | `src/trm_signal/extract.py` | Funciona. Filtra por rango con `$where`, ordena, `raise_for_status()`, timeout de 30 s. Endpoint verificado en vivo: HTTP 200. |
| Preservación del crudo | `src/trm_signal/storage.py` | Guarda el JSON **sin modificar**, particionado `YYYY/MM/DD`. El principio de "zona raw" está bien entendido. |
| Carga a staging | `src/trm_signal/load.py` | UPSERT con `ON CONFLICT (valid_from) DO UPDATE`. **Idempotente** — esto es justamente lo que hará seguros los reintentos. Maneja respuesta vacía (fines de semana / festivos). |
| Métricas con pandas | `src/trm_signal/transform.py` | `pct_change`, `ma_7`, `ma_30`, `pct_vs_ma_30`, `z_score` (ventana móvil de 252 días) y `pctl_abs`. Excede lo que pedía la fase. |
| Modelo en Postgres | `sql/001_staging.sql`, `sql/002_marts.sql` | Esquemas separados, PK, `CHECK` de rango y de valor positivo, `ingested_at` / `computed_at`. |
| Backfill ejecutado | `data/raw/2026/08/07/trm_20260807T111205.json` | **8 322 registros reales**, de 1991-12-02 a 2026-08-07. El histórico completo está descargado. |
| Documentación | `docs/exploracion_api.md`, `docs/metricas.md`, `docs/hallazgos.md` | Muy por encima de lo exigido. `metricas.md` explica *por qué* se guardan z-score **y** percentil (colas pesadas). Es material de portafolio. |

## Lo que falta o está mal ❌

### 1. 🐛 Bug de orden de ejecución — bloqueante

En `scripts/run_daily.py:12` y `scripts/run_backfill.py:11` la recalculación de marts está **a nivel de módulo**, fuera de `main()`:

```python
metricas = guardar_marts(calcular_metricas(leer_staging()))   # ← se ejecuta al importar
print(f"marts: {metricas} filas recalculadas")

def main() -> None:
    ...  # extract → store → load a staging
```

Python ejecuta el módulo de arriba abajo: **primero recalcula marts** (con el staging viejo) y **después** carga los datos nuevos. Resultado: `marts.trm_daily` va siempre **una corrida atrasada** respecto a `staging.trm`.

> 🤔 **Para pensar:** si corrés el script dos veces seguidas sin datos nuevos, ¿marts queda correcto? ¿Y si lo corrés una sola vez al día, qué dato le falta al mart?

Efecto secundario: los strings de las líneas 15-16 / 14 **no son docstrings**. Al ir después de código son expresiones sueltas que Python evalúa y descarta. Un docstring de módulo debe ser la primera sentencia del archivo.

### 2. ⚠️ No hay S3 — el crudo está en disco local

`storage.py:4` usa `RAW_DIR = Path("data/raw")`. La arquitectura (sección 6 del documento) y la Fase 1 dicen S3. No hay `boto3` en `pyproject.toml` y `aws sts get-caller-identity` responde `NoCredentials`.

Además `data/` está en `.gitignore:224`, así que hoy la zona raw **no está respaldada en ningún lado**. Si se borra el disco, se pierden 35 años de historia descargada.

### 3. ⚠️ Rutas relativas — romperán dentro de Docker

Dos rutas se resuelven contra el *current working directory*:

- `storage.py:4` → `data/raw`
- `.env` → `DB_SSLROOTCERT=./global-bundle.pem`

Funcionan hoy porque corrés desde la raíz del repo. Dentro de un contenedor de Airflow el cwd es `/opt/airflow` y ambas fallan.

### 4. ⚠️ La base RDS está inalcanzable

Diagnóstico ejecutado el 2026-08-09: el DNS resuelve (`trm-signal-db…us-east-1.rds.amazonaws.com` → `52.45.216.176`) pero el TCP al puerto 5432 hace timeout. La red general sí funciona — la API de datos.gov.co respondió 200 en la misma corrida.

Causa típica: la instancia está detenida, o el security group tiene tu IP anterior en la regla de entrada y tu IP cambió.

**Consecuencia:** no se pudieron verificar los conteos reales de `staging.trm` ni de `marts.trm_daily`. Esa parte de la verificación queda pendiente hasta el Paso 0.

### 5. Menores — no bloquean

- Sin tests ni logging (usa `print`).
- `transform.py:34` usa `BDay(1)` para `market_date`, que ignora los festivos colombianos. Aproximación conocida; vale documentarla.
- `README.md` tiene una línea. Es alcance de Fase 4.
- Las migraciones SQL se corrieron a mano, sin registro de cuándo.

## Veredicto

**Fase 1 está sustancialmente completa** en lo conceptual: el flujo `extract → raw → staging → marts` existe, corrió con datos reales y produjo hallazgos documentados.

**Pero no está lista para automatizar.** El bug de orden y la ausencia de S3 se resuelven en los pasos 1 y 2 de esta fase.

---

# Parte B — Plan de ejecución

## Decisiones tomadas

| Decisión | Elección | Razón |
|---|---|---|
| Zona raw | Migrar a **S3** en esta fase | Cierra la brecha con la arquitectura y resuelve solo el problema del disco efímero del contenedor |
| Airflow | Partir del **compose oficial 3.3.0** y quitarle lo que no se usa | Se aprende leyendo el archivo real de producción y decidiendo qué sobra |
| Código en el contenedor | **Volumen montado + `PYTHONPATH`** | Editás en tu máquina y el DAG lo ve al instante, sin reconstruir imagen |
| Diseño del DAG | **4 tareas:** extract → store → load → transform | Ves qué paso falló, reintentás solo ese, y practicás XCom |

## Principio rector

> **El DAG es una capa delgada de orquestación. La lógica vive en el paquete `trm_signal`.**

El DAG solo debe decir *en qué orden* y *bajo qué condiciones* correr las funciones — nunca contener lógica de negocio.

**Prueba de fuego:** `scripts/run_daily.py` debe seguir funcionando después de la Fase 2. Si dejó de funcionar, la lógica se filtró al DAG.

---

## Paso 0 — Restaurar el acceso a RDS

Nada más se puede verificar hasta resolver esto.

1. Consola AWS → RDS → si la instancia está `stopped`, arrancarla.
2. Si está `available`, revisar el Security Group: la regla de entrada al 5432 debe tener tu IP pública actual.
   ```bash
   curl -s ifconfig.me
   ```
3. Confirmar con una consulta de solo lectura:
   ```bash
   .venv/bin/python -c "
   import psycopg
   from trm_signal.config import DB_CONFIG
   with psycopg.connect(**DB_CONFIG) as c:
       print('staging:', c.execute('SELECT count(*), max(valid_from) FROM staging.trm').fetchone())
       print('marts:  ', c.execute('SELECT count(*), max(valid_from) FROM marts.trm_daily').fetchone())
   "
   ```

**Esperado:** ~8 322 filas en staging, con `max(valid_from)` = 2026-08-07.

**Si marts tiene menos filas o un `max(valid_from)` anterior** → es el bug #1 confirmado en producción. Buena señal: significa que entendiste el diagnóstico antes de verlo.

---

## Paso 1 — Arreglar el bug de orden

Mover la recalculación de marts **adentro** de `main()`, al final, en ambos scripts:

```python
"""Docstring del módulo — primera sentencia del archivo."""
from datetime import date, timedelta

from trm_signal.extract import fetch_trm
# ... resto de imports

VENTANA = timedelta(days=7)
MARGEN_FUTURO = timedelta(days=7)


def main() -> None:
    hoy = date.today()
    desde, hasta = hoy - VENTANA, hoy + MARGEN_FUTURO

    texto = fetch_trm(desde, hasta)
    ruta = guardar_crudo(texto)
    filas = cargar_archivo(ruta)
    print(f"diario: {filas} filas [{desde} .. {hasta}] -> {ruta}")

    metricas = guardar_marts(calcular_metricas(leer_staging()))
    print(f"marts: {metricas} filas recalculadas")


if __name__ == "__main__":
    main()
```

**Verificación:** correr `run_daily.py` una vez y volver a comparar `max(valid_from)` de staging contra marts. Deben coincidir.

---

## Paso 2 — Migrar la zona raw a S3

### 2.1 Infraestructura

- Crear el bucket (nombre sugerido `trm-signal-raw-<sufijo-único>`), **misma región que RDS** (`us-east-1`).
- Bloquear acceso público. Habilitar versionado.
- Usuario IAM con política mínima: `s3:PutObject` y `s3:GetObject` **solo sobre ese bucket**.
- `aws configure` en local con esas llaves.

### 2.2 Refactor de `storage.py`

**El problema de diseño:** hoy `load.py` recibe un `Path` y lo lee del disco. Con S3 ya no hay `Path`. Hay dos formas de resolverlo, y la elección importa:

| Opción | Cómo | Problema |
|---|---|---|
| **A** | `store` devuelve el contenido, `load` lo recibe | El crudo viaja por XCom. En un backfill son 976 KB metidos en la base de metadata de Airflow. |
| **B ✅** | `store` devuelve la **URI** `s3://…`, `load` la descarga | Se pasa una *referencia*, no un *payload* |

> 📌 **Regla general de Airflow:** XCom es para **metadata pequeña**, no para datos. El límite práctico son unos pocos KB.

Firmas propuestas — el cuerpo lo escribís vos:

```python
# src/trm_signal/storage.py
S3_BUCKET = os.environ["S3_BUCKET"]

def guardar_crudo(contenido: str, momento: datetime | None = None) -> str:
    """Sube la respuesta cruda a S3 sin modificarla. Devuelve la URI s3://..."""

def descargar_crudo(uri: str) -> str:
    """Descarga un objeto de la zona raw y devuelve su contenido como texto."""
```

Mantené el mismo esquema de key: `raw/2026/08/09/trm_20260809T180000.json`.

> 🤔 **Para pensar:** ¿por qué conviene que `load` lea de S3 en vez de recibir el texto directo de `extract`?
> *Pista:* pensá qué pasa si mañana descubrís un bug en `_a_fila` y tenés que reprocesar 35 años de historia. ¿Querés volver a llamar la API 8 322 veces?

### 2.3 Ajustar `load.py`

Separar *de dónde viene el texto* de *cómo se parsea*:

```python
def cargar_texto(texto: str, origen: str) -> int:
    """Parsea el JSON crudo y hace upsert a staging.trm. Devuelve filas procesadas."""

def cargar_desde_s3(uri: str) -> int:
    """Descarga de la zona raw y carga a staging. Devuelve filas procesadas."""
```

`source_file` en staging pasa a guardar la URI de S3 — mejora la trazabilidad.

### 2.4 Dependencias

Agregar `boto3` a `pyproject.toml` y correr `uv sync`.

---

## Paso 3 — Preparar la configuración para Docker

El problema: `config.py` lee `DB_SSLROOTCERT=./global-bundle.pem`, una ruta relativa al cwd.

La solución mínima — que la ruta venga del entorno, y que en el contenedor apunte a una ruta absoluta montada:

| Entorno | Valor |
|---|---|
| Local | `DB_SSLROOTCERT=./global-bundle.pem` (se mantiene, funciona desde la raíz) |
| Contenedor | `DB_SSLROOTCERT=/opt/airflow/certs/global-bundle.pem` |

Con S3, el problema de `RAW_DIR` se resuelve solo: la ruta local desaparece.

Actualizar `.env.example` con las llaves nuevas: `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`.

---

## Paso 4 — Levantar Airflow con Docker Compose

### 4.1 Descargar el compose oficial

```bash
mkdir -p dags logs config plugins
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.3.0/docker-compose.yaml'
echo "AIRFLOW_UID=$(id -u)" > .env.docker
```

El archivo trae **337 líneas y 10 servicios**. La tarea es leerlo y decidir qué sobra.

### 4.2 Adelgazarlo

| Servicio | Acción | Por qué |
|---|---|---|
| `postgres` | **Mantener** | Base de metadata de Airflow. ⚠️ **No es tu RDS.** Airflow guarda ahí sus corridas, no tus datos de TRM. Son dos Postgres distintos y conviene tenerlo clarísimo. |
| `redis` | **Quitar** | Es el broker de mensajes de Celery. Sin Celery no hace falta. |
| `airflow-worker` | **Quitar** | Worker de Celery. Con `LocalExecutor` las tareas corren como subprocesos del scheduler. |
| `flower` | **Quitar** | UI de monitoreo de Celery. |
| `airflow-cli` | **Quitar** | Va en profile `debug`; lo mismo se logra con `docker compose run`. |
| `airflow-apiserver` | **Mantener** | Es la UI web. En Airflow 3 se llama `api-server`, ya no `webserver`. |
| `airflow-scheduler` | **Mantener** | El corazón: decide qué correr y cuándo. |
| `airflow-dag-processor` | **Mantener** | En Airflow 3 el parseo de DAGs es un proceso aparte, **obligatorio**. |
| `airflow-triggerer` | **Mantener** | No lo usás hoy (es para operadores diferibles), pero es liviano y evita advertencias confusas. |
| `airflow-init` | **Mantener** | Corre las migraciones de la metadata DB y crea el usuario admin. |

Cambios en el bloque `x-airflow-common`:

- `AIRFLOW__CORE__EXECUTOR: LocalExecutor`
- Borrar `AIRFLOW__CELERY__RESULT_BACKEND` y `AIRFLOW__CELERY__BROKER_URL`
- Borrar la dependencia `redis: condition: service_healthy` de `depends_on`
- Agregar `PYTHONPATH: /opt/airflow/project_src`
- Pasar tus variables: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE`, `DB_SSLROOTCERT`, `S3_BUCKET`, `AWS_*`

Volúmenes a agregar:

```yaml
- ${AIRFLOW_PROJ_DIR:-.}/src:/opt/airflow/project_src:ro
- ${AIRFLOW_PROJ_DIR:-.}/global-bundle.pem:/opt/airflow/certs/global-bundle.pem:ro
```

> ⚠️ **Sobre `PYTHONPATH`:** el paquete vive en `src/trm_signal/`, así que la ruta debe apuntar a **`src`**, no a `src/trm_signal`. Si apuntás mal, el DAG falla con `ModuleNotFoundError: trm_signal`.

### 4.3 Las dependencias sí necesitan un Dockerfile

Matiz importante sobre la decisión de "volumen montado": el **código** se monta, pero `pandas`, `psycopg`, `requests`, `boto3` y `python-dotenv` tienen que estar **instalados** en la imagen. Dos caminos:

| Camino | Ventaja | Costo |
|---|---|---|
| `_PIP_ADDITIONAL_REQUIREMENTS` | Una línea | Reinstala en cada arranque de cada contenedor. El propio compose oficial lo desaconseja para uso continuo. |
| **Dockerfile mínimo ✅** | Se construye una vez y casi nunca cambia | Hay que reconstruir si cambian las dependencias (rara vez) |

```dockerfile
FROM apache/airflow:3.3.0
RUN pip install --no-cache-dir pandas psycopg[binary] requests python-dotenv boto3
```

Y en el compose: reemplazar `image:` por `build: .`.

**Tu código sigue montado como volumen** — solo las dependencias quedan horneadas en la imagen. Es la combinación correcta: lo que cambia todos los días se monta, lo que cambia una vez al mes se hornea.

> 💡 **Decisión relacionada:** **no** instalar `apache-airflow-providers-amazon` ni usar `S3Hook`.
>
> Usar `boto3` directo mantiene `trm_signal` ejecutable **fuera** de Airflow — recordá la prueba de fuego: `run_daily.py` tiene que seguir funcionando. El costo es no gestionar credenciales desde la UI de Airflow. Es un intercambio consciente, no un descuido.

### 4.4 Ignorar los artefactos

Agregar a `.gitignore`: `logs/`, `.env.docker`, `plugins/`, `config/`.

---

## Paso 5 — Escribir el DAG

Archivo: `dags/trm_daily.py`

### Estructura con TaskFlow API

```python
from datetime import timedelta

import pendulum
from airflow.sdk import dag, task

BOGOTA = pendulum.timezone("America/Bogota")


@dag(
    dag_id="trm_daily",
    schedule="0 18 * * 1-5",
    start_date=pendulum.datetime(2026, 8, 1, tz=BOGOTA),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["trm"],
)
def trm_daily():

    @task(retries=4, retry_delay=timedelta(minutes=10), retry_exponential_backoff=True)
    def extract() -> str:
        ...   # devuelve el texto crudo

    @task
    def store(texto: str) -> str:
        ...   # devuelve la URI s3://

    @task
    def load(uri: str) -> int:
        ...   # devuelve filas cargadas

    @task
    def transform() -> int:
        ...   # devuelve filas en marts

    transform_task = transform()
    load(store(extract())) >> transform_task


trm_daily()
```

> Nota de versión: en Airflow 3 los decoradores se importan de `airflow.sdk`, no de `airflow.decorators`. Y el parámetro es `schedule`, no `schedule_interval`.

### Los porqués de cada parámetro

**`schedule="0 18 * * 1-5"`**
6:00 p.m., después de las 5:30 p.m. que exige la fuente. `1-5` porque la TRM no se publica sábados ni domingos.

> Airflow interpreta el cron en la zona horaria del `start_date`. Colombia no tiene horario de verano, así que 18:00 Bogotá siempre es 23:00 UTC. Te ahorrás el problema clásico de DST que sufre cualquiera que programe DAGs en zonas de EE. UU. o Europa.

**`catchup=False`**

> 🤔 **Antes de aceptarlo, razonalo:** tu `main()` siempre pide una ventana móvil de "los últimos 7 días **desde hoy**", no un rango derivado de la fecha de ejecución. Si Airflow reejecutara 200 corridas atrasadas, ¿qué datos traería cada una?

**Reintentos asimétricos** — `extract` tiene 4 reintentos con backoff exponencial; las demás heredan 2.

> 🤔 **La pregunta que justifica la diferencia:** *¿qué tipo de falla estás esperando en cada tarea?*
>
> La API caída es **transitoria**: se arregla sola esperando, y el backoff exponencial le da tiempo. Un `KeyError` en `_a_fila` es un **bug**: reintentarlo 4 veces con esperas crecientes solo retrasa el momento en que te enterás.
>
> Reintentar todo por igual no es "más seguro" — es no haber pensado en el modo de falla.

**Por qué los reintentos son seguros aquí** — porque el pipeline ya es idempotente: `load` hace UPSERT y `transform` hace TRUNCATE + INSERT.

> 🤔 **Pregunta clave:** si `load.py` usara un `INSERT` simple en vez de `ON CONFLICT DO UPDATE`, ¿qué pasaría cuando la tarea se reintenta después de haber insertado la mitad de las filas?
>
> Este es el motivo real por el que la idempotencia importa en orquestación. No es purismo académico: es la diferencia entre un reintento que te salva y uno que te corrompe la tabla.

**`transform` no depende del XCom de `load`** — lee directo de la base. Pero sí debe correr *después*, y por eso la dependencia se declara con `>>`.

> Es la distinción entre **dependencia de datos** (implícita, al pasar un valor de una tarea a otra) y **dependencia de orden** (explícita, con `>>`). Airflow soporta las dos y hay que saber cuándo usar cada una.

---

## Paso 6 — Verificación end-to-end

1. **Arrancar**
   ```bash
   docker compose --env-file .env.docker up airflow-init
   docker compose --env-file .env.docker up -d
   docker compose ps      # todos healthy
   ```

2. **UI** en http://localhost:8080 (usuario / clave por defecto: `airflow` / `airflow`).
   El DAG `trm_daily` debe aparecer **sin errores de import**.
   Si ves `ModuleNotFoundError` → revisá `PYTHONPATH` (Paso 4.2).

3. **Disparo manual** desde la UI. Las 4 tareas en verde.

4. **Inspeccionar XCom** (pestaña XCom de cada tarea): confirmá que `store` devolvió una URI corta y **no** 976 KB de JSON. Esta es la validación visual del Paso 2.2.

5. **Verificar el efecto real** — la prueba que de verdad importa:
   ```sql
   SELECT max(valid_from) FROM staging.trm;
   SELECT max(valid_from), max(computed_at) FROM marts.trm_daily;
   ```
   Deben coincidir en `valid_from`, y `computed_at` debe ser de hace segundos.

   > Que las tareas estén en verde solo dice que Python no lanzó excepciones. Que el dato llegó es otra afirmación, y se verifica en la base.

6. **Verificar S3**
   ```bash
   aws s3 ls s3://<bucket>/raw/ --recursive | tail -5
   ```

7. **Probar los reintentos a propósito** — ejercicio, no opcional.
   Cambiá temporalmente la URL en `extract.py` por una inválida, disparás el DAG, y observás en la UI cómo `extract` reintenta con espera creciente antes de marcar fallo. Revertí después.

   > Ver el backoff exponencial ocurriendo en la línea de tiempo de la UI enseña más que leer la documentación de `retries`.

8. **Dejarlo correr varios días** sin tocarlo. **Ese es el entregable real de la Fase 2.**

---

## Resumen de archivos

**Nuevos**
`plan/phase_2.md` · `dags/trm_daily.py` · `docker-compose.yaml` (descargado y adelgazado) · `Dockerfile` · `.env.docker`

**Modificados**
`src/trm_signal/storage.py` (S3) · `src/trm_signal/load.py` (leer de S3) · `scripts/run_daily.py` y `scripts/run_backfill.py` (bug de orden) · `pyproject.toml` (`boto3`) · `.env` / `.env.example` · `.gitignore`

**Sin cambios**
`src/trm_signal/extract.py` · `src/trm_signal/transform.py` · `src/trm_signal/config.py` · `sql/*`

> Que el núcleo de la lógica no se toque al orquestar **es buena señal**: confirma que la separación entre lógica y orquestación estaba bien planteada desde la Fase 1.

---

## Riesgos conocidos

| Riesgo | Mitigación |
|---|---|
| RDS inalcanzable (bloqueante hoy) | Paso 0, antes que nada |
| El contenedor no llega a RDS | Sale por NAT con la IP pública del host — la misma que ya tenés autorizada. Si funciona en local, funciona en Docker. |
| `ModuleNotFoundError: trm_signal` | `PYTHONPATH` debe apuntar a `src`, no a `src/trm_signal` |
| Docker Desktop sin RAM | Al quitar redis + worker + flower baja bastante; con 4 GB alcanza |
| Filtrar secretos al repo | `.env` ya está en `.gitignore:151`. **No commitear `.env.docker` ni llaves AWS.** |

---

## Fuera de alcance de la Fase 2

- Alertas por email / Telegram → **Fase 5**
- Migrar las transformaciones de pandas a dbt → **Fase 3**
- Tests automatizados
- Desplegar Airflow fuera de local
