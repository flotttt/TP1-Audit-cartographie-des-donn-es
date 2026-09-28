SELECT audit_join(:'run_id'::uuid, :'phase', 'U01', 'unicite', :'schema' || '.event',
    format('SELECT COUNT(*) FROM %I.event', :'schema'),
    format($fmt$SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) AS c FROM %I.event GROUP BY id HAVING COUNT(*) > 1) t$fmt$, :'schema'),
    'event.id duplique');

SELECT audit_join(:'run_id'::uuid, :'phase', 'U02', 'unicite', :'schema' || '.earthquake',
    format('SELECT COUNT(*) FROM %I.earthquake', :'schema'),
    format($fmt$SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) AS c FROM %I.earthquake GROUP BY id HAVING COUNT(*) > 1) t$fmt$, :'schema'),
    'earthquake.id duplique');

SELECT audit_join(:'run_id'::uuid, :'phase', 'U03', 'unicite', :'schema' || '.earthquake',
    format('SELECT COUNT(*) FROM %I.earthquake', :'schema'),
    format($fmt$SELECT COALESCE(SUM(c - 1), 0) FROM (
        SELECT COUNT(*) AS c FROM %I.earthquake
        GROUP BY date_trunc('minute', time), ROUND(latitude, 1), ROUND(longitude, 1), ROUND(magnitude, 1)
        HAVING COUNT(*) > 1
    ) t$fmt$, :'schema'),
    'earthquake quasi-doublon (memes minute + 0.1 deg + 0.1 magnitude)');

SELECT audit_join(:'run_id'::uuid, :'phase', 'U04', 'unicite', :'schema' || '.category',
    format('SELECT COUNT(*) FROM %I.category', :'schema'),
    format($fmt$SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) AS c FROM %I.category GROUP BY id HAVING COUNT(*) > 1) t$fmt$, :'schema'),
    'category.id duplique');

SELECT audit_join(:'run_id'::uuid, :'phase', 'U05', 'unicite', :'schema' || '.source',
    format('SELECT COUNT(*) FROM %I.source', :'schema'),
    format($fmt$SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) AS c FROM %I.source GROUP BY id HAVING COUNT(*) > 1) t$fmt$, :'schema'),
    'source.id duplique');
