CREATE TABLE event (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    link VARCHAR(255) NOT NULL,
    closed TIMESTAMPTZ,
    CONSTRAINT event_title_not_blank CHECK (char_length(btrim(title)) > 0),
    CONSTRAINT event_link_is_url CHECK (link ~ '^https?://')
);

CREATE TABLE category (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    CONSTRAINT category_title_not_blank CHECK (char_length(btrim(title)) > 0)
);

CREATE TABLE source (
    id VARCHAR(50) PRIMARY KEY,
    url VARCHAR(255) NOT NULL,
    CONSTRAINT source_url_is_url CHECK (url ~ '^https?://')
);

CREATE TABLE geometry (
    geometry_id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    type VARCHAR(20) NOT NULL,
    coordinates JSONB NOT NULL,
    CONSTRAINT geometry_event_fk FOREIGN KEY (event_id) REFERENCES event (id) ON DELETE CASCADE,
    CONSTRAINT geometry_type_valid CHECK (type IN ('Point', 'Polygon')),
    CONSTRAINT geometry_coordinates_valid CHECK (
        CASE
            WHEN jsonb_typeof(coordinates) <> 'array' THEN FALSE
            WHEN type = 'Point' THEN
                jsonb_array_length(coordinates) = 2
                AND (coordinates ->> 0)::NUMERIC BETWEEN -180 AND 180
                AND (coordinates ->> 1)::NUMERIC BETWEEN -90 AND 90
            ELSE TRUE
        END
    ),
    CONSTRAINT geometry_unique_observation UNIQUE (event_id, date, coordinates)
);

CREATE TABLE event_category (
    event_id VARCHAR(50) NOT NULL,
    category_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (event_id, category_id),
    CONSTRAINT event_category_event_fk FOREIGN KEY (event_id) REFERENCES event (id) ON DELETE CASCADE,
    CONSTRAINT event_category_category_fk FOREIGN KEY (category_id) REFERENCES category (id) ON DELETE RESTRICT
);

CREATE TABLE event_source (
    event_id VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (event_id, source_id),
    CONSTRAINT event_source_event_fk FOREIGN KEY (event_id) REFERENCES event (id) ON DELETE CASCADE,
    CONSTRAINT event_source_source_fk FOREIGN KEY (source_id) REFERENCES source (id) ON DELETE RESTRICT
);

CREATE TABLE earthquake (
    id VARCHAR(50) PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    magnitude NUMERIC(4, 2),
    mag_type VARCHAR(20),
    place TEXT,
    longitude NUMERIC(9, 5) NOT NULL,
    latitude NUMERIC(8, 5) NOT NULL,
    depth_km NUMERIC(7, 3),
    tsunami BOOLEAN NOT NULL DEFAULT FALSE,
    significance INTEGER,
    url VARCHAR(255),
    CONSTRAINT earthquake_longitude_valid CHECK (longitude BETWEEN -180 AND 180),
    CONSTRAINT earthquake_latitude_valid CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT earthquake_magnitude_valid CHECK (magnitude IS NULL OR magnitude BETWEEN -1 AND 10),
    CONSTRAINT earthquake_url_is_url CHECK (url IS NULL OR url ~ '^https?://')
);

CREATE TABLE event_earthquake (
    event_id VARCHAR(50) NOT NULL,
    earthquake_id VARCHAR(50) NOT NULL,
    distance_km NUMERIC(8, 2),
    delay_hours NUMERIC(8, 2),
    PRIMARY KEY (event_id, earthquake_id),
    CONSTRAINT event_earthquake_event_fk FOREIGN KEY (event_id) REFERENCES event (id) ON DELETE CASCADE,
    CONSTRAINT event_earthquake_earthquake_fk FOREIGN KEY (earthquake_id) REFERENCES earthquake (id) ON DELETE CASCADE
);

CREATE INDEX geometry_event_id_idx ON geometry (event_id);
CREATE INDEX event_category_category_id_idx ON event_category (category_id);
CREATE INDEX event_source_source_id_idx ON event_source (source_id);
CREATE INDEX event_closed_idx ON event (closed);
CREATE INDEX earthquake_time_idx ON earthquake (time);
CREATE INDEX earthquake_magnitude_idx ON earthquake (magnitude);
CREATE INDEX event_earthquake_earthquake_id_idx ON event_earthquake (earthquake_id);
