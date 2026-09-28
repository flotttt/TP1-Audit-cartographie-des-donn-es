# Résultats, avant et après nettoyage

## Résumé du run d'audit

Exécution : `./run-audit.sh`. Extrait de `data_quality_report` (fail_rate en pourcentage pour la lisibilité).

### Vue synthétique par dimension

| Phase | Dimension | Contrôles | En échec | Total anomalies |
|---|---|---|---|---|
| before staging plus public | Complétude | 18 (9 fois 2) | 2 | 50 |
| before staging plus public | Unicité | 10 (5 fois 2) | 2 | 97 |
| before staging plus public | Validité | 16 (8 fois 2) | 0 | 0 |
| before staging plus public | Cohérence | 10 (5 fois 2) | 2 | 14 |
| before staging plus public | Intégrité | 10 (5 fois 2) | 0 | 0 |
| after staging | Complétude | 9 | 0 | 0 |
| after staging | Unicité | 5 | 0 | 0 |
| after staging | Validité | 8 | 0 | 0 |
| after staging | Cohérence | 5 | 1 | 7 (conservés) |
| after staging | Intégrité | 5 | 0 | 0 |

### Détail des contrôles en échec (before et after)

| Phase | Contrôle | Dimension | Table | Total | En échec | Fail rate | Décision |
|---|---|---|---|---|---|---|---|
| before | C02 | complétude | `staging.event` | 50 | 25 | 50 pour cent | Imputé `''` |
| before | C02 | complétude | `public.event` | 50 | 25 | 50 pour cent | conservé par Spark |
| before | U04 | unicité | `staging.category` | 50 | 47 | 94 pour cent | Dédupliqué |
| before | U05 | unicité | `staging.source` | 55 | 50 | 91 pour cent | Dédupliqué |
| before | Co02 | cohérence | `staging.earthquake` | 500 | 7 | 1.4 pour cent | Conservé (peut être tsunami local) |
| before | Co02 | cohérence | `public.earthquake` | 500 | 7 | 1.4 pour cent | Conservé |
| after | Co02 | cohérence | `staging.earthquake` | 500 | 7 | 1.4 pour cent | Conservé (choix métier) |

## Interprétation

### Efficacité du nettoyage TP3

Le nettoyage SQL du TP3 résout entièrement :

Complétude C02 (description NULL) : 25 sur 50, ramené à 0, gain de 100 pour cent, imputation par chaîne vide.

Unicité U04 (catégories dupliquées) : 47 sur 50, ramené à 0, gain de 100 pour cent, dédup par `id`, garde le plus récent (`_ingested_at DESC`).

Unicité U05 (sources dupliquées) : 50 sur 55, ramené à 0, gain de 100 pour cent, même logique.

Total anomalies avant : 122. Total anomalies après : 7 (conservées volontairement). Taux de résolution : 94 pour cent.

### Cohérence Spark et SQL

`staging.*` et `public.*` produisent les mêmes anomalies avant nettoyage pour les contrôles C02 (description NULL) et Co02 (tsunami). C'est normal, Spark ne filtre pas ces cas (règle métier vs contrainte physique).

Pour tous les autres contrôles (validité, intégrité, unicité stricte), `public.*` est déjà propre grâce à Spark, `fail_rate = 0` sans intervention. C'est la complémentarité voulue entre les deux couches de nettoyage :

| Couche | Rôle | Actions |
|---|---|---|
| Spark (public) | Barrière stricte | Suppression des lignes qui violent les contraintes physiques (coords, magnitude, URL) |
| SQL TP3 (staging) | Nettoyage fin | Imputation des NULLs, correction des formats, dédup |

### Anomalies conservées (Co02)

Les 7 séismes avec `tsunami=true` et `magnitude < 6.5` sont conservés :

Raison métier : les tsunamis locaux (magnitude 5 à 6) existent (glissement de terrain sous-marin, séisme côtier peu profond).

Le flag `tsunami=true` peut aussi être une alerte préventive USGS.

Suppression égale risque de perdre des événements réels.

Ces 7 anomalies sont documentées mais non corrigées, conformément à la stratégie décrite dans `04-corrections.md`.

## Reproduire

```bash
./TP3/run-audit.sh
```

Chaque exécution crée un `run_id` unique. Comparer deux exécutions :

```sql
SELECT run_id, run_at, phase, SUM(failing_rows) AS anomalies
FROM data_quality_report
GROUP BY run_id, run_at, phase
ORDER BY run_at DESC;
```

## Requête pour extraction Excel ou Metabase

```sql
SELECT
    phase,
    dimension,
    control_id,
    table_name,
    total_rows,
    failing_rows,
    ROUND(fail_rate * 100, 2) AS fail_pct,
    details
FROM data_quality_report
WHERE run_id = (SELECT run_id FROM data_quality_report ORDER BY run_at DESC LIMIT 1)
ORDER BY phase, dimension, control_id;
```
