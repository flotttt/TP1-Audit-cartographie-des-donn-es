#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
    echo ">> .env absent, copie depuis .env.example"
    cp .env.example .env
fi

echo ">> Build + demarrage de la stack"
docker compose up -d --build

echo ""
echo ">> Attente que Metabase soit initialise (peut prendre 1-3 min)"
until docker inspect tp-metabase-init --format '{{.State.Status}}' 2>/dev/null | grep -qE "exited"; do
    sleep 5
    echo "   toujours en cours..."
done

EXIT_CODE=$(docker inspect tp-metabase-init --format '{{.State.ExitCode}}')
if [ "$EXIT_CODE" != "0" ]; then
    echo "!! metabase-init a echoue (exit $EXIT_CODE), voir 'docker compose logs metabase-init'"
else
    echo ">> Metabase provisionne"
fi

echo ""
echo "============================================================"
echo " Stack prete."
echo "============================================================"
echo " Metabase   : http://localhost:3000   (admin@tp.com / admin1234)"
echo " Kafka UI   : http://localhost:8080"
echo " pgAdmin    : http://localhost:5050   (admin@eonet.com / admin)"
echo " PostgreSQL : localhost:5432          (eonet / eonet)"
echo " S3 API     : http://localhost:4566   (minio / minio12345)"
echo "============================================================"
echo ""
echo " Un premier run du pipeline Spark tourne dans les 30-60s."
echo " Consulter le dashboard : http://localhost:3000/dashboard/2"
echo ""
