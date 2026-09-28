DELETE FROM staging.earthquake
WHERE longitude IS NULL OR latitude IS NULL;

DELETE FROM staging.earthquake
WHERE longitude < -180 OR longitude > 180
   OR latitude < -90 OR latitude > 90;

DELETE FROM staging.earthquake
WHERE magnitude IS NOT NULL AND (magnitude < -1 OR magnitude > 10);

DELETE FROM staging.earthquake
WHERE depth_km IS NOT NULL AND depth_km < 0;

DELETE FROM staging.event
WHERE title IS NULL OR btrim(title) = '' OR link IS NULL;

DELETE FROM staging.geometry
WHERE coordinates IS NULL
   OR type NOT IN ('Point', 'Polygon');

DELETE FROM staging.event_category ec
WHERE NOT EXISTS (SELECT 1 FROM staging.event e WHERE e.id = ec.event_id)
   OR NOT EXISTS (SELECT 1 FROM staging.category c WHERE c.id = ec.category_id);

DELETE FROM staging.event_source es
WHERE NOT EXISTS (SELECT 1 FROM staging.event e WHERE e.id = es.event_id)
   OR NOT EXISTS (SELECT 1 FROM staging.source s WHERE s.id = es.source_id);

DELETE FROM staging.geometry g
WHERE NOT EXISTS (SELECT 1 FROM staging.event e WHERE e.id = g.event_id);
