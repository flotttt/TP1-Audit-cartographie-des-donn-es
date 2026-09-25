# Dictionnaire de données — EONET (NASA) & USGS

Sources :
- EONET : https://eonet.gsfc.nasa.gov/docs/v3 — endpoints `/events`, `/categories`, `/sources`
- USGS : https://earthquake.usgs.gov/fdsnws/event/1/ — web service FDSN (GeoJSON)

---

## Entité : EVENT

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Exemple |
|---|---|---|---|---|---|---|---|---|
| `id` | Identifiant événement | Identifiant unique de l'événement naturel | VARCHAR | Non | Format `EONET_xxxxx` | EONET `/events` | Publique | `EONET_6501` |
| `title` | Titre | Nom court décrivant l'événement | VARCHAR(255) | Non | Texte libre | EONET `/events` | Publique | `Wildfire - Los Angeles County, California` |
| `description` | Description | Description détaillée de l'événement | TEXT | Oui | Texte libre | EONET `/events` | Publique | `null` (souvent vide dans EONET) |
| `link` | Lien détail | URL vers la fiche complète de l'événement | VARCHAR(255) | Non | URL valide | EONET `/events` | Publique | `https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6501` |
| `closed` | Date de clôture | Horodatage de clôture de l'événement | TIMESTAMPTZ | Oui | ISO 8601 ou `null` si en cours | EONET `/events` | Publique | `null` (événement ouvert) |

---

## Entité : CATEGORY

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Exemple |
|---|---|---|---|---|---|---|---|---|
| `id` | Identifiant catégorie | Identifiant unique du type d'événement | VARCHAR | Non | `wildfires`, `severeStorms`, `volcanoes`, `floods`, `earthquakes`, `seaLakeIce`, `landslides`, `drought`, `dustHaze`, `snow`, `tempExtremes`, `waterColor`, `manmade` | EONET `/categories` | Publique | `wildfires` |
| `title` | Libellé catégorie | Nom lisible de la catégorie | VARCHAR(100) | Non | Texte contrôlé | EONET `/categories` | Publique | `Wildfires` |
| `description` | Description catégorie | Explication du périmètre de la catégorie | TEXT | Oui | Texte libre | EONET `/categories` | Publique | `Wildfires includes all nature of fire...` |

---

## Entité : SOURCE

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Exemple |
|---|---|---|---|---|---|---|---|---|
| `id` | Identifiant fournisseur | Identifiant de l'organisme ayant remonté l'événement | VARCHAR | Non | Ex : `InciWeb`, `GDACS`, `NWS` | EONET `/sources` | Publique | `InciWeb` |
| `url` | URL source | Lien vers le site de l'organisme source | VARCHAR(255) | Non | URL valide | EONET `/sources` | Publique | `https://inciweb.wildfire.gov` |

---

## Entité : GEOMETRY

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Exemple |
|---|---|---|---|---|---|---|---|---|
| `geometry_id` | Identifiant géométrie | Identifiant technique du point d'observation | SERIAL | Non | Auto-incrément | Généré | Publique | `1` |
| `event_id` | Événement rattaché | Référence vers l'événement EONET | VARCHAR | Non | FK vers `event` | Généré | Publique | `EONET_6501` |
| `date` | Date d'observation | Horodatage de la position enregistrée | TIMESTAMPTZ | Non | ISO 8601 | EONET `/events` (sous-objet `geometry`) | Publique | `2026-09-10T18:00:00Z` |
| `type` | Type géométrique | Type de géométrie GeoJSON | VARCHAR(20) | Non | `Point`, `Polygon` | EONET `/events` (sous-objet `geometry`) | Publique | `Point` |
| `coordinates` | Coordonnées | Position géographique (longitude, latitude) | JSONB | Non | Tableau GeoJSON valide | EONET `/events` (sous-objet `geometry`) | Publique | `[-118.24, 34.05]` |

---

