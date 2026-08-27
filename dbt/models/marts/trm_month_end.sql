/* 
EL EFECTO DE FIN DE MES
El truco está en el row_number() descendente.
Para saber "cuántos días de mercado faltan para cerrar el mes" tendrías que averiguar cuántos días hábiles tiene cada mes, restar festivos colombianos, y manejar los meses cortos. Nada de eso hace falta: ordenás al revés dentro de la partición del mes y el primero es el último.
*/

with pos as (
    select
        pct_change,
        row_number() over (partition by date_trunc('month', market_date)
                           order by market_date)      as dia_del_mes,
        row_number() over (partition by date_trunc('month', market_date)
                           order by market_date desc) as dias_al_cierre
    from {{ ref('int_trm_returns') }}
    where pct_change is not null
      and market_date is not null
)
select
    case when dias_al_cierre <= 3 then 'ultimos_3'
         when dia_del_mes    <= 3 then 'primeros_3'
         else 'resto' end                     as tramo,
    count(*)                                  as n,
    avg(pct_change)                           as avg_pct_change,
    stddev_samp(pct_change)                   as sd_pct_change,
    stddev_samp(pct_change) / sqrt(count(*))  as std_error
from pos
group by 1