## 2. Sources de données

Nous utilisons une seule source l'api eonest de la nasa, dont nous exploitons plusieurs endpoints

### Fiche de la source

| Élément | Détail |
|---|---|
| Nom | EONET Earth Observatory Natural Event Tracker (API version 3) |
| Organisation / origine | NASA (Earth Observatory) |
| URL de la documentation | https://eonet.gsfc.nasa.gov/docs/v3 |
| URL de l'API | https://eonet.gsfc.nasa.gov/api/v3 |
| Format | JSON (également disponible en GeoJSON, RSS et Atom) |
| Nature | Semi-structurée : JSON imbriqué, avec des listes (catégories, sources, géométries) à l'intérieur de chaque événement |
| Mise à jour | quasi temps réel : par défaut l'api renvoie les événement actuellement ouvert |
| Date de récupération de notre échantillon | 24/09/2026 |

### Description

EONET est un référentiel de métadonnées sur les événements naturels (feux de forêt, tempêtes, volcans...). chaque événement a un titre un statut ouvert ou fermé une ou plusieurs catégories, une ou plusieurs sources d'information, et une ou plusieurs géométries (une date associée à un lieu, de type Point ou Polygon). Certains événements ont aussi une magnitude.

L'api permet de filtrer les événements par source, catégorie, statut, période, zone géographique (bbox) ou magnitude.

### Endpoints utilisés

| Endpoint | Contenu |
|---|---|
| `/events` | Les événements naturels (données principales) |
| `/categories` | Les types d'événements (par exemple wildfires, severeStorms) |
| `/sources` | Les organismes qui référencent les événements |
| `/layers` | Les services d'imagerie liés à chaque catégorie |
| `/magnitudes` | Les types de magnitude utilisables comme filtre |

### Limites à garder en tête

- La nasa précise que ces métadonnées ne constituent pas une source officielle pour des donnée spatiales ou temporelle précises.
- Les donnée évoluent : des événements s'ouvrent et se ferment. nous figeons donc un échantillon daté pour que le travail reste reproductible.
