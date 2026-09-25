# Entités, attributs, relations et cardinalités — EONET & USGS

Sources :
- EONET : https://eonet.gsfc.nasa.gov/docs/v3
- USGS : https://earthquake.usgs.gov/fdsnws/event/1/

---

## 1. Entités et attributs

**EVENT** (EONET)
- `id`
- `title`
- `description`
- `link`
- `closed`

**CATEGORY** (EONET)
- `id`
- `title`
- `description`

**SOURCE** (EONET)
- `id`
- `url`

**GEOMETRY** (EONET)
- `geometry_id`
- `date`
- `type`
- `coordinates`

**EARTHQUAKE** (USGS)
- `id`
- `time`
- `magnitude`
- `mag_type`
- `place`
- `longitude`
- `latitude`
- `depth_km`
- `tsunami`
- `significance`
- `url`

**Justification** : chaque entité correspond à un objet métier identifiable, avec son propre identifiant et sa logique d'existence indépendante. EVENT, CATEGORY, SOURCE et GEOMETRY proviennent d'EONET ; EARTHQUAKE provient de l'USGS.

---

## 2. Relations et cardinalités

```text
EVENT 1 ───── N GEOMETRY
```
**Justification** : un événement est suivi dans le temps par plusieurs points de localisation datés au fur et à mesure de son évolution. Un point de géométrie n'a de sens que rattaché à un seul événement.

```text
EVENT N ───── N CATEGORY
```
**Justification** : un événement peut appartenir à plusieurs catégories, et une catégorie regroupe plusieurs événements. Le champ `categories` de l'API est une liste.

```text
EVENT N ───── N SOURCE
```
**Justification** : un événement peut être rapporté par plusieurs organismes, et une source alimente plusieurs événements. Le champ `sources` de l'API est une liste.

```text
EVENT N ───── N EARTHQUAKE
```
**Justification** : c'est le lien métier entre les deux sources. Un événement EONET (notamment volcanique) peut être rapproché de plusieurs séismes USGS proches en lieu et en date, et un séisme peut concerner plusieurs événements d'une même zone. Le rapprochement est calculé sur des critères spatio-temporels (distance et écart de temps).

---

## 3. Point d'attention pour la modélisation logique

Les trois relations N ↔ N deviennent des tables de jonction au niveau du modèle logique :
- `EVENT_CATEGORY`
- `EVENT_SOURCE`
- `EVENT_EARTHQUAKE` (porte en plus les attributs `distance_km` et `delay_hours` issus du calcul d'agrégation)
