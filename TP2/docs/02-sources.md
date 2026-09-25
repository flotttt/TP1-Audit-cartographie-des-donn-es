## 2. Sources de données

Nous utilisons deux sources complémentaires : l'API EONET de la NASA (source principale, déjà exploitée au TP1) et le web service FDSN de l'USGS (nouvelle source pour le TP2).

### Source 1 — API EONET (NASA)

| Élément | Détail |
|---|---|
| Nom | EONET Earth Observatory Natural Event Tracker (API version 3) |
| Organisation / origine | NASA (Earth Observatory) |
| URL de la documentation | https://eonet.gsfc.nasa.gov/docs/v3 |
| URL de l'API | https://eonet.gsfc.nasa.gov/api/v3 |
| Format | JSON (également disponible en GeoJSON, RSS et Atom) |
| Nature | Semi-structurée : JSON imbriqué, avec des listes (catégories, sources, géométries) à l'intérieur de chaque événement |
| Mise à jour | Quasi temps réel : par défaut l'API renvoie les événements actuellement ouverts |
| Rôle dans le projet | Source principale des événements naturels, alimentée en continu via Kafka |

Endpoints utilisés :

| Endpoint | Contenu |
|---|---|
| `/events` | Les événements naturels (données principales) |
| `/categories` | Les types d'événements (par exemple wildfires, severeStorms) |
| `/sources` | Les organismes qui référencent les événements |

### Source 2 — Web service FDSN (USGS)

| Élément | Détail |
|---|---|
| Nom | USGS Earthquake Catalog (FDSN event web service) |
| Organisation / origine | United States Geological Survey (USGS) |
| URL de la documentation | https://earthquake.usgs.gov/fdsnws/event/1/ |
| URL des feeds temps réel | https://earthquake.usgs.gov/earthquakes/feed/ |
| Format | GeoJSON (également CSV, QuakeML) |
| Nature | Semi-structurée : GeoJSON FeatureCollection, une feature par séisme |
| Mise à jour | Temps réel, feeds rafraîchis chaque minute |
| Rôle dans le projet | Enrichir la vision des risques naturels avec l'activité sismique |

Paramètres de requête utilisés : `starttime`, `endtime`, `minmagnitude`, `bbox`, `format=geojson`.

### Lien métier entre les deux sources

Les deux sources décrivent des événements naturels localisés (coordonnées) et datés. Le rapprochement se fait donc sur une base **spatio-temporelle** : pour un événement EONET donné, on identifie les séismes USGS survenus à proximité et dans une fenêtre de temps proche.

Ce rapprochement a un sens géophysique fort pour les volcans (l'activité volcanique s'accompagne souvent d'essaims sismiques), et plus largement il permet d'analyser conjointement plusieurs risques naturels sur une même zone et une même période.

### Limites à garder en tête

- La NASA précise que les métadonnées EONET ne constituent pas une source officielle pour des données spatiales ou temporelles précises.
- Les deux sources évoluent en continu : nous figeons des échantillons datés pour que le travail reste reproductible.
- Les deux sources sont des API. Le critère du TP est respecté car elles sont complémentaires et présentent un lien métier exploitable ; dans le pipeline, EONET est consommée en continu via Kafka et l'USGS est collectée comme flux GeoJSON.
