CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.event (
    id            VARCHAR(100),
    title         VARCHAR(500),
    description   TEXT,
    link          VARCHAR(500),
    closed        TIMESTAMPTZ,
    _ingested_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.category (
    id            VARCHAR(100),
    title         VARCHAR(200),
    description   TEXT,
    _ingested_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.source (
    id            VARCHAR(100),
    url           VARCHAR(500),
    _ingested_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.geometry (
    event_id      VARCHAR(100),
    date          VARCHAR(100),
    type          VARCHAR(50),
    coordinates   JSONB,
    _ingested_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.event_category (
    event_id      VARCHAR(100),
    category_id   VARCHAR(100),
    _ingested_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.event_source (
    event_id      VARCHAR(100),
    source_id     VARCHAR(100),
    _ingested_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.earthquake (
    id            VARCHAR(100),
    time          TIMESTAMPTZ,
    magnitude     NUMERIC,
    mag_type      VARCHAR(50),
    place         TEXT,
    longitude     NUMERIC,
    latitude      NUMERIC,
    depth_km      NUMERIC,
    tsunami       BOOLEAN,
    significance  INTEGER,
    url           TEXT,
    _ingested_at  TIMESTAMPTZ DEFAULT now()
);
