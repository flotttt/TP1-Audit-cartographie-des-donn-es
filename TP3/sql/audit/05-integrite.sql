SELECT audit_join(:'run_id'::uuid, :'phase', 'I01', 'integrite', :'schema' || '.event_category',
    format('SELECT COUNT(*) FROM %I.event_category', :'schema'),
    format($fmt$SELECT COUNT(*) FROM %I.event_category ec
        WHERE NOT EXISTS (SELECT 1 FROM %I.event e WHERE e.id = ec.event_id)$fmt$, :'schema', :'schema'),
    'event_category.event_id orphelin');

SELECT audit_join(:'run_id'::uuid, :'phase', 'I02', 'integrite', :'schema' || '.event_category',
    format('SELECT COUNT(*) FROM %I.event_category', :'schema'),
    format($fmt$SELECT COUNT(*) FROM %I.event_category ec
        WHERE NOT EXISTS (SELECT 1 FROM %I.category c WHERE c.id = ec.category_id)$fmt$, :'schema', :'schema'),
    'event_category.category_id orphelin');

SELECT audit_join(:'run_id'::uuid, :'phase', 'I03', 'integrite', :'schema' || '.event_source',
    format('SELECT COUNT(*) FROM %I.event_source', :'schema'),
    format($fmt$SELECT COUNT(*) FROM %I.event_source es
        WHERE NOT EXISTS (SELECT 1 FROM %I.event e WHERE e.id = es.event_id)$fmt$, :'schema', :'schema'),
    'event_source.event_id orphelin');

SELECT audit_join(:'run_id'::uuid, :'phase', 'I04', 'integrite', :'schema' || '.event_source',
    format('SELECT COUNT(*) FROM %I.event_source', :'schema'),
    format($fmt$SELECT COUNT(*) FROM %I.event_source es
        WHERE NOT EXISTS (SELECT 1 FROM %I.source s WHERE s.id = es.source_id)$fmt$, :'schema', :'schema'),
    'event_source.source_id orphelin');

SELECT audit_join(:'run_id'::uuid, :'phase', 'I05', 'integrite', :'schema' || '.geometry',
    format('SELECT COUNT(*) FROM %I.geometry', :'schema'),
    format($fmt$SELECT COUNT(*) FROM %I.geometry g
        WHERE NOT EXISTS (SELECT 1 FROM %I.event e WHERE e.id = g.event_id)$fmt$, :'schema', :'schema'),
    'geometry.event_id orphelin');
