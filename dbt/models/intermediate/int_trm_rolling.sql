/*
This model calculates rolling metrics for the TRM returns, including:
- 7-day moving average (ma_7)
- 30-day moving average (ma_30)
- Percentage change vs 30-day moving average (pct_vs_ma_30)
- Z-score of percentage change over a 252-day window (z_score)
*/

select
    *,
    case when count(*) over w7  = 7  then avg(value) over w7  end as ma_7,
    case when count(*) over w30 = 30 then avg(value) over w30 end as ma_30,
    case when count(*) over w30 = 30
         then 100.0 * (value / nullif(avg(value) over w30, 0) - 1)
    end as pct_vs_ma_30,
    case when count(pct_change) over w252 >= 60
         then (pct_change - avg(pct_change) over w252)
              / nullif(stddev_samp(pct_change) over w252, 0)
    end as z_score
from {{ ref('int_trm_returns') }}
window
    w7   as (order by valid_from rows between   6 preceding and current row),
    w30  as (order by valid_from rows between  29 preceding and current row),
    w252 as (order by valid_from rows between 251 preceding and current row)