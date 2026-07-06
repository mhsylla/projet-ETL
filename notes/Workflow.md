## **Storytelling du projet : De l'histoire du football à la prédiction des favoris de la Coupe du Monde 2026**

### Contexte

Depuis 1930, la Coupe du Monde est le théâtre des plus grands exploits du football. Certaines sélections comme le Brésil, l'Allemagne ou l'Argentine ont marqué l'histoire par leur régularité, tandis que d'autres ont créé des surprises mémorables. Mais une question demeure : **est-il possible d'identifier les futurs favoris d'une Coupe du Monde à partir des données historiques ?**

Pour répondre à cette question, notre projet ne se limite pas à analyser des statistiques. Il met en œuvre un processus complet d'**ingénierie des données**, depuis l'intégration de plusieurs sources jusqu'à la construction d'un modèle de Machine Learning capable d'estimer les chances de succès des équipes lors de la Coupe du Monde 2026.

---

# La problématique

Les données relatives à la Coupe du Monde sont réparties dans plusieurs jeux de données, chacun apportant une vision différente :

- le premier contient des informations très détaillées sur les matchs (buts, arbitres, stades, entraîneurs, capitaines, statistiques de jeu, etc.) ;
    
- le second regroupe les informations historiques des éditions, des équipes et des classements, tout en intégrant les données préparatoires de la Coupe du Monde 2026.
    

Utilisés séparément, ces datasets ne permettent pas d'obtenir une vision globale. Notre objectif est donc de **les fusionner au sein d'un Data Warehouse grâce à un processus ETL**, afin de créer une base de données analytique unique.

---

# Phase 1 : ETL

## Extraction

Les données sont extraites des deux datasets.

Le premier apporte une vision **micro**, centrée sur chaque match.

Le second apporte une vision **macro**, décrivant les équipes, les éditions et l'évolution historique des compétitions.

---

## Transformation

Cette étape consiste à rendre les deux sources compatibles.

Les principales opérations sont :

- harmonisation des noms des pays (ex. Allemagne de l'Ouest → Allemagne) ;
    
- suppression des doublons ;
    
- traitement des valeurs manquantes ;
    
- uniformisation des formats de dates ;
    
- normalisation des noms de stades, compétitions et phases.
    

Une fois les données nettoyées, de nouveaux indicateurs sont calculés :

- nombre total de participations ;
    
- nombre de titres ;
    
- taux de victoire ;
    
- moyenne de buts marqués ;
    
- moyenne de buts encaissés ;
    
- différence de buts ;
    
- performances selon les phases du tournoi ;
    
- performance des pays organisateurs ;
    
- historique des confrontations ;
    
- évolution des performances au fil des éditions.
    

---

## Chargement

Les données sont ensuite organisées dans un entrepôt de données composé de tables de faits et de dimensions.

Par exemple :

Dimensions :

- Équipe
    
- Édition
    
- Match
    
- Stade
    
- Pays
    

Table de faits :

- résultats des matchs
    
- statistiques des équipes
    
- performances historiques
    

Cette architecture facilite les analyses multidimensionnelles et l'alimentation du modèle prédictif.

---

# Phase 2 : Analyse exploratoire

À partir de cette base consolidée, plusieurs questions peuvent être étudiées.

### Qui domine réellement l'histoire de la Coupe du Monde ?

Classement des équipes selon :

- le nombre de titres ;
    
- les finales disputées ;
    
- les demi-finales ;
    
- les participations.
    

---

### Le football est-il devenu plus offensif ?

Étude de :

- l'évolution des buts par match ;
    
- la répartition des scores selon les décennies.
    

---

### Quel est l'impact du pays organisateur ?

Comparer les performances :

- des équipes à domicile ;
    
- des équipes en déplacement.
    

---

### Existe-t-il des cycles de domination ?

Visualiser les périodes où certaines nations dominent avant de laisser place à de nouvelles générations.

---

### Les surprises deviennent-elles plus fréquentes ?

Comparer :

- classement FIFA ;
    
- résultat obtenu dans la compétition.
    

---

### Quels continents progressent le plus ?

Comparer les performances de :

- l'Europe ;
    
- l'Amérique du Sud ;
    
- l'Afrique ;
    
- l'Asie ;
    
- la CONCACAF.
    

---

### Quels facteurs expliquent le mieux les succès ?

Analyser l'influence de :

- l'expérience ;
    
- l'efficacité offensive ;
    
- la solidité défensive ;
    
- les performances récentes.
    

---

# Phase 3 : Création des variables pour le Machine Learning

À partir du Data Warehouse, une nouvelle table est construite où chaque ligne représente une sélection nationale avant une édition de la Coupe du Monde.

Exemple :

|Équipe|Année|Participations|Titres|Victoires (%)|Buts marqués/match|Buts encaissés/match|Classement FIFA|Pays hôte|Champion|
|---|---|---|---|---|---|---|---|---|---|

Cette table constitue le jeu d'entraînement du modèle.

---

# Phase 4 : Modélisation prédictive

L'objectif est de prédire quelles équipes ont le plus de chances :

- d'atteindre les demi-finales ;
    
- d'atteindre la finale ;
    
- ou de remporter la Coupe du Monde.
    

Plusieurs algorithmes pourront être comparés :

- Régression Logistique ;
    
- Random Forest ;
    
- XGBoost ;
    
- LightGBM.
    

Les performances seront évaluées à l'aide de métriques adaptées (Accuracy, F1-score, ROC-AUC, etc.).

---

# Phase 5 : Interprétation des résultats

Au-delà des prédictions, il est essentiel de comprendre les facteurs qui influencent le plus les résultats du modèle.

L'analyse de l'importance des variables permettra de répondre à des questions telles que :

- Le classement FIFA est-il réellement un bon indicateur ?
    
- L'expérience dans la compétition est-elle déterminante ?
    
- Une défense solide pèse-t-elle davantage qu'une attaque performante ?
    
- L'avantage de jouer à domicile influence-t-il encore les résultats ?
    

Ces réponses offriront une interprétation des mécanismes qui conduisent au succès dans une Coupe du Monde.

---

# Perspective

Ce projet ne vise pas uniquement à analyser le passé, mais à transformer les données historiques en un outil d'aide à la décision. En combinant deux sources complémentaires grâce à un processus ETL, il construit une base analytique robuste sur laquelle s'appuie un modèle de Machine Learning. À terme, ce modèle pourra estimer les probabilités de succès des équipes qualifiées pour la Coupe du Monde 2026 et produire un classement des favoris. Il pourra ensuite être enrichi avec des données plus récentes (forme des équipes, résultats des éliminatoires, statistiques individuelles des joueurs ou cotes des bookmakers) afin d'améliorer encore la qualité des prédictions. Cette approche illustre une chaîne complète de valorisation des données, allant de leur intégration à la création d'un système prédictif orienté vers la prise de décision.