## 1. Présentation du sujet

### Thème

Environnement : le suivi des événements naturels dans le monde (feux de forêt, tempêtes, volcans...).

### Contexte

Nous avons choisi ce sujet parce que les événements naturels sont suivi en continu à l'échelle mondiale la nasa propose eonet (earth observatory natural event tracker) une api publique qui fourni des métadonnée d'événement naturel, mises à jour en quasi temps réel

Chaque événement est rattaché à une ou plusieurs catégories, à des sources, et à des positions datées. les données sont fournie en JSON (et GeoJSON) à noter : la nasa précise que ces donnée ne sont pas une source officielle pour des informations spatiales ou temporelle précises

### Problématique

Quand nous récupérons les données via l'api, nous obtenons du json imbriqué, où un même événement peut avoir plusieurs catégories, plusieurs sources et plusieurs géométries

Comment l'organiser en base relationnelle, propre et sans doublons, pour pouvoir l'interroger facilement (par exemple compter les événements ouverts par catégorie) ?

### Objectif

Partir de données réelles, les documenter (sources et dictionnaire), les modéliser (MCD et MLD), puis les implémenter dans PostgreSQL avec quelques données de test
