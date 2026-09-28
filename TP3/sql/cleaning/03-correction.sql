UPDATE staging.event
SET title = btrim(title);

UPDATE staging.source
SET url = 'https://' || url
WHERE url IS NOT NULL AND url !~ '^https?://' AND url ~ '^[a-zA-Z0-9]';

UPDATE staging.event
SET link = 'https://' || link
WHERE link IS NOT NULL AND link !~ '^https?://' AND link ~ '^[a-zA-Z0-9]';

WITH ranked AS (
    SELECT ctid, ROW_NUMBER() OVER (PARTITION BY id ORDER BY _ingested_at DESC) AS rn
    FROM staging.earthquake
)
DELETE FROM staging.earthquake e
USING ranked r
WHERE e.ctid = r.ctid AND r.rn > 1;

WITH ranked AS (
    SELECT ctid, ROW_NUMBER() OVER (PARTITION BY id ORDER BY _ingested_at DESC) AS rn
    FROM staging.event
)
DELETE FROM staging.event e
USING ranked r
WHERE e.ctid = r.ctid AND r.rn > 1;

WITH ranked AS (
    SELECT ctid, ROW_NUMBER() OVER (PARTITION BY id ORDER BY _ingested_at DESC) AS rn
    FROM staging.category
)
DELETE FROM staging.category c
USING ranked r
WHERE c.ctid = r.ctid AND r.rn > 1;

WITH ranked AS (
    SELECT ctid, ROW_NUMBER() OVER (PARTITION BY id ORDER BY _ingested_at DESC) AS rn
    FROM staging.source
)
DELETE FROM staging.source s
USING ranked r
WHERE s.ctid = r.ctid AND r.rn > 1;

DELETE FROM staging.event_category ec1
USING staging.event_category ec2
WHERE ec1.ctid < ec2.ctid
  AND ec1.event_id = ec2.event_id
  AND ec1.category_id = ec2.category_id;

DELETE FROM staging.event_source es1
USING staging.event_source es2
WHERE es1.ctid < es2.ctid
  AND es1.event_id = es2.event_id
  AND es1.source_id = es2.source_id;

DELETE FROM staging.geometry g1
USING staging.geometry g2
WHERE g1.ctid < g2.ctid
  AND g1.event_id = g2.event_id
  AND g1.date IS NOT DISTINCT FROM g2.date
  AND g1.coordinates::text = g2.coordinates::text;
