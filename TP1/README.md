# TP1 — Audit & cartographie des données : NASA EONET

Cartographie d'un jeu de données réel, de la source brute jusqu'à une base PostgreSQL
interrogeable. Le sujet retenu est l'environnement, à travers le suivi des
événements naturels dans le monde (feux de forêt, tempêtes, volcans...) via l'API
publique EONET (Earth Observatory Natural Event Tracker) de la NASA.

> **Portée de ce document.** Ce README couvre le **livrable TP1** uniquement : la
> cartographie, la modélisation et le schéma initial. Le dépôt contient aujourd'hui
> les trois TP et une stack unique orchestrée depuis la racine — pour lancer quoi que
> ce soit, voir le [README racine](../README.md). Le TP2 industrialise le pipeline
> (Kafka, Data Lake, Spark, Metabase, monitoring) et le TP3 ajoute l'audit qualité.

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
| 6 | Modèle logique (MLD) | [`docs/06-mld.md`](docs/06-mld.md) |
| 7 | Base PostgreSQL (script + données de test) | [`sql/init.sql`](sql/init.sql) · [`sql/seed.sql`](sql/seed.sql) |

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

> **Évolution au TP2.** Le schéma est étendu à **8 tables** avec l'ajout de la source
> USGS : `earthquake` (séismes) et `event_earthquake` (rapprochement spatio-temporel
> event ↔ séisme, calculé par Spark). Le schéma effectivement appliqué au démarrage de
> la stack est [`TP2/postgres/init.sql`](../TP2/postgres/init.sql) ; le script
> [`sql/init.sql`](sql/init.sql) de ce dossier reste le livrable du TP1, à périmètre
> EONET.

---

## Architecture technique

Au TP1, la stack tenait en trois services. Depuis le TP2, tout est orchestré par le
`docker-compose.yml` de la racine — les composants ci-dessous y sont toujours présents,
sous les noms de conteneurs indiqués.

| Composant | Conteneur | Rôle | Fichier |
|-----------|-----------|------|---------|
| **PostgreSQL 16** | `tp-db` | Base de données, schéma créé au démarrage | [`TP2/postgres/init.sql`](../TP2/postgres/init.sql) |
| **Worker Python** | — *(voir note)* | Extraction API EONET → upsert en base | [`worker/worker.py`](worker/worker.py) |
| **pgAdmin** | `tp-pgadmin` | Administration de la base via navigateur | — |
| **Docker Compose** | — | Orchestration de l'ensemble des services | [`../docker-compose.yml`](../docker-compose.yml) |

> **Note sur le worker.** `worker/worker.py` est l'implémentation d'origine du TP1 :
> il interroge l'API EONET et écrit directement en base. Au TP2, ce rôle est repris par
> les **producers Kafka** (`TP2/api/` pour EONET, `TP2/source2/` pour USGS), qui
> publient dans des topics au lieu d'écrire en base. Le worker est conservé dans le
> dépôt comme livrable du TP1 et comme référence de la logique d'upsert.

---

## Démarrage

Prérequis : Docker et Docker Compose. Voir le [README racine](../README.md) pour les
pré-requis complets (RAM, ports) et le détail des services.

### Lancer la stack

Depuis **la racine du dépôt** :

```bash
cp .env.example .env      # les valeurs par défaut fonctionnent en local
./start.sh                # ou : docker compose up -d --build
```

Une fois démarré, les services utiles au périmètre TP1 :

| Service | URL | Login |
|---|---|---|
| **PostgreSQL** | `localhost:5432` | `eonet` / `change-me` |
| **pgAdmin** | http://localhost:5050 | `admin@eonet.com` / `change-me` |

Dans pgAdmin : *Add New Server* → Name `tp` → Connection : Host `db`, User `eonet`,
Password `change-me`.

### Charger les données de test du TP1

Le pipeline alimente la base en continu ; le seed n'est utile que pour disposer d'un
jeu minimal sans attendre un cycle de collecte. Il est idempotent, rejouable sans
risque de doublon :

```bash
docker exec -i tp-db psql -U eonet -d eonet < TP1/sql/seed.sql
```

### Vérifier le contenu de la base

```bash
docker exec tp-db psql -U eonet -d eonet -c \
  "SELECT 'event', count(*) FROM event UNION ALL SELECT 'category', count(*) FROM category;"
```

### Arrêter la stack

```bash
docker compose down          # conserve les données (volumes)
docker compose down -v       # supprime aussi les données
```

---

## Le worker TP1

`worker/worker.py` interroge les endpoints `/categories`, `/sources` et `/events` de
l'API EONET, puis insère les données en base avec une logique d'`upsert`
(`INSERT ... ON CONFLICT`) pour éviter les doublons à chaque passage.

Il se resynchronise en boucle. La fréquence et le périmètre se règlent dans le `.env`
de la racine :

| Variable | Rôle | Défaut |
|----------|------|--------|
| `EONET_STATUS` | Statut des événements (`open` / `closed` / `all`) | `open` |
| `EONET_DAYS` | Fenêtre en jours | `30` |
| `EONET_LIMIT` | Nombre max d'événements récupérés | `50` |
| `WORKER_INTERVAL_SECONDS` | Intervalle entre deux synchros (`0` = une seule passe) | `900` (15 min) |

Ces mêmes variables pilotent aujourd'hui les producers Kafka du TP2 : la cadence et le
périmètre de collecte EONET n'ont pas changé, seule la destination des messages a
évolué.

---

## Structure du dossier

```text
TP1/
├── README.md                 # ce fichier
├── docs/                     # livrables 1 à 6
│   ├── 01-presentation.md
│   ├── 02-sources.md
│   ├── 03-dictionnaire.md
│   ├── 04-entites-relations.md
│   ├── 05-mcd.md
│   └── 06-mld.md
├── sql/
│   ├── init.sql              # schéma TP1 : tables + contraintes (livrable 7)
│   └── seed.sql              # données de test (livrable 7)
└── worker/
    ├── Dockerfile
    ├── requirements.txt
    └── worker.py             # extraction API → base (version TP1)
```

L'orchestration (`docker-compose.yml`, `start.sh`, `.env.example`) se trouve à la
**racine du dépôt** et couvre les trois TP.

---

## Suite du projet

| TP | Objet | Documentation |
|---|---|---|
| **TP1** | Cartographie, modélisation, base PostgreSQL | ce document |
| **TP2** | Industrialisation : Kafka, Data Lake S3, PySpark, Metabase, monitoring | [README racine](../README.md) |
| **TP3** | Audit qualité et nettoyage des données | [`TP3/README.md`](../TP3/README.md) |
