/*
This model calculates the percentage change of the TRM value from one period to the next. It uses the lag function to get the previous value and computes the percentage change accordingly. The result is materialized as a table for further analysis or reporting.
*/

{{ config(materialized='table') }}

SELECT
    *,
    100.0 * (value / nullif(lag(value) over (order by valid_from), 0) - 1) AS pct_change
FROM {{ ref('stg_trm') }}