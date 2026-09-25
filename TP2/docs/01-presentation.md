## 1. Présentation du sujet

### Thème

Environnement : le suivi des événements naturels dans le monde (feux de forêt, tempêtes, volcans, séismes...).

### Contexte

Ce TP2 prolonge le TP1. Dans le TP1 nous avions cartographié et modélisé une source unique, l'API EONET de la NASA (Earth Observatory Natural Event Tracker), qui fournit des métadonnées d'événements naturels mises à jour en quasi temps réel.

Pour le TP2 nous ajoutons une seconde source, le web service FDSN de l'USGS, qui fournit un catalogue mondial de séismes. L'objectif est de construire une plateforme data automatisée qui collecte, agrège, stocke, traite et expose les données des deux sources.

### Problématique

Les deux sources décrivent des risques naturels localisés et datés, mais avec des formats et des périmètres différents. EONET couvre surtout les feux, tempêtes et volcans ; l'USGS couvre les séismes.

Comment rapprocher ces deux sources dans un modèle relationnel propre, sans doublons, pour pouvoir croiser les événements EONET et l'activité sismique proche dans le temps et l'espace (par exemple des séismes autour d'un volcan actif) ?

### Objectif

Partir de deux sources réelles, les documenter (sources et dictionnaire), les modéliser (MCD et MLD) en intégrant leur lien métier, puis les implémenter dans PostgreSQL au sein d'un pipeline reproductible.
