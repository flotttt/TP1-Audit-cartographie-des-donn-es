# Script Speaker B

Total pour B, environ 7 minutes 30 sur 15. Passages en alternance stricte avec Speaker A.

## Slide 1, intro conjointe, 20 secondes

Merci A. Pour préciser, on suit l'ordre chronologique de nos rendus. TP1 pour poser le modèle, TP2 pour industrialiser le pipeline, TP3 pour formaliser la qualité. On enchaîne.

## Slide 3, les deux sources en détail, 1 minute (B)

EONET est notre source 1. On récupère 50 événements ouverts par cycle, format JSON, avec pour chaque event un tableau de catégories, un tableau de sources et un tableau de géométries datées. L'API expose plusieurs endpoints, categories, sources et events. On interroge events toutes les 15 minutes.

USGS est notre source 2. On récupère jusqu'à 500 séismes de magnitude supérieure ou égale à 4.5 par cycle, format GeoJSON, avec les propriétés physiques du séisme, magnitude, profondeur, tsunami, et un point unique en géométrie. Même fréquence, 15 minutes.

Le lien métier entre les deux, c'est un rapprochement spatial et temporel. Pour chaque point de géométrie d'un event EONET, on cherche les séismes qui ont eu lieu dans un rayon de 500 kilomètres et dans une fenêtre plus ou moins 7 jours. La distance est calculée avec la formule haversine, en SQL Spark.

Passe à A pour la modélisation TP1.

## Slide 5, TP1 base PostgreSQL, 1 minute (B)

Sur la partie infra du TP1, on a un Docker Compose avec 3 services, la base Postgres en version 16 avec un init.sql qui crée toutes les tables et contraintes au démarrage, un worker Python qui extrait EONET et fait des upserts, et pgAdmin pour visualiser.

Le worker fait de l'INSERT ON CONFLICT DO UPDATE sur toutes les tables, ce qui garantit l'idempotence, on peut relancer sans risquer de doublons. Il tourne en boucle infinie avec un intervalle configurable via WORKER_INTERVAL_SECONDS.

Côté livrables, on a la cartographie des sources, le dictionnaire de données, le tableau des entités et relations avec cardinalités, le MCD, le MLD, et le script init.sql commenté avec un seed pour les tests. La base est opérationnelle, prête à être étendue au TP2.

Passe à A pour l'architecture TP2.

## Slide 7, TP2 ingestion Kafka, 1 minute (B)

Sur l'ingestion, on a fait un choix. Le brief demandait Kafka pour la source 1 API, la source 2 pouvant être batch. On a choisi de mettre les deux sources en Kafka pour homogénéiser le pattern d'ingestion, les deux sont des API temps réel.

Un producer Python par source, tp-eonet-producer et tp-usgs-producer, avec confluent-kafka. Chaque producer publie sur son propre topic, eonet.events et usgs.earthquakes. La key est l'id de l'event ou du séisme, la value est le JSON complet.

Le broker Kafka est en mode KRaft, la nouvelle architecture Apache Kafka sans Zookeeper. On tourne sur l'image officielle apache slash kafka en 3.9. On a un healthcheck sur kafka-broker-api-versions pour que les autres services sachent quand Kafka est prêt à accepter des connexions.

En bonus on a Kafka UI sur le port 8080, très pratique pour visualiser en direct les topics et le contenu des messages pendant la démo.

L'apport de Kafka, c'est le découplage. Si Postgres tombe, les messages restent dans Kafka et sont rattrapés au reboot. On peut aussi ajouter des consumers sans toucher aux producers.

Passe à A pour le Data Lake.

## Slide 9, TP2 traitement PySpark, 1 minute 30 (B)

Le job Spark tourne en boucle, toutes les 15 minutes. Image apache slash spark en 3.5.3, mode local slash étoile, avec les packages Hadoop AWS pour lire S3 et le driver JDBC PostgreSQL pour écrire en base.

Ce que fait le job, dans l'ordre. Il tronque toutes les tables cible, on est en pattern reprocess complet. Il lit récursivement les fichiers JSONL depuis LocalStack S3. Il écrit d'abord la donnée brute dans staging point étoile, sans nettoyage, on y reviendra sur le TP3. Il applique ensuite le nettoyage, contrôle des types, deduplication sur id, filtres sur les valeurs invalides. Il charge en JDBC dans public point étoile. Et enfin il calcule l'agrégation event et séisme via la formule haversine.

