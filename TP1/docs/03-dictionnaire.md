# Dictionnaire de données — NASA EONET API v3

Source : https://eonet.gsfc.nasa.gov/docs/v3
Périmètre : endpoints `/events`, `/categories`, `/sources`

---

## Entité : EVENT

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Responsable | Exemple |
|---|---|---|---|---|---|---|---|---|---|
| `id` | Identifiant événement | Identifiant unique de l'événement naturel | VARCHAR | Non | Format `EONET_xxxxx` | API EONET `/events` | Publique | Équipe data | `EONET_6501` |
| `title` | Titre | Nom court décrivant l'événement | VARCHAR(255) | Non | Texte libre | API EONET `/events` | Publique | Équipe data | `Wildfire - Los Angeles County, California` |
| `description` | Description | Description détaillée de l'événement | TEXT | Oui | Texte libre | API EONET `/events` | Publique | Équipe data | `null` (souvent vide dans EONET) |
| `link` | Lien détail | URL vers la fiche complète de l'événement sur EONET | VARCHAR(255) | Non | URL valide | API EONET `/events` | Publique | Équipe data | `https://eonet.gsfc.nasa.gov/api/v3/events/EONET_6501` |
| `closed` | Date de clôture | Date à laquelle l'événement a été considéré comme terminé | DATE | Oui | Format `YYYY-MM-DD` ou `null` si événement en cours | API EONET `/events` | Publique | Équipe data | `null` (événement ouvert) |

---

## Entité : CATEGORY

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Responsable | Exemple |
|---|---|---|---|---|---|---|---|---|---|
| `id` | Identifiant catégorie | Identifiant unique du type d'événement | VARCHAR | Non | `wildfires`, `severeStorms`, `volcanoes`, `floods`, `earthquakes`, `seaLakeIce`, `landslides`, `drought`, `dustHaze`, `snow`, `tempExtremes`, `waterColor`, `manmade` | API EONET `/categories` | Publique | Équipe data | `wildfires` |
| `title` | Libellé catégorie | Nom lisible de la catégorie | VARCHAR(100) | Non | Texte contrôlé | API EONET `/categories` | Publique | Équipe data | `Wildfires` |
| `description` | Description catégorie | Explication du périmètre de la catégorie | TEXT | Oui | Texte libre | API EONET `/categories` | Publique | Équipe data | `Wildfires includes all nature of fire...` |

---

## Entité : SOURCE

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Responsable | Exemple |
|---|---|---|---|---|---|---|---|---|---|
| `id` | Identifiant fournisseur | Identifiant de l'organisme ayant remonté l'événement | VARCHAR | Non | Ex : `InciWeb`, `USGS_EHP`, `GDACS`, `NWS` | API EONET `/sources` | Publique | Équipe data | `InciWeb` |
| `url` | URL source | Lien vers le site de l'organisme source | VARCHAR(255) | Non | URL valide | API EONET `/sources` | Publique | Équipe data | `https://inciweb.wildfire.gov` |

---

## Entité : GEOMETRY (point de localisation daté d'un event)

| Nom technique | Nom métier | Description | Type / Taille | Nullable ? | Valeurs autorisées | Source | Sensibilité | Responsable | Exemple |
|---|---|---|---|---|---|---|---|---|---|
| `date` | Date d'observation | Horodatage de la position enregistrée | TIMESTAMP | Non | Format ISO 8601 | API EONET `/events` (sous-objet `geometry`) | Publique | Équipe data | `2026-09-10T18:00:00Z` |
| `type` | Type géométrique | Type de géométrie GeoJSON | VARCHAR | Non | `Point`, `Polygon` | API EONET `/events` (sous-objet `geometry`) | Publique | Équipe data | `Point` |
| `coordinates` | Coordonnées | Position géographique (longitude, latitude) | FLOAT[2] | Non | Coordonnées GPS valides | API EONET `/events` (sous-objet `geometry`) | Publique | Équipe data | `[-118.24, 34.05]` |

---

## Notes d'audit

- Toutes les données EONET sont **publiques et non sensibles** (données géophysiques, aucune donnée personnelle).
- `closed` est la clé de lecture du statut d'un événement (ouvert vs terminé) — pas de champ `status` explicite dans le payload brut.
- Un `event` peut avoir **plusieurs points `geometry`** dans le temps (un incendie qui se déplace, une tempête qui évolue) → relation 1 → N à modéliser.
- Un `event` peut avoir **plusieurs `categories`** et **plusieurs `sources`** → relations N → N potentielles à confirmer selon les cas réels observés dans l'API.
