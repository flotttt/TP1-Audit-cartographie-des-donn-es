---
marp: true
theme: default
paginate: true
size: 16:9
---

# Audit, cartographie et pipeline data

## EONET (NASA) et USGS

TP1, TP2 et TP3

**Speaker A** et **Speaker B**

---

<!-- Slide 2, Speaker A, environ 1 min -->

## Sujet et problématique

**Suivi des événements naturels dans le monde**

Feux, tempêtes, volcans, icebergs, séismes

**Deux sources publiques, deux formats, deux périmètres**

EONET (NASA) : catalogue temps réel des events, JSON imbriqué

USGS (US Geological Survey) : catalogue mondial des séismes, GeoJSON

**Problématique**

Comment croiser ces deux sources pour repérer des liens spatio-temporels ?
Un séisme proche d'un volcan actif dans les 7 jours, par exemple.

---

<!-- Slide 3, Speaker B, environ 1 min -->

## Les deux sources en détail

**EONET, source 1**

50 événements ouverts par cycle, format JSON avec catégories, sources et géométries imbriquées

Endpoint `/events` interrogé toutes les 15 minutes

**USGS, source 2**

Jusqu'à 500 séismes de magnitude supérieure ou égale à 4.5 par cycle, format GeoJSON

Endpoint `/fdsnws/event/1/query` interrogé toutes les 15 minutes

**Lien métier**

Rapprochement spatial (haversine, rayon 500 km) et temporel (fenêtre plus ou moins 7 jours) entre les geometry points EONET et les séismes USGS.

---

<!-- Slide 4, Speaker A, environ 1 min -->

## TP1, modélisation

**Passage du JSON imbriqué EONET à un schéma relationnel normalisé**

```
event  1 --- N  geometry             un event, plusieurs points datés
event  N --- N  category              via event_category
event  N --- N  source                via event_source
```

**6 tables initiales pour la source EONET, plus 2 pour l'intégration USGS au TP2**

`event`, `category`, `source`, `geometry`, `event_category`, `event_source`, `earthquake`, `event_earthquake`

**Contraintes en base**

PK, FK, CHECK (URLs, coordonnées, magnitudes), UNIQUE (unicité des observations)

---

<!-- Slide 5, Speaker B, environ 1 min -->

## TP1, base PostgreSQL

**Docker Compose, 3 services au départ**

`db` (Postgres 16 avec `init.sql`), `worker` (Python, extract API vers upsert), `pgadmin` (administration)

**Worker EONET, extraction en boucle**

`INSERT ... ON CONFLICT` pour éviter les doublons entre 2 cycles

**Livrables du TP1**

Cartographie des sources, dictionnaire de données, entités et relations, MCD, MLD, script SQL et seed

**Base opérationnelle, prête à être étendue**

---

<!-- Slide 6, Speaker A, environ 1 min 30 -->

## TP2, architecture cible

**Objectif, transformer le worker en plateforme data professionnelle**

```
API EONET  -> Producer -> Kafka -+
                                 +-> Consumer -> Data Lake S3 -> PySpark -> PostgreSQL -> Metabase
API USGS   -> Producer -> Kafka -+

Monitoring, cAdvisor, docker-stats-exporter, postgres_exporter,
pipeline-exporter -> Prometheus -> Grafana
```

**Chaque étape est un service Docker, orchestré par un unique `docker-compose.yml`**

**16 conteneurs au total**, démarrage en une commande, `./start.sh`

---

<!-- Slide 7, Speaker B, environ 1 min -->

## TP2, ingestion Kafka

**Deux producers, un pattern homogène**

`tp-eonet-producer` fetch EONET, publie sur le topic `eonet.events`

`tp-usgs-producer` fetch USGS, publie sur le topic `usgs.earthquakes`

**Broker Kafka en mode KRaft**

Apache Kafka 3.9 sans Zookeeper, mono-broker, healthcheck sur `kafka-broker-api-versions`

**Kafka UI en bonus**, `http://localhost:8080` pour visualiser les topics et les payloads

**Découplage acquis**, si Postgres tombe, les messages restent dans Kafka et sont rattrapés

---

<!-- Slide 8, Speaker A, environ 1 min -->

## TP2, Data Lake S3

**LocalStack S3 comme serveur S3 compatible en local**

API S3 standard, `boto3` marche pareil qu'avec AWS

**Un consumer Kafka écrit des fichiers JSONL partitionnés Hive-style**

```
raw/
  eonet/year=2026/month=09/day=25/hour=09/eonet-...jsonl
  usgs/ year=2026/month=09/day=25/hour=09/usgs-...jsonl
```

**Rôle**, la source de vérité brute, on peut retraiter à l'infini

**Batch adaptatif**, 200 messages ou 30 secondes, ce qui arrive en premier

---

