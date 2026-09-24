# TP1 Audit & cartographie des données : NASA EONET

Cartographie d'un jeu de données réel, de la source brute jusqu'à une base PostgreSQL
interrogeable. Le sujet retenu est l'environnement, à travers le suivi des
événements naturels dans le monde (feux de forêt, tempêtes, volcans...) via l'API
publique EONET (Earth Observatory Natural Event Tracker) de la NASA.

---

## Sommaire des livrables

Chaque livrable du TP est traité dans un document dédié du dossier [`docs/`](docs/).

| # | Livrable | Document |
|---|----------|----------|
| 1 | Présentation du sujet (contexte, problématique, objectif) | [`docs/01-presentation.md`](docs/01-presentation.md) |
| 2 | Sources de données (origine, URL, formats, nature) | [`docs/02-sources.md`](docs/02-sources.md) |
| 3 | Dictionnaire de données | [`docs/03-dictionnaire.md`](docs/03-dictionnaire.md) |
| 4 | Entités, attributs, relations et cardinalités | [`docs/04-entites-relations.md`](docs/04-entites-relations.md) |
| 5 | Modèle conceptuel (MCD) | [`docs/05-mcd.md`](docs/05-mcd.md) |
| 5 | Modèle logique (MLD) | [`docs/06-mld.md`](docs/06-mld.md) |
| 6 | Base PostgreSQL (script + données de test) | [`sql/init.sql`](sql/init.sql) |

---

## Cartographie globale

Vue d'ensemble du cheminement, de la donnée réelle jusqu'à la base interrogeable :

```text
   API EONET (NASA)                 Modélisation                 PostgreSQL
   JSON imbriqué          ──►        MCD ──► MLD          ──►     6 tables
   /events /categories              (entités, relations,          + contraintes
   /sources                          cardinalités)                + clés PK/FK
        │                                                              ▲
        └──────────────►   worker.py (extraction + upsert)   ──────────┘
```

- **Source** : API REST publique, données JSON/GeoJSON semi-structurées, quasi temps réel.
- **Modélisation** : le JSON imbriqué (un événement → plusieurs catégories / sources /
  géométries) est éclaté en un schéma relationnel normalisé, sans doublons.
- **Implémentation** : PostgreSQL 16, alimenté automatiquement par un worker Python,
  le tout orchestré avec Docker Compose.

---

## Modèle de données

6 tables : 4 entités (`event`, `category`, `source`, `geometry`) et 2 tables de
jonction pour les relations N↔N (`event_category`, `event_source`).

```text
event 1 ─── N geometry            (un événement suivi par plusieurs points datés)
event N ─── N category            via event_category
event N ─── N source              via event_source
```

Le détail des attributs, types, clés et contraintes est dans le [MLD](docs/06-mld.md)
et le script [`sql/init.sql`](sql/init.sql) (PK/FK, `CHECK` sur les URLs, validation
GeoJSON des coordonnées, contrainte d'unicité des observations).

---

## Architecture technique

| Composant | Rôle | Fichier |
|-----------|------|---------|
| **PostgreSQL 16** | Base de données, schéma créé au démarrage | [`sql/init.sql`](sql/init.sql) |
| **Worker Python** | Extraction API EONET → upsert en base | [`worker/worker.py`](worker/worker.py) |
| **pgAdmin** | Administration de la base via navigateur | — |
| **Docker Compose** | Orchestration des 3 services | [`docker-compose.yml`](docker-compose.yml) |

---

## Démarrage

Prérequis : Docker et Docker Compose.

### Tout démarrer d'un coup (recommandé)

Le script `start.sh` crée le `.env` si besoin, build et lance les services, attend
que la base soit prête, puis charge les données de test :

```bash
./start.sh
```

### Ou manuellement, étape par étape

```bash
# 1. Créer le fichier d'environnement à partir du modèle
cp .env.example .env      # puis ajuster les mots de passe si besoin

# 2. Lancer la stack (build + démarrage)
docker compose up -d --build

# 3. Charger les données de test (idempotent, rejouable sans risque de doublon)
docker exec -i eonet-db psql -U eonet -d eonet < sql/seed.sql

# 4. Suivre l'alimentation de la base par le worker
docker compose logs -f worker
```

Une fois démarré :
- **PostgreSQL** : `localhost:5432` (identifiants du `.env`)
- **pgAdmin** : http://localhost:5050 (email / mot de passe du `.env`)

Vérifier le contenu de la base :

```bash
docker exec eonet-db psql -U eonet -d eonet -c \
  "SELECT 'event', count(*) FROM event UNION ALL SELECT 'category', count(*) FROM category;"
```

Arrêter la stack :

```bash
docker compose down          # conserve les données (volume pgdata)
docker compose down -v       # supprime aussi les données
```

---

## Le worker

`worker/worker.py` interroge les endpoints `/categories`, `/sources` et `/events` de
l'API EONET, puis insère les données en base avec une logique d'`upsert`
(`INSERT ... ON CONFLICT`) pour éviter les doublons à chaque passage.

Il se resynchronise en boucle. La fréquence et le périmètre se règlent dans le `.env` :

| Variable | Rôle | Défaut |
|----------|------|--------|
| `EONET_STATUS` | Statut des événements (`open` / `closed` / `all`) | `open` |
| `EONET_DAYS` | Fenêtre en jours | `30` |
| `EONET_LIMIT` | Nombre max d'événements récupérés | `50` |
| `WORKER_INTERVAL_SECONDS` | Intervalle entre deux synchros (`0` = une seule passe) | `900` (15 min) |

---

## Structure du dépôt

```text
.
├── README.md                 # ce fichier
├── start.sh                  # démarre tout + charge les données de test
├── docker-compose.yml        # orchestration des 3 services
├── .env.example              # modèle de configuration (à copier en .env)
├── docs/                     # livrables du TP (parties 1 à 5)
│   ├── 01-presentation.md
│   ├── 02-sources.md
│   ├── 03-dictionnaire.md
│   ├── 04-entites-relations.md
│   ├── 05-mcd.md
│   └── 06-mld.md
├── sql/
│   ├── init.sql              # création des tables + contraintes (livrable 6)
│   └── seed.sql              # données de test (livrable 6)
└── worker/
    ├── Dockerfile
    ├── requirements.txt
    └── worker.py             # extraction API → base
```
