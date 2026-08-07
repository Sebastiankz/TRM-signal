CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.trm (
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    value NUMERIC(12, 4) NOT NULL,
    currency TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_file TEXT NOT NULL,
    CONSTRAINT pk_trm PRIMARY KEY (valid_from),
    CONSTRAINT ck_trm_rango CHECK (valid_to >= valid_from),
    CONSTRAINT ck_trm_valor CHECK (value > 0)
);