/* 
This model calculates daily metrics for the TRM returns, including:
- 7-day moving average (ma_7)
- 30-day moving average (ma_30)
- Percentage change vs 30-day moving average (pct_vs_ma_30)
- Z-score of percentage change over a 252-day window (z_score)
- Percentile rank of absolute percentage change (pctl_abs)
*/

select
    r.valid_from,
    r.valid_to,
    r.market_date,
    r.value,
    r.pct_change,
    r.ma_7,
    r.ma_30,
    r.pct_vs_ma_30, 
    r.z_score,
    p.pctl_abs,
    now() as computed_at
from {{ ref('int_trm_rolling') }} r
left join {{ ref('int_trm_pctl') }} p using (valid_from)