## Entité : EARTHQUAKE (source USGS)

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Exemple |
|---|---|---|---|---|---|---|---|---|
| `id` | Identifiant séisme | Identifiant unique du séisme | VARCHAR | Non | Code USGS | USGS `feature.id` | Publique | `us7000pn9k` |
| `time` | Date du séisme | Horodatage de l'événement sismique | TIMESTAMPTZ | Non | ISO 8601 (converti depuis epoch ms) | USGS `properties.time` | Publique | `2026-09-15T06:12:00Z` |
| `magnitude` | Magnitude | Magnitude mesurée | NUMERIC(4,2) | Oui | Env. -1 à 10 | USGS `properties.mag` | Publique | `5.40` |
| `mag_type` | Type de magnitude | Méthode de mesure de la magnitude | VARCHAR(20) | Oui | `mb`, `ml`, `mw`, `md`... | USGS `properties.magType` | Publique | `mww` |
| `place` | Localisation | Description textuelle du lieu | TEXT | Oui | Texte libre | USGS `properties.place` | Publique | `120 km SSW of Kokopo, Papua New Guinea` |
| `longitude` | Longitude | Longitude de l'épicentre | NUMERIC(9,5) | Non | -180 à 180 | USGS `geometry.coordinates[0]` | Publique | `152.06400` |
| `latitude` | Latitude | Latitude de l'épicentre | NUMERIC(8,5) | Non | -90 à 90 | USGS `geometry.coordinates[1]` | Publique | `-4.36700` |
| `depth_km` | Profondeur | Profondeur du foyer en km | NUMERIC(7,3) | Oui | >= 0 | USGS `geometry.coordinates[2]` | Publique | `35.000` |
| `tsunami` | Alerte tsunami | Indicateur de risque tsunami | BOOLEAN | Non | `true` / `false` | USGS `properties.tsunami` | Publique | `false` |
| `significance` | Importance | Score d'importance de l'événement | INTEGER | Oui | >= 0 | USGS `properties.sig` | Publique | `449` |
| `url` | Lien détail | URL vers la fiche USGS du séisme | VARCHAR(255) | Oui | URL valide | USGS `properties.url` | Publique | `https://earthquake.usgs.gov/earthquakes/eventpage/us7000pn9k` |

---

## Entité : EVENT_EARTHQUAKE (rapprochement)

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Exemple |
|---|---|---|---|---|---|---|---|---|
| `event_id` | Événement EONET | Référence vers l'événement | VARCHAR | Non | FK vers `event` | Calculé (agrégation) | Publique | `EONET_6501` |
| `earthquake_id` | Séisme USGS | Référence vers le séisme | VARCHAR | Non | FK vers `earthquake` | Calculé (agrégation) | Publique | `us7000pn9k` |
| `distance_km` | Distance | Distance entre l'événement et l'épicentre | NUMERIC(8,2) | Oui | >= 0 | Calculé (PySpark) | Publique | `42.30` |
| `delay_hours` | Écart temporel | Écart de temps entre les deux événements | NUMERIC(8,2) | Oui | Texte libre | Calculé (PySpark) | Publique | `12.50` |

---

## Notes d'audit

- Toutes les données EONET et USGS sont **publiques et non sensibles** (données géophysiques, aucune donnée personnelle).
- `closed` (EONET) est modélisée en `TIMESTAMPTZ` et non en `DATE` : le payload fournit un horodatage complet.
- `coordinates` (EONET) est stockée en `JSONB` et non en tableau de floats : cela permet de gérer indifféremment un `Point` et un `Polygon`.
- Un `event` EONET peut avoir plusieurs `geometry` dans le temps → relation 1 → N.
- Un `event` EONET peut avoir plusieurs `categories` et plusieurs `sources` → relations N → N (tables de jonction).
- Le rapprochement `event` ↔ `earthquake` est une relation N → N calculée sur des critères spatio-temporels lors de l'étape d'agrégation.
