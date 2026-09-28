# Synthèse orale — TP3

## Message central

> Nous avons ajouté au pipeline TP1/TP2 un **audit qualité formalisé** en SQL, avec un schéma `staging` qui capture les données brutes, une matrice de **32 contrôles** sur 5 dimensions, un **nettoyage SQL** et un **rapport avant/après** stocké dans `data_quality_report`. Résultat : **94% des anomalies résolues**, les 6% restantes conservées par choix métier justifié.

## Plan (3 min)

1. **Contexte** (30s)
   - TP1/TP2 : pipeline temps réel EONET + USGS → PostgreSQL. Spark filtre déjà silencieusement les données invalides.
   - Problème : sans audit, on ne sait pas **combien** ni **quoi** est filtré. Pas de traçabilité qualité.

2. **Approche** (45s)
   - Ajout d'un schéma `staging` **sans contraintes** → capture les données brutes du Data Lake avant tout nettoyage.
   - Matrice de contrôles sur 5 dimensions : complétude, unicité, validité, cohérence, intégrité (32 contrôles au total).
   - Chaque contrôle est une fonction PL/pgSQL `audit_control(schema, table, where_clause, ...)` → insère un enregistrement dans `data_quality_report`.

3. **Démo** (1 min)
   - Lancer `./TP3/run-audit.sh`.
   - Montrer le tableau final : 122 anomalies détectées avant, 7 après (conservées volontairement).
   - Ouvrir la table `data_quality_report` pour montrer la traçabilité.

4. **Choix de correction** (30s)
   - Suppression pour l'irrécupérable (coords invalides, PK dupliquées, URL malformées).
   - Imputation pour les NULLs informatifs (`description=''`, `mag_type='unknown'`).
   - Correction pour le récupérable (préfixage `https://` sur URLs sans schéma).
   - Conservation pour les cas ambigus (tsunami de magnitude < 6.5 : peut être un vrai tsunami local).

5. **Résultat** (15s)
   - `public.*` reste alimenté par Spark → dashboards Metabase inchangés, pipeline opérationnel.
   - `data_quality_report` alimente un futur dashboard qualité Metabase / Grafana.
   - Traçabilité complète : chaque run laisse une trace UUID datée.

## Chiffres clés à annoncer

- **32 contrôles** sur 5 dimensions
- **122 anomalies** détectées en staging brut
- **-94%** après nettoyage SQL (**115 corrigées**, 7 conservées)
- **fail_rate = 0** pour 30/32 contrôles après nettoyage

## Questions/réponses anticipées

**Q : Pourquoi un schéma staging alors que Spark nettoie déjà ?**
R : Pour matérialiser le "avant" et pouvoir mesurer l'apport du nettoyage. Sans staging, on n'a que la donnée déjà propre — impossible de démontrer la qualité du pipeline.

**Q : Pourquoi ne pas corriger les 7 anomalies Co02 restantes ?**
R : Choix métier documenté : un tsunami avec magnitude 5-6 peut être local (glissement sous-marin, séisme côtier peu profond). Supprimer ferait perdre des événements réels. La conservation est explicite et tracée.

**Q : L'audit est-il rejouable ?**
R : Oui. Chaque exécution génère un `run_id` UUID. Les résultats de N runs sont conservés dans `data_quality_report` → on peut comparer l'évolution qualité dans le temps.

**Q : Comment automatiser l'audit ?**
R : `run-audit.sh` peut être exécuté par cron ou intégré au compose comme un service `audit-runner` qui tourne toutes les X heures. Pour ce TP nous avons privilégié l'exécution manuelle pour la démo.

**Q : Est-ce que ça marche sur d'autres tables ?**
R : Oui. La fonction `audit_control(p_schema, p_table, p_where, ...)` est générique — on ajoute un contrôle en écrivant une ligne SQL dans un fichier de `sql/audit/`.
