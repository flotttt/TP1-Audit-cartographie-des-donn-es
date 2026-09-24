#!/usr/bin/env bash
# Démarre toute la stack EONET et charge les données de test.
set -euo pipefail

cd "$(dirname "$0")"

# 1. Créer le .env à partir du modèle s'il n'existe pas encore
if [ ! -f .env ]; then
    echo "→ .env absent, création à partir de .env.example"
    cp .env.example .env
fi

# 2. Build + démarrage des services (db, worker, pgadmin)
echo "→ Démarrage de la stack Docker..."
docker compose up -d --build

# 3. Attendre que PostgreSQL soit prêt (healthcheck)
echo "→ Attente de la base de données..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' eonet-db 2>/dev/null)" = "healthy" ]; do
    sleep 2
done

# 4. Charger les données de test (idempotent : ON CONFLICT DO NOTHING)
echo "→ Chargement des données de test (seed.sql)..."
docker exec -i eonet-db psql -U eonet -d eonet < sql/seed.sql

echo ""
echo "✅ Stack prête."
echo "   PostgreSQL : localhost:5432"
echo "   pgAdmin    : http://localhost:5050"
echo "   Logs worker: docker compose logs -f worker"
