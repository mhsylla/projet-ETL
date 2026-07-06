# Projet ETL & Data Science — Prédiction Coupe du Monde 2026

> Pipeline de données de bout en bout : de l'historique brut des matchs (1930–2022) à la prédiction du vainqueur 2026 par Intelligence Artificielle, le tout visualisé sur un Dashboard interactif.

---

## Objectif du Projet

Ce projet répond à une question analytique ambitieuse :

> **Est-il possible d'identifier les futurs favoris d'une Coupe du Monde à partir de l'historique sportif et géopolitique ?**

Pour y répondre, nous avons conçu un **Écosystème Data Complet** (Data Engineering -> Business Intelligence -> Data Science) divisé en 5 phases :
1. **Extract** : Récupération de données brutes sur Kaggle.
2. **Transform** : Nettoyage, harmonisation géopolitique et Feature Engineering avec Pandas.
3. **Load** : Création dynamique d'un Data Warehouse (SQLite) en Schéma en Étoile.
4. **Machine Learning** : Entraînement d'un modèle Random Forest (sans fuite de données) sur les données ELO historiques pour prédire l'édition 2026.
5. **Dashboarding** : Visualisation des "Insights" et des prédictions via Streamlit.

---

## Structure du Projet

```text
projet-ETL/
├── main.py                  # Orchestrateur du pipeline ETL + ML
├── scripts/
│   ├── extract.py           # Phase 1 : Extraction
│   ├── transform.py         # Phase 2 : Nettoyage & Feature Engineering
│   ├── load.py              # Phase 3 : Chargement SQLite
│   └── build_ml_dataset.py  # Création du dataset pour l'entraînement
├── data/
│   ├── raw/                 # Fichiers bruts (Kaggle)
│   ├── processed/           # Datasets nettoyés et prédictions IA
│   └── datawarehouse.db     # Base de données (Constellation de faits)
├── dashboard/
│   ├── app.py               # Point d'entrée de l'application Streamlit
│   └── pages/               # Pages analytiques et prédictives
├── notebooks/
│   └── 01_ml_prediction_2026.ipynb  # Modèle d'entraînement et prédiction
└── README.md
```

---

## Démarrage Rapide

### 1. Prérequis et Installation

```bash
# Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate

# Installer les dépendances
pip install pandas numpy scikit-learn streamlit plotly sqlalchemy
```

### 2. Lancer le Pipeline ETL et ML

Le script principal exécute automatiquement l'Extraction, la Transformation, le Chargement, et la création du Dataset Machine Learning :

```bash
python main.py
```
*Le script générera la base de données `data/datawarehouse.db` et le fichier d'entraînement `data/processed/ml_dataset_historical.csv`.*

### 3. Lancer le Dashboard Analytique

L'interface web permet d'explorer les données historiques et de consulter les prédictions finales de l'IA :

```bash
streamlit run dashboard/app.py
```

---

## Modélisation de Données (Schéma en Étoile)

Notre Data Warehouse repose sur une architecture optimisée pour la Business Intelligence (Constellation de faits) :

- **Tables de Dimensions (dénormalisées)** : `dim_team`, `dim_stadium`, `dim_edition`
- **Tables de Faits** : `fact_matches`, `fact_team_performance`, `fact_phase_performance`, `fact_head_to_head`

---

## Prédiction 2026 (Machine Learning)

### Méthodologie
- **Modèle** : `RandomForestClassifier`
- **Features Historiques** : Score ELO, Participations, Titres, Avantage du Pays Hôte.
- **Data Leakage** : Évité en calculant strictement les statistiques d'une équipe *avant* le début de chaque édition historique.

### Résultats (Top 3 des probabilités Top 4)
1. **États-Unis** (76.2%) - Fortement poussé par l'avantage statistique du pays organisateur.
2. **Mexique** (70.9%)
3. **Espagne** (70.6%)

*(Le cas très spécifique du Brésil, sanctionné par le modèle à cause de ses récents échecs en quart de finale malgré de fortes statistiques, est expliqué dans nos analyses comme un cas de surapprentissage "Outlier").*

---

## Dashboard (Business Intelligence)

L'application Streamlit contient 8 pages d'analyses approfondies :
1. Vue Globale (Exploration du Data Warehouse)
2. Évolution Offensive
3. Avantage de l'Organisateur
4. Cycles de Domination
5. Upsets et Surprises
6. Les Forteresses Inviolables
7. Matrice de Succès
8. **Prédictions 2026 (Résultats IA)**
