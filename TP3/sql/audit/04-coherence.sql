SELECT audit_join(:'run_id'::uuid, :'phase', 'Co01', 'coherence', :'schema' || '.event',
    format($fmt$SELECT COUNT(*) FROM %I.event WHERE closed IS NOT NULL$fmt$, :'schema'),
    format($fmt$SELECT COUNT(*) FROM %I.event e
        WHERE e.closed IS NOT NULL
          AND e.closed < (
              SELECT MIN(to_timestamp_safe(g.date::text))
              FROM %I.geometry g
              WHERE g.event_id = e.id
          )$fmt$, :'schema', :'schema'),
    'event.closed anterieur au premier point de geometrie');

SELECT audit_control(:'run_id'::uuid, :'phase', 'Co02', 'coherence', :'schema', 'earthquake',
    'tsunami = true AND (magnitude IS NULL OR magnitude < 6.5)',
    'earthquake tsunami=true mais magnitude < 6.5');

SELECT audit_control(:'run_id'::uuid, :'phase', 'Co03', 'coherence', :'schema', 'earthquake',
    $$time > now() + interval '1 day'$$,
    'earthquake dans le futur');

SELECT audit_control(:'run_id'::uuid, :'phase', 'Co04', 'coherence', :'schema', 'earthquake',
    $$time < now() - interval '365 days'$$,
    'earthquake > 1 an (fenetre USGS_DAYS = 30, donc suspect)');

SELECT audit_control(:'run_id'::uuid, :'phase', 'Co05', 'coherence', :'schema', 'event',
    $$closed IS NOT NULL AND closed > now() + interval '1 day'$$,
    'event.closed dans le futur');
