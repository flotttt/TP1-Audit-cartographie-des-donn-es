BEGIN;

INSERT INTO category (id, title, description) VALUES
    ('wildfires',    'Wildfires',     'Feux de forêt et de végétation.'),
    ('severeStorms', 'Severe Storms', 'Tempêtes, cyclones et systèmes orageux.'),
    ('volcanoes',    'Volcanoes',     'Activité et éruptions volcaniques.')
ON CONFLICT (id) DO NOTHING;

INSERT INTO source (id, url) VALUES
    ('InciWeb', 'https://inciweb.wildfire.gov'),
    ('GDACS',   'https://www.gdacs.org'),
    ('SIVOLC',  'https://volcano.si.edu')
ON CONFLICT (id) DO NOTHING;

INSERT INTO event (id, title, description, link, closed) VALUES
    ('TEST_0001', 'Wildfire - Los Angeles County, California',
        NULL, 'https://eonet.gsfc.nasa.gov/api/v3/events/TEST_0001', NULL),
    ('TEST_0002', 'Tropical Storm - Gulf of Mexico',
        NULL, 'https://eonet.gsfc.nasa.gov/api/v3/events/TEST_0002',
        '2026-09-20T00:00:00Z'),
    ('TEST_0003', 'Volcano - Kilauea, Hawaii',
        NULL, 'https://eonet.gsfc.nasa.gov/api/v3/events/TEST_0003', NULL)
ON CONFLICT (id) DO NOTHING;

INSERT INTO event_category (event_id, category_id) VALUES
    ('TEST_0001', 'wildfires'),
    ('TEST_0002', 'severeStorms'),
    ('TEST_0003', 'volcanoes'),
    ('TEST_0001', 'severeStorms')
ON CONFLICT (event_id, category_id) DO NOTHING;

INSERT INTO event_source (event_id, source_id) VALUES
    ('TEST_0001', 'InciWeb'),
    ('TEST_0002', 'GDACS'),
    ('TEST_0003', 'SIVOLC'),
    ('TEST_0002', 'InciWeb')
ON CONFLICT (event_id, source_id) DO NOTHING;

INSERT INTO geometry (event_id, date, type, coordinates) VALUES
    ('TEST_0001', '2026-09-18T18:00:00Z', 'Point', '[-118.24, 34.05]'),
    ('TEST_0001', '2026-09-19T18:00:00Z', 'Point', '[-118.30, 34.10]'),
    ('TEST_0002', '2026-09-17T12:00:00Z', 'Point', '[-90.00, 25.00]'),
    ('TEST_0003', '2026-09-15T06:00:00Z', 'Point', '[-155.28, 19.42]')
ON CONFLICT (event_id, date, coordinates) DO NOTHING;

COMMIT;
