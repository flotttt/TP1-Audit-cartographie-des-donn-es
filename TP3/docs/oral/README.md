# Support de présentation orale, 15 minutes, 2 speakers

Trois fichiers à utiliser ensemble.

`diapo.md`, le deck à projeter. 15 slides, format Marp. Un slide par minute environ.

`speaker-A.md`, script complet et timings pour la personne A. 8 prises de parole, cumul environ 7 minutes 30.

`speaker-B.md`, script complet et timings pour la personne B. 7 prises de parole plus intro conjointe, cumul environ 7 minutes 30.

## Comment rendre le deck visible

Le format `diapo.md` est du Marp. Plusieurs options.

Option 1, extension VS Code Marp for VS Code, ouvrir `diapo.md`, cliquer sur l'icône presentation.

Option 2, CLI Marp, `npx @marp-team/marp-cli --html diapo.md --output diapo.html`, puis ouvrir le HTML dans un navigateur.

Option 3, export PDF, `npx @marp-team/marp-cli --pdf diapo.md`.

## Structure des 15 slides et alternance

| # | Slide | Speaker | Durée |
|---|---|---|---|
| 1 | Titre et intro conjointe | A puis B | 30 s |
| 2 | Sujet et problématique | A | 1 min |
| 3 | Les deux sources en détail | B | 1 min |
| 4 | TP1 modélisation | A | 1 min |
| 5 | TP1 base PostgreSQL | B | 1 min |
| 6 | TP2 architecture cible | A | 1 min 30 |
| 7 | TP2 ingestion Kafka | B | 1 min |
| 8 | TP2 Data Lake S3 | A | 1 min |
| 9 | TP2 traitement PySpark | B | 1 min 30 |
| 10 | TP2 data viz Metabase | A | 1 min |
| 11 | TP2 monitoring et Raw vs Clean | B | 1 min 30 |
| 12 | TP3 problématique | A | 1 min 15 |
| 13 | TP3 matrice des 32 contrôles | B | 1 min 30 |
| 14 | TP3 résultats avant et après | A | 1 min 30 |
| 15 | Conclusion | B | 45 s |

Total, 15 minutes pile.

## Conseils de coordination

Se répartir les rôles avant, A et B. Un des deux clique la diapo, ou chacun clique quand il commence à parler.

Éviter les recouvrements de voix. Une pause de 2 secondes entre les passes suffit pour éviter les blancs et garder du rythme.

Si une démo live est prévue, la caler sur slide 8 (Data Lake) ou slide 10 (Metabase) ou slide 14 (query SQL sur data_quality_report). Prévoir des captures d'écran de secours.

Ne pas oublier de respirer et de ralentir sur les slides à 1 minute 30, ce sont les plus denses.

## Backup si la démo live échoue

Captures utiles à préparer, http localhost 3000 slash dashboard slash 2 (Metabase), http localhost 3001 slash d slash tp2-pipeline (Grafana), résultat de docker exec tp-db psql -U eonet -d eonet -c pour la table data_quality_report.
