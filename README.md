#  Projet ETL — Prédiction Coupe du Monde 2026

> Pipeline de données complet : de l'historique des matchs de football (1930–2022) à un Data Warehouse prêt pour le Machine Learning.

---

##  Objectif du Projet

Ce projet répond à une question analytique ambitieuse :

> **Est-il possible d'identifier les futurs favoris d'une Coupe du Monde à partir des données historiques ?**

Pour y répondre, nous avons conçu un pipeline **ETL complet** (Extract → Transform → Load) qui :
1. **Extrait** des données brutes provenant de deux sources CSV distinctes
2. **Transforme** ces données en nettoyant, harmonisant et calculant des indicateurs prédictifs
3. **Charge** le tout dans un Data Warehouse SQLite structuré en **Schéma en Étoile**, prêt pour l'analyse et le Machine Learning

---

##  Structure du Projet

```
projet-ETL/
├── main.py                  # Orchestrateur du pipeline complet
├── scripts/
│   ├── extract.py           # Phase 1 : Extraction des données brutes
│   ├── transform.py         # Phase 2 : Nettoyage & Feature Engineering
│   └── load.py              # Phase 3 : Chargement dans le Data Warehouse
├── data/
│   ├── raw/
│   │   ├── matches/         # Données matchs (1930–2022, classement FIFA...)
│   │   └── compets/         # Données compétitions (historique, H2H, équipes 2026...)
│   └── datawarehouse.db     #  Base SQLite générée par le pipeline
├── notebooks/               # Analyses exploratoires (EDA)
└── README.md
```

---

##  Lancer le Pipeline

### Prérequis

```bash
# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install pandas numpy
```

### Exécution complète

```bash
python main.py
```

**Sortie attendue :**
```
===================================
 DÉMARRAGE DU PIPELINE ETL
===================================

[1/3] Phase d'Extraction...
[2/3] Phase de Transformation...
[3/3] Phase de Chargement...

 Dimension chargée : dim_team (83 lignes)
 Dimension chargée : dim_edition (22 lignes)
 Dimension chargée : dim_stadium (...)
 Fait chargé : fact_matches (1015 lignes)
 Fait chargé : fact_team_performance (...)
 Fait chargé : fact_phase_performance (...)

 Data Warehouse généré avec succès dans : data/datawarehouse.db
===================================
 PIPELINE ETL TERMINÉ
===================================
```

---

##  Documentation Détaillée par Phase

Chaque phase dispose de sa propre documentation technique :

| Phase | Script | Documentation |
|---|---|---|
| **1 — Extract** | `scripts/extract.py` | [ README Extract](scripts/README_extract.md) |
| **2 — Transform** | `scripts/transform.py` | [ README Transform](scripts/README_transform.md) |
| **3 — Load** | `scripts/load.py` | [ README Load](scripts/README_load.md) |

---

##  Sources de Données

| Dossier | Contenu |
|---|---|
| `data/raw/matches/` | Matchs internationaux 1930–2022, classement FIFA, résultats Coupe du Monde |
| `data/raw/compets/` | Statistiques historiques, head-to-head, données équipes 2026, groupes CdM 2026 |

---

##  Architecture du Data Warehouse

Le Data Warehouse final (`data/datawarehouse.db`) suit un **Schéma en Étoile** :

```
                      ┌──────────────┐
                      │  dim_edition │
                      │  (22 éditions│
                      │   CdM)       │
                      └──────┬───────┘
                             │
┌──────────────┐    ┌────────▼────────┐    ┌───────────────────┐
│  dim_stadium │───│  fact_matches   │◀───│     dim_team      │
│  (stades)    │    │  (1015 matchs)  │    │  (83 équipes +    │
└──────────────┘    └────────┬────────┘    │   stats globales) │
                             │             └─────────┬─────────┘
                             │                       │
                    ┌────────▼────────┐   ┌──────────▼──────────┐
                    │fact_team_perf   │   │ fact_phase_perf      │
                    │(stats offens./  │   │ (perf. par phase     │
                    │ défens. / équipe│   │  du tournoi)         │
                    └─────────────────┘   └─────────────────────┘
```

---

##  Indicateurs Calculés (Feature Engineering)

| Indicateur | Description |
|---|---|
| `win_rate` | Taux de victoire global (corrigé : victoires / matchs joués) |
| `goals_per_game` | Buts marqués par match |
| `conceded_per_game` | Buts encaissés par match |
| `goal_diff` | Différence de buts globale |
| `titles` | Nombre de Coupes du Monde remportées |
| `phase_performance` | Nombre de matchs joués par phase (Groupes, 1/8, 1/4, Finale...) |
| `home_advantage_index` | Indice d'avantage à domicile global |

---

##  Étapes Suivantes

- **Phase 2 : Analyse Exploratoire (EDA)** — Visualisations dans les notebooks
- **Phase 3 : Machine Learning** — Modèle de prédiction des favoris CdM 2026
