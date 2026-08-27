/* 
This model calculates the percentile rank of the absolute percentage change in TRM returns over a rolling 252-day window. The percentile is only calculated for days where there are at least 60 valid observations in the window. The output includes:
- valid_from: The date of the TRM return.
- pctl_abs: The percentile rank of the absolute percentage change, expressed as a percentage.
*/

select
    b.valid_from,
    case when v.n >= 60
         then 100.0 * (v.menores + (v.iguales + 1) / 2.0) / v.n
    end as pctl_abs
from {{ ref('int_trm_returns') }} b
cross join lateral (
    select
        count(p.pct_change)                                             as n,
        count(*) filter (where abs(p.pct_change) < abs(b.pct_change))   as menores,
        count(*) filter (where abs(p.pct_change) = abs(b.pct_change))   as iguales
    from {{ ref('int_trm_returns') }} p
    where p.rn between b.rn - 251 and b.rn
      and p.pct_change is not null
) v