Sur notre dernier run, on avait 50 events EONET, 486 séismes USGS et 17 rapprochements détectés dans la fenêtre 500 kilomètres et 7 jours. Par exemple l'ouragan Polo au Mexique rapproché d'un séisme M 5.3 au large du Michoacan à 39 kilomètres, cohérent géographiquement.

Passe à A pour Metabase.

## Slide 11, TP2 monitoring et Raw vs Clean, 1 minute 30 (B)

Sur le monitoring on a Prometheus qui scrape 4 exporters.

Le premier, cAdvisor, image officielle Google, qui donne l'état des conteneurs. On l'a doublé avec un exporter maison, docker-stats-exporter, qui interroge directement l'API Docker Engine. Pourquoi les deux, parce que cAdvisor a des limitations sous certains drivers cgroup, notamment cgroup v2 avec systemd, on a documenté ça dans le README.

Le deuxième, postgres-exporter, connexions actives, taille des bases, activité SQL, tout ce qu'il faut pour surveiller Postgres.

Le troisième, pipeline-exporter, c'est celui qu'on a écrit spécifiquement pour ce TP. Il expose des gauges Prometheus, pipeline_raw_lines_total et pipeline_clean_rows_total, en interrogeant à la fois S3 pour compter les lignes JSONL brutes et Postgres pour compter les lignes propres.

Le dashboard Grafana est auto-provisionné, on livre le fichier JSON dans le repo et Grafana le charge au boot. 9 panels, dont le panel Raw vs Clean qui superpose les courbes du volume raw et du volume clean. On voit en direct que le pipeline traite bien ce qu'il collecte.

C'est exactement l'indicateur exigé par le brief.

Passe à A pour le TP3.

## Slide 13, TP3 matrice des 32 contrôles, 1 minute 30 (B)

La matrice couvre 5 dimensions. 9 contrôles de complétude, par exemple event.title non vide, earthquake avec coordonnées renseignées. 5 contrôles d'unicité, PK unique, plus un contrôle de quasi-doublon pour les séismes, on considère qu'ils sont dupliqués s'ils sont dans la même minute, à moins de 0.1 degré et 0.1 magnitude près.

8 contrôles de validité, les URL doivent matcher https, les longitudes doivent être dans plus ou moins 180, les magnitudes doivent être dans moins 1 à 10. 5 contrôles de cohérence, un tsunami implique généralement une magnitude supérieure ou égale à 6.5, les dates ne doivent pas être dans le futur. 5 contrôles d'intégrité, chaque enfant doit avoir son parent, event_category vers event et vers category.

Techniquement, chaque contrôle est un appel à la fonction PL slash pgSQL audit_control. On lui passe un schéma, une table, une clause WHERE et une description, elle exécute deux COUNT et insère le résultat dans data_quality_report avec un run_id, une phase et un timestamp.

Passe à A pour les résultats.

## Slide 15, conclusion, 45 secondes (B)

Pour conclure. Sur le TP1 on a livré la cartographie complète et la base Postgres. Sur le TP2 on a industrialisé, 16 conteneurs orchestrés, deux dashboards auto-provisionnés, Metabase pour le métier et Grafana pour l'infra. Sur le TP3 on a formalisé l'audit qualité, 32 contrôles, 94 pour cent des anomalies résolues.

Le prof a besoin de deux commandes. start.sh pour démarrer toute la stack, run-audit.sh pour lancer l'audit qualité. Tout le reste, y compris les dashboards, se configure automatiquement.

Merci pour votre attention, on est disponibles pour vos questions.

## Notes de coordination

Avant la présentation, se caler sur qui clique la diapo. Suggéré, chacun clique quand il commence à parler.

Timing serré, 15 minutes pile pour 15 slides, environ 1 minute par slide. Le speaker B parle sur 7 slides plus l'intro conjointe, cumul environ 7 minutes 30.

Sur slide 7 et slide 11, ce sont mes deux passages les plus techniques, 1 minute 30 chacun. Bien respirer entre les phrases, ne pas courir.

Sur la conclusion, ne pas hésiter à ralentir, c'est la dernière impression que le prof garde.

Prévoir un plan B si la démo live échoue, on a des captures dans le repo au niveau de TP2 docs et TP3 docs.
