# Classement des anomalies

Ce document classe les anomalies détectées par ordre de criticité, c'est-à-dire d'impact métier. Les chiffres sont un instantané typique après un cycle de Spark. Ils varient à chaque exécution puisque les producers refetchent leur fenêtre à chaque cycle.

## Niveaux de criticité

Haute : donnée inutilisable, empêche l'insertion en `public.*` (bloquée par CHECK ou FK) ou casse une jointure.

Moyenne : donnée dégradée mais utilisable, nécessite imputation ou attention.

Faible : signal informatif, pas d'impact fonctionnel.

## Top anomalies typiquement observées

### Criticité haute

| ID | Anomalie | Volumétrie typique staging | Cause probable |
|---|---|---|---|
| U01 et U02 | Doublons de PK (`event.id`, `earthquake.id`) | Élevée (les producers refetchent à chaque cycle 15 minutes) | Comportement attendu du pipeline, Spark déduplique côté public |
| V01 et V02 | URL sans schéma `http(s)://` | Rare (0 à 2 lignes) | Bug ponctuel API source |
| C08 | `earthquake` sans coordonnées | Rare | Feature sismique incomplète côté USGS |
| I01 à I05 | FK orphelines | 0 en staging (car staging est complet) | Théoriquement impossible dans le flux normal |

### Criticité moyenne

| ID | Anomalie | Volumétrie typique | Traitement |
|---|---|---|---|
| C04 | `earthquake.magnitude` NULL | 0 à 1 pour cent | Conservation (info précieuse même sans magnitude) |
| U03 | Quasi-doublons séismes | 0 à 5 pour cent | Conservation (peuvent être 2 secousses distinctes) |
| V06 | Profondeur négative | 0 en pratique | Suppression si observé |
| Co03 et Co05 | Dates dans le futur | 0 en pratique | Suppression si observé |

### Criticité faible

| ID | Anomalie | Volumétrie typique | Traitement |
|---|---|---|---|
| C02 | `event.description` NULL | 30 à 60 pour cent | Imputation `''` (EONET ne fournit souvent pas de description) |
| C05 | `earthquake.mag_type` NULL | 0 à 5 pour cent | Imputation `'unknown'` |
| C06 | `earthquake.place` NULL | Rare | Imputation `'unknown'` |
| C07 | `earthquake.depth_km` NULL | 5 à 10 pour cent | Conservation (info manquante est aussi une info) |

## Effet du pipeline Spark

Le job Spark applique déjà, avant écriture en `public.*` :

Dédup sur `id` (résout U01, U02, U04, U05).
Filtre URL invalide (résout V01, V02).
Filtre coords hors bornes (résout V03, V04).
Filtre magnitude hors [-1, 10] (résout V05).
Filtre géométrie sans coords ou type inconnu (résout V07, V08).
Filtre événement sans titre ou sans lien (résout C01, C03).

Conséquence : sur `public.*`, on observe typiquement `fail_rate = 0` pour environ 90 pour cent des contrôles. Les seules anomalies qui subsistent en `public` sont les NULLs informatifs (C02, C05, C06, C07, C04) que le pipeline conserve volontairement.

## Volumétrie mesurée automatiquement

Le tableau ci-dessus est indicatif. Les chiffres réels sont dans `data_quality_report` après exécution de `./run-audit.sh`. Le document `05-resultats.md` présente le comparatif chiffré avant et après.

```sql
SELECT
    dimension,
    COUNT(*) AS controles,
    SUM(failing_rows) AS total_anomalies
FROM data_quality_report
WHERE phase = 'before' AND table_name LIKE 'staging.%'
GROUP BY dimension
ORDER BY total_anomalies DESC;
```
