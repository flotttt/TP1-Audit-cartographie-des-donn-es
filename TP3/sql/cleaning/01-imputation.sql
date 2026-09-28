UPDATE staging.earthquake
SET mag_type = 'unknown'
WHERE mag_type IS NULL;

UPDATE staging.earthquake
SET place = 'unknown'
WHERE place IS NULL OR btrim(place) = '';

UPDATE staging.event
SET description = ''
WHERE description IS NULL;

UPDATE staging.category
SET title = id
WHERE title IS NULL OR btrim(title) = '';
