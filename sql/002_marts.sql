CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS marts.trm_daily (
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    market_date DATE,
    value NUMERIC(12, 4) NOT NULL,
    pct_change NUMERIC(10, 6),
    ma_7 NUMERIC(12, 4),
    ma_30 NUMERIC(12, 4),
    pct_vs_ma_30 NUMERIC(10, 6),
    z_score NUMERIC(10, 6),
    pctl_abs NUMERIC(6, 3),
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_trm_daily PRIMARY KEY (valid_from)
);