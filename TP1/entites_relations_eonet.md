# Entités, attributs, relations et cardinalités — NASA EONET API

Source : https://eonet.gsfc.nasa.gov/docs/v3

---

## 1. Entités et attributs

**EVENT**
- `id`
- `title`
- `description`
- `link`
- `closed`

**CATEGORY**
- `id`
- `title`
- `description`

**SOURCE**
- `id`
- `url`

**GEOMETRY_POINT**
- `date`
- `type`
- `coordinates`

**Justification** : ce sont les 4 objets métier identifiables distinctement dans le payload EONET — chacun a son propre identifiant ou sa propre logique d'existence indépendante.

---

## 2. Relations et cardinalités

```text
EVENT 1 ───── N GEOMETRY_POINT
```
**Justification** : un événement (ex : un incendie) est suivi dans le temps par plusieurs points de localisation datés au fur et à mesure de son évolution géographique. Un point de géométrie n'a de sens que rattaché à un seul événement → relation de composition claire.

```text
EVENT N ───── N CATEGORY
```
**Justification** : un événement peut appartenir à plusieurs catégories à la fois (ex : un événement combinant feu + fumée), et une catégorie regroupe forcément plusieurs événements. Le champ `categories` dans l'API est bien une liste.

```text
EVENT N ───── N SOURCE
```
**Justification** : un événement peut être rapporté par plusieurs organismes en parallèle (ex : USGS + GDACS sur un même séisme), et une même source alimente de nombreux événements. Le champ `sources` est aussi une liste dans l'API.

---

## 3. Point d'attention pour la modélisation logique

Les deux relations N↔N (`EVENT-CATEGORY` et `EVENT-SOURCE`) devront devenir des **tables de jonction** au niveau du modèle logique :
- `EVENT_CATEGORY`
- `EVENT_SOURCE`
