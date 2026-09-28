# Matrice de contrôles qualité

Chaque contrôle produit une ligne dans `data_quality_report`, avec `total_rows`, `failing_rows` et `fail_rate`.

## Dimensions

| Dimension | Question posée |
|---|---|
| **Complétude** | Les champs obligatoires sont-ils renseignés ? |
| **Unicité** | Y a-t-il des doublons (stricts ou fuzzy) ? |
| **Validité** | Les valeurs respectent-elles les règles de format / bornes ? |
| **Cohérence** | Les valeurs sont-elles logiques entre elles / dans le temps ? |
| **Intégrité** | Les références (FK) pointent-elles vers des lignes existantes ? |

## Matrice

| ID | Dimension | Table | Contrôle | Règle en échec | Criticité |
|---|---|---|---|---|---|
| **C01** | Complétude | `event` | Titre présent | `title IS NULL OR btrim(title) = ''` | 🔴 Haute |
| **C02** | Complétude | `event` | Description présente | `description IS NULL` | 🟢 Faible (informatif) |
| **C03** | Complétude | `event` | Lien présent | `link IS NULL` | 🔴 Haute |
| **C04** | Complétude | `earthquake` | Magnitude présente | `magnitude IS NULL` | 🟠 Moyenne |
| **C05** | Complétude | `earthquake` | Type de magnitude présent | `mag_type IS NULL` | 🟢 Faible |
| **C06** | Complétude | `earthquake` | Lieu présent | `place IS NULL` | 🟢 Faible |
| **C07** | Complétude | `earthquake` | Profondeur présente | `depth_km IS NULL` | 🟢 Faible |
| **C08** | Complétude | `earthquake` | Coordonnées présentes | `longitude IS NULL OR latitude IS NULL` | 🔴 Haute |
| **C09** | Complétude | `geometry` | Coordonnées présentes | `coordinates IS NULL` | 🔴 Haute |
| **U01** | Unicité | `event` | PK unique | `id` en doublon | 🔴 Haute |
| **U02** | Unicité | `earthquake` | PK unique | `id` en doublon | 🔴 Haute |
| **U03** | Unicité | `earthquake` | Pas de quasi-doublon | Même minute + ±0.1° + ±0.1 mag | 🟠 Moyenne |
| **U04** | Unicité | `category` | PK unique | `id` en doublon | 🟠 Moyenne |
| **U05** | Unicité | `source` | PK unique | `id` en doublon | 🟠 Moyenne |
| **V01** | Validité | `event` | URL bien formée | `link !~ '^https?://'` | 🔴 Haute |
| **V02** | Validité | `source` | URL bien formée | `url !~ '^https?://'` | 🔴 Haute |
| **V03** | Validité | `earthquake` | Longitude dans bornes | `longitude ∉ [-180, 180]` | 🔴 Haute |
| **V04** | Validité | `earthquake` | Latitude dans bornes | `latitude ∉ [-90, 90]` | 🔴 Haute |
| **V05** | Validité | `earthquake` | Magnitude plausible | `magnitude ∉ [-1, 10]` | 🔴 Haute |
| **V06** | Validité | `earthquake` | Profondeur ≥ 0 | `depth_km < 0` | 🟠 Moyenne |
| **V07** | Validité | `geometry` | Type reconnu | `type ∉ {'Point', 'Polygon'}` | 🟠 Moyenne |
| **V08** | Validité | `geometry` | Coordonnées Point valides | Point avec tableau ≠ 2 valeurs | 🔴 Haute |
| **Co01** | Cohérence | `event` | Fermeture après le début | `closed < min(geometry.date)` | 🟠 Moyenne |
| **Co02** | Cohérence | `earthquake` | Tsunami cohérent | `tsunami=true AND magnitude < 6.5` | 🟢 Faible |
| **Co03** | Cohérence | `earthquake` | Date pas dans le futur | `time > now() + 1j` | 🟠 Moyenne |
| **Co04** | Cohérence | `earthquake` | Date dans la fenêtre USGS | `time < now() - 365j` | 🟢 Faible |
| **Co05** | Cohérence | `event` | Fermeture pas dans le futur | `closed > now() + 1j` | 🟠 Moyenne |
| **I01** | Intégrité | `event_category` | FK vers `event` valide | Aucun event correspondant | 🔴 Haute |
| **I02** | Intégrité | `event_category` | FK vers `category` valide | Aucune category correspondante | 🔴 Haute |
| **I03** | Intégrité | `event_source` | FK vers `event` valide | Aucun event correspondant | 🔴 Haute |
| **I04** | Intégrité | `event_source` | FK vers `source` valide | Aucune source correspondante | 🔴 Haute |
| **I05** | Intégrité | `geometry` | FK vers `event` valide | Aucun event correspondant | 🔴 Haute |

**Total : 32 contrôles** (9 complétude, 5 unicité, 8 validité, 5 cohérence, 5 intégrité).

## Interprétation

- Un contrôle est en **échec** dès que `failing_rows > 0`.
- Le `fail_rate` = `failing_rows / total_rows` donne une mesure normalisée entre 0 et 1.
- Un contrôle à **criticité Haute** en échec = donnée non chargeable en `public.*` (bloquée par les CHECK / FK Postgres → filtrée par Spark).
- Un contrôle à criticité Moyenne/Faible en échec = donnée chargeable mais qualité dégradée (imputation recommandée).
