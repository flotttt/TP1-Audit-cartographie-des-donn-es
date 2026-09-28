CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS data_quality_report (
    id            SERIAL PRIMARY KEY,
    run_id        UUID NOT NULL,
    run_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    phase         TEXT NOT NULL CHECK (phase IN ('before', 'after')),
    control_id    TEXT NOT NULL,
    dimension     TEXT NOT NULL,
    table_name    TEXT NOT NULL,
    total_rows    BIGINT NOT NULL,
    failing_rows  BIGINT NOT NULL,
    fail_rate     NUMERIC(7, 4) GENERATED ALWAYS AS (
        CASE WHEN total_rows = 0 THEN 0
             ELSE ROUND(failing_rows::numeric / total_rows, 4)
        END
    ) STORED,
    details       TEXT
);

CREATE INDEX IF NOT EXISTS data_quality_report_run_idx
    ON data_quality_report (run_id, phase);

CREATE OR REPLACE FUNCTION to_timestamp_safe(p_text TEXT) RETURNS TIMESTAMPTZ AS $$
BEGIN
    RETURN p_text::TIMESTAMPTZ;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION audit_control(
    p_run_id       UUID,
    p_phase        TEXT,
    p_control_id   TEXT,
    p_dimension    TEXT,
    p_schema       TEXT,
    p_table        TEXT,
    p_where        TEXT,
    p_details      TEXT
) RETURNS void AS $$
DECLARE
    v_total    BIGINT;
    v_failing  BIGINT;
BEGIN
    EXECUTE format('SELECT COUNT(*) FROM %I.%I', p_schema, p_table) INTO v_total;
    EXECUTE format('SELECT COUNT(*) FROM %I.%I WHERE %s', p_schema, p_table, p_where) INTO v_failing;
    INSERT INTO data_quality_report (run_id, phase, control_id, dimension, table_name, total_rows, failing_rows, details)
    VALUES (p_run_id, p_phase, p_control_id, p_dimension, p_schema || '.' || p_table, v_total, v_failing, p_details);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION audit_join(
    p_run_id       UUID,
    p_phase        TEXT,
    p_control_id   TEXT,
    p_dimension    TEXT,
    p_table_label  TEXT,
    p_total_sql    TEXT,
    p_failing_sql  TEXT,
    p_details      TEXT
) RETURNS void AS $$
DECLARE
    v_total    BIGINT;
    v_failing  BIGINT;
BEGIN
    EXECUTE p_total_sql INTO v_total;
    EXECUTE p_failing_sql INTO v_failing;
    INSERT INTO data_quality_report (run_id, phase, control_id, dimension, table_name, total_rows, failing_rows, details)
    VALUES (p_run_id, p_phase, p_control_id, p_dimension, p_table_label, v_total, v_failing, p_details);
END;
$$ LANGUAGE plpgsql;
