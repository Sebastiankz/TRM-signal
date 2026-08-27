select
    valid_from,
    valid_to,
    value,
    currency,
    lag(valid_to)  over (order by valid_from) as market_date,
    row_number()   over (order by valid_from) as rn
from  {{ source('landing', 'trm') }}