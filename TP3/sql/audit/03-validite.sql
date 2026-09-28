SELECT audit_control(:'run_id'::uuid, :'phase', 'V01', 'validite', :'schema', 'event',
    $$link IS NOT NULL AND link !~ '^https?://'$$,
    'event.link ne commence pas par http(s)://');

SELECT audit_control(:'run_id'::uuid, :'phase', 'V02', 'validite', :'schema', 'source',
    $$url IS NOT NULL AND url !~ '^https?://'$$,
    'source.url ne commence pas par http(s)://');

SELECT audit_control(:'run_id'::uuid, :'phase', 'V03', 'validite', :'schema', 'earthquake',
    'longitude IS NOT NULL AND (longitude < -180 OR longitude > 180)',
    'earthquake.longitude hors [-180, 180]');

SELECT audit_control(:'run_id'::uuid, :'phase', 'V04', 'validite', :'schema', 'earthquake',
    'latitude IS NOT NULL AND (latitude < -90 OR latitude > 90)',
    'earthquake.latitude hors [-90, 90]');

SELECT audit_control(:'run_id'::uuid, :'phase', 'V05', 'validite', :'schema', 'earthquake',
    'magnitude IS NOT NULL AND (magnitude < -1 OR magnitude > 10)',
    'earthquake.magnitude hors [-1, 10]');

SELECT audit_control(:'run_id'::uuid, :'phase', 'V06', 'validite', :'schema', 'earthquake',
    'depth_km IS NOT NULL AND depth_km < 0',
    'earthquake.depth_km negative');

SELECT audit_control(:'run_id'::uuid, :'phase', 'V07', 'validite', :'schema', 'geometry',
    $$type IS NOT NULL AND type NOT IN ('Point', 'Polygon')$$,
    'geometry.type inconnu');

SELECT audit_control(:'run_id'::uuid, :'phase', 'V08', 'validite', :'schema', 'geometry',
    $$type = 'Point' AND (
        jsonb_typeof(coordinates) <> 'array'
        OR jsonb_array_length(coordinates) < 2
    )$$,
    'geometry Point avec coordonnees mal formees');
