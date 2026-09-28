# Cartographie mise à jour (TP3)

Le TP3 étend le pipeline TP1/TP2 avec une couche `staging` : les données brutes du Data Lake sont désormais également chargées **sans nettoyage** dans un schéma dédié, pour permettre l'audit qualité avant/après.

## Vue macro du flux de données

```
API EONET ─┐
           ├─► Kafka ─► S3 Data Lake ──► Spark ─┬─► staging.*  (brut, sans contraintes)
API USGS ──┘                                    │
                                                └─► public.*   (cleaned, avec contraintes)
                                                       │
                                                       └─► Metabase (BI métier)

                                                staging.* + public.*
                                                       │
                                                       ▼
                                                TP3 audit SQL ─► data_quality_report
```

## Schémas Postgres

### `public` (donnée nettoyée par Spark)

Schéma défini dans `TP2/postgres/init.sql`. Toutes les contraintes CHECK et FK sont en place. Une ligne qui atterrit ici a été validée par Spark **et** par Postgres.

| Table | Rôle | Contraintes clés |
|---|---|---|
| `event` | Événement EONET | PK, `title` non vide, `link` matche `^https?://` |
| `category` | Catégorie EONET | PK, `title` non vide |
| `source` | Source EONET | PK, `url` matche `^https?://` |
| `geometry` | Points/polygones datés | FK vers `event`, `type ∈ {Point, Polygon}`, coords valides |
| `event_category` | N↔N event ↔ category | PK composite, 2 FK |
| `event_source` | N↔N event ↔ source | PK composite, 2 FK |
| `earthquake` | Séisme USGS | PK, coords dans les bornes, magnitude ∈ [-1, 10] |
| `event_earthquake` | Rapprochement EONET ↔ USGS | PK composite, 2 FK, distance & délai |

### `staging` (donnée brute, sans contraintes) — nouveau TP3

Schéma défini dans `TP3/sql/00-schema-staging.sql`. **Aucune contrainte** (pas de PK, FK, CHECK, NOT NULL). Reçoit ce que Spark lit depuis le Data Lake, avant tout filtrage.

Chaque table `staging.*` a une colonne supplémentaire `_ingested_at` (timestamp d'insertion) pour le dédoublonnage et le suivi.

| Table `staging.*` | Origine | Différences avec `public.*` |
|---|---|---|
| `event` | Direct du JSON EONET | Titre/description/link peuvent être NULL/vides/mal formés |
| `category` | Explode du JSON EONET | Titre potentiellement NULL, doublons possibles |
| `source` | Explode du JSON EONET | URL possiblement invalide, doublons possibles |
| `geometry` | Explode du JSON EONET | `date` en TEXT (accepte formats invalides), coords non validées |
| `event_category` | Explode du JSON | Peut contenir des FK orphelines |
| `event_source` | Explode du JSON | Peut contenir des FK orphelines |
| `earthquake` | Direct du GeoJSON USGS | Coords / magnitude non bornées, `mag_type` NULL possible |

## Table `data_quality_report`

Trace **chaque exécution** de chaque contrôle qualité. C'est le pivot du dashboard qualité et du reporting avant/après.

| Colonne | Type | Rôle |
|---|---|---|
| `run_id` | UUID | Groupe une exécution complète (before + after) |
| `phase` | `'before'` \| `'after'` | Étape de nettoyage |
| `control_id` | TEXT | ID de la matrice (`C01`, `U02`, `V03`, …) |
| `dimension` | TEXT | `completude` / `unicite` / `validite` / `coherence` / `integrite` |
| `table_name` | TEXT | `staging.event`, `public.earthquake`, … |
| `total_rows` | BIGINT | Volumétrie de la table auditée |
| `failing_rows` | BIGINT | Lignes en échec du contrôle |
| `fail_rate` | NUMERIC | Ratio calculé automatiquement |
| `details` | TEXT | Description humaine du contrôle |

## Cycle d'audit typique

```
1. Spark tourne          → staging.* et public.* remplis
2. run-audit.sh          → audit staging (phase=before)
                        → audit public  (phase=before)  ← ce que Spark a laissé
                        → cleaning SQL sur staging     ← imputation, suppression, correction
                        → audit staging (phase=after)  ← anomalies corrigées
3. Rapport               → SELECT ... FROM data_quality_report WHERE run_id = ...
```
