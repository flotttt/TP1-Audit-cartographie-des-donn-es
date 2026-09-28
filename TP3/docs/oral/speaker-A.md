# Script Speaker A

Total pour A, environ 7 minutes 30 sur 15. Passages en alternance stricte avec Speaker B.

## Slide 1, intro conjointe, 20 secondes

Bonjour, nous sommes A et B. Nous allons vous présenter notre projet Audit, cartographie et pipeline data autour des événements naturels dans le monde, à partir des API EONET de la NASA et USGS pour la sismologie.

Notre présentation couvre les TP1, TP2 et TP3, du modèle de données jusqu'à l'audit qualité, en 15 minutes. On se partage la parole.

## Slide 2, sujet et problématique, 1 minute (A)

Notre sujet est le suivi environnemental des événements naturels dans le monde, feux, tempêtes, volcans, icebergs, séismes.

On s'est appuyés sur deux API publiques. EONET, l'Earth Observatory Natural Event Tracker de la NASA, qui fournit un catalogue quasi temps réel des événements naturels au format JSON. Et l'USGS, le service géologique américain, qui fournit un catalogue mondial des séismes en GeoJSON.

Le problème métier qu'on a voulu adresser, c'est le rapprochement de ces deux sources. Par exemple, comment identifier des séismes qui surviennent à proximité d'un volcan actif dans les 7 jours qui suivent. Ce croisement n'existe pas dans les sources elles-mêmes, il fallait le construire.

Passe à B pour détailler les deux sources.

## Slide 4, TP1 modélisation, 1 minute (A)

Sur le TP1, la difficulté principale c'est que EONET renvoie du JSON imbriqué, un event contient plusieurs catégories, plusieurs sources et plusieurs points de géométrie datés. Il fallait éclater ça en tables normalisées, sans doublons, dans une base relationnelle.

On a modélisé 6 entités pour la partie EONET, event, category, source, geometry, event_category, event_source, et on a ajouté au TP2 les tables earthquake et event_earthquake pour la partie USGS et le rapprochement.

Les contraintes en base sont explicites. Les clés primaires et étrangères garantissent l'intégrité référentielle, les CHECK contraintes vérifient les formats d'URL, les bornes de coordonnées et de magnitude, et une contrainte UNIQUE sur geometry empêche les observations doublonnées.

Passe à B pour la partie base Postgres.

## Slide 6, TP2 architecture, 1 minute 30 (A)

Au TP2 on a transformé le worker du TP1 en plateforme data professionnelle.

Le pipeline part des deux API. Chaque API a son propre producer Python qui publie dans Kafka. Un consumer lit les topics et dépose des fichiers JSONL dans un Data Lake S3. Un job PySpark tourne toutes les 15 minutes, lit le Data Lake, nettoie, agrège, et charge dans PostgreSQL. Enfin Metabase interroge Postgres pour la data viz métier.

Le tout est supervisé par Prometheus qui scrape 4 exporters, cAdvisor, docker-stats, postgres-exporter et un exporter pipeline qu'on a écrit nous-mêmes. Grafana fournit le dashboard de monitoring.

16 conteneurs, orchestrés par un seul docker-compose.yml. Un script start.sh démarre tout d'un coup.

Passe à B pour Kafka.

## Slide 8, Data Lake S3, 1 minute (A)

Pour le Data Lake on utilise LocalStack, qui simule une vraie API S3 en local. On aurait pu utiliser MinIO mais son image n'est plus en pull anonyme sur Docker Hub.

L'intérêt du choix S3, c'est que boto3 et PySpark utilisent exactement les mêmes appels qu'en production sur AWS. Le jour où on migre vers du cloud, on change juste l'endpoint et les credentials.

Le consumer Kafka batch les messages, 200 messages ou 30 secondes, et les écrit en JSONL. Le partitionnement est en Hive-style, year, month, day, hour, ce qui permettra à PySpark de ne lire que les partitions utiles.

C'est notre source de vérité brute. On peut retraiter à l'infini sans re-fetch les API.

Passe à B pour PySpark.

## Slide 10, Metabase, 1 minute (A)

Point fort du projet, l'auto-provisionnement de Metabase.

Un service qu'on a écrit, metabase-init, attend que Metabase soit up, puis appelle son API REST pour, dans l'ordre, faire le setup admin, ajouter la connexion PostgreSQL, créer 12 questions SQL, créer un dashboard, y attacher les 12 questions.

Résultat, quand le prof clone le repo et lance start.sh, il n'a rien à configurer dans Metabase. Le dashboard TP2 EONET vs USGS est prêt à consulter sur localhost 3000 slash dashboard slash 2, il contient les KPIs, la carte des séismes, la carte des events, la table des rapprochements, tout est déjà en place.

Passe à B pour le monitoring.

## Slide 12, TP3 problématique, 1 minute 15 (A)

Sur le TP3, on est parti d'un constat. Spark fait déjà du nettoyage silencieux en amont, il filtre les URL invalides, les coordonnées hors bornes, les magnitudes aberrantes. Résultat, la base publique est propre, mais on n'a aucune trace de ce que Spark a filtré et pourquoi. Pas de traçabilité qualité.

Notre approche, matérialiser l'avant. On a ajouté un schéma staging dans Postgres, sans aucune contrainte, et on a modifié Spark pour qu'il écrive d'abord dans staging avec la donnée brute, puis dans public avec la donnée nettoyée.

Ensuite on a défini une matrice de 32 contrôles SQL sur les 5 dimensions classiques de la qualité, complétude, unicité, validité, cohérence, intégrité. Chaque contrôle est une simple règle SQL, si failing_rows est supérieur à zéro on a une anomalie.

Passe à B pour détailler la matrice.

## Slide 14, TP3 résultats, 1 minute 30 (A)

Le script run-audit.sh orchestre tout. Il génère un run_id UUID unique, il lance les 32 contrôles sur staging avec la phase before, puis les 32 mêmes contrôles sur public toujours en phase before pour montrer l'apport de Spark, puis il applique les scripts de cleaning sur staging, imputation, correction, suppression dans cet ordre, et enfin il relance les contrôles sur staging avec la phase after.

Sur notre run de démonstration, on avait 161 anomalies avant, dont 47 catégories dupliquées, 50 sources dupliquées, 25 events sans description et 7 séismes tsunami de faible magnitude. Après cleaning, il ne reste que 7 anomalies.

Les 7 qui restent, c'est un choix métier documenté. Ce sont des séismes flaggés tsunami avec une magnitude entre 4.8 et 6.3, tous localisés en Alaska ou dans le Pacifique. Ces zones connaissent des tsunamis locaux réels, générés par des glissements sous-marins par exemple. Supprimer ces lignes ferait perdre des événements réels. On les conserve donc explicitement, avec la justification tracée dans la doc.

94 pour cent des anomalies résolues, avec traçabilité complète dans data_quality_report.

Passe à B pour la conclusion.

## Notes de coordination

Avant la présentation, se caler sur qui clique la diapo. Suggéré, chacun clique quand il commence à parler.

Timing serré, 15 minutes pile pour 15 slides, environ 1 minute par slide. Le speaker A parle sur 8 slides, cumul environ 7 minutes 45 en comptant l'intro conjointe.

Éviter de couper l'autre, mais bien enchaîner. Une petite pause de 2 secondes entre chaque passe donne du rythme sans casser le fil.

Si une démo est possible sur écran, la caler sur slide 8 pour le Data Lake ou slide 10 pour Metabase, prévoir un backup screenshot au cas où.
