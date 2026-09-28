# TP3 — Audit qualité & nettoyage des données

Extension du TP1/TP2. Ajoute un **audit qualité formalisé** en SQL sur les données produites par le pipeline (Data Lake → Spark → PostgreSQL), avec un rapport chiffré **avant/après** nettoyage.

## Livrables (mapping brief)

| Exigence | Où |
|---|---|
| Cartographie mise à jour | [`docs/01-cartographie.md`](docs/01-cartographie.md) |
| Matrice de contrôles qualité | [`docs/02-matrice-controles.md`](docs/02-matrice-controles.md) |
| Classement des anomalies | [`docs/03-anomalies.md`](docs/03-anomalies.md) |
| Stratégies de correction | [`docs/04-corrections.md`](docs/04-corrections.md) |
| Résultats avant/après | [`docs/05-resultats.md`](docs/05-resultats.md) |
| Synthèse pour l'oral | [`docs/06-synthese-orale.md`](docs/06-synthese-orale.md) |
| Scripts SQL d'audit | [`sql/audit/`](sql/audit/) |
| Scripts SQL de nettoyage | [`sql/cleaning/`](sql/cleaning/) |
| Table de rapport | [`sql/01-report-table.sql`](sql/01-report-table.sql) |
| Orchestrateur | [`run-audit.sh`](run-audit.sh) |

## Approche

Le TP1/TP2 alimentait directement `public.*` avec des données déjà nettoyées par Spark. Pour pouvoir mesurer la qualité **avant** intervention, le TP3 ajoute :

1. Un **schéma `staging`** qui reçoit les données brutes du Data Lake **sans contraintes** — mêmes tables que `public.*`, mais tout est nullable et sans FK.
2. Une modification du job Spark : il écrit **d'abord dans `staging.*`** (raw), **puis** dans `public.*` (cleaned).
3. Une **matrice de 32 contrôles SQL** sur 5 dimensions (complétude, unicité, validité, cohérence, intégrité).
4. Des **scripts de nettoyage SQL** (imputation, correction, suppression) qui transforment `staging.*`.
5. Une **table `data_quality_report`** qui trace chaque exécution de chaque contrôle avec un `run_id` UUID.

## Prérequis

Stack TP1/TP2 démarrée (`./start.sh` depuis la racine). Le job Spark doit avoir tourné au moins une fois.

## Lancer l'audit

```bash
./TP3/run-audit.sh
```

Le script :
1. Applique le schéma `staging` et la table `data_quality_report` (idempotent).
2. Lance les 32 contrôles sur `staging.*` (phase `before`).
3. Lance les 32 contrôles sur `public.*` (phase `before`, montre l'apport de Spark).
4. Exécute le nettoyage SQL sur `staging.*` (imputation → correction → suppression).
5. Re-lance les contrôles sur `staging.*` (phase `after`).
6. Affiche un rapport synthétique.

## Consulter les résultats

Rapport synthétique par dimension pour le dernier run :

```sql
SELECT phase, dimension,
       COUNT(*) AS controles,
       SUM(failing_rows) AS anomalies,
       COUNT(*) FILTER (WHERE failing_rows > 0) AS controles_en_echec
FROM data_quality_report
WHERE run_id = (SELECT run_id FROM data_quality_report ORDER BY run_at DESC LIMIT 1)
GROUP BY phase, dimension
ORDER BY phase, dimension;
```

Détail des contrôles en échec :

```sql
SELECT phase, control_id, dimension, table_name, total_rows, failing_rows,
       ROUND(fail_rate * 100, 2) AS fail_pct, details
FROM data_quality_report
WHERE run_id = (SELECT run_id FROM data_quality_report ORDER BY run_at DESC LIMIT 1)
  AND failing_rows > 0
ORDER BY phase DESC, dimension, control_id;
```

## Structure

```
TP3/
├── README.md
├── run-audit.sh
├── docs/
│   ├── 01-cartographie.md
│   ├── 02-matrice-controles.md
│   ├── 03-anomalies.md
│   ├── 04-corrections.md
│   ├── 05-resultats.md
│   └── 06-synthese-orale.md
└── sql/
    ├── 00-schema-staging.sql       # CREATE SCHEMA staging + tables sans contraintes
    ├── 01-report-table.sql         # data_quality_report + fonctions audit_control/audit_join/to_timestamp_safe
    ├── audit/
    │   ├── 01-completude.sql       # 9 contrôles
    │   ├── 02-unicite.sql          # 5 contrôles
    │   ├── 03-validite.sql         # 8 contrôles
    │   ├── 04-coherence.sql        # 5 contrôles
    │   └── 05-integrite.sql        # 5 contrôles
    └── cleaning/
        ├── 01-imputation.sql       # NULL → valeur par défaut
        ├── 02-suppression.sql      # DELETE des lignes irrécupérables
        └── 03-correction.sql       # normalisation + dédup
```

## Résultats typiques

- **~120 anomalies détectées** sur staging brut
- **~7 anomalies restantes** après cleaning (conservées volontairement, cf. `04-corrections.md`)
- **~94% de résolution**
- `public.*` déjà propre pour 30/32 contrôles grâce à Spark

Voir [`docs/05-resultats.md`](docs/05-resultats.md) pour les chiffres détaillés.
