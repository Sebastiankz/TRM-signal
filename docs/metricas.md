# Las métricas, en simple

Cada fila de la serie es **una publicación de la TRM**. Sobre ese valor se calculan seis cosas.

Vamos a usar una fila real como ejemplo:

| valid_from | value | pct_change | ma_7 | ma_30 | pct_vs_ma_30 | z_score |
|---|---|---|---|---|---|---|
| 2026-08-04 | 3230.44 | +2.74% | 3190.77 | 3304.13 | -2.23% | +3.77 |

---

## 1. `value` — el valor

La TRM publicada, en pesos por dólar. El dato tal cual viene de la fuente.

## 2. `pct_change` — cuánto cambió desde la publicación anterior

> El 4 de agosto la TRM subió **2.74%** respecto a la publicación anterior.

Cada publicación está separada de la anterior por **un día hábil de mercado**, así que este número siempre significa lo mismo: cuánto se movió el dólar en una jornada.

- Positivo → el dólar subió (el peso se debilitó)
- Negativo → el dólar bajó (el peso se fortaleció)

## 3. `ma_7` y `ma_30` — los promedios móviles

El promedio de las últimas 7 y 30 publicaciones.

Sirven para **ver la tendencia sin el ruido diario**. Un solo día puede saltar por cualquier motivo; el promedio de 30 se mueve despacio y muestra hacia dónde va la serie de verdad.

Regla rápida:

- `value` por encima de `ma_30` → la TRM viene subiendo
- `value` por debajo de `ma_30` → viene bajando

Las primeras filas de la serie aparecen vacías: no hay 30 días previos para promediar, y preferimos un vacío honesto antes que un promedio inventado con menos datos.

## 4. `pct_vs_ma_30` — qué tan lejos está de su promedio del mes

> El 4 de agosto la TRM estaba **2.23% por debajo** de su promedio de los últimos 30 días.

Esta es **la métrica más útil para una persona normal**. Responde directo: *¿el dólar de hoy está caro o barato comparado con el último mes?*

- Cerca de 0% → hoy es un día típico
- Muy negativo → el dólar está más barato que su promedio reciente
- Muy positivo → está más caro

## 5. `z_score` — qué tan inusual fue el movimiento de hoy

Mide el `pct_change` de hoy contra cómo se venía moviendo la TRM **el último año**, en unidades de "desviaciones estándar".

> +3.77 significa que ese salto fue mucho más grande de lo normal para esta serie.

Cómo leerlo:

| \|z\| | Qué tan raro |
|---|---|
| menos de 1 | Día normal |
| entre 1 y 2 | Algo notable |
| entre 2 y 3 | Inusual |
| más de 3 | Movimiento fuerte, vale la pena mirar qué pasó |

**El signo no indica nada malo.** Negativo solo quiere decir "por debajo del promedio", y eso pasa aproximadamente la mitad de los días. Lo que importa es el número sin signo.

## 6. `pctl_abs` — el percentil del movimiento

> 99.6 significa: solo el 0.4% de los movimientos del último año fueron más grandes que el de hoy.

Es la versión **contada** de la métrica anterior: no supone nada sobre la forma de los datos, simplemente ordena los últimos 252 movimientos y dice en qué lugar quedó el de hoy.

---

## Por qué guardamos z-score *y* percentil

El z-score se entiende fácil, pero su interpretación clásica ("más de 3 desviaciones ocurre el 0.3% de las veces") **asume que los datos siguen una campana normal, y la TRM no la sigue**.

Medido sobre los 35 años de historia:

| | Observado | Si fuera normal |
|---|---|---|
| \|z\| > 3 | 1.5% de los días | 0.3% |
| \|z\| > 4 | 45 veces | menos de 1 vez |
| \|z\| > 5 | 24 veces | prácticamente nunca |

Los movimientos extremos son **mucho más frecuentes** de lo que predice el modelo normal. Es una característica conocida de las series financieras (*colas pesadas*).

Por eso:

- El **z-score** sirve para comunicar y comparar ("hoy se movió más que ayer").
- El **percentil** sirve cuando el número tiene que ser defendible, porque no supone ninguna distribución: solo cuenta.

---

## Lo que estas métricas **no** son

Son **descriptivas**: dicen qué tan distinto es hoy respecto a lo reciente. No predicen nada ni recomiendan comprar o vender.

Además, la TRM refleja las operaciones del **día hábil anterior**, no el mercado en tiempo real.
