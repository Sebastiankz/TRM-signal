select valid_from
from {{ ref('stg_trm') }}
where market_date is not NULL
    and valid_from - market_date <> 1