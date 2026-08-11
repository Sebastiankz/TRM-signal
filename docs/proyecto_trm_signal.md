# TRM Signal — documento de planeación del proyecto

*Proyecto de portafolio que combina Data Engineering y Data Analytics. Nombre de trabajo: "TRM Signal" (podés renombrarlo).*

## Índice

1. [Propósito](#1-propósito)
2. [El problema y por qué importa](#2-el-problema-y-por-qué-importa)
3. [La solución y el valor que aporta](#3-la-solución-y-el-valor-que-aporta)
4. [Habilidades que demuestra](#4-habilidades-que-demuestra)
5. [Alcance del proyecto](#5-alcance-del-proyecto)
6. [Arquitectura general](#6-arquitectura-general)
7. [Stack tecnológico](#7-stack-tecnológico)
8. [Fuente de datos](#8-fuente-de-datos)
9. [Métricas y análisis (capa de Data Analyst)](#9-métricas-y-análisis-capa-de-data-analyst)
10. [Fases de desarrollo](#10-fases-de-desarrollo)
11. [Cómo comunicarlo en el portafolio](#11-cómo-comunicarlo-en-el-portafolio)
12. [Riesgos y limitaciones](#12-riesgos-y-limitaciones)
13. [Próximos pasos inmediatos](#13-próximos-pasos-inmediatos)

---

## 1. Propósito

La TRM es un dato público, oficial y diario — pero se publica sin contexto. Nadie te dice si el número de hoy es normal o atípico frente al comportamiento reciente. Este proyecto construye la infraestructura y el análisis necesarios para convertir ese dato aislado en una **señal diaria accionable**: qué tan lejos está la TRM de hoy respecto a su comportamiento reciente, y si eso es parte de un patrón reconocible.

El propósito de portafolio es demostrar, con un caso real y verificable, la capacidad de sostener un análisis útil de punta a punta: desde que el dato existe de forma confiable (ingeniería de datos) hasta que se convierte en una conclusión legible (análisis de datos).

## 2. El problema y por qué importa

La TRM la calcula a diario la Superintendencia Financiera con base en las operaciones de cambio del día anterior, y se publica como un número suelto: sin histórico accesible, sin tendencia, sin nada que ayude a decidir. Cualquiera que necesite convertir dólares — recibir una remesa, cobrar un freelance, ahorrar, importar — solo puede mirar el número de hoy, sin saber si es un buen o mal momento comparado con lo reciente.

No es un problema de nicho:

- Colombia recibió **USD 13.098 millones en remesas durante 2025**, un crecimiento del 10,6% frente a 2024, equivalente a cerca del **3% del PIB nacional**, y hasta **2,1 millones de colombianos** se benefician directamente de ese ingreso (Banco de la República / Migración Colombia).
- La volatilidad no es teórica: entre el 7 de abril y el 7 de julio de 2026 el dólar pasó de **$3.664 a $3.350** (una revaluación del peso de 8,56% en tres meses), y para finales de julio de 2026 la TRM ya estaba en **$3.205,80**, su nivel más bajo en siete años.

Alguien que convierte dólares en el momento equivocado del mes pierde poder adquisitivo real, de forma silenciosa — y hoy no tiene ninguna herramienta simple que se lo señale.

## 3. La solución y el valor que aporta

El proyecto convierte el dato crudo en una señal diaria del tipo: *"hoy la TRM está X% por encima/debajo del promedio de los últimos 30 días, y esta variación es/no es atípica frente al histórico"*. Eso no existe ya calculado en ningún sitio público.

Valor concreto:

- **Histórico propio y consultable**, no dependiente de revisar manualmente un portal día a día.
- **Detección de patrones** que hoy nadie responde fácil: ¿hay diferencias por día de la semana? ¿un efecto de fin de mes? ¿la volatilidad sube cerca de decisiones del Banco de la República?
- **Reduce fricción**: de "revisar todos los días a mano" a "leer una conclusión ya calculada".

Importante como principio de diseño: el proyecto entrega **información descriptiva** (qué tan atípico es el movimiento de hoy frente al histórico), no una recomendación de inversión ni una señal de "compra/venta". Esa distinción es deliberada — mantiene el proyecto honesto y evita que parezca asesoría financiera.

## 4. Habilidades que demuestra

**Data Engineering** — lo que hace que el dato *exista de forma confiable*:
- Extracción automatizada y resiliente de una fuente externa
- Preservación del dato crudo (zona raw) antes de transformarlo
- Modelado de datos en un warehouse
- Orquestación de todo el flujo sin intervención manual

**Data Analyst** — lo que convierte el dato confiable en una *conclusión*:
- Diseño de métricas derivadas (promedios móviles, variación, desviación atípica)
- Detección de patrones y comunicación de hallazgos
- Traducir un resultado técnico en una conclusión legible para alguien no técnico

Juntas cuentan una historia de portafolio más completa que un proyecto puramente técnico: no solo "sé mover datos" ni solo "sé graficar", sino "puedo sostener un análisis útil de principio a fin". Como referencia, tu tesis (BQ-SafeRoutes) ya mostró que podés construir un pipeline con Airflow y pandas — acá el complemento genuino es la capa analítica/financiera y el modelado en SQL vía dbt, que tu portafolio todavía no cubre.

## 5. Alcance del proyecto

**Sí incluye:**
- Una sola serie (TRM) — no múltiples monedas ni mercados, para no dispersar el foco
- Promedio móvil, variación %, y una medida simple de qué tan atípica es la variación de hoy
- Orquestación diaria automática
- Un dashboard o reporte simple que comunique 2-3 hallazgos concretos

**Deliberadamente fuera de alcance (para mantenerlo manejable):**
- Forecasting o modelos predictivos (ARIMA, ML) — se menciona como extensión futura, no como parte de la primera versión
- Cualquier tipo de recomendación de inversión o trading automatizado
- Múltiples divisas o mercados
- Infraestructura de alta disponibilidad a escala productiva

## 6. Arquitectura general

```
Fuente (API pública, datos.gov.co)
        │
        ▼
   Extraer (Python)
        │
        ▼
   S3 — zona raw (JSON crudo, un archivo por día)
        │
        ▼
   Staging (Postgres) — el dato crudo aterriza sin transformar
        │
        ▼
   Transformar (dbt) — calcula métricas derivadas
        │
        ▼
   Marts (Postgres) — tablas finales, listas para consultar
        │
        ▼
   Consultar (SQL / dashboard)

Todo el flujo, orquestado por Airflow — corre 1 vez al día.
```

La idea de aterrizar primero en una zona "raw" antes de transformar es deliberada: si mañana se te ocurre una métrica nueva que hoy no calculaste, el dato crudo ya está preservado y no tenés que esperar a que vuelva a ocurrir.

## 7. Stack tecnológico

| Etapa | Herramienta | Por qué |
|---|---|---|
| Extraer | Python (`requests`) | Ya lo dominás por tu trabajo en backend |
| Almacenar crudo | AWS S3 | Ya tenés cuenta AWS activa; practica el patrón de "zona raw" que se pide en la mayoría de vacantes junior |
| Staging / Warehouse | PostgreSQL | Ya lo conocés de tus otros proyectos; toda la energía nueva se va a las piezas que sí son nuevas |
| Transformar | dbt | Pieza nueva para vos: transformación declarativa en SQL con control de versiones y tests de calidad |
| Orquestar | Apache Airflow (Docker Compose local) | Ya tenés una primera exposición por tu tesis; acá lo profundizás con un caso simple y bien acotado |
| Consultar / comunicar | SQL directo, o un dashboard simple (Streamlit) | Suficiente para mostrar los hallazgos sin construir un producto pulido |

## 8. Fuente de datos

- **Dataset oficial**: *"Tasa de Cambio Representativa del Mercado - TRM"* en datos.gov.co (ID del dataset: `32sa-8pi3`), que replica los datos históricos del Banco de la República.
- **Endpoint REST (API Socrata/SODA)**: `https://www.datos.gov.co/resource/32sa-8pi3.json` — permite filtrar por fecha, ordenar y limitar resultados vía parámetros de consulta estándar de Socrata.
- **Frecuencia de actualización**: diaria, después de las 5:30 p.m. hora Colombia (cuando se publica la TRM del día). Este horario define cuándo programar el DAG de Airflow.
- Para uso con más volumen de llamadas, se puede registrar un App Token gratuito de Socrata — no es obligatorio para uso normal de este proyecto.
- El dataset tiene un histórico amplio (proyectos públicos han extraído series de varias décadas usando este mismo endpoint), así que no vas a tener problema para calcular promedios de 7/30 días desde el arranque.
- **Origen autoritativo** si querés validar o profundizar: Banco de la República — Portal de Estadísticas Económicas (también ofrece series vía SDMX).

## 9. Métricas y análisis (capa de Data Analyst)

- Promedio móvil de 7 y 30 días
- Variación % diaria y variación % respecto al promedio móvil
- Una medida simple de qué tan atípica es la variación de hoy frente a su desviación histórica (ej. z-score)
- Patrones por día de la semana (¿lunes se comporta distinto a viernes?)
- Efecto de fin de mes
- *(Fase avanzada, opcional)* cruce simple con fechas de decisiones de política monetaria del Banco de la República

## 10. Fases de desarrollo

**Fase 0 — Preparación**
- Confirmar acceso a S3, Postgres (local o RDS free tier) y entorno Python
- Explorar el endpoint de datos.gov.co manualmente (`curl` o Postman) para entender la forma real del dato
- *Entregable:* acceso confirmado + un JSON de ejemplo guardado

**Fase 1 — Pipeline manual de punta a punta**
- Script en Python que llama la API, guarda el crudo en S3, calcula las métricas básicas con pandas, y carga a Postgres
- Todo corrido a mano, para validar que el flujo completo funciona antes de automatizar nada
- *Entregable:* un pipeline funcional ejecutado manualmente, con datos reales ya en Postgres

**Fase 2 — Orquestación con Airflow**
- Envolver el mismo código en un DAG, corriendo Airflow local vía Docker Compose
- Programar la ejecución diaria después de las 5:30 p.m. hora Colombia
- Manejo básico de errores (reintentos si la API falla)
- *Entregable:* el DAG corriendo solo, varios días seguidos, sin intervención manual

**Fase 3 — Capa analítica con dbt**
- Migrar las transformaciones de pandas a modelos dbt (staging → intermedio → marts)
- Agregar pruebas de calidad de datos en dbt (valores no nulos, rangos razonables)
- Calcular las métricas de la sección 9
- *Entregable:* proyecto dbt documentado, mostrando el linaje de las tablas (dbt docs)

**Fase 4 — Comunicación**
- Un dashboard simple (Streamlit o similar) con la serie histórica, el promedio móvil y la señal del día
- Redactar 2-3 hallazgos concretos con números reales (ej. "los lunes la variación promedio es de X%")
- *Entregable:* dashboard funcional + un README con los hallazgos

**Fase 5 — Extensión futura (fuera del MVP)**
- Alertas (email/Telegram) cuando la señal supere cierto umbral
- Un modelo simple de forecasting (ARIMA) como comparación exploratoria — dejando explícito que no es una recomendación financiera
- Se menciona solo como roadmap, no como parte del entregable inicial

## 11. Cómo comunicarlo en el portafolio

- El README debe abrir con la pregunta de negocio (la sección 2), no con la lista de tecnologías
- Un diagrama de arquitectura simple (como el de la sección 6) ayuda más que un párrafo largo
- Cerrar con 2-3 hallazgos concretos y con números reales — eso es lo que un entrevistador recuerda, no el stack
- Conectar explícitamente con la relevancia real del problema (remesas, freelancers cobrando en USD) en una o dos líneas

## 12. Riesgos y limitaciones

- La API puede fallar un día puntual — se mitiga con reintentos y manejo de errores en el DAG, no con lógica compleja
- El esquema del dataset podría cambiar — vale la pena una validación mínima al cargar el dato crudo
- La TRM refleja operaciones del día *anterior*, no el mercado en tiempo real — esto debe quedar explícito en el proyecto para no sobre-prometer
- Cualquier "señal" que el proyecto genere es descriptiva, no una recomendación financiera validada con backtesting riguroso — eso queda fuera de alcance a propósito

## 13. Próximos pasos inmediatos

1. Explorar el endpoint `https://www.datos.gov.co/resource/32sa-8pi3.json` manualmente y revisar la forma del dato
2. Crear el bucket S3 y la base Postgres que vas a usar
3. Escribir el script de la Fase 1 (sin Airflow todavía)

---

*Fuentes consultadas para las cifras y la fuente de datos: Banco de la República (banrep.gov.co), Migración Colombia / Observatorio OM3, datos.gov.co (dataset 32sa-8pi3), y coberturas de prensa económica sobre el comportamiento de la TRM en 2026 (Bloomberg Línea, Semana, Infobae, Wilkinson PC).*
