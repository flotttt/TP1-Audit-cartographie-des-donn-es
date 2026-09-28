# Stratégie de correction

Pour chaque type d'anomalie détecté, un choix est fait entre 4 stratégies. La règle générale : **suppression** pour les anomalies bloquantes (données inexploitables), **imputation** pour les champs informatifs manquants, **correction** pour les valeurs récupérables.

Les scripts SQL correspondants sont dans `TP3/sql/cleaning/`.

## Matrice des décisions

| Contrôle | Anomalie | Stratégie | Justification | Script |
|---|---|---|---|---|
| **C01** — event.title vide | Titre absent | 🗑 Suppression | Un event sans titre est inexploitable métier (rien à afficher, rien à chercher) | `02-suppression.sql` |
| **C02** — event.description NULL | Description absente | 💧 Imputation `''` | Champ informatif ; NULL bruite les requêtes, chaîne vide neutre | `01-imputation.sql` |
| **C03** — event.link NULL | Lien absent | 🗑 Suppression | Pas de lien → pas de traçabilité source, event orphelin | `02-suppression.sql` |
| **C04** — earthquake.magnitude NULL | Magnitude absente | ⚠ Conservation | Pertinent pour l'analyse (existence du séisme même sans mesure fiable) | (aucun) |
| **C05** — earthquake.mag_type NULL | Type non renseigné | 💧 Imputation `'unknown'` | Valeur par défaut standard USGS, permet les GROUP BY | `01-imputation.sql` |
| **C06** — earthquake.place NULL | Lieu vide | 💧 Imputation `'unknown'` | Idem, permet les regroupements géographiques | `01-imputation.sql` |
| **C07** — earthquake.depth_km NULL | Profondeur absente | ⚠ Conservation | Non systématique dans USGS, NULL sémantiquement correct | (aucun) |
| **C08** — earthquake sans coords | Point non localisable | 🗑 Suppression | Sans coords → inutile pour toute cartographie/agrégation spatiale | `02-suppression.sql` |
| **C09** — geometry.coordinates NULL | Point vide | 🗑 Suppression | Idem | `02-suppression.sql` |
| **U01/U02/U04/U05** — PK dupliquée | Doublon strict d'id | ✏ Correction : garder le plus récent (`_ingested_at DESC`) | Les producers ré-envoient les mêmes ids à chaque cycle → doublon en staging attendu, la version la plus récente prime | `03-correction.sql` |
| **U03** — Quasi-doublon séisme | Même minute + 0.1° + 0.1 mag | ⚠ Conservation | Peut être 2 vrais événements successifs — la magnitude et l'id USGS restent distincts | (aucun) |
| **V01/V02** — URL sans schéma | `example.com/x` au lieu de `https://example.com/x` | ✏ Correction : préfixer `https://` | Récupérable automatiquement, préserve la donnée | `03-correction.sql` |
| **V03/V04** — Coords hors bornes | lon > 180 etc. | 🗑 Suppression | Ligne invalide, pas de correction fiable | `02-suppression.sql` |
| **V05** — Magnitude aberrante | mag > 10 ou < -1 | 🗑 Suppression | Impossible physiquement | `02-suppression.sql` |
| **V06** — Profondeur négative | depth_km < 0 | 🗑 Suppression | Impossible physiquement | `02-suppression.sql` |
| **V07** — Geometry.type inconnu | `LineString`, `MultiPoint`… | 🗑 Suppression | Non prévu par le modèle | `02-suppression.sql` |
| **V08** — Coords Point mal formées | tableau ≠ 2 valeurs | 🗑 Suppression | Ligne cassée | `02-suppression.sql` |
| **Co01** — closed antérieur au 1er point | Bug source | ⚠ Conservation + alerte | Rare, à investiguer manuellement (peut refléter une correction API rétroactive) | (aucun) |
| **Co02** — Tsunami mag < 6.5 | Flag tsunami sur petit séisme | ⚠ Conservation | Peut être un tsunami local ou une alerte préventive USGS | (aucun) |
| **Co03/Co05** — Date dans le futur | Bug source ou fuseau | 🗑 Suppression | Aberration temporelle | (à ajouter si observé) |
| **Co04** — Date > 1 an | Hors fenêtre attendue | 🗑 Suppression | Ne devrait pas exister avec `USGS_DAYS=30` | (à ajouter si observé) |
| **I01-I05** — FK orphelines | Enfant sans parent | 🗑 Suppression de l'enfant | Sans le parent, l'enfant est inutile (pas de jointure possible) | `02-suppression.sql` |

## Ordre d'exécution du nettoyage

```
1. Imputation      (01-imputation.sql)   — corrige les NULLs récupérables
2. Correction      (03-correction.sql)   — normalise formats + déduplique
3. Suppression     (02-suppression.sql)  — enlève ce qui reste d'aberrant
```

L'ordre est important : on impute d'abord (pour préserver un maximum), on normalise ensuite (pour dédupliquer proprement), on supprime en dernier (l'irrécupérable).

## Complémentarité avec Spark

Le job Spark applique déjà une politique de **suppression** sur les cas graves (URL invalide, coords hors bornes, magnitude aberrante). Le résultat qu'on voit dans `public.*` est donc déjà "propre" pour ces contrôles.

Le nettoyage SQL du TP3 apporte **en plus** :
- L'**imputation** des NULLs informatifs (`mag_type='unknown'`, `place='unknown'`, `description=''`)
- La **correction** des URLs récupérables (Spark les supprime brutalement)
- Une trace **auditée** de chaque correction (via `data_quality_report`)

## Justification d'ensemble

- On privilégie la **récupération** (imputation, correction) à la suppression tant que la sémantique est préservée.
- On supprime dès qu'une valeur est **physiquement impossible** ou empêche l'usage aval (agrégation, jointure, cartographie).
- On conserve ce qui est **suspect mais plausible** (magnitude NULL, tsunami mag < 6.5) : l'analyste métier tranchera à l'usage.
