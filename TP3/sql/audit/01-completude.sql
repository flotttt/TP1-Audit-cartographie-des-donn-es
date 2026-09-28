SELECT audit_control(:'run_id'::uuid, :'phase', 'C01', 'completude', :'schema', 'event',
    $$title IS NULL OR btrim(title) = ''$$,
    'event.title manquant ou vide');

SELECT audit_control(:'run_id'::uuid, :'phase', 'C02', 'completude', :'schema', 'event',
    'description IS NULL',
    'event.description manquante (informatif)');

SELECT audit_control(:'run_id'::uuid, :'phase', 'C03', 'completude', :'schema', 'event',
    'link IS NULL',
    'event.link manquant');

SELECT audit_control(:'run_id'::uuid, :'phase', 'C04', 'completude', :'schema', 'earthquake',
    'magnitude IS NULL',
    'earthquake.magnitude manquante');

SELECT audit_control(:'run_id'::uuid, :'phase', 'C05', 'completude', :'schema', 'earthquake',
    'mag_type IS NULL',
    'earthquake.mag_type manquant');

SELECT audit_control(:'run_id'::uuid, :'phase', 'C06', 'completude', :'schema', 'earthquake',
    'place IS NULL',
    'earthquake.place manquant');

SELECT audit_control(:'run_id'::uuid, :'phase', 'C07', 'completude', :'schema', 'earthquake',
    'depth_km IS NULL',
    'earthquake.depth_km manquante');

SELECT audit_control(:'run_id'::uuid, :'phase', 'C08', 'completude', :'schema', 'earthquake',
    'longitude IS NULL OR latitude IS NULL',
    'earthquake sans coordonnees');

SELECT audit_control(:'run_id'::uuid, :'phase', 'C09', 'completude', :'schema', 'geometry',
    'coordinates IS NULL',
    'geometry.coordinates manquantes');
