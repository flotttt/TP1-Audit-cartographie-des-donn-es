#!/usr/bin/env bash
set -euo pipefail

DB_CONTAINER="${DB_CONTAINER:-tp-db}"
DB_USER="${POSTGRES_USER:-eonet}"
DB_NAME="${POSTGRES_DB:-eonet}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

psql() {
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" "$@"
}

psql_stdin() {
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" "$@"
}

echo ">> Setup schema staging + table de rapport"
psql -q -v ON_ERROR_STOP=1 -f /tp3/sql/00-schema-staging.sql >/dev/null
psql -q -v ON_ERROR_STOP=1 -f /tp3/sql/01-report-table.sql >/dev/null

RUN_ID=$(psql -q -tA -c "SELECT gen_random_uuid()")
echo ">> run_id = $RUN_ID"

run_audit() {
    local phase="$1"
    local schema="$2"
    echo ">> Audit phase=$phase schema=$schema"
    for f in "$SCRIPT_DIR"/sql/audit/*.sql; do
        local basename
        basename="$(basename "$f")"
        psql -q -v ON_ERROR_STOP=1 \
            -v run_id="$RUN_ID" -v phase="$phase" -v schema="$schema" \
            -f "/tp3/sql/audit/$basename" >/dev/null
    done
}

echo ""
echo "=========================================="
echo " Phase 1 : audit du raw (staging)"
echo "=========================================="
run_audit before staging

echo ""
echo "=========================================="
echo " Phase 2 : audit de la donnee Spark-cleaned (public)"
echo "=========================================="
run_audit before public

echo ""
echo "=========================================="
echo " Phase 3 : nettoyage SQL du staging"
echo "=========================================="
for f in "$SCRIPT_DIR"/sql/cleaning/*.sql; do
    bn="$(basename "$f")"
    echo "   -> $bn"
    psql -q -v ON_ERROR_STOP=1 -f "/tp3/sql/cleaning/$bn" >/dev/null
done

echo ""
echo "=========================================="
echo " Phase 4 : re-audit staging apres nettoyage SQL"
echo "=========================================="
run_audit after staging

echo ""
echo "=========================================="
echo " Rapport final"
echo "=========================================="
psql -c "
SELECT
    phase,
    dimension,
    COUNT(*) AS controles,
    SUM(failing_rows) AS anomalies_totales,
    COUNT(*) FILTER (WHERE failing_rows > 0) AS controles_en_echec
FROM data_quality_report
WHERE run_id = '$RUN_ID'
GROUP BY phase, dimension
ORDER BY phase, dimension;
"

echo ""
echo ">> Rapport detaille : "
echo "   docker exec tp-db psql -U eonet -d eonet -c \"SELECT phase, control_id, dimension, table_name, total_rows, failing_rows, fail_rate, details FROM data_quality_report WHERE run_id = '$RUN_ID' ORDER BY phase, control_id\""
echo ""
echo ">> run_id conserve : $RUN_ID"
