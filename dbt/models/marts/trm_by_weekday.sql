/* 
This model calculates metrics for the TRM returns by weekday, including:
- Average percentage change (avg_pct_change)
- Standard deviation of percentage change (sd_pct_change)
- Standard error of the mean (std_error)
*/

select
    extract(isodow from market_date)::int    as dow_num,
    trim(to_char(market_date, 'Day'))        as dow,
    count(*)                                 as n,
    avg(pct_change)                          as avg_pct_change,
    stddev_samp(pct_change)                  as sd_pct_change,
    stddev_samp(pct_change) / sqrt(count(*)) as std_error
from {{ ref('int_trm_returns') }}
where pct_change is not null
  and market_date is not null
group by 1, 2