<!-- Slide 9, Speaker B, environ 1 min 30 -->

## TP2, traitement PySpark

**Job qui tourne toutes les 15 minutes**

Image `apache/spark:3.5.3`, `local[*]`, packages Hadoop AWS et JDBC PostgreSQL

**Ce que fait le job**

1. Lit `s3a://raw/eonet/` et `s3a://raw/usgs/` récursivement
2. Écrit d'abord la donnée brute dans `staging.*` (pour l'audit TP3)
3. Nettoie, dédoublonne, valide les types
4. Charge dans `public.*` via JDBC
5. Agrège les 2 sources, formule haversine, rayon 500 km, fenêtre plus ou moins 7 jours

**Résultat**, 50 events, 486 séismes, 17 rapprochements détectés

---

<!-- Slide 10, Speaker A, environ 1 min -->

## TP2, data viz Metabase

**Auto-provisionnement complet au premier boot**

Service `metabase-init`, script Python qui appelle l'API Metabase

Setup admin, connexion Postgres, création de 12 questions SQL, création du dashboard

**Dashboard "TP2 EONET vs USGS"**

KPI, cartes, séries temporelles, table des rapprochements event et séisme

**Le prof clone, lance `./start.sh`, ouvre `http://localhost:3000/dashboard/2`**

Zero clic manuel

---

<!-- Slide 11, Speaker B, environ 1 min 30 -->

## TP2, monitoring et Raw vs Clean

**Stack Prometheus et Grafana, 4 exporters**

`cAdvisor`, état des conteneurs, `docker-stats-exporter` custom, CPU et mémoire par conteneur

`postgres-exporter`, connexions, taille, activité de la base

`pipeline-exporter` custom, l'indicateur Raw vs Clean exigé par le brief

**Dashboard Grafana auto-provisionné**

9 panels, conteneurs actifs, Postgres up, CPU, mémoire, connexions, taille base, Raw vs Clean

**Preuve que le pipeline traite bien ce qu'il collecte**

Volume raw dans S3 vs volume clean dans Postgres, courbes qui se suivent

---

<!-- Slide 12, Speaker A, environ 1 min 15 -->

## TP3, problématique de la qualité

**Constat, Spark filtre déjà les données invalides**

`public.*` est propre, mais on n'a aucune trace de ce qui a été filtré et pourquoi

**Approche TP3, matérialiser l'avant**

Ajout d'un schéma `staging` sans contraintes, Spark y écrit la donnée brute

Ajout d'une matrice de 32 contrôles SQL sur 5 dimensions

**Dimensions couvertes**

Complétude, unicité, validité, cohérence, intégrité

**Chaque contrôle est une règle SQL**, `failing_rows > 0` égale anomalie détectée

---

<!-- Slide 13, Speaker B, environ 1 min 30 -->

## TP3, matrice des 32 contrôles

**Répartition sur 5 dimensions**

| Dimension | Contrôles | Exemples |
|---|---|---|
| Complétude | 9 | `event.title` non vide, `earthquake.coords` renseignés |
| Unicité | 5 | PK unique, quasi-doublons séismes |
| Validité | 8 | URL `^https?://`, `lon in [-180, 180]`, `mag in [-1, 10]` |
| Cohérence | 5 | tsunami avec magnitude, dates pas dans le futur |
| Intégrité | 5 | FK theoriques, event_category vers event et category |

**Fonction PL/pgSQL `audit_control(schema, table, where_clause, ...)`**

Insère une ligne dans `data_quality_report` avec `run_id`, `phase`, `total_rows`, `failing_rows`, `fail_rate`

---

<!-- Slide 14, Speaker A, environ 1 min 30 -->

## TP3, résultats avant et après

**Un `run-audit.sh`, un `run_id` UUID unique**

Audit staging phase before, audit public phase before, cleaning SQL, audit staging phase after

**Chiffres du run de démonstration**

| Phase | Anomalies | Contrôles en échec |
|---|---|---|
| before staging | 161 | 4 sur 32 |
| after staging | 7 | 1 sur 32 |

**94 pour cent des anomalies résolues**

**Les 7 qui restent, conservation volontaire**, tsunamis magnitude 5 à 6 en Alaska et Pacifique, tsunamis locaux réels, ne pas supprimer

---

<!-- Slide 15, Speaker B, environ 45 s -->

## Conclusion

**Ce qu'on a livré**

TP1, cartographie et modélisation, base Postgres

TP2, pipeline temps réel complet, 16 conteneurs, deux dashboards auto-provisionnés

TP3, audit qualité formalisé, 32 contrôles, 94 pour cent d'anomalies résolues

**Une commande pour tout démarrer**, `./start.sh`

**Une commande pour tout auditer**, `./TP3/run-audit.sh`

**Merci, questions ?**
