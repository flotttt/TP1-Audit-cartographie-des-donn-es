# TP2 — Plan de travail : Pipeline Data temps réel

Plateforme data automatisée et observable, dans la continuité du TP1 (sujet **EONET**).

**Chaîne cible :**

```
API EONET ──► Producer ──► Kafka ──┐
                                   ├──► Agrégation ──► Data Lake ──► PySpark ──► PostgreSQL ──► Data Viz
Source 2 ──────────────────────────┘
                                       Prometheus ──► Grafana (monitoring + Raw vs Clean)
```

---

## 0. Décisions à prendre avant de coder

- [ ] Choisir la **Source 2** (lien métier avec EONET : enrichissement / jointure / consolidation)
  - Pistes : météo par coordonnées (Open-Meteo), référentiel géo (pays/région via reverse-geocoding), population par zone, catalogue sismique USGS...
- [ ] Choisir la solution **Data Lake** (simple : volume Docker + arborescence de fichiers Parquet/JSON ; ou MinIO S3)
- [ ] Choisir l'outil **Data Viz** (Metabase, Superset, ou Grafana avec datasource PostgreSQL)
- [ ] Valider la clé de rapprochement des 2 sources (probablement coordonnées / zone géo / date)

---

## 1. Architecture & documentation

- [ ] Schéma d'architecture (diagramme dans `docs/architecture.png` ou Mermaid)
- [ ] Faire apparaître les services Docker et les volumes de persistance
- [ ] Description des choix techniques
- [ ] Description des deux sources (format, rôle, lien métier)
- [ ] README de déploiement et d'utilisation

---

## 2. Pipeline de données

### Étape A — Collecte
- [ ] **Source 1 (API EONET)** : développer le **producer** Kafka (réutiliser `worker/worker.py`)
- [ ] Envoyer les événements dans un **topic Kafka**
- [ ] Vérifier la réception des messages (consumer de test / `kafka-console-consumer`)
- [ ] **Source 2** : mettre en place le mécanisme de récupération
- [ ] Documenter son format et son rôle

### Étape B — Agrégation
- [ ] Construire la logique de rapprochement des 2 sources
- [ ] Justifier la logique par le besoin métier

### Étape C — Data Lake
- [ ] Conserver les **données brutes** de façon identifiable
- [ ] Arborescence type : `data-lake/raw/api/`, `data-lake/raw/source2/`, `data-lake/aggregated/`

### Étape D — Traitement PySpark
- [ ] Lecture du Data Lake par PySpark
- [ ] Contrôle des types
- [ ] Gestion des valeurs manquantes
- [ ] Gestion des doublons
- [ ] Normalisation / transformation
- [ ] Enrichissement ou agrégation
- [ ] Production d'une version « propre » exploitable

### Étape E — PostgreSQL
- [ ] Charger les données propres (structure cohérente avec le modèle du TP1)
- [ ] Réutiliser / adapter `sql/init.sql`

### Étape F — Data Visualization
- [ ] Connecter PostgreSQL à l'outil de Data Viz
- [ ] Dashboard avec des indicateurs métier pertinents

---

## 3. Observabilité — Prometheus & Grafana

- [ ] Déployer Prometheus + Grafana
- [ ] **Infrastructure** : état des conteneurs, disponibilité des services, CPU / mémoire
- [ ] **PostgreSQL** : disponibilité, activité, métriques (via `postgres_exporter`)
- [ ] **Pipeline** : suivre le volume de données brutes → traitées → chargées
- [ ] **Indicateur Raw vs Clean** (comparaison volume brut / volume propre)

---

## 4. Dockerisation & automatisation

- [ ] `docker-compose.yml` orchestrant tous les composants :
  - [ ] Kafka (+ Zookeeper/KRaft)
  - [ ] Producer API
  - [ ] Source 2
  - [ ] Data Lake (volume)
  - [ ] Spark / PySpark
  - [ ] PostgreSQL
  - [ ] Data Viz
  - [ ] Prometheus
  - [ ] Grafana
- [ ] Volumes de persistance configurés
- [ ] Démarrage reproductible : `docker compose up -d` sans intervention manuelle

---

## 5. Arborescence cible

```text
TP2/
├── docker-compose.yml
├── README.md
├── api/            # producer EONET → Kafka
├── source2/        # collecte source complémentaire
├── kafka/          # config Kafka
├── spark/          # jobs PySpark
├── datalake/       # données brutes + agrégées
├── postgres/       # init.sql (repris du TP1)
├── dataviz/        # config dashboard
├── monitoring/     # prometheus + grafana
└── docs/
    └── architecture.png
```

---

## 6. Critères de réussite (checklist de validation finale)

- [ ] Deux sources complémentaires intégrées
- [ ] L'API alimente Kafka
- [ ] Les deux sources sont agrégées
- [ ] Données brutes conservées dans le Data Lake
- [ ] PySpark produit les données propres
- [ ] PostgreSQL alimenté automatiquement
- [ ] Le dashboard Data Viz exploite PostgreSQL
- [ ] Prometheus collecte les métriques
- [ ] Grafana permet le monitoring
- [ ] Volume Raw vs Clean observable
- [ ] Tous les services orchestrés avec Docker Compose
- [ ] Projet documenté et reproductible

---

## Réutilisable depuis le TP1

| Élément TP1 | Rôle en TP2 |
|---|---|
| `worker/worker.py` | Base du **producer Kafka** (Source 1) |
| `sql/init.sql` | Schéma **PostgreSQL** cible (étape E) |
| `docker-compose.yml` | Socle à étendre avec les nouveaux services |
| `docs/` (dico, MCD, MLD) | Modélisation de référence pour la cohérence du schéma |
